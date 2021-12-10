import asyncio
import random

import aiohttp

from .errors import RPCError, MaxRetries
from .types import Results, UrlParameterType

DEFAULT_AURWEB_VERSION = 5
MAX_WORKERS = 10

METHODS = {'search', 'info', 'multiinfo', 'msearch', 'suggest',
           'suggest-pkgbase', 'get-comment-form'}
FIELDS = {'name', 'name-desc', 'maintainer', 'depends',
          'makedepends', 'optdepends', 'checkdepends'}


class AsyncRPC:
    """
    https://wiki.archlinux.org/title/Aurweb_RPC_interface
    """

    RPC_URL = 'https://aur.archlinux.org/rpc/'

    def __init__(self, max_workers: int = MAX_WORKERS):
        self._client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10))
        self.sem = asyncio.Semaphore(max_workers)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._client.close()

    async def _post(self, params: dict) -> dict:
        async with self.sem:
            for i in range(5):
                try:
                    async with self._client.get(self.RPC_URL, params=params) as resp:
                        resp.raise_for_status()
                        return await resp.json()
                except aiohttp.ServerTimeoutError:
                    await asyncio.sleep(3 * random.random())
                    continue
            raise MaxRetries

    async def request(self,
                      method: str,
                      method_params: dict[str, UrlParameterType],
                      ):
        params = {
            'v': DEFAULT_AURWEB_VERSION,
            'type': method,
            **method_params
        }
        json_response = await self._post(params)
        if 'error' in json_response:
            raise RPCError(method, json_response['error'])
        return Results.parse(json_response)

    async def search(self,
                     arg: UrlParameterType,
                     search_by: str = None,
                     ):
        method_params = {
            'by': search_by or [],
            'arg': arg,
        }
        return await self.request('search', method_params)

    async def info(self,
                   arg: UrlParameterType,
                   ):
        return await self.multiinfo(arg)

    async def multiinfo(self,
                        arg: UrlParameterType,
                        ):
        method_params = {
            'arg[]': arg,
        }
        return await self.request('multiinfo', method_params)

    async def msearch(self, arg: UrlParameterType):
        return await self.search(arg, search_by='maintainer')
