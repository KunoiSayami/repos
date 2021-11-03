#!/usr/bin/env python3

import argparse
import asyncio
import logging
import re
from pathlib import Path
from typing import Tuple

import aiofiles
import aiohttp


async def check_pkg(session: aiohttp.ClientSession, num: int, pkg: str) -> Tuple[int, bool]:
    logging.info(f'Checking {pkg}')
    ret = await session.head(f'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkg}')
    return num, ret.status == 200


async def main() -> int:
    parser = argparse.ArgumentParser(description='check-aur.py')
    parser.add_argument('paths', metavar='sub_path', type=str, nargs='*', help='sub-path for repo root')

    args = parser.parse_args()
    repo_dir = Path(*args.paths)
    pkgbuild_file = repo_dir.joinpath('PKGBUILD')
    if not pkgbuild_file.exists():
        logging.error("Can't locate PKGBUILD file, please specify directory in arguments or chdir to folder")
        return 1

    async with aiofiles.open(pkgbuild_file, 'r', encoding='utf-8') as f:
        pkgbuild_text = await f.read()

    deps_match = re.search(r"makedepends=\((?P<DEPS>([^)]|\n)+)\)", pkgbuild_text, re.M)
    if not deps_match:
        logging.error("Can't found `makedepends' keyword, if you think this is mistake, please report issue")
        return 2

    deps = deps_match.group('DEPS').split()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        tasks = [asyncio.create_task(check_pkg(session, n, pkg)) for n, pkg in enumerate(deps)]
        yay_dep_nums = []
        for task in asyncio.as_completed(tasks):
            n, r = await task
            if r:
                yay_dep_nums.append(n)

    yaydeps_dir = repo_dir.parent.joinpath('.yaydeps')

    if len(yay_dep_nums) > 0:
        async with aiofiles.open(yaydeps_dir.joinpath(repo_dir.stem), 'w', encoding='utf-8') as f:
            await f.write('\n'.join([*(deps[n] for n in sorted(yay_dep_nums)), '']))

    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    loop = asyncio.get_event_loop()
    exit(loop.run_until_complete(main()))
