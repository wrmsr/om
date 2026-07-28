import abc
import typing as ta

from ... import lang
from ...asyncs.asynclite import all as asl


##


ConcurrencyIdentity = ta.NewType('ConcurrencyIdentity', object)


class Concurrency(lang.Abstract):
    @abc.abstractmethod
    def current_identity(self) -> ConcurrencyIdentity:
        raise NotImplementedError

    @abc.abstractmethod
    def make_promise(self) -> asl.Promise:
        raise NotImplementedError
