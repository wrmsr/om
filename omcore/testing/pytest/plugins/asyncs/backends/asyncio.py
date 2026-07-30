import functools
import sys
import typing as ta

from ...... import check
from ...... import lang
from .base import AsyncsBackend


if ta.TYPE_CHECKING:
    import asyncio
else:
    asyncio = lang.proxy_import('asyncio')


##


class AsyncioAsyncsBackend(AsyncsBackend):
    name = 'asyncio'

    def is_available(self) -> bool:
        return True

    def is_imported(self) -> bool:
        return 'asyncio' in sys.modules

    #

    def wrap_runner(self, fn):
        @functools.wraps(fn)
        def wrapper(**kwargs):
            with asyncio.Runner() as runner:
                loop_cls = type(runner.get_loop())
                check.equal(loop_cls.__module__.split('.')[0], 'asyncio')
                return runner.run(fn(**kwargs))

        return wrapper
