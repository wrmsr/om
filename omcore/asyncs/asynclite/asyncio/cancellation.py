# ruff: noqa: UP045
# @om-lite
from ..cancellation import AsyncliteCancellation
from .base import AsyncioAsyncliteApi


##


class AsyncioAsyncliteCancellation(AsyncliteCancellation, AsyncioAsyncliteApi):
    pass
