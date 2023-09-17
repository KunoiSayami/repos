#!/usr/bin/env python
import argparse
import asyncio
import logging
import os

import aiohttp
import aiohttp_socks

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def build_data(args: argparse.Namespace, action: str) -> dict[str, str]:
    return {"token": args.token, "arch": args.arch, "action": action}


# source: https://stackoverflow.com/a/1094933
def sizeof_fmt(num: int, suffix: str = "B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


# TODO: use upload in chunks to big file
async def send_file(
    session: aiohttp.ClientSession, args: argparse.Namespace, file: str
) -> None:
    data = aiohttp.FormData()
    data.add_field("file", open(file, "rb"), filename=file)
    data.add_field("token", args.token)
    data.add_field("arch", args.arch)
    async with session.post(args.remote_address, data=data) as req:
        logger.debug("%s", (await req.text()).strip())


async def main(args: argparse.Namespace) -> int:
    pending_upload = []
    for file in os.listdir("."):
        if ".pkg" in file:
            pending_upload.append(file)

    logger.debug("Pending upload (%d): %s", len(pending_upload), pending_upload)

    if not len(pending_upload):
        logger.info("Could not find any packaged packages, skip upload")
        return 0

    if proxy := os.getenv("http_proxy"):
        logger.debug("Using proxy %s", proxy)
        proxies = aiohttp_socks.ProxyConnector.from_url(proxy, rdns=False)
    else:
        proxies = None

    async with aiohttp.ClientSession(
        raise_for_status=True, timeout=aiohttp.ClientTimeout(30), connector=proxies
    ) as session:
        async with session.post(
            args.remote_address, data=build_data(args, "REQUIRE_CLEAN")
        ):
            pass
        for file in pending_upload:
            logger.info("Start upload %s (%s)", file, sizeof_fmt(os.stat(file).st_size))
            for retries in range(3):
                try:
                    await send_file(session, args, file)
                    break
                except asyncio.TimeoutError:
                    if retries == 2:
                        raise
        async with session.post(args.remote_address, data=build_data(args, "UPLOADED")):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser("upload.py")
    parser.add_argument("remote_address")
    parser.add_argument("token")
    parser.add_argument("arch")
    parser.add_argument("--directory")
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

    if args_.directory is not None:
        os.chdir(args_.directory)

    exit(asyncio.run(main(args_)))
