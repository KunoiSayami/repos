#!/usr/bin/env python3
# Copyright (C) 2021 KunoiSayami and contributors
#
# This module is part of KunoiSayami/repos and is released under
# the AGPL v3 License: https://www.gnu.org/licenses/agpl-3.0.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import argparse
import asyncio
import logging
import re

from collections.abc import Coroutine
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiohttp

MAX_WORKERS = 32


@dataclass
class Version:
    pkgver: list[str]
    pkgrel: list[str]
    epoch: int

    @classmethod
    def from_str(cls, s: str) -> Version:
        match = re.search(r"pkgver=(?P<VER>.*)", s)
        if not match:
            raise ValueError('pkgver keyword not found')
        else:
            pkgver = match.group('VER').split('.')
        match = re.search(r"pkgrel=(?P<REL>.*)", s)
        if not match:
            pkgrel = ['1']
        else:
            pkgrel = match.group('REL').split('.')
        match = re.search(r"epoch=(?P<EPOCH>\d+)", s)
        if not match:
            epoch = 0
        else:
            epoch = int(match.group('EPOCH'))
        return cls(pkgver, pkgrel, epoch)

    @classmethod
    async def from_file(cls, file: str | Path) -> Version:
        async with aiofiles.open(file, 'r', encoding='utf-8') as fin:
            return cls.from_str(await fin.read())

    def __eq__(self, other: Version) -> bool:
        return self.epoch == other.epoch \
               and self.pkgver == self.pkgver \
               and self.pkgrel == other.pkgrel

    def __gt__(self, other: Version) -> bool:
        return self.epoch > other.epoch \
               or self.pkgver > other.pkgver \
               or (self.pkgver == other.pkgver and self.pkgrel > other.pkgrel)

    def __ne__(self, other: Version) -> bool:
        return not self.__eq__(other)

    def __ge__(self, other: Version) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other: Version) -> bool:
        return not self.__ge__(other)

    def __str__(self) -> str:
        prefix = f'{self.epoch}:' if self.epoch > 0 else ''
        return f'{prefix}{self.pkgver}-{self.pkgrel}'


async def with_sem(sem: asyncio.Semaphore, coro: Coroutine):
    async with sem:
        return await coro


async def aur_check_update(session: aiohttp.ClientSession, item: Path, dry_run: bool) -> None:
    if item.name.startswith('.') or not item.is_dir():
        return
    pkgbuild_file = item.joinpath('PKGBUILD')
    if not pkgbuild_file.exists():
        logging.warning(f'PKGBUILD not in {str(item)}, SKIP!')
        return
    version = await Version.from_file(pkgbuild_file)
    async with session.get(f'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={item.name}') as resp:
        if resp.status != 200:
            logging.info(f'{item.name} not register in AUR')
            return
        new_version = Version.from_str(await resp.text())

    if new_version == version:
        return
    elif new_version < version:
        logging.warning(f'Warning: {version} is newer than AUR')
        return
    if item.joinpath('.git').exists():
        if not dry_run:
            await asyncio.create_subprocess_exec('git', '-C', f'{str(item)}', 'pull', 'origin', 'master')
        logging.info(f'Upgrade {item.name} from {version} to {new_version}')
    else:
        logging.info(f'Found update {item.name}({version}) (local: {new_version})')


async def main() -> int:
    parser = argparse.ArgumentParser(description='aur-check-update.py')
    parser.add_argument('--dry', help='dry run', action='store_true')
    parser.add_argument('--max-workers', dest='workers', metavar='MAX_WORKERS',
                        help=f'aur check max workers, default: {MAX_WORKERS}',
                        default=MAX_WORKERS, action='store', type=int)
    parser.add_argument(dest='repo_dir', metavar='REPO_DIR', help='repository directory', nargs='?')

    args = parser.parse_args()

    dry_run = args.dry
    sem = asyncio.Semaphore(args.workers)

    if args.repo_dir is None:
        logging.error('repository directory not found')
        return 1

    repo_dir = Path(args.repo_dir)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        tasks = [asyncio.create_task(
            with_sem(sem, aur_check_update(session, item, dry_run))
        ) for item in repo_dir.iterdir()]
        await asyncio.gather(*tasks)

    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    loop = asyncio.get_event_loop()
    exit(loop.run_until_complete(main()))
