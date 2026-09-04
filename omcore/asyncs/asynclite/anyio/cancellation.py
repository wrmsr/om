# ruff: noqa: UP045
from ..cancellation import AsyncliteCancellation
from .base import AnyioAsyncliteApi


##


class AnyioAsyncliteCancellation(AsyncliteCancellation, AnyioAsyncliteApi):
    pass
