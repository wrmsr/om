import abc
import typing as ta

from ... import dataclasses as dc
from ... import lang
from ..dependencies import Dependencies
from ..injector import AsyncInjector
from ..inspect import KwargsTarget
from ..providers import AsyncFnProvider
from ..providers import ConstProvider
from ..providers import CtorProvider
from ..providers import FnProvider
from ..providers import LinkProvider
from ..providers import Provider


##


class ProviderImpl(lang.Abstract):
    ##
    # **Shallow** accessors.

    @property
    def providers(self) -> ta.Sequence[Provider]:
        return ()

    @property
    def children(self) -> ta.Sequence[ProviderImpl]:
        return ()

    def known_dependencies(self) -> Dependencies | None:
        return None

    ##

    @ta.final
    def traverse(self) -> ta.Iterator[ProviderImpl]:
        yield self
        for child in self.children:
            yield from child.traverse()

    @ta.final
    @lang.cached_function
    def deep_known_dependencies(self) -> Dependencies | None:
        return Dependencies.merge(*[
            ds
            for c in self.traverse()
            for ds in [c.known_dependencies()]
            if ds
        ]) or None

    ##

    @abc.abstractmethod
    def provide(self, injector: AsyncInjector) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError


##


@dc.dataclass(frozen=True, eq=False)
class InternalProvider(Provider):
    impl: ProviderImpl


##


@dc.dataclass(frozen=True, eq=False)
class AsyncCallableProviderImpl(ProviderImpl, lang.Final):
    p: AsyncFnProvider
    kt: KwargsTarget

    @property
    def providers(self) -> ta.Sequence[Provider]:
        return (self.p,)

    def known_dependencies(self) -> Dependencies | None:
        return self.kt.kwargs.dependencies or None

    #

    async def provide(self, injector: AsyncInjector) -> ta.Any:
        return await (await injector.inject(self.kt))


##


@dc.dataclass(frozen=True, eq=False)
class CallableProviderImpl(ProviderImpl, lang.Final):
    p: FnProvider | CtorProvider
    kt: KwargsTarget

    @property
    def providers(self) -> ta.Sequence[Provider]:
        return (self.p,)

    def known_dependencies(self) -> Dependencies | None:
        return self.kt.kwargs.dependencies or None

    #

    async def provide(self, injector: AsyncInjector) -> ta.Any:
        return await injector.inject(self.kt)


##


@dc.dataclass(frozen=True, eq=False)
class ConstProviderImpl(ProviderImpl, lang.Final):
    p: ConstProvider

    @property
    def providers(self) -> ta.Sequence[Provider]:
        return (self.p,)

    #

    async def provide(self, injector: AsyncInjector) -> ta.Any:
        return self.p.v


##


@dc.dataclass(frozen=True, eq=False)
class LinkProviderImpl(ProviderImpl, lang.Final):
    p: LinkProvider

    @property
    def providers(self) -> ta.Sequence[Provider]:
        return (self.p,)

    def known_dependencies(self) -> Dependencies:
        return Dependencies(frozenset([self.p.k]))

    #

    async def provide(self, injector: AsyncInjector) -> ta.Any:
        return await injector.provide(self.p.k)
