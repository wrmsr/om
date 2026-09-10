import abc
import itertools
import typing as ta
import uuid

from ... import lang
from .types import Id


##


class JsonrpcIdCreator(lang.Abstract):
    """
    Produces the ids for the requests one side of a connection sends. Ids only need to be unique among that side's
    pending requests, so a simple counter suffices and is what most peers expect to see.
    """

    @abc.abstractmethod
    def __call__(self) -> Id:
        raise NotImplementedError


class IntJsonrpcIdCreator(JsonrpcIdCreator):
    def __init__(self, start: int = 1) -> None:
        super().__init__()

        # itertools.count is atomic under both the GIL and free-threading.
        self._counter = itertools.count(start)

    def __call__(self) -> Id:
        return next(self._counter)


class UuidJsonrpcIdCreator(JsonrpcIdCreator):
    def __call__(self) -> Id:
        return str(uuid.uuid7())


class FnJsonrpcIdCreator(JsonrpcIdCreator):
    def __init__(self, fn: ta.Callable[[], Id]) -> None:
        super().__init__()

        self._fn = fn

    def __call__(self) -> Id:
        return self._fn()


JsonrpcIdCreatorLike: ta.TypeAlias = JsonrpcIdCreator | ta.Callable[[], Id]


def jsonrpc_id_creator_of(obj: JsonrpcIdCreatorLike | None) -> JsonrpcIdCreator:
    if obj is None:
        return IntJsonrpcIdCreator()
    if isinstance(obj, JsonrpcIdCreator):
        return obj
    if callable(obj):
        return FnJsonrpcIdCreator(obj)
    raise TypeError(obj)
