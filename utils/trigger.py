#!/usr/bin/env python
import argparse
import logging
import os
import signal
import socket
import subprocess
import threading
from socketserver import StreamRequestHandler, TCPServer

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Handler(StreamRequestHandler):
    def handle(self):
        while line := self.rfile.readline():
            if b"ARCH=" in line:
                (
                    subprocess.Popen(
                        [
                            "systemctl",
                            "--no-block",
                            "start",
                            f"update-repo@{line.split(b'=')[1].decode().strip()}",
                        ]
                    )
                ).wait()
                os.kill(os.getpid(), signal.SIGUSR1)
                return
            logger.info("Recv: %s", line)


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


def main():
    def server_shutdown_wrapper(*_args) -> None:
        logger.debug("Shutdown the server")
        threading.Thread(
            target=server.shutdown,
            daemon=True,
        ).start()

    server = Server(("localhost", 0), Handler)
    signal.signal(signal.SIGUSR1, server_shutdown_wrapper)

    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

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

    main()
