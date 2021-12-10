from dataclasses import dataclass
from datetime import datetime
from collections.abc import Iterator
from typing import Union

from .aur_deps import depends_strip

UrlParameterType = Union[str, list[str]]


@dataclass()
class Package:

    ID: int
    Name: str
    PackageBaseID: int
    PackageBase: str
    Version: str
    Description: str
    URL: str
    NumVotes: int
    Popularity: float
    OutOfDate: int
    Maintainer: str
    FirstSubmitted: int
    LastModified: int
    URLPath: str
    Conflicts: list[str] = None
    Provides: list[str] = None
    Depends: list[str] = None
    MakeDepends: list[str] = None
    OptDepends: list[str] = None
    License: list[str] = None
    Keywords: list[str] = None

    @property
    def depends(self) -> list[str]:
        return list(map(depends_strip, self.Depends))

    @property
    def makedepends(self) -> list[str]:
        return list(map(depends_strip, self.MakeDepends))

    @property
    def optdepends(self) -> list[str]:
        return list(self.OptDepends)

    @property
    def first_submitted(self) -> datetime:
        return datetime.fromtimestamp(self.FirstSubmitted)

    @property
    def last_modified(self) -> datetime:
        return datetime.fromtimestamp(self.LastModified)

    def get_version(self) -> str:
        return self.Version


@dataclass
class Results:

    resultcount: int
    results: list
    type: str
    version: int

    @classmethod
    def parse(cls, json_response: dict):
        return Results(**json_response)

    def empty(self) -> bool:
        return self.resultcount == 0

    def packages(self) -> Iterator[Package]:
        if self.type in {'multiinfo', 'search'}:
            return [Package(**i) for i in self.results]
        return []
