import pyalpm  # type: ignore


def vercmp(ver1: str, ver2: str) -> int:
    return pyalpm.vercmp(ver1, ver2)