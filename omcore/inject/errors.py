import typing as ta

from .. import dataclasses as dc
from .keys import Key
from .types import Scope


##


@dc.dataclass()
class BaseKeyError(Exception):
    key: Key

    source: ta.Any = None
    name: str | None = None


@dc.dataclass()
class UnboundKeyError(BaseKeyError):
    pass


@dc.dataclass()
class ConflictingKeyError(BaseKeyError):
    pass


@dc.dataclass()
class DuplicateMapKeyError(BaseKeyError):
    map_key: ta.Any = None


@dc.dataclass()
class CyclicDependencyError(BaseKeyError):
    chain: ta.Sequence[Key] | None = None


##


@dc.dataclass()
class InjectorConcurrencyError(Exception):
    pass


@dc.dataclass()
class DeadInjectorError(Exception):
    pass


##


@dc.dataclass()
class ScopeError(Exception):
    scope: Scope


@dc.dataclass()
class ScopeAlreadyOpenError(ScopeError):
    pass


@dc.dataclass()
class ScopeNotOpenError(ScopeError):
    pass


@dc.dataclass()
class ScopeEagerUnsupportedError(ScopeError):
    key: Key | None = None


@dc.dataclass()
class ScopeFrozenError(ScopeError):
    key: Key | None = None
