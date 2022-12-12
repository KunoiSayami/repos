#!/usr/bin/env python
import argparse
import asyncio
import os
import pathlib

try:
    import pkgbuild
except ModuleNotFoundError:
    import utils.pkgbuild as pkgbuild


async def fetch_and_get(_remote_addr: str):
    raise NotImplementedError("TODO!")


async def show_diff(database: str, path: str) -> None:
    pkg_dir = pathlib.Path(os.getcwd()).joinpath(path).resolve()
    database_result = pkgbuild.fetch_database(database)
    pending = []
    for package in await pkgbuild.fetch_packages_from_directory(pkg_dir):
        if (package := package.result()).name in database_result:
            if database_result[package.name] < package.version:
                pending.append(package)
        else:
            pending.append(package)
    for package in pending:
        print(package.name, package.version)


async def main(args: argparse.Namespace):
    if args.sub == "show":
        print(pkgbuild.fetch_database(args.database))
    elif args.sub == "show_local":
        pkg_dir = pathlib.Path(os.getcwd()).joinpath(args.path).resolve()
        for package in await pkgbuild.fetch_packages_from_directory(pkg_dir):
            print(package.result())
    elif args.sub == "show_internet":
        await fetch_and_get(args.database)
    elif args.sub == 'diff':
        await show_diff(args.database, args.path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('pkgman.py')
    sub = parser.add_subparsers(title="subcommand", dest="sub")
    decmp_parser = sub.add_parser("show", description="Show databases")
    decmp_parser.add_argument("database")

    local_show_parser = sub.add_parser("show_local")
    local_show_parser.add_argument("path", default="./repo")

    decmp_online_parser = sub.add_parser("show_internet", description="Show remote databases")
    decmp_online_parser.add_argument("database")

    show_diff_parser = sub.add_parser("diff")
    show_diff_parser.add_argument("database")
    show_diff_parser.add_argument("path")

    args_ = parser.parse_args()
    asyncio.run(main(args_))
