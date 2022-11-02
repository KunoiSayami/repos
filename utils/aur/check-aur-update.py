#!/usr/bin/env python3

import asyncio
import argparse
import heapq
import logging
from collections.abc import Coroutine
from pathlib import Path
from typing import Optional

import aiohttp
import aiofiles

from AURUtils.srcinfo import SRCINFO
from AURUtils.version import vercmp


MAX_WORKERS = 16


async def check_pkg(session: aiohttp.ClientSession, num: int, pkg: str) -> tuple[int, bool]:
    logging.info(f'Checking {pkg}')
    ret = await session.head(f'https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkg}')
    return num, ret.status == 200


async def check_aur_update(
        session: aiohttp.ClientSession,
        item: Path, dry_run: bool,
        parse_pkgbuild: Optional[Path] = None,
        check_deps: bool = True
) -> None:
    if item.name.startswith('.') or not item.is_dir():
        return
    pkgbuild_file = item.joinpath('PKGBUILD')
    if not pkgbuild_file.exists():
        logging.warning(f'PKGBUILD not in {str(item)}, SKIP!')
        return
    srcinfo_file = item.joinpath('.SRCINFO')
    if not srcinfo_file.exists():
        if parse_pkgbuild.exists():
            logging.warning(f'.SRCINFO not in {str(item)}, try to parse')
            proc = await asyncio.create_subprocess_exec(
                f'{str(parse_pkgbuild.resolve())}',
                f'{str(pkgbuild_file)}',
                stdout=asyncio.subprocess.PIPE,
            )
            srcinfo = SRCINFO.parse((await proc.stdout.read()).decode())
            logging.info(f'extract .SRCINFO from {srcinfo.pkgbase}')
        else:
            logging.warning(f'.SRCINFO not in {str(item)}, no tool to parse')
            return
    else:
        async with aiofiles.open(srcinfo_file, 'r') as f:
            srcinfo = SRCINFO.parse(await f.read())
    version = srcinfo.get_version()
    async with session.get(f'https://aur.archlinux.org/cgit/aur.git/plain/.SRCINFO?h={srcinfo.pkgbase}') as resp:
        if resp.status != 200:
            logging.info(f'{item.name} not register in AUR')
            return
        new_srcinfo = SRCINFO.parse(await resp.text())
        new_version = new_srcinfo.get_version()
        result = vercmp(new_version, version)
        if result == 0:
            return
        elif result < 0:
            logging.warning(f'Warning: {item.name}({version}) is newer than AUR')
        else:
            if item.joinpath('.git').exists():
                if not dry_run:
                    await asyncio.create_subprocess_exec('git', '-C', f'{str(item)}', 'pull', 'origin', 'master')
                logging.info(f'Upgrade {item.name} from {version} to {new_version}')
            else:
                logging.info(f'Found update {item.name}({new_version}) (local: {version})')
            if check_deps:
                deps = [*new_srcinfo.makedepends, *new_srcinfo.depends]
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
                    tasks = [asyncio.create_task(check_pkg(session, n, pkg)) for n, pkg in enumerate(deps)]
                    yay_dep_nums = []
                    for task in asyncio.as_completed(tasks):
                        n, r = await task
                        if r:
                            heapq.heappush(yay_dep_nums, n)

                yaydeps_dir = item.parent.joinpath('.yaydeps')

                if len(yay_dep_nums) > 0:
                    async with aiofiles.open(yaydeps_dir.joinpath(item.stem), 'w', encoding='utf-8') as f:
                        await f.write(
                            '\n'.join([*(deps[heapq.heappop(yay_dep_nums)] for _ in range(len(yay_dep_nums))), '']))


async def with_sem(sem: asyncio.Semaphore, coro: Coroutine):
    async with sem:
        return await coro


async def main() -> int:
    parser = argparse.ArgumentParser(description='aur-check-update.py')
    parser.add_argument('--dry-run', dest='dry', help='dry run', action='store_true')
    parser.add_argument('--check-deps', dest='deps', help='check deps', action='store_true')
    parser.add_argument('--parse-pkgbuild', dest='script', metavar='SCRIPT',
                        help='a script to parse pkgbuild',
                        action='store')
    parser.add_argument('--miax-workers', dest='workers', metavar='MAX_WORKERS',
                        help=f'aur check max workers, default: {MAX_WORKERS}',
                        default=MAX_WORKERS, action='store', type=int)
    parser.add_argument(dest='repo_dir', metavar='REPO_DIR', help='repository directory', nargs='?')

    args = parser.parse_args()

    dry_run = args.dry
    check_deps = args.deps
    sem = asyncio.Semaphore(args.workers)

    if args.repo_dir is None:
        logging.error('repository directory not found')
        return 1

    script_file = Path(args.script)
    if args.script is None or not (script_file.is_file() and script_file.exists()):
        logging.info(f'Parse script {str(script_file)+" " if args.script is None else ""} not found')
        script_file = None

    repo_dir = Path(args.repo_dir)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        tasks = [asyncio.create_task(
            with_sem(sem, check_aur_update(
                session=session,
                item=item,
                dry_run=dry_run,
                parse_pkgbuild=script_file,
                check_deps=check_deps
        ))
        ) for item in repo_dir.iterdir()]
        await asyncio.gather(*tasks)

    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s')
    asyncio.run(main())
