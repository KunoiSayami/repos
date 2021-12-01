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
import argparse
import asyncio
import heapq
import logging
import re
from pathlib import Path

import aiofiles
import aiohttp


async def check_pkg(session: aiohttp.ClientSession, num: int, pkg: str) -> tuple[int, bool]:
    logging.info(f'Checking {pkg}')
    ret = await session.head(f'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkg}')
    return num, ret.status == 200


async def main() -> int:
    parser = argparse.ArgumentParser(description='check-aur-dependencies.py')
    parser.add_argument('paths', metavar='sub_path', type=str, nargs='*', help='sub-path for repo root')

    args = parser.parse_args()
    repo_dir = Path(*args.paths)
    pkgbuild_file = repo_dir.joinpath('PKGBUILD')
    if not pkgbuild_file.exists():
        logging.error("Can't locate PKGBUILD file, please specify directory in arguments or chdir to folder")
        return 1

    async with aiofiles.open(pkgbuild_file, 'r', encoding='utf-8') as f:
        pkgbuild_text = await f.read()

    runtime_deps_match = re.search(r"depends=\((?P<DEPS>([^)]|\n)*)\)", pkgbuild_text, re.M)
    if not runtime_deps_match:
        logging.warning("Can't found 'depends' keyword, if you think this is mistake, please report issue")

    make_deps_match = re.search(r"makedepends=\((?P<DEPS>([^)]|\n)*)\)", pkgbuild_text, re.M)
    if not make_deps_match:
        logging.warning("Can't found `makedepends' keyword, if you think this is mistake, please report issue")

    deps = [dep.strip('\'') for m in {runtime_deps_match, make_deps_match} if m for dep in m.group('DEPS').split()]

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        tasks = [asyncio.create_task(check_pkg(session, n, pkg)) for n, pkg in enumerate(deps)]
        yay_dep_nums = []
        for task in asyncio.as_completed(tasks):
            n, r = await task
            if r:
                heapq.heappush(yay_dep_nums, n)

    yaydeps_dir = repo_dir.parent.joinpath('.yaydeps')

    if len(yay_dep_nums) > 0:
        async with aiofiles.open(yaydeps_dir.joinpath(repo_dir.stem), 'w', encoding='utf-8') as f:
            await f.write('\n'.join([*(deps[heapq.heappop(yay_dep_nums)] for _ in range(len(yay_dep_nums))), '']))

    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    exit(asyncio.run(main()))
