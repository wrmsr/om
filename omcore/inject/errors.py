import typing as ta

from .. import dataclasses as dc
from .keychain import KeyChain
from .keys import Key
from .types import Scope


##


def _key_chain_repr(kl: ta.Sequence[Key]) -> str:
    return '\n'.join([
        f'  {k!r}{" ->" if i < len(kl) - 1 else ""}'
        for i, k in enumerate(kl)
    ])


##


@dc.dataclass()
class BaseKeyError(Exception):
    key: Key

    source: ta.Any = None
    name: str | None = None


@dc.dataclass()
class UnboundKeyError(BaseKeyError):
    chain: KeyChain | None = None

    def __str__(self) -> str:
        parts = [f'Unbound key: {self.key!r}']
        if self.chain:
            parts.append(f'Provision path:\n{self.chain.render()}')
        return '\n'.join(parts)


@dc.dataclass()
class ConflictingKeyError(BaseKeyError):
    pass


@dc.dataclass()
class DuplicateMapKeyError(BaseKeyError):
    map_key: ta.Any = None


@dc.dataclass()
class CyclicDependencyError(BaseKeyError):
    # The provision (or compilation) path, from the requested root to the repeated key.
    chain: KeyChain | None = None

    # Wait-graph edges are distinct from the local provision path: each may hide many provider calls.
    wait_chain: KeyChain | None = None

    def __str__(self) -> str:
        parts = [f'Cyclic dependency: {self.key!r}']
        if self.chain:
            parts.append(f'Provision path:\n{self.chain.render()}')
        if self.wait_chain:
            if len(self.wait_chain) == 1:
                parts.append(f'Waiting for own in-progress provision: {self.wait_chain[0]!r}')
            else:
                parts.append(f'Provision wait cycle:\n{self.wait_chain.render(tail=[self.wait_chain[0]])}')
        return '\n'.join(parts)


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
class ScopeNotRegisteredError(ScopeError):
    key: Key | None = None


@dc.dataclass()
class ScopeAlreadyRegisteredError(ScopeError):
    pass


@dc.dataclass()
class ScopeEagerUnsupportedError(ScopeError):
    key: Key | None = None


@dc.dataclass()
class ScopeEagerNonLocalError(ScopeError):
    key: Key | None = None


@dc.dataclass()
class ScopeFrozenError(ScopeError):
    key: Key | None = None
