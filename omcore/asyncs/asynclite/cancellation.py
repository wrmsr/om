# ruff: noqa: UP045
# @om-lite
from ...lite.abstract import Abstract
from .base import AsyncliteApi


##


class AsyncliteCancellation(AsyncliteApi, Abstract):
    pass
