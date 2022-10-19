#!/usr/bin/env python
from __future__ import annotations
import argparse
import asyncio
import dataclasses
import lzma
import logging
import os
import pathlib
import subprocess

import aiofiles

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@dataclasses.dataclass
class PackageVersion:
    name: str
    version: str

    def __eq__(self, other: PackageVersion) -> bool:
        return other.version == self.version

    def __gt__(self, other: PackageVersion) -> bool:
        return self.version > other.version

    def __lt__(self, other: PackageVersion) -> bool:
        return self.version < other.version

    def __le__(self, other: PackageVersion) -> bool:
        return self < other or self == other

    def __ge__(self, other: PackageVersion) -> bool:
        return self > other or self == other

    def __ne__(self, other: PackageVersion) -> bool:
        return not self == other

    def __str__(self) -> str:
        return f'{self.name} {self.version}'


def fetch_database(pkg_db: str) -> dict[str, str]:
    name_read = False
    version_read = False
    pkg_name = ''
    package_storage = {}
    with lzma.open(pkg_db) as fin:
        for line in fin:
            line = line.strip()
            if name_read:
                pkg_name = line.decode()
                name_read = False
            elif version_read:
                package_storage.update({pkg_name: line.decode()})
                #logger.debug(pkg_name, line.decode())
                version_read = False
                pkg_name = ''
            if line == b"%NAME%":
                assert not name_read
                name_read = True
            if line == b"%VERSION%":
                assert not version_read
                version_read = True
            assert (name_read is False and version_read is False) or (version_read != name_read)
    return package_storage


def get_src_info(s: str) -> PackageVersion:
    base = ''
    ver = ''
    rel = ''
    for line in s.splitlines(False):
        if (line := line.strip()).startswith('pkgver'):
            ver = line.split('=', maxsplit=2)[1]
        elif line.startswith('pkgrel'):
            rel = line.split('=', maxsplit=2)[1]
        elif line.startswith('pkgbase'):
            base = line.split('=', maxsplit=2)[1]
    return PackageVersion(base.strip(), f'{ver.strip()}-{rel.strip()}')


async def parse_srcinfo(path: pathlib.PurePath) -> PackageVersion:
    if (path := pathlib.Path(path.joinpath('.SRCINFO'))).is_file():
        async with aiofiles.open(str(path)) as fin:
            return get_src_info(await fin.read())
    else:
        p = await asyncio.create_subprocess_exec('makepkg', '--printsrcinfo', stdout=subprocess.PIPE, cwd=path.parent)
        (stdout, stderr) = (await p.communicate())
        return get_src_info(stdout.decode())


async def do_work(pkg_db: str):

    repo = fetch_database(pkg_db)
    home_directory = pathlib.Path(os.getcwd())

    tasks = []
    pending_build = []

    for folder in os.listdir("."):
        if folder.startswith("."):
            continue
        if os.path.isfile(folder):
            continue

        tasks.append(asyncio.create_task(parse_srcinfo(home_directory.joinpath(folder))))

    finished, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    for future in finished:
        pkg = future.result()
        if pkg.name in repo:
            #print(pkg.name, repo[pkg.name], pkg.version)
            if repo[pkg.name] < pkg.version:
                pending_build.append(pkg.name)
        else:
            pending_build.append(pkg.name)

    print(pending_build)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pkgbuild.py')
    parser.add_argument('db_file')
    args = parser.parse_args()
    asyncio.run(do_work(args.db_file))