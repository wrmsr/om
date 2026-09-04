# ruff: noqa: UP045
# @om-lite
from ..cancellation import AsyncliteCancellation
from .base import SyncAsyncliteApi


##


class SyncAsyncliteCancellation(AsyncliteCancellation, SyncAsyncliteApi):
    pass
