#!/usr/bin/env python
import argparse
import asyncio
import logging
import os
import pathlib
import shutil
import subprocess


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


async def add_package(dest: pathlib.Path, pkg_name: str, key: str) -> None:
    await (
        await asyncio.create_subprocess_exec(
            "repo-add",
            str(dest),
            pkg_name,
            "-s",
            "-v",
            "-R",
            "-k",
            key,
            stdout=subprocess.STDOUT,
        )
    ).wait()


async def main(remote_dest: str, repo_base_name: str, sign_key: str) -> None:
    cwd = pathlib.Path(os.getcwd()).resolve()
    remote_dest = pathlib.Path(remote_dest).resolve()
    database_dest = cwd.joinpath(repo_base_name).resolve()

    for file in os.listdir(str(remote_dest)):
        logger.debug("Copy file: %s", file)
        shutil.copy(str(remote_dest.joinpath(file).joinpath()), str(cwd))

    for file in os.listdir(str(remote_dest)):
        if ".pkg.tar.zst" in file:
            await add_package(database_dest, file.split(".pkg.tar.zst")[0], sign_key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("update-db.py")
    parser.add_argument("cwd")
    parser.add_argument("basename")
    parser.add_argument("sign_key")

    args_ = parser.parse_args()

    try:
        import coloredlogs

        coloredlogs.install(
            logging.DEBUG,
            fmt="%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s",
        )
    except ModuleNotFoundError:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s",
        )
    main(args_.cwd, args_.basename, args_.sign_key)
