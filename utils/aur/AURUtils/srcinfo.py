import re
from collections import defaultdict
from itertools import chain
from typing import Optional, Union

from .errors import PackageNotFound
from .aur_deps import depends_strip

key_value_pattern = re.compile(r'(?P<KEY>.+?)=(?P<VALUE>.+)')
multivalued_attrs = {
    'source', 'provides', 'conflicts', 'depends', 'replaces', 'optdepends', 'makedepends', 'checkdepends',
    'md5sums', 'sha1sums', 'sha224sums', 'sha256sums', 'sha384sums', 'sha512sums', 'arch'
}


class SRCINFO:

    def __init__(self, pkgbase: str, pkgbase_opt: dict, pkgs_opt: dict):
        self.pkgbase = pkgbase
        self.pkgbase_opt = pkgbase_opt
        self.pkgs_opt = pkgs_opt

    @classmethod
    def parse(cls, source: str):
        pkgbase = None
        pkgbase_opt = defaultdict(list)
        pkgs_opt = {}
        handler = None
        for l in source.splitlines():
            m = key_value_pattern.search(l.strip())
            if m is None:
                continue
            key, value = m.group('KEY').strip(), m.group('VALUE').strip()
            if key == 'pkgbase':
                pkgbase = value
                handler = pkgbase_opt
            elif key == 'pkgname':
                pkgs_opt[value] = defaultdict(list)
                handler = pkgs_opt[value]
            else:
                if key in multivalued_attrs:
                    handler[key].append(value)
                else:
                    handler[key] = value
        return SRCINFO(pkgbase, pkgbase_opt, pkgs_opt)

    @property
    def pkgs(self) -> dict:
        return {
            k: {i: self.get_pkg_opt(k, i) for i in chain(self.pkgbase_opt.keys(), v.keys())}
            for k, v in self.pkgs_opt.items()
        }

    @property
    def pkgs_name(self) -> list:
        return list(self.pkgs_opt.keys())

    def _chain_pkg_opt(self, pkgname: str, opt: str) -> chain:
        if pkgname not in self.pkgs_name:
            raise PackageNotFound(f'{pkgname} not found in {self.pkgbase}')
        return chain(self.pkgbase_opt.get(opt, []), self.pkgs_opt[pkgname].get(opt, []))

    def _chain_opt(self, opt: str) -> chain:
        return chain(self.pkgbase_opt.get(opt, []), *(i.get(opt, []) for i in self.pkgs_opt.values()))

    def get_pkg_opt(self, pkgname: str, opt: str) -> Union[list, str]:
        if pkgname not in self.pkgs_name:
            raise PackageNotFound(f'{pkgname} not found in {self.pkgbase}')
        if opt in multivalued_attrs:
            return list(self._chain_pkg_opt(pkgname, opt))
        return self.pkgbase_opt.get(opt)

    def get_opt(self, opt: str) -> Union[list, str]:
        if opt in multivalued_attrs:
            return list(self._chain_opt(opt))
        return self.pkgbase_opt.get(opt)

    @property
    def depends(self) -> list[str]:
        return list(map(depends_strip, self._chain_opt('depends')))

    @property
    def makedepends(self) -> list[str]:
        return list(map(depends_strip, self._chain_opt('makedepends')))

    @property
    def optdepends(self) -> list[str]:
        return list(self._chain_opt('optdepends'))

    @property
    def version(self) -> tuple[Optional[str], str, str]:
        return self.pkgbase_opt.get('epoch', None), \
               self.pkgbase_opt['pkgver'], self.pkgbase_opt['pkgrel']

    def get_version(self) -> str:
        epoch = f"{self.pkgbase_opt['epoch']}:" if self.pkgbase_opt.get('epoch') else ''
        return f"{epoch}{self.pkgbase_opt['pkgver']}-{self.pkgbase_opt['pkgrel']}"
