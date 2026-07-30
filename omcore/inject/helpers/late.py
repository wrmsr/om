"""
A minor tidiness for hiding refs to [Async]Injector in circ-dep workarounds. Unfortunately unsuitable outside of
injection modules due to it itself being in here (as user code shouldn't reference injector guts), but at least it's
something.
"""
import abc
import typing as ta
import weakref

from ... import check
from ... import lang
from ... import reflect as rfl
from ..binder import bind
from ..elements import Elements
from ..elements import as_elements
from ..errors import DeadInjectorError
from ..injector import AsyncInjector
from ..inspect import KwargsTarget
from ..keys import Key
from ..keys import as_key
from ..sync import Injector


T = ta.TypeVar('T')


##


class Late(lang.Abstract, ta.Generic[T]):
    @abc.abstractmethod
    def __call__(self) -> T:
        raise NotImplementedError


class AsyncLate(lang.Abstract, ta.Generic[T]):
    @abc.abstractmethod
    def __call__(self) -> ta.Awaitable[T]:
        raise NotImplementedError


#


def _make_late_fn(i: ta.Any, key: Key) -> ta.Callable[[], ta.Any]:
    # The injector is held weakly: a late must not pin - or, when held by a scope-cached service, cycle with - the
    # injector whose graph it came from. A late that outlives its injector (eg. reached through a service extracted
    # from a dropped graph) raises loudly rather than resolving stale.
    wr = weakref.ref(i)

    def late_fn():
        if (li := wr()) is None:
            raise DeadInjectorError
        return li.provide(key)

    return late_fn


def _bind_late(
        injector_cls: type,
        late_cls: ta.Any,
        inner: ta.Any,
        outer: ta.Any | None = None,
) -> Elements:
    inner_key = as_key(inner)

    outer_key: Key
    outer_fac: ta.Callable[[ta.Any], ta.Any]
    if outer is None:
        inner_ann = rfl.to_runtime_annotation(inner_key.rty)
        outer_ann = late_cls[inner_ann]
        outer_key = Key(rfl.reflect_type(outer_ann), tag=inner_key.tag)
        outer_fac = lang.identity
    else:
        outer_key = as_key(outer)
        outer_pty = check.isinstance(rfl.get_proper_type(outer_key.rty), rfl.Instance).type.runtime_object
        outer_cls = check.isinstance(outer_pty, type)
        outer_fac = outer_cls

    return as_elements(
        bind(outer_key, to_fn=KwargsTarget.of(  # noqa
            lambda i: outer_fac(_make_late_fn(i, inner_key)),
            i=injector_cls,
        )),
    )


def bind_late(inner: ta.Any, outer: ta.Any | None = None) -> Elements:
    return _bind_late(Injector, Late, inner, outer)


def bind_async_late(inner: ta.Any, outer: ta.Any | None = None) -> Elements:
    return _bind_late(AsyncInjector, AsyncLate, inner, outer)
