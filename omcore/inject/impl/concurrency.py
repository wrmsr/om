import abc
import threading
import typing as ta

from ... import lang
from ...asyncs.asynclite import all as asl
from ..errors import InjectorConcurrencyError


##


ConcurrencyIdentity = ta.NewType('ConcurrencyIdentity', object)


class Concurrency(lang.Abstract):
    @abc.abstractmethod
    def current_identity(self) -> ConcurrencyIdentity:
        raise NotImplementedError

    @abc.abstractmethod
    def make_promise(self) -> asl.Promise:
        raise NotImplementedError


##


@ta.final
class NoConcurrency(Concurrency):
    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity(None)

    def make_promise(self) -> asl.Promise:
        raise InjectorConcurrencyError


##


@ta.final
class SyncConcurrency(Concurrency):
    def __init__(self) -> None:
        self._api = asl.sync.All()

    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity(self._api.current_identity())

    def make_promise(self) -> asl.Promise:
        return self._api.make_promise()


##


@ta.final
class AsyncioConcurrency(Concurrency):
    def __init__(self) -> None:
        self._api = asl.asyncio.All()

    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity((threading.get_ident(), self._api.current_identity()))

    def make_promise(self) -> asl.Promise:
        return self._api.make_promise()
