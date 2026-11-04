# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Request id creators. Ids are opaque and scoped to the direction they were issued in, so they only need to be unique
among the issuing side's pending requests and pings: a counter suffices, and is the default.
"""
import abc
import itertools
import typing as ta
import uuid

from ..lite.abstract import Abstract


RpcIdCreatorLike = ta.Union['RpcIdCreator', ta.Callable[[], ta.Any]]  # ta.TypeAlias


##


class RpcIdCreator(Abstract):
    @abc.abstractmethod
    def __call__(self) -> ta.Any:
        raise NotImplementedError


class IntRpcIdCreator(RpcIdCreator):
    def __init__(self, start: int = 1) -> None:
        super().__init__()

        # itertools.count is atomic under both the GIL and free-threading.
        self._counter = itertools.count(start)

    def __call__(self) -> ta.Any:
        return next(self._counter)


class UuidRpcIdCreator(RpcIdCreator):
    def __call__(self) -> ta.Any:
        return str(uuid.uuid4())


class FnRpcIdCreator(RpcIdCreator):
    def __init__(self, fn: ta.Callable[[], ta.Any]) -> None:
        super().__init__()

        self._fn = fn

    def __call__(self) -> ta.Any:
        return self._fn()


def rpc_id_creator_of(obj: ta.Optional[RpcIdCreatorLike]) -> RpcIdCreator:
    if obj is None:
        return IntRpcIdCreator()
    if isinstance(obj, RpcIdCreator):
        return obj
    if callable(obj):
        return FnRpcIdCreator(obj)
    raise TypeError(obj)
