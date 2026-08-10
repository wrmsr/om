"""
The Runtime is the state-owning heart of a marshaling universe: one config registry, one reflection mirror, one pair of
root factories, and all handler caches, under one lock. Factories and handlers remain stateless and shareable;
contexts remain ephemeral per-op views; the Runtime is the one thing with a lifetime.

Handler caching is footprint-keyed: while a handler is being constructed, every config read made through the
construction context is recorded (including misses, and transitively through recursively-constructed child handlers)
as that cache entry's config footprint. The registry's snapshot version is the fast-path fence - an entry built at the
current version is served without further checks - and on version mismatch the footprint is revalidated against the
live registry, either restamping the entry in place (nothing it read has changed) or discarding it for rebuild. Late
config registrations therefore invalidate exactly the handlers whose construction observed the touched keys.

The registry is the only mutable config source and thus the only footprinted one - object metadata, dataclass field
metadata, and manifests are append-only and deliberately outside the invalidation model. Reflection-time config reads
(ReflectOverride) are likewise not footprinted: the mirror is built once per runtime and bakes overrides in, preserving
the documented register-before-first-reflection contract.
"""
import abc
import typing as ta

from ... import lang
from ... import reflect as rfl
from .configs import ConfigRegistry
from .configs import ConfigValues
from .contexts import MarshalFactoryContext
from .contexts import UnmarshalFactoryContext
from .types import Marshaler
from .types import MarshalerFactory
from .types import Unmarshaler
from .types import UnmarshalerFactory


##


class Runtime(lang.Abstract):
    @property
    @abc.abstractmethod
    def config_registry(self) -> ConfigRegistry:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def marshaler_factory(self) -> MarshalerFactory | None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def unmarshaler_factory(self) -> UnmarshalerFactory | None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def get_factory_configs(
            self,
            key: ta.Any = None,
            *,
            identity: bool | None = None,
    ) -> ConfigValues:
        """The construction-time view: reads made through this while a handler is being built are footprinted."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def get_mirror(self) -> rfl.Mirror:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def ensure_warm(self) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def flush(self) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def make_marshaler(self, ctx: MarshalFactoryContext, o: ta.Any) -> Marshaler:
        raise NotImplementedError

    @abc.abstractmethod
    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, o: ta.Any) -> Unmarshaler:
        raise NotImplementedError
