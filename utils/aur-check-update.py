#!/usr/bin/env python3
# Copyright (C) 2021 KunoiSayami
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
import asyncio
import logging
import os
import re
import sys

from dataclasses import dataclass

import aiofiles
import aiohttp


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
    async def from_file(cls, file: str) -> Version:
        async with aiofiles.open(file) as fin:
            return cls.from_str(await fin.read())

    def __eq__(self, other: Version) -> bool:
        return all((self.epoch == other.epoch, self.pkgver == self.pkgver, self.pkgrel == other.pkgrel))

    def __gt__(self, other: Version) -> bool:
        if self.epoch > other.epoch:
            return True
        if self.pkgver > other.pkgver:
            return True
        if self.pkgver == other.pkgver and self.pkgrel > other.pkgrel:
            return True
        return False

    def __ne__(self, other: Version) -> bool:
        return not self.__eq__(other)

    def __ge__(self, other: Version) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other: Version) -> bool:
        return not self.__ge__(other)

    def __str__(self) -> str:
        prefix = f'{self.epoch}:' if self.epoch > 0 else ''
        return f'{prefix}{self.pkgver}-{self.pkgrel}'


async def main() -> int:
    dry_run = '--dry' in sys.argv
    os.chdir(sys.argv[1])
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        for item in os.listdir():
            if item.startswith('.'):
                continue
            if not os.path.isdir(item):
                continue
            os.chdir(item)
            version = await Version.from_file('PKGBUILD')
            async with session.get(f'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={item}') as response:
                if response.status != 200:
                    logging.info('%s not register in AUR', item)
                    os.chdir('..')
                    continue
                new_version = Version.from_str(await response.text())
            if new_version == version:
                os.chdir('..')
                continue
            elif new_version < version:
                logging.warning('Warning: %s is newer than AUR', version)
                os.chdir('..')
                continue
            if '.git' in os.listdir():
                if not dry_run:
                    await asyncio.create_subprocess_exec('git', 'pull')
                logging.info('Upgrade %s from %s to %s', item, version, new_version)
            else:
                logging.info('Found update %s(%s) (local: %s)', item, new_version, version)
            os.chdir('..')
    return 0

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage:', sys.argv[0], '<repository directory>')
        exit(1)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    loop = asyncio.get_event_loop()
    exit(loop.run_until_complete(main()))
