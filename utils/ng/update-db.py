#!/usr/bin/env python
import argparse
import logging
import os
import pathlib
import signal
import subprocess
import threading
import time
from socketserver import TCPServer, StreamRequestHandler
import socket
from queue import Queue


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


"""class DataHandler(asyncio.Protocol):
    def data_received(self, data: bytes) -> None:
        logger.debug(data)

    def eof_received(self) -> bool | None:
        logger.debug("eof")


class Server:
    def __init__(self, unix_sockets: str):
        self.unix_sockets = unix_sockets
        self.server = None

    async def connect(self) -> None:
        #self.server = await asyncio.start_unix_server(self.handle_connection, self.unix_sockets, start_serving=False)
        self.server = await asyncio.get_running_loop().create_unix_server(DataHandler, None,
                                                            sock=socket.fromfd(3, socket.AF_UNIX, socket.SOCK_STREAM))

    async def serving(self) -> None:
        await self.server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        logger.debug("Connected")
        while True:
            task = asyncio.create_task(reader.readline())
            finished, pending = await asyncio.wait([task], timeout=10)
            if len(finished):
                logger.debug(finished.pop().result())
            break

        writer.close()
        await writer.wait_closed()
        await self.close()

    async def close(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()


async def main(unix_sockets: str) -> None:
    logger.debug("Create connection")
    #os.unlink(unix_sockets)
    server = Server(unix_sockets)
    await server.connect()
    #await server.server()"""

queue = Queue()

ARCH = os.getenv("ARCH")


def get_arch() -> str:
    p = subprocess.Popen(["uname", "-m"], stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    return stdout.decode().lower().strip()


if ARCH is None:
    ARCH = get_arch()
    logger.warning("Warning: You should specify arch environment variable, use current platform: %s", ARCH)


class Handler(StreamRequestHandler):
    def handle(self):
        while line := self.rfile.readline():
            if b"EOF" in line:
                os.kill(os.getpid(), signal.SIGUSR1)
                return
            logger.info("Recv: %s", line)
            # self.wfile.write(line.upper())


# source: https://gist.github.com/drmalex07/333d8a88c4918954e8e4
class Server(TCPServer):
    # The constant would be better initialized by a systemd module
    SYSTEMD_FIRST_SOCKET_FD = 3

    def __init__(self, server_address, handler_cls):
        # Invoke base but omit bind/listen steps (performed by systemd activation!)
        TCPServer.__init__(self, server_address, handler_cls, bind_and_activate=False)
        # Override socket
        self.socket = socket.fromfd(
            self.SYSTEMD_FIRST_SOCKET_FD, self.address_family, self.socket_type
        )


class RepoProcessThread(threading.Thread):
    def __init__(self, dest: pathlib.Path, key: str, pkg_src: pathlib.Path):
        super().__init__()
        self.exit_event = threading.Event()
        self.dest = dest
        self.key = key
        self.pkg_src = pkg_src

    def run(self) -> None:
        while not self.exit_event.is_set():
            while not queue.empty():
                logger.info("Adding %s", repo := queue.get_nowait())
                self.pkg_src.joinpath(repo)
                subprocess.Popen(
                    ["repo-add", str(self.dest), repo, "-s", "-v", "-R", "-k", self.key],
                    stdout=subprocess.STDOUT
                ).wait()
            time.sleep(1)

    def set_exit_event(self) -> None:
        self.exit_event.set()


def main(cwd: str):
    def server_shutdown_wrapper(*_args) -> None:
        logger.debug("Shutdown the server")
        threading.Thread(target=server.shutdown, daemon=True,).start()

    server = Server(("localhost", 0), Handler)
    signal.signal(signal.SIGUSR1, server_shutdown_wrapper)

    remote_path = pathlib.Path(cwd).resolve()
    cwd = pathlib.Path(os.getcwd()).resolve()

    RepoProcessThread(
        cwd.joinpath("packages", ARCH, "kunoisayami.db.tar.gz").resolve(),
        "4A0F0C8BC709ACA4341767FB243975C8DB9656B9",
        remote_path
    ).start()
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("update-db.py")
    parser.add_argument("cwd")

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
    main(args_.cwd)
