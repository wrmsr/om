import threading
import typing as ta

from .. import lang
from ..asyncs.asynclite import all as asl
from .elements import Elemental
from .impl.concurrency import Concurrency
from .impl.concurrency import ConcurrencyIdentity
from .injector import AsyncInjector
from .injector import _InjectorCreator


if ta.TYPE_CHECKING:
    from .helpers import managed as _managed
    from .impl import injector as _injector
else:
    _managed = lang.proxy_import('.helpers.managed', __package__)
    _injector = lang.proxy_import('.impl.injector', __package__)


##


@ta.final
class _AsyncioConcurrency(Concurrency):
    def __init__(self) -> None:
        self._api = asl.asyncio.All()

    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity((threading.get_ident(), self._api.current_identity()))

    def make_promise(self) -> asl.Promise:
        return self._api.make_promise()


#


create_asyncio_injector = _InjectorCreator[AsyncInjector, ta.Awaitable[AsyncInjector]](
    lambda ce, p=None, *, concurrency=None: _injector.create_async_injector(ce, p, concurrency=concurrency),
    lambda: _AsyncioConcurrency(),
)


##


def create_asyncio_managed_injector(
        *args: Elemental,
) -> ta.AsyncContextManager[_injector.AsyncInjector]:
    return _managed.create_async_managed_injector(
        *args,
        factory=create_asyncio_injector,
    )
