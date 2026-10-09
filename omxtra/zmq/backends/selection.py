"""
Explicit backend selection by name. Nothing is chosen implicitly - in particular the native backend is never chosen just
because pyzmq happens to be installed - and selecting it without pyzmq raises BackendUnavailableError.
"""
import typing as ta

from ..api.backends import Backend
from .pipelines.asyncio.backends import AsyncioPipelinesBackend
from .pyzmq.backends import PyzmqBackend


##


BACKEND_NAMES: ta.Sequence[str] = ('pipelines', 'pyzmq')


def new_backend(name: str) -> Backend:
    if name == 'pipelines':
        return AsyncioPipelinesBackend()
    elif name == 'pyzmq':
        return PyzmqBackend()
    else:
        raise ValueError(f'unknown backend: {name!r}')
