#!/usr/bin/env python3
import asyncio
import logging
import os
import re
import sys

import aiohttp
import aiofiles


async def main() -> int:
    # target_file = os.path.join(os.path.abspath(sys.argv[0].rsplit('/', maxsplit=2)[0]), '.aur.db')

    pkgbuild_file = None
    if os.path.exists(s := os.path.abspath('./PKGBUILD')):
        pkgbuild_file = s
    elif len(sys.argv) > 1 and os.path.exists(s := os.path.join(sys.argv[1], "PKGBUILD")):
        pkgbuild_file = s

    if pkgbuild_file is None:
        logging.error("Can't locate PKGBUILD file, please specify directory in arguments or chdir to folder")
        return 1

    current_folder = pkgbuild_file.rsplit('/', maxsplit=1)[0]
    async with aiofiles.open(pkgbuild_file) as fin:
        f = await fin.read()

    if deps := re.search(r"makedepends=\((([^)]|\n)+)\)", f, re.M):
        result = deps.group(1)
    else:
        logging.error("Can't found `makedepends' keyword, if you think this is mistake, please report issue")
        return 2

    if '\n' in result:
        result = ' '.join(map(lambda x: x.strip(), result.splitlines()))

    result = result.replace('\'', '')
    is_written = False
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        async with aiofiles.open(yaydep_file := os.path.join(
                current_folder, '..', '.yaydeps', current_folder.rsplit('/', maxsplit=1)[1]), 'w') as yayfile:
            for pkg in result.split():
                logging.info('Checking %s', pkg)
                ret = await session.head(f'https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h={pkg}')
                if ret.status == 200:
                    await yayfile.write(f'{pkg}\n')
                    is_written = True
    if not is_written:
        os.remove(yaydep_file)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    loop = asyncio.get_event_loop()
    exit(loop.run_until_complete(main()))

