import collections
import itertools
import typing as ta
import weakref

from .. import cached
from .. import dataclasses as dc
from .. import lang
from .keys import Key
from .types import AnyInjector


##


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True, default_repr_fn=lang.opt_repr)
class KeyChainEntry:
    key: Key

    _: dc.KW_ONLY

    injector_ref: weakref.ref[AnyInjector] | None = None

    @property
    def injector(self) -> AnyInjector | None:
        if (ir := self.injector_ref) is None:
            return None
        return ir()


@ta.final
class KeyChain(ta.Sequence[KeyChainEntry]):
    def __init__(self) -> None:
        super().__init__()

        self._entries: collections.deque[KeyChainEntry] = collections.deque()

    def __hash__(self) -> int:
        raise TypeError(self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}([{", ".join(map(repr, self))}])'

    #

    @lang.opt_self
    def add(
            self: KeyChain | None,
            *keys: Key,
            injector: AnyInjector | None = None,
            where: ta.Literal['head', 'tail'] = 'tail',
    ) -> KeyChain:
        if (chain := self) is None:
            chain = KeyChain()

        entries = [
            KeyChainEntry(
                key,
                injector_ref=weakref.ref(injector) if injector is not None else None,
            )
            for key in keys
        ]

        match where:
            case 'head':
                chain._entries.extendleft(entries)
            case 'tail':
                chain._entries.extend(entries)
            case _:
                raise ValueError(where)

        return chain

    #

    def render(
            self,
            *,
            indent: str | None = '  ',
            suffix: str | None = ' ->',

            head: ta.Sequence[KeyChainEntry] | None = None,
            tail: ta.Sequence[KeyChainEntry] | None = None,
    ) -> str:
        head = head or ()
        tail = tail or ()

        def render_entry(e: KeyChainEntry) -> str:
            # TODO: add injector
            return repr(e.key)

        cl = len(self._entries) + len(head) + len(tail)
        return '\n'.join([
            ''.join([
                indent or '',
                render_entry(e),
                suffix if suffix and i < cl - 1 else '',
            ])
            for i, e in enumerate(itertools.chain(head, self._entries, tail))
        ])

    #

    def __bool__(self) -> int:
        return len(self._entries) > 0

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> ta.Iterator[KeyChainEntry]:
        return iter(self._entries)

    @ta.overload
    def __getitem__(self, index: int, /) -> KeyChainEntry: ...

    @ta.overload
    def __getitem__(self, index: slice[int | None], /) -> ta.Sequence[KeyChainEntry]: ...  # noqa

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._entries[index]

        elif isinstance(index, slice):
            return tuple(itertools.islice(self, *index.indices(len(self._entries))))

        else:
            raise TypeError(index)

    #

    _cache_: _Cache | None = None

    def _cache(self) -> _Cache:
        if (cache := self._cache_) is None:
            cache = self._cache_ = KeyChain._Cache(self)
        return cache

    def _invalidate_cache(self) -> None:
        self._cache_ = None

    class _Cache:
        def __init__(self, kc: KeyChain) -> None:
            super().__init__()

            self._kc = kc

        @cached.property
        def keys(self) -> ta.Sequence[Key]:
            return tuple(e.key for e in self._kc._entries)  # noqa

    @property
    def keys(self) -> ta.Sequence[Key]:
        return self._cache().keys

    #

    def injectors(self) -> ta.AbstractSet[AnyInjector]:
        dct: dict[AnyInjector, None] = {}
        for e in self._entries:
            if (i := e.injector) is not None and i not in dct:
                dct[i] = None
        return dct.keys()
