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


class NO_CONCURRENCY_IDENTITY(lang.Marker):  # noqa
    pass


@ta.final
class NoConcurrency(Concurrency):
    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity(NO_CONCURRENCY_IDENTITY)

    def make_promise(self) -> asl.Promise:
        raise InjectorConcurrencyError


##


@ta.final
class SyncConcurrency(Concurrency):
    def __init__(self) -> None:
        self._api = asl.sync.All()

    def current_identity(self) -> ConcurrencyIdentity:
        return ConcurrencyIdentity(threading.get_ident())

    def make_promise(self) -> asl.Promise:
        return self._api.make_promise()
