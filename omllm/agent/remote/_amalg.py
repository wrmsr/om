#!/usr/bin/env python3
# noinspection DuplicatedCode
# @om-lite
# @om-script
# @om-generated
# @om-amalg-output main.py
# @om-git-diff-omit
# ruff: noqa: PYI034 UP006 UP007 UP036 UP037 UP043 UP045
"""Entrypoint for the ephemeral remote agent payload launched through pyremote."""
import abc
import asyncio
import base64
import collections
import collections.abc
import dataclasses as dc
import datetime
import decimal
import enum
import fractions
import functools
import glob as glob_
import hashlib
import inspect
import json
import os
import platform
import pwd
import select
import signal
import site
import stat as stat_
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import types
import typing as ta
import uuid
import weakref
import zlib


########################################


if sys.version_info < (3, 8):
    raise OSError(f'Requires python (3, 8), got {sys.version_info} from {sys.executable}')  # noqa


def __om_amalg__():  # noqa
    return dict(
        src_files=[
            dict(path='../../../omcore/asyncs/asyncio/streams.py', sha1='980c47ed90047f93bdcc9effe70d5249eeeb8eab'),
            dict(path='../../../omcore/lite/abstract.py', sha1='a2fc3f3697fa8de5247761e9d554e70176f37aac'),
            dict(path='../../../omcore/lite/cached.py', sha1='4f5466ce20a485428519e284b2a388a9ef8e4786'),
            dict(path='../../../omcore/lite/check.py', sha1='62b9ccea94c4f7bcef97e7adae8674b8cb11d4af'),
            dict(path='../../../omcore/lite/objects.py', sha1='9566bbf3530fd71fcc56321485216b592fae21e9'),
            dict(path='../../../omcore/lite/reflect.py', sha1='64d51b5de91131349d56e4154ed235eb7fff4fd0'),
            dict(path='../../../omcore/lite/strings.py', sha1='b31b8e4b0e4fec4562ea3fa602e4ef2475e5fe7c'),
            dict(path='../../../omcore/os/pyremote/core.py', sha1='a663184c584cf8d8449981d424337f8fbb61c7e8'),
            dict(path='../../../omcore/lite/marshal.py', sha1='9b3f4ff802344313147f412f8f028922afc52b2f'),
            dict(path='protocol.py', sha1='374a0c94df0b7469b6ce29c61848c83e0517f718'),
            dict(path='../../core/rpc/errors.py', sha1='41e06a92d0a0139b6fc0530fe5892071c34cfd23'),
            dict(path='../../core/rpc/handlers.py', sha1='6910c32940e50afb033686045241efc5a0528824'),
            dict(path='../../core/rpc/messages.py', sha1='fdab342fadbd32f1d4930bc0d1ee6fbf370e9395'),
            dict(path='../../core/rpc/channels.py', sha1='8f49bf867159274422557a1f681ecdbffde5c887'),
            dict(path='../../core/rpc/peers.py', sha1='50e7bae64a1e909f546bbb30ab7dbf03cee14fab'),
            dict(path='server.py', sha1='f5c9e900b7439cd1c234517ca88e717c5ba904db'),
            dict(path='main.py', sha1='12eef0f46ab416d4ccc8ae492388e5466d5f6be1'),
        ],
    )


########################################


# ../../../omcore/lite/abstract.py
T = ta.TypeVar('T')

# ../../../omcore/lite/cached.py
CallableT = ta.TypeVar('CallableT', bound=ta.Callable)

# ../../../omcore/lite/check.py
SizedT = ta.TypeVar('SizedT', bound=ta.Sized)
CheckMessage = ta.Union[str, ta.Callable[..., ta.Optional[str]], ta.Type[Exception], None]  # ta.TypeAlias
CheckLateConfigureFn = ta.Callable[['Checks'], None]  # ta.TypeAlias
CheckOnRaiseFn = ta.Callable[[Exception], None]  # ta.TypeAlias
CheckExceptionFactory = ta.Callable[..., Exception]  # ta.TypeAlias
CheckArgsRenderer = ta.Callable[..., ta.Optional[str]]  # ta.TypeAlias

# ../../core/rpc/handlers.py
RpcMethod = ta.Callable[[ta.Any], ta.Awaitable[ta.Any]]  # ta.TypeAlias
RpcNotificationErrorHandler = ta.Callable[['RpcNotificationMessage', BaseException], None]  # ta.TypeAlias

# ../../core/rpc/peers.py
RpcPeerCloseCallback = ta.Callable[['RpcPeer'], None]  # ta.TypeAlias


########################################
# ../../../../omcore/asyncs/asyncio/streams.py


##


ASYNCIO_DEFAULT_BUFFER_LIMIT = 2 ** 16


async def asyncio_open_stream_reader(
        f: ta.IO,
        loop: ta.Any = None,
        *,
        limit: int = ASYNCIO_DEFAULT_BUFFER_LIMIT,
) -> asyncio.StreamReader:
    if loop is None:
        loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader(limit=limit, loop=loop)
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader, loop=loop),
        f,
    )

    return reader


class AsyncioWritePipeProtocol(asyncio.streams.FlowControlMixin):
    """
    The protocol behind `asyncio_open_stream_writer`: flow control, plus the close waiter that
    `StreamWriter.wait_closed` awaits through the protocol's `_get_close_waiter` hook. A bare `FlowControlMixin` raises
    NotImplementedError there.
    """

    def __init__(self, loop: ta.Any = None) -> None:
        super().__init__(loop=loop)

        self._close_waiter: asyncio.Future = self._loop.create_future()  # type: ignore[attr-defined]

    def connection_lost(self, exc: ta.Optional[Exception]) -> None:
        if not self._close_waiter.done():
            if exc is None:
                self._close_waiter.set_result(None)
            else:
                self._close_waiter.set_exception(exc)
                # Marked retrieved: a failed close nobody waits for is not an unhandled error.
                self._close_waiter.exception()
        super().connection_lost(exc)

    def _get_close_waiter(self, stream: asyncio.StreamWriter) -> asyncio.Future:
        return self._close_waiter


async def asyncio_open_stream_writer(
        f: ta.IO,
        loop: ta.Any = None,
) -> asyncio.StreamWriter:
    if loop is None:
        loop = asyncio.get_running_loop()

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: AsyncioWritePipeProtocol(loop=loop),
        f,
    )

    return asyncio.streams.StreamWriter(
        writer_transport,
        writer_protocol,
        None,
        loop,
    )


########################################
# ../../../../omcore/lite/abstract.py


##


_ABSTRACT_METHODS_ATTR = '__abstractmethods__'
_IS_ABSTRACT_METHOD_ATTR = '__isabstractmethod__'


def is_abstract_method(obj: ta.Any) -> bool:
    return bool(getattr(obj, _IS_ABSTRACT_METHOD_ATTR, False))


def compute_abstract_methods(cls: type) -> ta.FrozenSet[str]:
    # ~> https://github.com/python/cpython/blob/f3476c6507381ca860eec0989f53647b13517423/Modules/_abc.c#L358

    # Stage 1: direct abstract methods

    abstracts = {
        a
        # Get items as a list to avoid mutation issues during iteration
        for a, v in list(cls.__dict__.items())
        if is_abstract_method(v)
    }

    # Stage 2: inherited abstract methods

    for base in cls.__bases__:
        # Get __abstractmethods__ from base if it exists
        if (base_abstracts := getattr(base, _ABSTRACT_METHODS_ATTR, None)) is None:
            continue

        # Iterate over abstract methods in base
        for key in base_abstracts:
            # Check if this class has an attribute with this name
            try:
                value = getattr(cls, key)
            except AttributeError:
                # Attribute not found in this class, skip
                continue

            # Check if it's still abstract
            if is_abstract_method(value):
                abstracts.add(key)

    return frozenset(abstracts)


def update_abstracts(cls: ta.Type[T], *, force: bool = False) -> ta.Type[T]:
    if not force and not hasattr(cls, _ABSTRACT_METHODS_ATTR):
        # Per stdlib: We check for __abstractmethods__ here because cls might by a C implementation or a python
        # implementation (especially during testing), and we want to handle both cases.
        return cls

    abstracts = compute_abstract_methods(cls)
    setattr(cls, _ABSTRACT_METHODS_ATTR, abstracts)
    return cls


#


class AbstractTypeError(TypeError):
    pass


_FORCE_ABSTRACT_ATTR = '__forceabstract__'


class Abstract:
    """
    Different from, but interoperable with, abc.ABC / abc.ABCMeta:

     - This raises AbstractTypeError during class creation, not instance instantiation - unless Abstract or abc.ABC are
       explicitly present in the class's direct bases.
     - This will forbid instantiation of classes with Abstract in their direct bases even if there are no
       abstractmethods left on the class.
     - This is a mixin, not a metaclass.
     - As it is not an ABCMeta, this does not support virtual base classes. As a result, operations like `isinstance`
       and `issubclass` are ~7x faster.
     - It additionally enforces a base class order of (Abstract, abc.ABC) to preemptively prevent common mro conflicts.

    If not mixed-in with an ABCMeta, it will update __abstractmethods__ itself.
    """

    __slots__ = ()

    __abstractmethods__: ta.ClassVar[ta.FrozenSet[str]] = frozenset()

    #

    def __forceabstract__(self):
        raise TypeError

    # This is done manually, rather than through @abc.abstractmethod, to mask it from static analysis.
    setattr(__forceabstract__, _IS_ABSTRACT_METHOD_ATTR, True)

    #

    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        setattr(
            cls,
            _FORCE_ABSTRACT_ATTR,
            getattr(Abstract, _FORCE_ABSTRACT_ATTR) if Abstract in cls.__bases__ else False,
        )

        super().__init_subclass__(**kwargs)

        if not (Abstract in cls.__bases__ or abc.ABC in cls.__bases__):
            if ams := compute_abstract_methods(cls):
                amd = {
                    a: mcls
                    for mcls in cls.__mro__[::-1]
                    for a in ams
                    if a in mcls.__dict__
                }

                raise AbstractTypeError(
                    f'Cannot subclass abstract class {cls.__name__} with abstract methods: ' +
                    ', '.join(sorted([
                        '.'.join([
                            *([
                                *([m] if (m := getattr(c, '__module__')) else []),
                                getattr(c, '__qualname__', getattr(c, '__name__')),
                            ] if c is not None else '?'),
                            a,
                        ])
                        for a in ams
                        for c in [amd.get(a)]
                    ])),
                )

        xbi = (Abstract, abc.ABC)  # , ta.Generic ?
        bis = [(cls.__bases__.index(b), b) for b in xbi if b in cls.__bases__]
        if bis != sorted(bis):
            raise TypeError(
                f'Abstract subclass {cls.__name__} must have proper base class order of '
                f'({", ".join(getattr(b, "__name__") for b in xbi)}), got: '
                f'({", ".join(getattr(b, "__name__") for _, b in sorted(bis))})',
            )

        if not isinstance(cls, abc.ABCMeta):
            update_abstracts(cls, force=True)


########################################
# ../../../../omcore/lite/cached.py


##


class _AbstractCachedNullary:
    def __init__(self, fn):
        super().__init__()

        self._fn = fn
        self._value = self._missing = object()
        functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):  # noqa
        raise TypeError

    def __get__(self, instance, owner=None):  # noqa
        if instance is None:
            return self
        bound = instance.__dict__[self._fn.__name__] = self.__class__(self._fn.__get__(instance, owner))
        return bound


##


class _CachedNullary(_AbstractCachedNullary):
    def __call__(self, *args, **kwargs):  # noqa
        if self._value is self._missing:
            self._value = self._fn()
        return self._value


def cached_nullary(fn: CallableT) -> CallableT:
    return _CachedNullary(fn)  # type: ignore


def static_init(fn: CallableT) -> CallableT:
    fn = cached_nullary(fn)
    fn()
    return fn


##


class _AsyncCachedNullary(_AbstractCachedNullary):
    async def __call__(self, *args, **kwargs):
        if self._value is self._missing:
            self._value = await self._fn()
        return self._value


def async_cached_nullary(fn):  # ta.Callable[..., T]) -> ta.Callable[..., T]:
    return _AsyncCachedNullary(fn)


##


cached_property = functools.cached_property


class _cached_property:  # noqa
    """Backported to pick up https://github.com/python/cpython/commit/056dfc71dce15f81887f0bd6da09d6099d71f979 ."""

    def __init__(self, func):
        self.func = func
        self.attrname = None  # noqa
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__

    _NOT_FOUND = object()

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name  # noqa
        elif name != self.attrname:
            raise TypeError(
                f'Cannot assign the same cached_property to two different names ({self.attrname!r} and {name!r}).',
            )

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError('Cannot use cached_property instance without calling __set_name__ on it.')

        try:
            cache = instance.__dict__
        except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
            raise TypeError(
                f"No '__dict__' attribute on {type(instance).__name__!r} instance to cache {self.attrname!r} property.",
            ) from None

        val = cache.get(self.attrname, self._NOT_FOUND)

        if val is self._NOT_FOUND:
            val = self.func(instance)
            try:
                cache[self.attrname] = val
            except TypeError:
                raise TypeError(
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance does not support item "
                    f"assignment for caching {self.attrname!r} property.",
                ) from None

        return val


globals()['cached_property'] = _cached_property


########################################
# ../../../../omcore/lite/check.py
"""
TODO:
 - def maybe(v: lang.Maybe[T])
 - def not_ ?
 - ** class @dataclass Raise - user message should be able to be an exception type or instance or factory
"""


##


class Checks:
    def __init__(self) -> None:
        super().__init__()

        self._config_lock = threading.RLock()
        self._on_raise_fns: ta.Sequence[CheckOnRaiseFn] = []
        self._exception_factory: CheckExceptionFactory = Checks.default_exception_factory
        self._args_renderer: ta.Optional[CheckArgsRenderer] = None
        self._late_configure_fns: ta.Sequence[CheckLateConfigureFn] = []

    #

    def register_on_raise(self, fn: CheckOnRaiseFn) -> None:
        with self._config_lock:
            self._on_raise_fns = [*self._on_raise_fns, fn]

    def unregister_on_raise(self, fn: CheckOnRaiseFn) -> None:
        with self._config_lock:
            self._on_raise_fns = [e for e in self._on_raise_fns if e != fn]

    #

    def register_on_raise_breakpoint_if_env_var_set(self, key: str) -> None:
        import os

        def on_raise(exc: Exception) -> None:  # noqa
            if key in os.environ:
                breakpoint()  # noqa

        self.register_on_raise(on_raise)

    #

    @staticmethod
    def default_exception_factory(exc_cls: ta.Type[Exception], *args, **kwargs) -> Exception:
        return exc_cls(*args, **kwargs)  # noqa

    def set_exception_factory(self, factory: CheckExceptionFactory) -> None:
        self._exception_factory = factory

    def set_args_renderer(self, renderer: ta.Optional[CheckArgsRenderer]) -> None:
        self._args_renderer = renderer

    #

    def register_late_configure(self, fn: CheckLateConfigureFn) -> None:
        with self._config_lock:
            self._late_configure_fns = [*self._late_configure_fns, fn]

    def _late_configure(self) -> None:
        if not self._late_configure_fns:
            return

        with self._config_lock:
            if not (lc := self._late_configure_fns):
                return

            for fn in lc:
                fn(self)

            self._late_configure_fns = []

    #

    class _ArgsKwargs:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    def _raise(
            self,
            exception_type: ta.Type[Exception],
            default_message: str,
            message: CheckMessage,
            ak: _ArgsKwargs = _ArgsKwargs(),
            *,
            render_fmt: ta.Optional[str] = None,
    ) -> ta.NoReturn:
        self._late_configure()

        exc_args: tuple = ()

        if isinstance(message, type):
            exception_type = message

        else:
            if callable(message):
                message = ta.cast(ta.Callable, message)(*ak.args, **ak.kwargs)
                if isinstance(message, tuple):
                    message, *exc_args = message  # type: ignore

            if message is None:
                message = default_message

            if render_fmt is not None and (af := self._args_renderer) is not None:
                rendered_args = af(render_fmt, *ak.args)
                if rendered_args is not None:
                    message = f'{message} : {rendered_args}'

            exc_args = (message, *exc_args)

        exc = self._exception_factory(
            exception_type,
            *exc_args,
            *ak.args,
            **ak.kwargs,
        )

        for fn in self._on_raise_fns:
            fn(exc)

        raise exc

    #

    def _unpack_isinstance_spec(self, spec: ta.Any) -> ta.Any:
        if spec == ta.Any:
            return object
        if spec is None:
            return None.__class__
        if not isinstance(spec, tuple):
            return spec
        if ta.Any in spec:
            return object
        if None in spec:
            spec = tuple(filter(None, spec)) + (None.__class__,)  # noqa
        return spec

    @ta.overload
    def isinstance(self, v: ta.Any, spec: ta.Type[T], msg: CheckMessage = None, /) -> T: ...

    @ta.overload
    def isinstance(self, v: ta.Any, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Any: ...

    def isinstance(self, v, spec, msg=None):
        if not isinstance(v, spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)):  # noqa
            self._raise(
                TypeError,
                'Must be instance',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='not isinstance(%s, %s)',
            )

        return v

    @ta.overload
    def of_isinstance(self, spec: ta.Type[T], msg: CheckMessage = None, /) -> ta.Callable[[ta.Any], T]: ...

    @ta.overload
    def of_isinstance(self, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Callable[[ta.Any], ta.Any]: ...

    def of_isinstance(self, spec, msg=None, /):
        spec = spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)  # noqa

        def inner(v):
            return self.isinstance(v, spec, msg)

        return inner

    def cast(self, v: ta.Any, cls: ta.Type[T], msg: CheckMessage = None, /) -> T:
        if not isinstance(v, cls):
            self._raise(
                TypeError,
                'Must be instance',
                msg,
                Checks._ArgsKwargs(v, cls),
            )

        return v

    def of_cast(self, cls: ta.Type[T], msg: CheckMessage = None, /) -> ta.Callable[[T], T]:
        def inner(v):
            return self.cast(v, cls, msg)

        return inner

    def not_isinstance(self, v: T, spec: ta.Any, msg: CheckMessage = None, /) -> T:  # noqa
        if isinstance(v, spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)):  # noqa
            self._raise(
                TypeError,
                'Must not be instance',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='isinstance(%s, %s)',
            )

        return v

    def of_not_isinstance(self, spec: ta.Any, msg: CheckMessage = None, /) -> ta.Callable[[T], T]:
        spec = spec if (st := type(spec)) is type or (st is tuple and all(type(x) is type for x in spec)) else self._unpack_isinstance_spec(spec)  # noqa

        def inner(v):
            return self.not_isinstance(v, spec, msg)

        return inner

    ##

    def issubclass(self, v: ta.Type[T], spec: ta.Any, msg: CheckMessage = None, /) -> ta.Type[T]:  # noqa
        if not issubclass(v, spec):
            self._raise(
                TypeError,
                'Must be subclass',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='not issubclass(%s, %s)',
            )

        return v

    def not_issubclass(self, v: ta.Type[T], spec: ta.Any, msg: CheckMessage = None, /) -> ta.Type[T]:
        if issubclass(v, spec):
            self._raise(
                TypeError,
                'Must not be subclass',
                msg,
                Checks._ArgsKwargs(v, spec),
                render_fmt='issubclass(%s, %s)',
            )

        return v

    def not_issubclass_except_nameerror(self, v: ta.Type[T], spec: ta.Callable[[], type], msg: CheckMessage = None, /) -> ta.Type[T]:  # noqa
        try:
            c = spec()
        except NameError:
            return v

        if issubclass(v, c):
            self._raise(
                TypeError,
                'Must not be subclass',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='issubclass(%s, %s)',
            )

        return v

    #

    def in_(self, v: T, c: ta.Container[T], msg: CheckMessage = None, /) -> T:
        if v not in c:
            self._raise(
                ValueError,
                'Must be in',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='%s not in %s',
            )

        return v

    def not_in(self, v: T, c: ta.Container[T], msg: CheckMessage = None, /) -> T:
        if v in c:
            self._raise(
                ValueError,
                'Must not be in',
                msg,
                Checks._ArgsKwargs(v, c),
                render_fmt='%s in %s',
            )

        return v

    def empty(self, v: SizedT, msg: CheckMessage = None, /) -> SizedT:
        if len(v) != 0:
            self._raise(
                ValueError,
                'Must be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def iterempty(self, v: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Iterable[T]:
        it = iter(v)
        try:
            next(it)
        except StopIteration:
            pass
        else:
            self._raise(
                ValueError,
                'Must be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def not_empty(self, v: SizedT, msg: CheckMessage = None, /) -> SizedT:
        if len(v) == 0:
            self._raise(
                ValueError,
                'Must not be empty',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def unique(self, it: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Iterable[T]:
        dupes = [e for e, c in collections.Counter(it).items() if c > 1]
        if dupes:
            self._raise(
                ValueError,
                'Must be unique',
                msg,
                Checks._ArgsKwargs(it, dupes),
            )

        return it

    def single(self, obj: ta.Iterable[T], msg: CheckMessage = None, /) -> T:
        try:
            [value] = obj
        except ValueError:
            self._raise(
                ValueError,
                'Must be single',
                msg,
                Checks._ArgsKwargs(obj),
                render_fmt='%s',
            )

        return value

    def opt_single(self, obj: ta.Iterable[T], msg: CheckMessage = None, /) -> ta.Optional[T]:
        it = iter(obj)
        try:
            value = next(it)
        except StopIteration:
            return None

        try:
            next(it)
        except StopIteration:
            return value  # noqa

        self._raise(
            ValueError,
            'Must be empty or single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    async def async_single(self, obj: ta.AsyncIterable[T], msg: CheckMessage = None, /) -> T:
        ait = obj.__aiter__()

        try:
            try:
                value = await ait.__anext__()
            except StopAsyncIteration:
                pass

            else:
                try:
                    await ait.__anext__()
                except StopAsyncIteration:
                    return value

        finally:
            if inspect.isasyncgen(ait):
                await ait.aclose()

        self._raise(
            ValueError,
            'Must be single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    async def async_opt_single(self, obj: ta.AsyncIterable[T], msg: CheckMessage = None, /) -> ta.Optional[T]:
        ait = obj.__aiter__()

        try:
            try:
                value = await ait.__anext__()
            except StopAsyncIteration:
                return None

            try:
                await ait.__anext__()
            except StopAsyncIteration:
                return value  # noqa

        finally:
            if inspect.isasyncgen(ait):
                await ait.aclose()

        self._raise(
            ValueError,
            'Must be empty or single',
            msg,
            Checks._ArgsKwargs(obj),
            render_fmt='%s',
        )

        raise RuntimeError  # noqa

    #

    def none(self, v: ta.Any, msg: CheckMessage = None, /) -> None:
        if v is not None:
            self._raise(
                ValueError,
                'Must be None',
                msg,
                render_fmt='%s',
            )

    def not_none(self, v: ta.Optional[T], msg: CheckMessage = None, /) -> T:
        if v is None:
            self._raise(
                ValueError,
                'Must not be None',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    #

    def equal(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o != v:
            self._raise(
                ValueError,
                'Must be equal',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s != %s',
            )

        return v

    def not_equal(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o == v:
            self._raise(
                ValueError,
                'Must not be equal',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s == %s',
            )

        return v

    def is_(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o is not v:
            self._raise(
                ValueError,
                'Must be the same',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s is not %s',
            )

        return v

    def is_not(self, v: T, o: ta.Any, msg: CheckMessage = None, /) -> T:
        if o is v:
            self._raise(
                ValueError,
                'Must not be the same',
                msg,
                Checks._ArgsKwargs(v, o),
                render_fmt='%s is %s',
            )

        return v

    def callable(self, v: T, msg: CheckMessage = None, /) -> T:  # noqa
        if not callable(v):
            self._raise(
                TypeError,
                'Must be callable',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def non_empty_str(self, v: ta.Optional[str], msg: CheckMessage = None, /) -> str:
        if not isinstance(v, str) or not v:
            self._raise(
                ValueError,
                'Must be non-empty str',
                msg,
                Checks._ArgsKwargs(v),
                render_fmt='%s',
            )

        return v

    def replacing(self, expected: ta.Any, old: ta.Any, new: T, msg: CheckMessage = None, /) -> T:
        if old != expected:
            self._raise(
                ValueError,
                'Must be replacing',
                msg,
                Checks._ArgsKwargs(expected, old, new),
                render_fmt='%s -> %s -> %s',
            )

        return new

    def replacing_none(self, old: ta.Any, new: T, msg: CheckMessage = None, /) -> T:
        if old is not None:
            self._raise(
                ValueError,
                'Must be replacing None',
                msg,
                Checks._ArgsKwargs(old, new),
                render_fmt='%s -> %s',
            )

        return new

    #

    def arg(self, v: bool, msg: CheckMessage = None, /) -> None:
        if not v:
            self._raise(
                RuntimeError,
                'Argument condition not met',
                msg,
                render_fmt='%s',
            )

    def state(self, v: bool, msg: CheckMessage = None, /) -> None:
        if not v:
            self._raise(
                RuntimeError,
                'State condition not met',
                msg,
                render_fmt='%s',
            )

    def inline(self, v: T, c: bool, msg: CheckMessage = None, /) -> T:
        if not c:
            self._raise(
                RuntimeError,
                'State condition not met',
                msg,
                render_fmt='%s',
            )
        return v


check = Checks()


########################################
# ../../../../omcore/lite/objects.py


##


def deep_subclasses(cls: ta.Type[T]) -> ta.Iterator[ta.Type[T]]:
    seen = set()
    todo = list(reversed(cls.__subclasses__()))
    while todo:
        cur = todo.pop()
        if cur in seen:
            continue
        seen.add(cur)
        yield cur
        todo.extend(reversed(cur.__subclasses__()))


##


def mro_owner_dict(
        instance_cls: type,
        owner_cls: ta.Optional[type] = None,
        *,
        bottom_up_key_order: bool = False,
        sort_keys: bool = False,
) -> ta.Mapping[str, ta.Tuple[type, ta.Any]]:
    if owner_cls is None:
        owner_cls = instance_cls

    mro = instance_cls.__mro__[-2::-1]
    try:
        pos = mro.index(owner_cls)
    except ValueError:
        raise TypeError(f'Owner class {owner_cls} not in mro of instance class {instance_cls}') from None

    dct: ta.Dict[str, ta.Tuple[type, ta.Any]] = {}
    if not bottom_up_key_order:
        for cur_cls in mro[:pos + 1][::-1]:
            for k, v in cur_cls.__dict__.items():
                if k not in dct:
                    dct[k] = (cur_cls, v)

    else:
        for cur_cls in mro[:pos + 1]:
            dct.update({k: (cur_cls, v) for k, v in cur_cls.__dict__.items()})

    if sort_keys:
        dct = dict(sorted(dct.items(), key=lambda t: t[0]))

    return dct


def mro_dict(
        instance_cls: type,
        owner_cls: ta.Optional[type] = None,
        *,
        bottom_up_key_order: bool = False,
        sort_keys: bool = False,
) -> ta.Mapping[str, ta.Any]:
    return {
        k: v
        for k, (o, v) in mro_owner_dict(
            instance_cls,
            owner_cls,
            bottom_up_key_order=bottom_up_key_order,
            sort_keys=sort_keys,
        ).items()
    }


def dir_dict(o: ta.Any) -> ta.Dict[str, ta.Any]:
    return {
        a: getattr(o, a)
        for a in dir(o)
    }


########################################
# ../../../../omcore/lite/reflect.py


##


_GENERIC_ALIAS_TYPES = (
    ta._GenericAlias,  # type: ignore  # noqa
    *([ta._SpecialGenericAlias] if hasattr(ta, '_SpecialGenericAlias') else []),  # noqa
    *([types.GenericAlias] if hasattr(types, 'GenericAlias') else []),  # noqa
)


def is_generic_alias(obj: ta.Any, *, origin: ta.Any = None) -> bool:
    return (
        isinstance(obj, _GENERIC_ALIAS_TYPES) and
        (origin is None or ta.get_origin(obj) is origin)
    )


# ta.get_origin returns the collections.abc class, never the typing alias.
is_callable_alias = functools.partial(is_generic_alias, origin=ta.get_origin(ta.Callable[..., ta.Any]))


##


_UNION_ALIAS_ORIGINS = frozenset([
    ta.get_origin(ta.Optional[int]),
    *(
        [
            ta.get_origin(int | None),
            ta.get_origin(getattr(ta, 'TypeVar')('_T') | None),
        ] if sys.version_info >= (3, 10) else ()
    ),
])


def is_union_alias(obj: ta.Any) -> bool:
    return ta.get_origin(obj) in _UNION_ALIAS_ORIGINS


#


def is_optional_alias(spec: ta.Any) -> bool:
    return (
        is_union_alias(spec) and
        len(ta.get_args(spec)) == 2 and
        any(a in (None, type(None)) for a in ta.get_args(spec))
    )


def get_optional_alias_arg(spec: ta.Any) -> ta.Any:
    [it] = [it for it in ta.get_args(spec) if it not in (None, type(None))]
    return it


##


def is_new_type(spec: ta.Any) -> bool:
    if isinstance(ta.NewType, type):
        return isinstance(spec, ta.NewType)
    else:
        # Before https://github.com/python/cpython/commit/c2f33dfc83ab270412bf243fb21f724037effa1a
        return isinstance(spec, types.FunctionType) and spec.__code__ is ta.NewType.__code__.co_consts[1]  # type: ignore  # noqa


def get_new_type_supertype(spec: ta.Any) -> ta.Any:
    return spec.__supertype__


##


def is_literal_type(spec: ta.Any) -> bool:
    if hasattr(ta, '_LiteralGenericAlias'):
        return isinstance(spec, ta._LiteralGenericAlias)  # noqa
    else:
        return (
            isinstance(spec, ta._GenericAlias) and  # type: ignore  # noqa
            spec.__origin__ is ta.Literal
        )


def get_literal_type_args(spec: ta.Any) -> ta.Iterable[ta.Any]:
    return spec.__args__


##


def type_form_repr(ty: ta.Any) -> str:
    if isinstance(ty, type):
        return f'{ty.__module__}.{ty.__qualname__}'

    elif ty is ta.Any:
        return 'typing.Any'

    elif is_optional_alias(ty):
        ety = get_optional_alias_arg(ty)
        return f'typing.Optional[{type_form_repr(ety)}]'

    elif is_union_alias(ty):
        args = ta.get_args(ty)
        return f'typing.Union[{", ".join(sorted(type_form_repr(a) for a in args))}]'

    elif is_callable_alias(ty):
        ptys, rty = ta.get_args(ty)
        return (
            f'typing.Callable[['
            f'{"..." if isinstance(ptys, types.EllipsisType) else ", ".join(type_form_repr(a) for a in ptys)}], '
            f'{type_form_repr(rty)}]'
        )

    elif is_literal_type(ty):
        args = ta.get_args(ty)
        return f'typing.Literal[{", ".join(sorted(repr(a) for a in args))}]'

    elif is_new_type(ty):
        raise NotImplementedError

    elif is_generic_alias(ty):
        origin = ta.get_origin(ty)
        args = ta.get_args(ty)
        if origin is tuple and args and isinstance(args[-1], types.EllipsisType):
            return (
                f'{type_form_repr(origin)}['
                f'{", ".join(type_form_repr(a) for a in args[:-1])}, ...]'
            )
        else:
            return (
                f'{type_form_repr(origin)}['
                f'{", ".join(type_form_repr(a) for a in args)}]'
            )

    else:
        raise TypeError(ty)


########################################
# ../../../../omcore/lite/strings.py


##


def camel_case(name: str, *, lower: bool = False) -> str:
    if not name:
        return ''
    s = ''.join(map(str.capitalize, name.split('_')))  # noqa
    if lower:
        s = s[0].lower() + s[1:]
    return s


def snake_case(name: str) -> str:
    uppers: list[int | None] = [i for i, c in enumerate(name) if c.isupper()]
    return '_'.join([name[l:r].lower() for l, r in zip([None, *uppers], [*uppers, None])]).strip('_')


##


def is_dunder(name: str) -> bool:
    return (
        name[:2] == name[-2:] == '__' and
        name[2:3] != '_' and
        name[-3:-2] != '_' and
        len(name) > 4
    )


def is_sunder(name: str) -> bool:
    return (
        len(name) > 2 and
        name[0] == name[-1] == '_' and
        name[1:2] != '_' and
        name[-2:-1] != '_'
    )


##


def strip_with_newline(s: str) -> str:
    if not s:
        return ''
    return s.strip() + '\n'


@ta.overload
def split_keep_delimiter(s: str, d: str) -> ta.List[str]: ...


@ta.overload
def split_keep_delimiter(s: bytes, d: bytes) -> ta.List[bytes]: ...


def split_keep_delimiter(s, d):
    if not d:
        raise ValueError(d)
    dl = len(d)
    ps = []
    i = 0
    while i < len(s):
        if (n := s.find(d, i)) < i:
            ps.append(s[i:])
            break
        ps.append(s[i:n + dl])
        i = n + dl
    return ps


##


FORMAT_NUM_BYTES_SUFFIXES: ta.Sequence[str] = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB']


def format_num_bytes(num_bytes: int) -> str:
    for i, suffix in enumerate(FORMAT_NUM_BYTES_SUFFIXES):
        value = num_bytes / 1024 ** i
        if num_bytes < 1024 ** (i + 1):
            if value.is_integer():
                return f'{int(value)}{suffix}'
            else:
                return f'{value:.2f}{suffix}'

    return f'{num_bytes / 1024 ** (len(FORMAT_NUM_BYTES_SUFFIXES) - 1):.2f}{FORMAT_NUM_BYTES_SUFFIXES[-1]}'


########################################
# ../../../../omcore/os/pyremote/core.py
"""
Basically (the first part of) this: https://mitogen.networkgenomics.com/howitworks.html

TODO:
 - log: ta.Optional[logging.Logger] = None + log.debug's
"""


##


@dc.dataclass(frozen=True)
class PyremoteBootstrapOptions:
    debug: bool = False

    DEFAULT_MAIN_NAME_OVERRIDE: ta.ClassVar[str] = '__pyremote__'
    main_name_override: ta.Optional[str] = DEFAULT_MAIN_NAME_OVERRIDE


##


@dc.dataclass(frozen=True)
class PyremoteEnvInfo:
    @dc.dataclass(frozen=True)
    class Sys:
        base_prefix: str
        byteorder: str
        defaultencoding: str
        exec_prefix: str
        executable: str
        implementation_name: str
        path: ta.List[str]
        platform: str
        prefix: str
        version: str
        version_info: ta.List[ta.Union[int, str]]

    sys: Sys

    @dc.dataclass(frozen=True)
    class Platform:
        architecture: ta.List[str]
        machine: str
        platform: str
        processor: str
        system: str
        release: str
        version: str

    platform: Platform

    @dc.dataclass(frozen=True)
    class Site:
        userbase: str

    site: Site

    @dc.dataclass(frozen=True)
    class Os:
        cwd: str
        gid: int
        loadavg: ta.List[float]
        login: ta.Optional[str]
        pgrp: int
        pid: int
        ppid: int
        uid: int

    os: Os

    @dc.dataclass(frozen=True)
    class Pw:
        name: str
        uid: int
        gid: int
        gecos: str
        dir: str
        shell: str

    pw: Pw

    @dc.dataclass(frozen=True)
    class Env:
        path: ta.Optional[str]

    env: Env

    #

    def to_dict(self) -> dict:
        return {
            f.name: dc.asdict(v) if dc.is_dataclass(v := getattr(self, f.name)) else v  # type: ignore[arg-type]
            for f in dc.fields(self)
        }

    @classmethod
    def from_dict(cls, dct: dict) -> 'PyremoteEnvInfo':
        flds_dct = {f.name: f for f in dc.fields(cls)}
        return cls(**{
            k: ft(**v) if isinstance((ft := flds_dct[k].type), type) and dc.is_dataclass(ft) is not None else v
            for k, v in dct.items()
        })


def _get_pyremote_env_info() -> PyremoteEnvInfo:
    os_uid = os.getuid()

    pw = pwd.getpwuid(os_uid)

    os_login: ta.Optional[str]
    try:
        os_login = os.getlogin()
    except OSError:
        os_login = None

    return PyremoteEnvInfo(
        sys=PyremoteEnvInfo.Sys(
            base_prefix=sys.base_prefix,
            byteorder=sys.byteorder,
            defaultencoding=sys.getdefaultencoding(),
            exec_prefix=sys.exec_prefix,
            executable=sys.executable,
            implementation_name=sys.implementation.name,
            path=sys.path,
            platform=sys.platform,
            prefix=sys.prefix,
            version=sys.version,
            version_info=list(sys.version_info),
        ),

        platform=PyremoteEnvInfo.Platform(
            architecture=list(platform.architecture()),
            machine=platform.machine(),
            platform=platform.platform(),
            processor=platform.processor(),
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
        ),

        site=PyremoteEnvInfo.Site(
            userbase=site.getuserbase(),
        ),

        os=PyremoteEnvInfo.Os(
            cwd=os.getcwd(),
            gid=os.getgid(),
            loadavg=list(os.getloadavg()),
            login=os_login,
            pgrp=os.getpgrp(),
            pid=os.getpid(),
            ppid=os.getppid(),
            uid=os_uid,
        ),

        pw=PyremoteEnvInfo.Pw(
            name=pw.pw_name,
            uid=pw.pw_uid,
            gid=pw.pw_gid,
            gecos=pw.pw_gecos,
            dir=pw.pw_dir,
            shell=pw.pw_shell,
        ),

        env=PyremoteEnvInfo.Env(
            path=os.environ.get('PATH'),
        ),
    )


##


class _PyremoteBootstrapConsts:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    TIMEOUT_S = 3 * 60
    GRACE_S = 10
    REAP_S = 3
    REAP_SLEEP_S = .02

    INPUT_FD = 100
    SRC_FD = 101
    DISARM_FD = 102

    WATCHDOG_PID_VAR = '_OPYR_WATCHDOG_PID'
    CHILD_PID_VAR = '_OPYR_CHILD_PID'
    ARGV0_VAR = '_OPYR_ARGV0'
    CONTEXT_NAME_VAR = '_OPYR_CONTEXT_NAME'
    SRC_FILE_VAR = '_OPYR_SRC_FILE'
    OPTIONS_JSON_VAR = '_OPYR_OPTIONS_JSON'

    ACK0 = b'OPYR000\n'
    ACK1 = b'OPYR001\n'
    ACK2 = b'OPYR002\n'
    ACK3 = b'OPYR003\n'

    PROC_TITLE_FMT = '(pyremote:%s)'

    IMPORTS = (
        'base64',
        'os',
        'select',
        'signal',
        'struct',
        'sys',
        'time',
        'zlib',
    )


def _pyremote_bootstrap_main(context_name: str) -> None:
    # Setup watchdog
    dl = time.monotonic() + _PyremoteBootstrapConsts.TIMEOUT_S + _PyremoteBootstrapConsts.GRACE_S
    pp = os.getpid()
    dr, dw = os.pipe()
    pfd = None  # type: int | None
    try:
        pfd = os.pidfd_open(os.getpid())  # type: ignore[attr-defined,unused-ignore]
    except (AttributeError, OSError):
        pass

    if not (wp := os.fork()):  # noqa
        # Watchdog process

        # Survive group-wide signals the target survives
        for s in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM]:
            signal.signal(s, signal.SIG_IGN)

        # Cleanup fd's
        nfd = os.open(os.devnull, os.O_WRONLY)
        for fd in [0, 1]:
            os.dup2(nfd, fd)

        wrl = [dr] + ([pfd] if pfd is not None else [])
        while (rem := dl - time.monotonic()) > 0:
            if not wrl:
                time.sleep(rem)
                continue

            rdy, _, _ = select.select(wrl, [], [], rem)
            if pfd in rdy:
                # Target exited
                break

            if dr in rdy:
                if os.read(dr, 1):
                    break  # explicit disarm

                # EOF: target died (with no pidfd, ppid tells) or fd closed behind our back -> clock
                if pfd is None and os.getppid() != pp:
                    break

                wrl.remove(dr)

        else:
            # No break: deadline passed
            try:
                if pfd is not None:
                    signal.pidfd_send_signal(pfd, signal.SIGALRM)  # type: ignore[attr-defined,unused-ignore]
                    rdy, _, _ = select.select([pfd], [], [], _PyremoteBootstrapConsts.GRACE_S)
                    if rdy:
                        signal.pidfd_send_signal(pfd, signal.SIGKILL)  # type: ignore[attr-defined,unused-ignore]

                elif os.getppid() == pp:  # FIXME: TOCTOU :/
                    os.kill(pp, signal.SIGALRM)
                    time.sleep(_PyremoteBootstrapConsts.GRACE_S)
                    if os.getppid() == pp:
                        os.kill(pp, signal.SIGKILL)

            except ProcessLookupError:
                pass

        os._exit(0)

    else:
        # Finish watchdog setup
        os.close(dr)
        if pfd is not None:
            os.close(pfd)
        os.environ[_PyremoteBootstrapConsts.WATCHDOG_PID_VAR] = str(wp)

        # Install timeout
        def timeout(*_):
            raise TimeoutError

        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(_PyremoteBootstrapConsts.TIMEOUT_S)

        # Get pid
        pid = os.getpid()

        # Two copies of payload src to be sent to parent
        pr0, pw0 = os.pipe()
        pr1, pw1 = os.pipe()

        if (cp := os.fork()):
            # Parent process

            # Dup original stdin to comm_fd for use as comm channel
            os.dup2(0, _PyremoteBootstrapConsts.INPUT_FD)

            # Overwrite stdin (fed to python repl) with first copy of src
            os.dup2(pr0, 0)

            # Dup second copy of src to src_fd to recover after launch
            os.dup2(pr1, _PyremoteBootstrapConsts.SRC_FD)

            # Dup disarm fd to disarm_fd
            os.dup2(dw, _PyremoteBootstrapConsts.DISARM_FD)

            # Close remaining fd's
            for f in [pr0, pw0, pr1, pw1]:
                os.close(f)

            # Save vars
            env = os.environ
            exe = sys.executable
            env[_PyremoteBootstrapConsts.CHILD_PID_VAR] = str(cp)
            env[_PyremoteBootstrapConsts.ARGV0_VAR] = exe
            env[_PyremoteBootstrapConsts.CONTEXT_NAME_VAR] = context_name

            # Re-arm timeout. It survives the exec (with SIGALRM back at its default, terminating disposition) and
            # bounds finalization, which cancels it.
            signal.alarm(_PyremoteBootstrapConsts.TIMEOUT_S)

            # Start repl reading stdin from r0
            os.execl(exe, exe + (_PyremoteBootstrapConsts.PROC_TITLE_FMT % (context_name,)))

        else:
            # Child process

            # Write first ack
            os.write(1, _PyremoteBootstrapConsts.ACK0)

            # Write pid
            os.write(1, struct.pack('<Q', pid))

            # Read payload src from stdin
            payload_z_len = struct.unpack('<I', os.read(0, 4))[0]
            if len(payload_z := os.fdopen(0, 'rb').read(payload_z_len)) != payload_z_len:
                raise EOFError
            payload_src = zlib.decompress(payload_z)

            # Write both copies of payload src. Must write to w0 (parent stdin) before w1 (copy pipe) as pipe will
            # likely fill and block and need to be drained by pyremote_bootstrap_finalize running in parent.
            for w in [pw0, pw1]:
                fp = os.fdopen(w, 'wb', 0)
                fp.write(payload_src)
                fp.close()

            # Write second ack
            os.write(1, _PyremoteBootstrapConsts.ACK1)

            # Exit child
            os._exit(0)


##


def pyremote_build_bootstrap_source(context_name: str) -> str:
    if any(c in context_name for c in '\'"'):
        raise NameError(context_name)

    import inspect
    import textwrap
    bs_src = textwrap.dedent(inspect.getsource(_pyremote_bootstrap_main))

    for an, av in sorted(_PyremoteBootstrapConsts.__dict__.items(), key=lambda kv: -len(kv[0])):
        bs_src = bs_src.replace(f'_PyremoteBootstrapConsts.{an}', repr(av))

    bs_src = '\n'.join(
        cl
        for l in bs_src.splitlines()
        if (cl := (l.split('#')[0]).rstrip())
        if cl.strip()
    )

    bs_z = zlib.compress(bs_src.encode('utf-8'), 9)
    bs_z85 = base64.b85encode(bs_z).replace(b'\n', b'')
    if b'"' in bs_z85:
        raise ValueError(bs_z85)

    stmts = [
        f'import {",".join(_PyremoteBootstrapConsts.IMPORTS)}',
        f'exec(zlib.decompress(base64.b85decode(b"{bs_z85.decode("ascii")}")))',
        f'_pyremote_bootstrap_main("{context_name}")',
    ]

    cmd = ';'.join(stmts)
    return cmd


##


@dc.dataclass(frozen=True)
class PyremotePayloadRuntime:
    input: ta.BinaryIO
    output: ta.BinaryIO
    context_name: str
    payload_src: str
    options: PyremoteBootstrapOptions
    env_info: PyremoteEnvInfo


def pyremote_bootstrap_finalize() -> PyremotePayloadRuntime:
    # If src file var is not present we need to do initial finalization
    if _PyremoteBootstrapConsts.SRC_FILE_VAR not in os.environ:
        # Read second copy of payload src
        pr1 = os.fdopen(_PyremoteBootstrapConsts.SRC_FD, 'rb', 0)
        payload_src = pr1.read().decode('utf-8')
        pr1.close()

        # Reap boostrap child. Must be done after reading second copy of source because source may be too big to fit in
        # a pipe at once.
        os.waitpid(int(os.environ.pop(_PyremoteBootstrapConsts.CHILD_PID_VAR)), 0)

        # Read options
        options_json_len = struct.unpack('<I', os.read(_PyremoteBootstrapConsts.INPUT_FD, 4))[0]
        if len(options_json := os.read(_PyremoteBootstrapConsts.INPUT_FD, options_json_len)) != options_json_len:
            raise EOFError
        options = PyremoteBootstrapOptions(**json.loads(options_json.decode('utf-8')))

        # If debugging, re-exec as file
        if options.debug:
            # Write temp source file
            import tempfile
            tfd, tfn = tempfile.mkstemp('-pyremote.py')
            os.write(tfd, payload_src.encode('utf-8'))
            os.close(tfd)

            # Set vars
            os.environ[_PyremoteBootstrapConsts.SRC_FILE_VAR] = tfn
            os.environ[_PyremoteBootstrapConsts.OPTIONS_JSON_VAR] = options_json.decode('utf-8')

            # Re-exec temp file
            exe = os.environ[_PyremoteBootstrapConsts.ARGV0_VAR]
            context_name = os.environ[_PyremoteBootstrapConsts.CONTEXT_NAME_VAR]
            os.execl(exe, exe + (_PyremoteBootstrapConsts.PROC_TITLE_FMT % (context_name,)), tfn)

    else:
        # Load options json var
        options_json_str = os.environ.pop(_PyremoteBootstrapConsts.OPTIONS_JSON_VAR)
        options = PyremoteBootstrapOptions(**json.loads(options_json_str))

        # Read temp source file
        with open(os.environ.pop(_PyremoteBootstrapConsts.SRC_FILE_VAR)) as sf:
            payload_src = sf.read()

    # Restore vars
    sys.executable = os.environ.pop(_PyremoteBootstrapConsts.ARGV0_VAR)
    context_name = os.environ.pop(_PyremoteBootstrapConsts.CONTEXT_NAME_VAR)

    # Write third ack
    os.write(1, _PyremoteBootstrapConsts.ACK2)

    # Write env info
    env_info = _get_pyremote_env_info()
    env_info_json = json.dumps(env_info.to_dict(), indent=None, separators=(',', ':'))  # noqa
    os.write(1, struct.pack('<I', len(env_info_json)))
    os.write(1, env_info_json.encode('utf-8'))

    # Setup IO
    input = os.fdopen(_PyremoteBootstrapConsts.INPUT_FD, 'rb', 0)  # noqa
    output = os.fdopen(os.dup(1), 'wb', 0)  # noqa
    os.dup2(nfd := os.open(os.devnull, os.O_WRONLY), 1)
    os.close(nfd)

    if (mn := options.main_name_override) is not None:
        # Inspections like typing.get_type_hints need an entry in sys.modules.
        sys.modules[mn] = sys.modules['__main__']

    # Cancel the bootstrap's alarm. It was re-armed right before the exec into this interpreter and survived it, and
    # SIGALRM is at its default disposition here: left alone, it would terminate the payload TIMEOUT_S after launch.
    signal.alarm(0)

    # Disarm watchdog
    try:
        os.write(_PyremoteBootstrapConsts.DISARM_FD, b'1')
    except OSError:
        pass  # watchdog already gone; the reap below tells the story
    os.close(_PyremoteBootstrapConsts.DISARM_FD)

    # Reap watchdog. It's our unreaped child: its pid can't be recycled, so waiting on it and killing it are both
    # race-free. Wait on a pidfd where available, poll otherwise.
    wp = int(os.environ.pop(_PyremoteBootstrapConsts.WATCHDOG_PID_VAR))
    pfd = None  # type: int | None
    try:
        pfd = os.pidfd_open(wp)  # type: ignore[attr-defined,unused-ignore]
    except (AttributeError, OSError):
        pass

    try:
        if pfd is not None:
            try:
                # Readable once it has exited
                select.select([pfd], [], [], _PyremoteBootstrapConsts.REAP_S)
            finally:
                os.close(pfd)
            done, _ = os.waitpid(wp, os.WNOHANG)

        else:
            reap_dl = time.monotonic() + _PyremoteBootstrapConsts.REAP_S
            while not (done := os.waitpid(wp, os.WNOHANG)[0]) and time.monotonic() < reap_dl:
                time.sleep(_PyremoteBootstrapConsts.REAP_SLEEP_S)

        if not done:
            os.kill(wp, signal.SIGKILL)
            os.waitpid(wp, 0)
            raise TimeoutError(f'Timeout reaping pyremote watchdog pid {wp}')

    except ChildProcessError:
        pass

    # Write fourth ack
    output.write(_PyremoteBootstrapConsts.ACK3)

    # Return
    return PyremotePayloadRuntime(
        input=input,
        output=output,
        context_name=context_name,
        payload_src=payload_src,
        options=options,
        env_info=env_info,
    )


##


class PyremoteBootstrapDriver:
    def __init__(
            self,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions = PyremoteBootstrapOptions(),
    ) -> None:
        super().__init__()

        self._payload_src = payload_src
        self._options = options

        self._prepared_payload_src = self._prepare_payload_src(payload_src, options)
        self._payload_z = zlib.compress(self._prepared_payload_src.encode('utf-8'))

        self._options_json = json.dumps(dc.asdict(options), indent=None, separators=(',', ':')).encode('utf-8')  # noqa

    #

    @classmethod
    def _prepare_payload_src(
            cls,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions,
    ) -> str:
        parts: ta.List[str]
        if isinstance(payload_src, str):
            parts = [payload_src]
        else:
            parts = []
            for i, p in enumerate(payload_src):
                if i:
                    parts.append('\n\n')
                parts.append(p)

        if (mn := options.main_name_override) is not None:
            # Must go on same single line as first line of user payload to preserve '<stdin>' line numbers. If more
            # things wind up having to be done here, it can still be crammed on one line into a single `exec()`.
            parts.insert(0, f'__name__ = {mn!r}; ')

        if len(parts) == 1:
            return parts[0]
        else:
            return ''.join(parts)

    #

    @dc.dataclass(frozen=True)
    class Read:
        sz: int

    @dc.dataclass(frozen=True)
    class Write:
        d: bytes

    class ProtocolError(Exception):
        pass

    @dc.dataclass(frozen=True)
    class Result:
        pid: int
        env_info: PyremoteEnvInfo

    def gen(self) -> ta.Generator[ta.Union[Read, Write], ta.Optional[bytes], Result]:
        # Read first ack (after fork)
        yield from self._expect(_PyremoteBootstrapConsts.ACK0)

        # Read pid
        d = yield from self._read(8)
        pid = struct.unpack('<Q', d)[0]

        # Write payload src
        yield from self._write(struct.pack('<I', len(self._payload_z)))
        yield from self._write(self._payload_z)

        # Read second ack (after writing src copies)
        yield from self._expect(_PyremoteBootstrapConsts.ACK1)

        # Write options
        yield from self._write(struct.pack('<I', len(self._options_json)))
        yield from self._write(self._options_json)

        # Read third ack (after reaping child process)
        yield from self._expect(_PyremoteBootstrapConsts.ACK2)

        # Read env info
        d = yield from self._read(4)
        env_info_json_len = struct.unpack('<I', d)[0]
        d = yield from self._read(env_info_json_len)
        env_info_json = d.decode('utf-8')
        env_info = PyremoteEnvInfo.from_dict(json.loads(env_info_json))

        # Read fourth ack (after finalization completed)
        yield from self._expect(_PyremoteBootstrapConsts.ACK3)

        # Return
        return self.Result(
            pid=pid,
            env_info=env_info,
        )

    def _read(self, sz: int) -> ta.Generator[Read, bytes, bytes]:
        d = yield self.Read(sz)
        if not isinstance(d, bytes):
            raise self.ProtocolError(f'Expected bytes after read, got {d!r}')
        if len(d) != sz:
            raise self.ProtocolError(f'Read {len(d)} bytes, expected {sz}')
        return d

    def _expect(self, e: bytes) -> ta.Generator[Read, bytes, None]:
        d = yield from self._read(len(e))
        if d != e:
            raise self.ProtocolError(f'Read {d!r}, expected {e!r}')

    def _write(self, d: bytes) -> ta.Generator[Write, ta.Optional[bytes], None]:
        i = yield self.Write(d)
        if i is not None:
            raise self.ProtocolError('Unexpected input after write')

    #

    def run(
            self,
            input: ta.IO,  # noqa
            output: ta.IO,
    ) -> Result:
        gen = self.gen()

        gi: ta.Optional[bytes] = None
        while True:
            try:
                if gi is not None:
                    go = gen.send(gi)
                else:
                    go = next(gen)
            except StopIteration as e:
                return e.value

            if isinstance(go, self.Read):
                buf = bytearray()
                while len(buf) < go.sz:
                    if not (d := input.read(go.sz - len(buf))):
                        raise EOFError
                    buf.extend(d)
                gi = bytes(buf)
            elif isinstance(go, self.Write):
                gi = None
                output.write(go.d)
                output.flush()
            else:
                raise TypeError(go)

    async def async_run(
            self,
            input: ta.Any,  # asyncio.StreamReader  # noqa
            output: ta.Any,  # asyncio.StreamWriter
    ) -> Result:
        gen = self.gen()

        gi: ta.Optional[bytes] = None
        while True:
            try:
                if gi is not None:
                    go = gen.send(gi)
                else:
                    go = next(gen)
            except StopIteration as e:
                return e.value

            if isinstance(go, self.Read):
                gi = await input.readexactly(go.sz)
            elif isinstance(go, self.Write):
                gi = None
                output.write(go.d)
                await output.drain()
            else:
                raise TypeError(go)


##


def pyremote_get_core_source() -> ta.Optional[str]:
    try:
        mod = sys.modules[__name__]
    except KeyError:
        return None

    import inspect
    return inspect.getsource(mod)


##


class PyremoteApi:
    def build_bootstrap_source(self, context_name: str) -> str:
        return pyremote_build_bootstrap_source(context_name)

    def bootstrap_finalize(self) -> PyremotePayloadRuntime:
        return pyremote_bootstrap_finalize()

    def make_driver(
            self,
            payload_src: ta.Union[str, ta.Sequence[str]],
            options: PyremoteBootstrapOptions = PyremoteBootstrapOptions(),
    ) -> PyremoteBootstrapDriver:
        return PyremoteBootstrapDriver(
            payload_src,
            options,
        )

    def get_core_source(self) -> ta.Optional[str]:
        return pyremote_get_core_source()


pyremote = PyremoteApi()


########################################
# ../../../../omcore/lite/marshal.py
"""
TODO:
 - pickle stdlib objs? have to pin to 3.8 pickle protocol, will be cross-version
 - Options.sequence_cls = list, mapping_cls = dict, ... - def with_mutable_containers() -> Options
"""


##


@dc.dataclass(frozen=True)
class ObjMarshalOptions:
    raw_bytes: bool = False
    non_strict_fields: bool = False


class ObjMarshaler(Abstract):
    @abc.abstractmethod
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        raise NotImplementedError


class NopObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o


class ProxyObjMarshaler(ObjMarshaler):
    def __init__(self, m: ta.Optional[ObjMarshaler] = None) -> None:
        super().__init__()

        self._m = m

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.not_none(self._m).marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.not_none(self._m).unmarshal(o, ctx)


class CastObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(o)


class DynamicObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return ctx.manager.marshal_obj(o, opts=ctx.options)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o


class Base64ObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return base64.b64encode(o).decode('ascii')

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(base64.b64decode(o))


class BytesSwitchedObjMarshaler(ObjMarshaler):
    def __init__(self, m: ObjMarshaler) -> None:
        super().__init__()

        self._m = m

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if ctx.options.raw_bytes:
            return o
        return self._m.marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if ctx.options.raw_bytes:
            return o
        return self._m.unmarshal(o, ctx)


class EnumObjMarshaler(ObjMarshaler):
    def __init__(self, ty: type) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o.name

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty.__members__[o]  # type: ignore


class OptionalObjMarshaler(ObjMarshaler):
    def __init__(self, item: ObjMarshaler) -> None:
        super().__init__()

        self._item = item

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if o is None:
            return None
        return self._item.marshal(o, ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if o is None:
            return None
        return self._item.unmarshal(o, ctx)


class PrimitiveUnionObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            pt: ta.Tuple[type, ...],
            x: ta.Optional[ObjMarshaler] = None,
    ) -> None:
        super().__init__()

        self._pt = pt
        self._x = x

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if isinstance(o, self._pt):
            return o
        elif self._x is not None:
            return self._x.marshal(o, ctx)
        else:
            raise TypeError(o)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        if self._x is not None:
            # The non-primitive member must be tried first - its marshaled form may itself be one of the union's
            # primitive types (e.g. Union[str, Decimal] wires Decimal as a str), which primitive-first dispatch would
            # shadow entirely. Such wire values are inherently ambiguous - the non-primitive parse is accepted only
            # when it faithfully round-trips back to the wire value, so lenient member unmarshalers (e.g. a Sequence
            # member iterating a str) don't capture values belonging to a primitive member.
            try:
                v = self._x.unmarshal(o, ctx)
            except Exception:  # noqa
                pass
            else:
                if not isinstance(o, self._pt):
                    return v
                try:
                    if self._x.marshal(v, ctx) == o:
                        return v
                except Exception:  # noqa
                    pass
        if isinstance(o, self._pt):
            return o
        raise TypeError(o)


class LiteralObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            item: ObjMarshaler,
            vs: frozenset,
    ) -> None:
        super().__init__()

        self._item = item
        self._vs = vs

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._item.marshal(check.in_(o, self._vs), ctx)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return check.in_(self._item.unmarshal(o, ctx), self._vs)


class MappingObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            km: ObjMarshaler,
            vm: ObjMarshaler,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._km = km
        self._vm = vm

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return {self._km.marshal(k, ctx): self._vm.marshal(v, ctx) for k, v in o.items()}

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty((self._km.unmarshal(k, ctx), self._vm.unmarshal(v, ctx)) for k, v in o.items())


class IterableObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            item: ObjMarshaler,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._item = item

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return [self._item.marshal(e, ctx) for e in o]

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(self._item.unmarshal(e, ctx) for e in o)


class FieldsObjMarshaler(ObjMarshaler):
    @dc.dataclass(frozen=True)
    class Field:
        att: str
        key: str
        m: ObjMarshaler

        omit_if_none: bool = False

    def __init__(
            self,
            ty: type,
            fs: ta.Sequence[Field],
            *,
            non_strict: bool = False,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._fs = fs
        self._non_strict = non_strict

        fs_by_att: dict = {}
        fs_by_key: dict = {}
        for f in self._fs:
            check.not_in(check.non_empty_str(f.att), fs_by_att)
            check.not_in(check.non_empty_str(f.key), fs_by_key)
            fs_by_att[f.att] = f
            fs_by_key[f.key] = f

        self._fs_by_att: ta.Mapping[str, FieldsObjMarshaler.Field] = fs_by_att
        self._fs_by_key: ta.Mapping[str, FieldsObjMarshaler.Field] = fs_by_key

    @property
    def ty(self) -> type:
        return self._ty

    @property
    def fs(self) -> ta.Sequence[Field]:
        return self._fs

    #

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        d = {}
        for f in self._fs:
            mv = f.m.marshal(getattr(o, f.att), ctx)
            if mv is None and f.omit_if_none:
                continue
            d[f.key] = mv
        return d

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        kw = {}
        for k, v in o.items():
            if (f := self._fs_by_key.get(k)) is None:
                if not (self._non_strict or ctx.options.non_strict_fields):
                    raise KeyError(k)
                continue
            kw[f.att] = f.m.unmarshal(v, ctx)
        return self._ty(**kw)


class SingleFieldObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
            fld: str,
    ) -> None:
        super().__init__()

        self._ty = ty
        self._fld = fld

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return getattr(o, self._fld)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty(**{self._fld: o})


class PolymorphicObjMarshaler(ObjMarshaler):
    class Impl(ta.NamedTuple):
        ty: type
        tag: str
        m: ObjMarshaler

    def __init__(
            self,
            impls_by_ty: ta.Mapping[type, Impl],
            impls_by_tag: ta.Mapping[str, Impl],
    ) -> None:
        super().__init__()

        self._impls_by_ty = impls_by_ty
        self._impls_by_tag = impls_by_tag

    @classmethod
    def of(cls, impls: ta.Iterable[Impl]) -> 'PolymorphicObjMarshaler':
        return cls(
            {i.ty: i for i in impls},
            {i.tag: i for i in impls},
        )

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        impl = self._impls_by_ty[type(o)]
        return {impl.tag: impl.m.marshal(o, ctx)}

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        [(t, v)] = o.items()
        impl = self._impls_by_tag[t]
        return impl.m.unmarshal(v, ctx)


class DatetimeObjMarshaler(ObjMarshaler):
    def __init__(
            self,
            ty: type,
    ) -> None:
        super().__init__()

        self._ty = ty

    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return o.isoformat()

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return self._ty.fromisoformat(o)  # type: ignore


class DecimalObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return str(check.isinstance(o, decimal.Decimal))

    def unmarshal(self, v: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return decimal.Decimal(check.isinstance(v, str))


class FractionObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        fr = check.isinstance(o, fractions.Fraction)
        return [fr.numerator, fr.denominator]

    def unmarshal(self, v: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        num, denom = check.isinstance(v, list)
        return fractions.Fraction(num, denom)


class UuidObjMarshaler(ObjMarshaler):
    def marshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return str(o)

    def unmarshal(self, o: ta.Any, ctx: 'ObjMarshalContext') -> ta.Any:
        return uuid.UUID(o)


##


_DEFAULT_OBJ_MARSHALERS: ta.Dict[ta.Any, ObjMarshaler] = {
    **{t: NopObjMarshaler() for t in (type(None),)},
    **{t: CastObjMarshaler(t) for t in (int, float, str, bool)},
    **{t: BytesSwitchedObjMarshaler(Base64ObjMarshaler(t)) for t in (bytes, bytearray)},
    **{t: IterableObjMarshaler(t, DynamicObjMarshaler()) for t in (list, tuple, set, frozenset)},
    **{t: MappingObjMarshaler(t, DynamicObjMarshaler(), DynamicObjMarshaler()) for t in (dict,)},

    **{t: DynamicObjMarshaler() for t in (ta.Any, object)},

    **{t: DatetimeObjMarshaler(t) for t in (datetime.date, datetime.time, datetime.datetime)},
    decimal.Decimal: DecimalObjMarshaler(),
    fractions.Fraction: FractionObjMarshaler(),
    uuid.UUID: UuidObjMarshaler(),
}

_OBJ_MARSHALER_GENERIC_MAPPING_TYPES: ta.Dict[ta.Any, type] = {
    **{t: t for t in (dict,)},
    **{t: dict for t in (collections.abc.Mapping, collections.abc.MutableMapping)},  # noqa
}

_OBJ_MARSHALER_GENERIC_ITERABLE_TYPES: ta.Dict[ta.Any, type] = {
    **{t: t for t in (list, tuple, set, frozenset)},
    collections.abc.Set: frozenset,
    collections.abc.MutableSet: set,
    collections.abc.Sequence: tuple,
    collections.abc.MutableSequence: list,
}

_OBJ_MARSHALER_PRIMITIVE_TYPES: ta.Set[type] = {
    int,
    float,
    bool,
    str,
}


##


_REGISTERED_OBJ_MARSHALERS_BY_TYPE: ta.MutableMapping[type, ObjMarshaler] = weakref.WeakKeyDictionary()


def register_type_obj_marshaler(ty: type, om: ObjMarshaler) -> None:
    _REGISTERED_OBJ_MARSHALERS_BY_TYPE[ty] = om


def register_single_field_type_obj_marshaler(fld, ty=None):
    def inner(ty):  # noqa
        register_type_obj_marshaler(ty, SingleFieldObjMarshaler(ty, fld))
        return ty

    if ty is not None:
        return inner(ty)
    else:
        return inner


##


class ObjMarshalerFieldMetadata:
    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError


class OBJ_MARSHALER_FIELD_KEY(ObjMarshalerFieldMetadata):  # noqa
    pass


class OBJ_MARSHALER_OMIT_IF_NONE(ObjMarshalerFieldMetadata):  # noqa
    pass


##


class ObjMarshalerManager(Abstract):
    @abc.abstractmethod
    def make_obj_marshaler(
            self,
            ty: ta.Any,
            rec: ta.Callable[[ta.Any], ObjMarshaler],
            *,
            non_strict_fields: bool = False,
    ) -> ObjMarshaler:
        raise NotImplementedError

    @abc.abstractmethod
    def set_obj_marshaler(
            self,
            ty: ta.Any,
            m: ObjMarshaler,
            *,
            override: bool = False,
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_obj_marshaler(
            self,
            ty: ta.Any,
            *,
            no_cache: bool = False,
            **kwargs: ta.Any,
    ) -> ObjMarshaler:
        raise NotImplementedError

    @abc.abstractmethod
    def make_context(self, opts: ta.Optional[ObjMarshalOptions]) -> 'ObjMarshalContext':
        raise NotImplementedError

    #

    def marshal_obj(
            self,
            o: ta.Any,
            ty: ta.Any = None,
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> ta.Any:
        m = self.get_obj_marshaler(ty if ty is not None else type(o))
        return m.marshal(o, self.make_context(opts))

    def unmarshal_obj(
            self,
            o: ta.Any,
            ty: ta.Union[ta.Type[T], ta.Any],
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> T:
        m = self.get_obj_marshaler(ty)
        return m.unmarshal(o, self.make_context(opts))

    def roundtrip_obj(
            self,
            o: ta.Any,
            ty: ta.Any = None,
            opts: ta.Optional[ObjMarshalOptions] = None,
    ) -> ta.Any:
        if ty is None:
            ty = type(o)
        m: ta.Any = self.marshal_obj(o, ty, opts)
        u: ta.Any = self.unmarshal_obj(m, ty, opts)
        return u


#


class ObjMarshalerManagerImpl(ObjMarshalerManager):
    def __init__(
            self,
            *,
            default_options: ObjMarshalOptions = ObjMarshalOptions(),

            default_obj_marshalers: ta.Dict[ta.Any, ObjMarshaler] = _DEFAULT_OBJ_MARSHALERS,  # noqa
            generic_mapping_types: ta.Dict[ta.Any, type] = _OBJ_MARSHALER_GENERIC_MAPPING_TYPES,  # noqa
            generic_iterable_types: ta.Dict[ta.Any, type] = _OBJ_MARSHALER_GENERIC_ITERABLE_TYPES,  # noqa

            registered_obj_marshalers: ta.Mapping[type, ObjMarshaler] = _REGISTERED_OBJ_MARSHALERS_BY_TYPE,
    ) -> None:
        super().__init__()

        self._default_options = default_options

        self._obj_marshalers = dict(default_obj_marshalers)
        self._generic_mapping_types = generic_mapping_types
        self._generic_iterable_types = generic_iterable_types
        self._registered_obj_marshalers = registered_obj_marshalers

        self._lock = threading.RLock()
        self._derived_obj_marshalers: ta.Dict[ta.Any, ObjMarshaler] = {}
        self._proxies: ta.Dict[ta.Any, ProxyObjMarshaler] = {}

    #

    @classmethod
    def _is_abstract(cls, ty: type) -> bool:
        return abc.ABC in ty.__bases__ or Abstract in ty.__bases__

    @classmethod
    def _get_field_type_hints(cls, ty: type) -> ta.Optional[ta.Mapping[str, ta.Any]]:
        """
        Best-effort resolution of string / forward-ref field annotations (`from __future__ import annotations` modules,
        self-referential fields) against their defining modules' namespaces, mro-aware. Returns None on failure (e.g.
        TYPE_CHECKING-only names, classes exec'd into namespaces absent from sys.modules) - callers fall back to the
        raw annotations, preserving behavior for already-evaluated ones.
        """

        try:
            return ta.get_type_hints(ty)
        except Exception:  # noqa
            return None

    #

    def make_obj_marshaler(
            self,
            ty: ta.Any,
            rec: ta.Callable[[ta.Any], ObjMarshaler],
            *,
            non_strict_fields: bool = False,
    ) -> ObjMarshaler:
        if isinstance(ty, type):
            if (reg := self._registered_obj_marshalers.get(ty)) is not None:
                return reg

            if self._is_abstract(ty):
                tn = ty.__name__
                impls: ta.List[ta.Tuple[type, str]] = [  # type: ignore[var-annotated]
                    (ity, ity.__name__)
                    for ity in deep_subclasses(ty)
                    if not self._is_abstract(ity)
                ]

                if all(itn.endswith(tn) for _, itn in impls):
                    impls = [
                        (ity, snake_case(itn[:-len(tn)]))
                        for ity, itn in impls
                    ]

                dupe_tns = sorted(
                    dn
                    for dn, dc in collections.Counter(itn for _, itn in impls).items()
                    if dc > 1
                )
                if dupe_tns:
                    raise KeyError(f'Duplicate impl names for {ty}: {dupe_tns}')

                return PolymorphicObjMarshaler.of([
                    PolymorphicObjMarshaler.Impl(
                        ity,
                        itn,
                        rec(ity),
                    )
                    for ity, itn in impls
                ])

            if issubclass(ty, enum.Enum):
                return EnumObjMarshaler(ty)

            if dc.is_dataclass(ty):
                hints = self._get_field_type_hints(ty) or {}
                return FieldsObjMarshaler(
                    ty,
                    [
                        FieldsObjMarshaler.Field(
                            att=f.name,
                            key=check.non_empty_str(fk),
                            m=rec(hints.get(f.name, f.type)),
                            omit_if_none=check.isinstance(f.metadata.get(OBJ_MARSHALER_OMIT_IF_NONE, False), bool),
                        )
                        for f in dc.fields(ty)
                        # init=False fields are excluded from both directions - unmarshal passes every key as a ctor
                        # kwarg, so marshaling them would produce round-trip-asymmetric output.
                        if f.init
                        if (fk := f.metadata.get(OBJ_MARSHALER_FIELD_KEY, f.name)) is not None
                    ],
                    non_strict=non_strict_fields,
                )

            if issubclass(ty, tuple) and hasattr(ty, '_fields'):
                hints = self._get_field_type_hints(ty) or {}
                return FieldsObjMarshaler(
                    ty,
                    [
                        FieldsObjMarshaler.Field(
                            att=p.name,
                            key=p.name,
                            # Untyped collections.namedtuple fields have empty annotations - marshal them dynamically.
                            m=rec(hints.get(
                                p.name,
                                p.annotation if p.annotation is not inspect.Parameter.empty else ta.Any,
                            )),
                        )
                        for p in inspect.signature(ty).parameters.values()
                    ],
                    non_strict=non_strict_fields,
                )

        if is_new_type(ty):
            return rec(get_new_type_supertype(ty))

        if is_literal_type(ty):
            lvs = frozenset(get_literal_type_args(ty))
            if None in lvs:
                is_opt = True
                lvs -= frozenset([None])
            else:
                is_opt = False
            lty = check.single(set(map(type, lvs)))
            lm: ObjMarshaler = LiteralObjMarshaler(rec(lty), lvs)
            if is_opt:
                lm = OptionalObjMarshaler(lm)
            return lm

        if is_generic_alias(ty):
            try:
                mt = self._generic_mapping_types[ta.get_origin(ty)]
            except KeyError:
                pass
            else:
                k, v = ta.get_args(ty)
                return MappingObjMarshaler(mt, rec(k), rec(v))

            try:
                st = self._generic_iterable_types[ta.get_origin(ty)]
            except KeyError:
                pass
            else:
                [e] = ta.get_args(ty)
                return IterableObjMarshaler(st, rec(e))

        if is_union_alias(ty):
            uts = frozenset(ta.get_args(ty))
            if None in uts or type(None) in uts:
                is_opt = True
                uts = frozenset(ut for ut in uts if ut not in (None, type(None)))
            else:
                is_opt = False

            um: ObjMarshaler
            if not uts:
                raise TypeError(ty)
            elif len(uts) == 1:
                um = rec(check.single(uts))
            else:
                pt = tuple({ut for ut in uts if ut in _OBJ_MARSHALER_PRIMITIVE_TYPES})
                np_uts = {ut for ut in uts if ut not in _OBJ_MARSHALER_PRIMITIVE_TYPES}
                if not np_uts:
                    um = PrimitiveUnionObjMarshaler(pt)
                elif len(np_uts) == 1:
                    um = PrimitiveUnionObjMarshaler(pt, x=rec(check.single(np_uts)))
                else:
                    raise TypeError(ty)

            if is_opt:
                um = OptionalObjMarshaler(um)
            return um

        raise TypeError(ty)

    #

    def set_obj_marshaler(
            self,
            ty: ta.Any,
            m: ObjMarshaler,
            *,
            override: bool = False,
    ) -> None:
        with self._lock:
            if not override and ty in self._obj_marshalers:
                raise KeyError(ty)
            self._obj_marshalers[ty] = m

    def get_obj_marshaler(
            self,
            ty: ta.Any,
            *,
            no_cache: bool = False,
            **kwargs: ta.Any,
    ) -> ObjMarshaler:
        with self._lock:
            ck = (ty, tuple(sorted(kwargs.items())))
            if not no_cache:
                # Explicitly set marshalers (and the defaults) are authoritative regardless of construction kwargs.
                try:
                    return self._obj_marshalers[ty]
                except KeyError:
                    pass

                # Derived marshalers are cached under their construction kwargs - a strict marshaler must not be
                # returned for a non-strict request, nor vice versa.
                try:
                    return self._derived_obj_marshalers[ck]
                except KeyError:
                    pass

            try:
                return self._proxies[ty]
            except KeyError:
                pass

            rec = functools.partial(
                self.get_obj_marshaler,
                no_cache=no_cache,
                **kwargs,
            )

            p = ProxyObjMarshaler()
            self._proxies[ty] = p
            try:
                m = self.make_obj_marshaler(ty, rec, **kwargs)
            finally:
                del self._proxies[ty]
            p._m = m  # noqa

            if not no_cache:
                self._derived_obj_marshalers[ck] = m
            return m

    def make_context(self, opts: ta.Optional[ObjMarshalOptions]) -> 'ObjMarshalContext':
        return ObjMarshalContext(
            options=opts or self._default_options,
            manager=self,
        )


def new_obj_marshaler_manager(**kwargs: ta.Any) -> ObjMarshalerManager:
    return ObjMarshalerManagerImpl(**kwargs)


##


@dc.dataclass(frozen=True)
class ObjMarshalContext:
    options: ObjMarshalOptions
    manager: ObjMarshalerManager


##


OBJ_MARSHALER_MANAGER = new_obj_marshaler_manager()

set_obj_marshaler = OBJ_MARSHALER_MANAGER.set_obj_marshaler
get_obj_marshaler = OBJ_MARSHALER_MANAGER.get_obj_marshaler

marshal_obj = OBJ_MARSHALER_MANAGER.marshal_obj
unmarshal_obj = OBJ_MARSHALER_MANAGER.unmarshal_obj


########################################
# ../protocol.py
"""JSON-compatible request/result/notification shapes shared by the host adapter and the remote agent payload."""


##


FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
FS_STAT_METHOD = 'fs.stat'
FS_READ_FILE_METHOD = 'fs.read_file'
FS_WRITE_FILE_METHOD = 'fs.write_file'
FS_LIST_DIR_METHOD = 'fs.list_dir'
FS_GLOB_METHOD = 'fs.glob'

PROCESS_SPAWN_METHOD = 'process.spawn'
PROCESS_SIGNAL_METHOD = 'process.signal'
PROCESS_CLOSE_METHOD = 'process.close'
PROCESS_WRITE_METHOD = 'process.write'
PROCESS_WRITE_EOF_METHOD = 'process.write_eof'
PROCESS_RESIZE_METHOD = 'process.resize'

PROCESS_OUTPUT_METHOD = 'process.output'
PROCESS_OUTPUT_END_METHOD = 'process.output_end'
PROCESS_EXITED_METHOD = 'process.exited'


##
# Filesystem


@dc.dataclass(frozen=True)
class PathParams:
    path: str


@dc.dataclass(frozen=True)
class StatResult:
    path: str
    size: int
    is_dir: bool
    is_file: bool
    is_symlink: bool

    def __post_init__(self) -> None:
        check.arg(self.size >= 0)


@dc.dataclass(frozen=True)
class ReadFileResult:
    data: bytes
    digest: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.digest)


@dc.dataclass(frozen=True)
class WriteFileParams:
    path: str
    content: bytes
    overwrite: bool
    expected_digest: ta.Optional[str]


@dc.dataclass(frozen=True)
class WriteFileResult:
    created: bool


@dc.dataclass(frozen=True)
class FsEntry:
    name: str
    path: str
    is_dir: bool
    is_file: bool
    is_symlink: bool


@dc.dataclass(frozen=True)
class GlobParams:
    pattern: str
    root: str
    max_results: ta.Optional[int]

    def __post_init__(self) -> None:
        if self.max_results is not None:
            check.arg(self.max_results >= 0)


@dc.dataclass(frozen=True)
class GlobResult:
    entries: ta.List[FsEntry]
    has_more: bool


##
# Processes


@dc.dataclass(frozen=True)
class StdioSpec:
    kind: str
    stdin: ta.Optional[str] = None
    stdout: ta.Optional[str] = None
    stderr: ta.Optional[str] = None
    rows: ta.Optional[int] = None
    cols: ta.Optional[int] = None
    term: ta.Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind == 'pipes':
            check.non_empty_str(self.stdin)
            check.non_empty_str(self.stdout)
            check.non_empty_str(self.stderr)
        elif self.kind == 'pty':
            check.arg(self.rows is not None and self.rows >= 1)
            check.arg(self.cols is not None and self.cols >= 1)
        else:
            raise ValueError(f'Invalid remote stdio kind: {self.kind!r}')


@dc.dataclass(frozen=True)
class SpawnParams:
    argv: ta.List[str]
    cwd: ta.Optional[str]
    env: ta.Optional[ta.Dict[str, str]]
    stdio: StdioSpec
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.not_empty(self.argv)


@dc.dataclass(frozen=True)
class SpawnResult:
    id: str
    pid: int
    created_at: float
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.pid >= 1)
        check.arg(self.created_at >= 0.)


@dc.dataclass(frozen=True)
class SignalParams:
    id: str
    signal: int
    process_group: bool

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.signal >= 1)


@dc.dataclass(frozen=True)
class ClosePolicySpec:
    signal: int
    grace_s: float
    kill_s: float
    close_stdin: bool
    process_group: bool
    drain_s: float

    def __post_init__(self) -> None:
        check.arg(self.signal >= 1)
        check.arg(self.grace_s >= 0.)
        check.arg(self.kill_s >= 0.)
        check.arg(self.drain_s >= 0.)


@dc.dataclass(frozen=True)
class CloseParams:
    id: str
    policy: ClosePolicySpec

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class CloseResult:
    returncode: int
    state: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.state)


@dc.dataclass(frozen=True)
class WriteParams:
    id: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ProcessRefParams:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ResizeParams:
    id: str
    rows: int
    cols: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.rows >= 1)
        check.arg(self.cols >= 1)


##
# Process notifications (agent -> host)


@dc.dataclass(frozen=True)
class OutputEvent:
    id: str
    fd: int
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.fd >= 1)


@dc.dataclass(frozen=True)
class OutputEndEvent:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ExitedEvent:
    id: str
    returncode: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


########################################
# ../../../core/rpc/errors.py


##


class RpcError(Exception):
    pass


class RpcProtocolError(RpcError):
    pass


class RpcConnectionClosedError(RpcError):
    pass


class RpcMethodNotFoundError(RpcError):
    def __init__(self, method: str) -> None:
        super().__init__(f'RPC method not found: {method!r}')

        self.method = method


@dc.dataclass(frozen=True)
class RpcRemoteErrorData:
    code: str
    remote_type: str = dc.field(metadata={OBJ_MARSHALER_FIELD_KEY: 'type'})  # 'type' on the wire
    message: str
    traceback: ta.Optional[str] = None


class RpcRemoteError(RpcError):
    def __init__(self, data: RpcRemoteErrorData) -> None:
        super().__init__(f'{data.remote_type}: {data.message}')

        self.data = data

    @property
    def code(self) -> str:
        return self.data.code

    @property
    def remote_type(self) -> str:
        return self.data.remote_type

    @property
    def remote_message(self) -> str:
        return self.data.message

    @property
    def remote_traceback(self) -> ta.Optional[str]:
        return self.data.traceback


class RpcRemoteCancelledError(RpcRemoteError):
    pass


########################################
# ../../../core/rpc/handlers.py


##


class RpcHandler(Abstract):
    @abc.abstractmethod
    def handle(self, method: str, params: ta.Any) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        """
        Offers a notification to the handler synchronously, on the receive loop, in wire order - returning False to have
        it dispatched to `handle` in its own task instead. Handling inline is what makes the stream's order the delivery
        order: a notification handled here is fully applied before anything the other side sent after it is seen. An
        implementation must not block or suspend here, and an exception it raises is reported to the peer's notification
        error handler.
        """

        return False


class RpcMethodHandler(RpcHandler):
    def __init__(self, methods: ta.Mapping[str, RpcMethod]) -> None:
        super().__init__()

        self._methods = dict(methods)

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None
        return await fn(params)


########################################
# ../../../core/rpc/messages.py


##


@dc.dataclass(frozen=True)
class RpcRequestMessage:
    id: int
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcResultMessage:
    id: int
    result: ta.Any = None

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcErrorMessage:
    id: int
    error: RpcRemoteErrorData

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcCancelMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcNotificationMessage:
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPingMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPongMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


RpcMessage = ta.Union[  # ta.TypeAlias  # om-amalg-typing-no-move
    RpcRequestMessage,
    RpcResultMessage,
    RpcErrorMessage,
    RpcCancelMessage,
    RpcNotificationMessage,
    RpcPingMessage,
    RpcPongMessage,
]


##


class RpcMessageCodec(Abstract):
    @abc.abstractmethod
    def encode(self, message: RpcMessage) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> RpcMessage:
        raise NotImplementedError


# The wire is a `{"type": <tag>, **fields}` object: the discriminator tag selects the message dataclass, whose fields
# marshal/unmarshal directly. There is no field/discriminator-tagged union in the lite marshaler, so the tag is managed
# here while the per-message field mapping (including the nested error's `remote_type` -> `type`) is the marshaler's.
_RPC_MESSAGE_TAGS: ta.Mapping[type, str] = {
    RpcRequestMessage: 'request',
    RpcResultMessage: 'result',
    RpcErrorMessage: 'error',
    RpcCancelMessage: 'cancel',
    RpcNotificationMessage: 'notification',
    RpcPingMessage: 'ping',
    RpcPongMessage: 'pong',
}

_RPC_MESSAGE_TYPES: ta.Mapping[str, type] = {tag: ty for ty, tag in _RPC_MESSAGE_TAGS.items()}


class JsonRpcMessageCodec(RpcMessageCodec):
    @staticmethod
    def _reject_json_constant(value: str) -> ta.NoReturn:
        raise ValueError(f'Invalid JSON constant: {value}')

    def encode(self, message: RpcMessage) -> bytes:
        try:
            tag = _RPC_MESSAGE_TAGS[type(message)]
        except KeyError:
            raise TypeError(message) from None
        try:
            obj = {'type': tag, **marshal_obj(message)}
            return json.dumps(
                obj,
                allow_nan=False,
                separators=(',', ':'),
            ).encode('utf-8')
        except (RecursionError, TypeError, ValueError) as e:
            raise RpcProtocolError(f'RPC message is not JSON-compatible: {e}') from e

    def decode(self, data: bytes) -> RpcMessage:
        try:
            obj = json.loads(data.decode('utf-8'), parse_constant=self._reject_json_constant)
        except (RecursionError, UnicodeDecodeError, ValueError) as e:
            raise RpcProtocolError(f'Invalid RPC JSON: {e}') from e

        if not isinstance(obj, dict):
            raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')
        try:
            tag = obj.pop('type')
        except KeyError:
            raise RpcProtocolError('RPC message is missing its type') from None
        try:
            ty = _RPC_MESSAGE_TYPES[tag]
        except KeyError:
            raise RpcProtocolError(f'Invalid RPC message type: {tag!r}') from None

        try:
            return unmarshal_obj(obj, ty)
        except RpcProtocolError:
            raise
        except Exception as e:  # noqa
            # Any failure to build the message from its wire fields - an unknown or missing field, a bad nested shape -
            # is a protocol error.
            raise RpcProtocolError(f'Invalid RPC {tag} message: {e}') from e


########################################
# ../../../core/rpc/channels.py


##


DEFAULT_RPC_MAX_FRAME_BYTES = 16 * 1024 * 1024

# Closing only has to flush what is already buffered, which a reading peer takes in at once: one that has not done so
# within this has stopped reading.
DEFAULT_RPC_CLOSE_TIMEOUT_S = 1.

_FRAME_HEADER = struct.Struct('!I')


class RpcStreamReader(ta.Protocol):
    def readexactly(self, size: int) -> ta.Awaitable[bytes]:
        raise NotImplementedError


class RpcStreamWriter(ta.Protocol):
    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def drain(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def wait_closed(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class RpcChannel(Abstract):
    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def send(self, message: RpcMessage) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def receive(self) -> ta.Awaitable[ta.Optional[RpcMessage]]:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class AsyncioStreamRpcChannel(RpcChannel):
    def __init__(
            self,
            reader: RpcStreamReader,
            writer: RpcStreamWriter,
            *,
            codec: ta.Optional[RpcMessageCodec] = None,
            max_frame_bytes: int = DEFAULT_RPC_MAX_FRAME_BYTES,
            close_timeout_s: float = DEFAULT_RPC_CLOSE_TIMEOUT_S,
    ) -> None:
        super().__init__()

        check.arg(max_frame_bytes > 0)
        check.arg(close_timeout_s > 0)

        self._reader = reader
        self._writer = writer
        self._codec = codec if codec is not None else JsonRpcMessageCodec()
        self._max_frame_bytes = max_frame_bytes
        self._close_timeout_s = close_timeout_s

        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    async def send(self, message: RpcMessage) -> None:
        if self._closed:
            raise RpcConnectionClosedError('RPC channel is closed')

        payload = self._codec.encode(message)
        if len(payload) > self._max_frame_bytes:
            raise RpcProtocolError(
                f'RPC frame is {len(payload)} bytes, exceeding limit {self._max_frame_bytes}',
            )

        frame = _FRAME_HEADER.pack(len(payload)) + payload
        async with self._write_lock:
            if self._closed:
                raise RpcConnectionClosedError('RPC channel is closed')
            try:
                self._writer.write(frame)
                await self._writer.drain()
            except (BrokenPipeError, ConnectionError, OSError) as e:
                raise RpcConnectionClosedError('RPC channel write failed') from e

    async def _read_exactly(self, size: int, *, allow_eof: bool = False) -> ta.Optional[bytes]:
        try:
            return await self._reader.readexactly(size)
        except asyncio.IncompleteReadError as e:
            if allow_eof and not e.partial:
                return None
            raise RpcProtocolError(
                f'RPC connection closed within a frame: expected {size} bytes, received {len(e.partial)}',
            ) from e
        except (ConnectionError, OSError) as e:
            raise RpcConnectionClosedError('RPC channel read failed') from e

    async def receive(self) -> ta.Optional[RpcMessage]:
        async with self._read_lock:
            if self._closed:
                return None

            header = await self._read_exactly(_FRAME_HEADER.size, allow_eof=True)
            if header is None:
                return None
            size = _FRAME_HEADER.unpack(header)[0]
            if size > self._max_frame_bytes:
                raise RpcProtocolError(
                    f'RPC frame is {size} bytes, exceeding limit {self._max_frame_bytes}',
                )

            payload = ta.cast(bytes, await self._read_exactly(size))
            return self._codec.decode(payload)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self._writer.close()
            # Bounded: the close completes only once what is already buffered has been flushed, and a peer which has
            # stopped reading would otherwise hold it - and whatever teardown follows it - forever. Past the bound the
            # transport is left to finish closing, or die with its peer, on its own.
            await asyncio.wait_for(self._writer.wait_closed(), self._close_timeout_s)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            pass
        except (BrokenPipeError, ConnectionError, OSError):
            pass


########################################
# ../../../core/rpc/peers.py


##


DEFAULT_RPC_MAX_IN_FLIGHT = 1024
DEFAULT_RPC_MAX_TRACEBACK_CHARS = 64 * 1024


def _exception_type_name(exc: BaseException) -> str:
    cls = type(exc)
    return f'{cls.__module__}.{cls.__qualname__}'


def _error_data(
        exc: BaseException,
        *,
        code: str = 'remote',
        max_traceback_chars: int = DEFAULT_RPC_MAX_TRACEBACK_CHARS,
) -> RpcRemoteErrorData:
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(tb) > max_traceback_chars:
        tb = tb[-max_traceback_chars:] if max_traceback_chars else ''
    return RpcRemoteErrorData(
        code=code,
        remote_type=_exception_type_name(exc),
        message=str(exc),
        traceback=tb,
    )


class _RejectingRpcHandler(RpcHandler):
    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        raise RpcMethodNotFoundError(method)


class RpcPeer:
    def __init__(
            self,
            channel: RpcChannel,
            *,
            handler: ta.Optional[RpcHandler] = None,
            notification_error_handler: ta.Optional[RpcNotificationErrorHandler] = None,
            max_in_flight: int = DEFAULT_RPC_MAX_IN_FLIGHT,
            max_traceback_chars: int = DEFAULT_RPC_MAX_TRACEBACK_CHARS,
    ) -> None:
        super().__init__()

        check.arg(max_in_flight > 0)
        check.arg(max_traceback_chars >= 0)

        self._channel = channel
        self._handler = handler if handler is not None else _RejectingRpcHandler()
        self._notification_error_handler = notification_error_handler
        self._max_in_flight = max_in_flight
        self._max_traceback_chars = max_traceback_chars

        self._next_id = 1
        self._outgoing: ta.Dict[int, asyncio.Future] = {}
        self._pings: ta.Dict[int, asyncio.Future] = {}
        self._incoming: ta.Dict[int, asyncio.Task] = {}
        self._notifications: ta.Set[asyncio.Task] = set()

        # Replies the receive loop owes the other side (pongs, 'busy' errors). They go out from one short-lived task
        # rather than being awaited in the loop itself, so a backpressured writer can never stall reading.
        self._replies: ta.Deque[RpcMessage] = collections.deque()
        self._reply_task: ta.Optional[asyncio.Task] = None

        self._receive_task: ta.Optional[asyncio.Task] = None
        self._receive_cancelled = False
        self._closed_event = asyncio.Event()
        self._close_callbacks: ta.List[RpcPeerCloseCallback] = []
        self._closing = False
        self._finished = False
        self._failure: ta.Optional[BaseException] = None
        self._background_failure: ta.Optional[BaseException] = None

    @property
    def closed(self) -> bool:
        return self._closed_event.is_set()

    @property
    def failure(self) -> ta.Optional[BaseException]:
        return self._failure

    @property
    def num_outgoing(self) -> int:
        return len(self._outgoing)

    @property
    def num_incoming(self) -> int:
        return len(self._incoming)

    def add_close_callback(self, callback: RpcPeerCloseCallback) -> None:
        """
        Registers a callback run synchronously, on the loop, as the last step of teardown: after every pending call has
        been failed and `closed` is set, before any `wait_closed` returns. Runs right away if the peer is already
        closed.
        """

        if self._closed_event.is_set():
            callback(self)
            return
        self._close_callbacks.append(callback)

    def _new_id(self) -> int:
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def _check_running(self) -> None:
        if self._receive_task is None:
            raise RuntimeError('RPC peer has not been started')
        if self._closing or self._finished:
            raise RpcConnectionClosedError('RPC peer is closed')

    def _cancel_receive(self) -> None:
        # At most once, and never once teardown has begun: the receive task runs the teardown itself, and a second
        # CancelledError would land inside it, skipping the steps that release everyone waiting on this peer.
        if self._finished or self._receive_cancelled:
            return
        task = self._receive_task
        if task is not None and not task.done():
            self._receive_cancelled = True
            task.cancel()

    def _abort(self, exc: BaseException) -> None:
        if self._background_failure is None:
            self._background_failure = exc
        self._cancel_receive()

    async def _try_send(self, message: RpcMessage) -> bool:
        if self._closing or self._finished:
            return False
        try:
            await self._channel.send(message)
            return True
        except Exception as e:  # noqa
            self._abort(e)
            return False

    async def _send(self, message: RpcMessage) -> None:
        try:
            await self._channel.send(message)
        except RpcConnectionClosedError as e:
            self._abort(e)
            raise

    def _queue_reply(self, message: RpcMessage) -> None:
        self._replies.append(message)
        if self._reply_task is None or self._reply_task.done():
            self._reply_task = asyncio.create_task(
                self._send_replies(),
                name='omllm-rpc-replies',
            )

    async def _send_replies(self) -> None:
        while self._replies:
            if not await self._try_send(self._replies.popleft()):
                self._replies.clear()
                return

    def _report_notification_error(self, message: RpcNotificationMessage, exc: BaseException) -> None:
        if self._notification_error_handler is not None:
            self._notification_error_handler(message, exc)

    async def start(self) -> None:
        if self._receive_task is not None or self._finished:
            raise RuntimeError('RPC peer has already been started')
        if self._channel.closed:
            raise RpcConnectionClosedError('RPC channel is closed')
        self._receive_task = asyncio.create_task(
            self._run(),
            name='omllm-rpc-receive',
        )

    async def _ensure_finished(self) -> None:
        # A receive task cancelled before it ever got to run never executed its body - and so never ran the teardown
        # that lives in its `finally`. Whoever notices runs it instead.
        task = self._receive_task
        if task is not None and task.done() and not self._finished:
            await self._finish(failure=None, message='RPC peer closed locally')

    async def wait_closed(self) -> None:
        if self._receive_task is None and not self._finished:
            raise RuntimeError('RPC peer has not been started')
        await self._ensure_finished()
        await self._closed_event.wait()

    async def serve(self) -> None:
        await self.start()
        await self.wait_closed()
        if self._failure is not None:
            raise self._failure

    async def call(self, method: str, params: ta.Any = None) -> ta.Any:
        self._check_running()

        request_id = self._new_id()
        future = asyncio.get_running_loop().create_future()
        self._outgoing[request_id] = future

        try:
            await self._send(RpcRequestMessage(request_id, method, params))
            return await future

        except asyncio.CancelledError:
            # Whether or not the request reached the other side, nothing waits for its reply any more: a late reply is
            # recognized as such and dropped (see `_pop_reply_future`), and a cancel is harmless for an id it never saw.
            self._outgoing.pop(request_id, None)
            future.cancel()
            await self._try_send(RpcCancelMessage(request_id))
            raise

        except BaseException:
            self._outgoing.pop(request_id, None)
            raise

    async def notify(self, method: str, params: ta.Any = None) -> None:
        self._check_running()
        await self._send(RpcNotificationMessage(method, params))

    async def ping(self) -> None:
        self._check_running()

        ping_id = self._new_id()
        future = asyncio.get_running_loop().create_future()
        self._pings[ping_id] = future
        try:
            await self._send(RpcPingMessage(ping_id))
            await future
        except BaseException:
            self._pings.pop(ping_id, None)
            raise

    def _request_done(self, request_id: int, task: asyncio.Task) -> None:
        if self._incoming.get(request_id) is task:
            self._incoming.pop(request_id, None)
        if not task.cancelled() and (exc := task.exception()) is not None:
            self._abort(exc)

    def _notification_done(self, task: asyncio.Task) -> None:
        self._notifications.discard(task)
        if not task.cancelled() and (exc := task.exception()) is not None:
            self._abort(exc)

    async def _send_handler_response(self, message: RpcMessage) -> None:
        try:
            await self._channel.send(message)
        except RpcProtocolError as e:
            if isinstance(message, RpcResultMessage):
                fallback = RpcErrorMessage(
                    message.id,
                    _error_data(
                        e,
                        code='result_encoding',
                        max_traceback_chars=self._max_traceback_chars,
                    ),
                )
                if await self._try_send(fallback):
                    return
            self._abort(e)
        except Exception as e:  # noqa
            self._abort(e)

    async def _handle_request(self, message: RpcRequestMessage) -> None:
        response: ta.Optional[RpcMessage] = None
        try:
            result = await self._handler.handle(message.method, message.params)
        except asyncio.CancelledError as e:
            if self._closing:
                return
            response = RpcErrorMessage(
                message.id,
                _error_data(
                    e,
                    code='cancelled',
                    max_traceback_chars=self._max_traceback_chars,
                ),
            )
        except RpcMethodNotFoundError as e:
            response = RpcErrorMessage(
                message.id,
                _error_data(
                    e,
                    code='method_not_found',
                    max_traceback_chars=self._max_traceback_chars,
                ),
            )
        except Exception as e:  # noqa
            response = RpcErrorMessage(
                message.id,
                _error_data(e, max_traceback_chars=self._max_traceback_chars),
            )
        else:
            response = RpcResultMessage(message.id, result)

        if response is None:
            raise RuntimeError('RPC handler produced no response')
        await self._send_handler_response(response)

    async def _handle_notification(self, message: RpcNotificationMessage) -> None:
        try:
            await self._handler.handle(message.method, message.params)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa
            self._report_notification_error(message, e)

    def _pop_reply_future(
            self,
            futures: ta.Dict[int, asyncio.Future],
            message_id: int,
            kind: str,
    ) -> ta.Optional[asyncio.Future]:
        try:
            return futures.pop(message_id)
        except KeyError:
            pass
        if message_id >= self._next_id:
            raise RpcProtocolError(f'Unexpected RPC {kind} id: {message_id}')
        # An id this side did issue but no longer waits on: the reply to a call or ping given up on (cancelled, or
        # timed out) that the other side answered anyway. Late, but legitimate.
        return None

    async def _dispatch(self, message: RpcMessage) -> None:
        if isinstance(message, RpcRequestMessage):
            if message.id in self._incoming:
                raise RpcProtocolError(f'Duplicate inbound RPC request id: {message.id}')
            if len(self._incoming) + len(self._notifications) >= self._max_in_flight:
                self._queue_reply(RpcErrorMessage(
                    message.id,
                    RpcRemoteErrorData(
                        code='busy',
                        remote_type='RpcTooManyRequestsError',
                        message=f'Too many in-flight RPC requests: {self._max_in_flight}',
                    ),
                ))
                return
            request_task = asyncio.create_task(
                self._handle_request(message),
                name=f'omllm-rpc-request-{message.id}',
            )
            self._incoming[message.id] = request_task
            request_task.add_done_callback(functools.partial(self._request_done, message.id))
            return

        if isinstance(message, RpcNotificationMessage):
            try:
                handled = self._handler.handle_notification_inline(message.method, message.params)
            except Exception as e:  # noqa
                self._report_notification_error(message, e)
                return
            if handled:
                return
            if len(self._incoming) + len(self._notifications) >= self._max_in_flight:
                return
            notification_task = asyncio.create_task(
                self._handle_notification(message),
                name='omllm-rpc-notification',
            )
            self._notifications.add(notification_task)
            notification_task.add_done_callback(self._notification_done)
            return

        if isinstance(message, RpcCancelMessage):
            if (incoming_task := self._incoming.get(message.id)) is not None:
                incoming_task.cancel()
            return

        if isinstance(message, RpcResultMessage):
            future = self._pop_reply_future(self._outgoing, message.id, 'result')
            if future is not None and not future.done():
                future.set_result(message.result)
            return

        if isinstance(message, RpcErrorMessage):
            future = self._pop_reply_future(self._outgoing, message.id, 'error')
            if future is not None and not future.done():
                if message.error.code == 'cancelled':
                    future.set_exception(RpcRemoteCancelledError(message.error))
                else:
                    future.set_exception(RpcRemoteError(message.error))
            return

        if isinstance(message, RpcPingMessage):
            self._queue_reply(RpcPongMessage(message.id))
            return

        if isinstance(message, RpcPongMessage):
            future = self._pop_reply_future(self._pings, message.id, 'pong')
            if future is not None and not future.done():
                future.set_result(None)
            return

        raise TypeError(message)

    def _connection_error(self, message: str) -> RpcConnectionClosedError:
        error = RpcConnectionClosedError(message)
        if self._failure is not None:
            error.__cause__ = self._failure
        return error

    async def _finish(
            self,
            *,
            failure: ta.Optional[BaseException],
            message: str,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        self._closing = True
        self._failure = failure

        try:
            try:
                await self._channel.aclose()
            finally:
                current = asyncio.current_task()
                tasks = [
                    task
                    for task in [*self._incoming.values(), *self._notifications, self._reply_task]
                    if task is not None and task is not current and not task.done()
                ]
                for task in tasks:
                    task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            # Unconditional, even if the waits above were interrupted: nothing may be left waiting on a peer that is
            # gone.
            self._incoming.clear()
            self._notifications.clear()
            self._replies.clear()

            for future in [*self._outgoing.values(), *self._pings.values()]:
                if not future.done():
                    future.set_exception(self._connection_error(message))
            self._outgoing.clear()
            self._pings.clear()

            # Waiters on the event only resume on a later loop iteration, so the callbacks run before any of them.
            self._closed_event.set()
            callbacks, self._close_callbacks = self._close_callbacks, []
            for callback in callbacks:
                try:
                    callback(self)
                except Exception:  # noqa
                    # A close callback is a courtesy to its registrant; its failure is not the peer's, and nothing here
                    # may prevent the peer from finishing.
                    pass

    async def _run(self) -> None:
        failure: ta.Optional[BaseException] = None
        message = 'RPC connection closed by peer'
        try:
            while True:
                incoming = await self._channel.receive()
                if incoming is None:
                    break
                await self._dispatch(incoming)

        except asyncio.CancelledError:
            if self._background_failure is not None:
                failure = self._background_failure
                message = 'RPC connection failed'
            elif not self._closing:
                failure = RpcConnectionClosedError('RPC receive loop was cancelled unexpectedly')
                message = 'RPC connection failed'

        except BaseException as e:  # noqa
            failure = e
            message = 'RPC connection failed'

        finally:
            await self._finish(failure=failure, message=message)

    async def aclose(self) -> None:
        if self._finished:
            await self._closed_event.wait()
            return
        if self._receive_task is None:
            await self._finish(failure=None, message='RPC peer closed locally')
            return

        self._closing = True
        try:
            await self._channel.aclose()
        finally:
            # The receive task runs the teardown. Closing the channel may already have woken it into that (a socket
            # reports EOF to its own reader), in which case it is left alone - `_cancel_receive` knows.
            self._cancel_receive()
            receive_task = self._receive_task
            if not receive_task.done():
                await asyncio.wait([receive_task])
            await self._ensure_finished()
            if not receive_task.cancelled() and (exc := receive_task.exception()) is not None:
                raise exc

    async def __aenter__(self) -> 'RpcPeer':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()


########################################
# ../server.py
"""Python-3.8-compatible filesystem and process services used by the remote agent amalgam."""


##


_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE = 64 * 1024

_REMOTE_CLD_EXITED = getattr(os, 'CLD_EXITED', 1)
_REMOTE_CLD_KILLED = getattr(os, 'CLD_KILLED', 2)
_REMOTE_CLD_DUMPED = getattr(os, 'CLD_DUMPED', 3)

_REMOTE_DARWIN_P_PID = 1
_REMOTE_DARWIN_WEXITED = 0x04
_REMOTE_DARWIN_WNOWAIT = 0x20

_REMOTE_PTY_CHILD_CODE = """
import fcntl
import json
import os
import sys
import termios

argv = json.loads(sys.argv[1])
os.setsid()
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
os.tcsetpgrp(0, os.getpgrp())
os.execvpe(argv[0], argv, os.environ)
"""


def _remote_process_returncode(si_code: int, si_status: int) -> int:
    if si_code == _REMOTE_CLD_EXITED:
        return si_status
    if si_code in (_REMOTE_CLD_KILLED, _REMOTE_CLD_DUMPED):
        return -si_status
    raise RuntimeError(f'Unexpected waitid result: si_code={si_code!r}, si_status={si_status!r}')


class _RemoteDarwinProcessWaiter(ta.Protocol):
    def __call__(self, pid: int, *, nohang: bool = False) -> ta.Optional[int]: ...


@cached_nullary
def _remote_darwin_process_waiter() -> _RemoteDarwinProcessWaiter:
    # CPython did not expose os.waitid on macOS until 3.13, although libc and the kernel have long provided it. Keep the
    # child waitable so its pid/pgid remain ours until close deliberately reaps it. The first six siginfo_t fields are
    # fixed-width scalars on Darwin; the tail only reserves enough space for libc to fill the complete structure.

    import ctypes as ct

    class Siginfo(ct.Structure):
        _fields_ = [
            ('si_signo', ct.c_int),
            ('si_errno', ct.c_int),
            ('si_code', ct.c_int),
            ('si_pid', ct.c_int),
            ('si_uid', ct.c_uint),
            ('si_status', ct.c_int),
            ('_tail', ct.c_ubyte * 104),
        ]

    _waitid = ct.CDLL(None, use_errno=True).waitid
    _waitid.argtypes = (ct.c_int, ct.c_uint, ct.c_void_p, ct.c_int)
    _waitid.restype = ct.c_int

    def waitpid(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
        info = Siginfo()
        options = _REMOTE_DARWIN_WEXITED | _REMOTE_DARWIN_WNOWAIT
        if nohang:
            options |= os.WNOHANG
        ct.set_errno(0)
        if _waitid(_REMOTE_DARWIN_P_PID, pid, ct.byref(info), options):
            errno = ct.get_errno()
            raise OSError(errno, os.strerror(errno))
        if nohang and not info.si_pid:
            return None
        return _remote_process_returncode(info.si_code, info.si_status)

    return waitpid


def _remote_darwin_process_wait(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
    return _remote_darwin_process_waiter()(pid, nohang=nohang)


def _remote_process_wait(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
    waitid: ta.Any = getattr(os, 'waitid', None)
    if waitid is None:
        platform: ta.Any = sys.platform
        if platform != 'darwin':
            raise RuntimeError('waitid is unavailable')
        return _remote_darwin_process_wait(pid, nohang=nohang)

    options = os.WEXITED | os.WNOWAIT
    if nohang:
        options |= os.WNOHANG
    info = waitid(os.P_PID, pid, options)
    if info is None:
        return None
    return _remote_process_returncode(info.si_code, info.si_status)


def _remote_fs_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _remote_glob_root(pattern: str) -> str:
    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)
    drive, tail = os.path.splitdrive(pattern)
    root = drive + os.sep
    for part in tail.lstrip(os.sep).split(os.sep):
        if any(char in part for char in '*?['):
            break
        root = os.path.join(root, part)
    return root


def _remote_path_is_under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


class _RemoteFsFileChangedError(RuntimeError):
    pass


class _RemoteFsService:
    @staticmethod
    def _resolve(path: str) -> str:
        return os.path.abspath(os.path.realpath(path))

    @staticmethod
    def _entry(path: str, name: ta.Optional[str] = None) -> FsEntry:
        return FsEntry(
            name=os.path.basename(path) if name is None else name,
            path=path,
            is_dir=os.path.isdir(path),
            is_file=os.path.isfile(path),
            is_symlink=os.path.islink(path),
        )

    @staticmethod
    def _check_expected_digest(path: str, expected_digest: str) -> None:
        try:
            with open(path, 'rb') as f:  # noqa
                actual_digest = _remote_fs_digest(f.read())
        except FileNotFoundError:
            actual_digest = None

        if actual_digest != expected_digest:
            raise _RemoteFsFileChangedError(f'File changed since it was read: {path!r}')

    async def resolve_path(self, params: ta.Any) -> str:
        p: PathParams = unmarshal_obj(params, PathParams)
        return self._resolve(p.path)

    async def stat(self, params: ta.Any) -> ta.Any:
        p: PathParams = unmarshal_obj(params, PathParams)
        lst = os.lstat(p.path)
        st = os.stat(p.path)
        return marshal_obj(StatResult(
            path=p.path,
            size=st.st_size,
            is_dir=stat_.S_ISDIR(st.st_mode),
            is_file=stat_.S_ISREG(st.st_mode),
            is_symlink=stat_.S_ISLNK(lst.st_mode),
        ))

    async def read_file(self, params: ta.Any) -> ta.Any:
        p: PathParams = unmarshal_obj(params, PathParams)
        with open(p.path, 'rb') as f:  # noqa
            data = f.read()
        return marshal_obj(ReadFileResult(
            data=data,
            digest=_remote_fs_digest(data),
        ))

    async def write_file(self, params: ta.Any) -> ta.Any:
        p: WriteFileParams = unmarshal_obj(params, WriteFileParams)
        path = p.path
        content = p.content
        overwrite = p.overwrite
        expected_digest = p.expected_digest

        dst_dir = os.path.dirname(path)
        tmp_dir = tempfile.mkdtemp(prefix='.omllm-write-', dir=dst_dir)
        tmp_path = os.path.join(tmp_dir, 'file')
        fd = -1
        try:
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            with os.fdopen(fd, 'wb') as f:
                fd = -1
                f.write(content)

            try:
                lst = os.lstat(path)
            except FileNotFoundError:
                if expected_digest is not None:
                    raise _RemoteFsFileChangedError(f'File changed since it was read: {path!r}') from None
                os.link(tmp_path, path)
                os.unlink(tmp_path)
                tmp_path = ''
                return marshal_obj(WriteFileResult(
                    created=True,
                ))

            if not overwrite:
                raise FileExistsError(path)
            if not stat_.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                self._check_expected_digest(path, expected_digest)

            os.chmod(tmp_path, stat_.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            tmp_path = ''
            return marshal_obj(WriteFileResult(
                created=False,
            ))

        finally:
            if fd >= 0:
                os.close(fd)
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
            os.rmdir(tmp_dir)

    async def list_dir(self, params: ta.Any) -> ta.Any:
        p: PathParams = unmarshal_obj(params, PathParams)
        return marshal_obj(
            [
                FsEntry(
                    name=entry.name,
                    path=entry.path,
                    is_dir=entry.is_dir(),
                    is_file=entry.is_file(),
                    is_symlink=entry.is_symlink(),
                )
                for entry in os.scandir(p.path)
            ],
            ta.List[FsEntry],
        )

    async def glob(self, params: ta.Any) -> ta.Any:
        p: GlobParams = unmarshal_obj(params, GlobParams)
        pattern = p.pattern
        root = p.root
        max_results = p.max_results

        resolved_root = self._resolve(root)
        resolved_glob_root = self._resolve(_remote_glob_root(pattern))
        if not _remote_path_is_under(resolved_glob_root, resolved_root):
            raise ValueError(f'glob root {resolved_glob_root!r} is outside permitted root {resolved_root!r}')

        entries: ta.List[FsEntry] = []
        has_more = False
        for path in glob_.iglob(pattern, recursive=True):
            if not _remote_path_is_under(self._resolve(path), resolved_root):
                continue
            if max_results is not None and len(entries) >= max_results:
                has_more = True
                break
            entries.append(self._entry(path))
        return marshal_obj(GlobResult(
            entries=entries,
            has_more=has_more,
        ))


##


def _remote_waitstatus_to_exitcode(status: int) -> int:
    # os.waitstatus_to_exitcode is 3.9+.
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    raise ValueError(f'Unexpected wait status: {status!r}')


def _remote_log(msg: str, *, exc: ta.Optional[BaseException] = None) -> None:
    """Writes a line of agent diagnostics - with a traceback, given `exc` - to stderr, which the host captures."""

    try:
        parts = [f'omllm remote agent: {msg}\n']
        if exc is not None:
            parts.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
        sys.stderr.write(''.join(parts))
        sys.stderr.flush()
    except Exception:  # noqa
        pass


class _RemoteServerProcess:
    def __init__(
            self,
            service: '_RemoteProcessService',  # noqa: UP037
            process_id: str,
            popen: subprocess.Popen,
            *,
            created_at: float,
            pty_master_fd: ta.Optional[int],
            pty_slave_fd: ta.Optional[int],
            pty_winsize: ta.Optional[ta.Tuple[int, int]],
    ) -> None:
        super().__init__()

        self._service = service
        self.id = process_id
        self.popen = popen
        self.created_at = created_at

        self._pty_master_fd = pty_master_fd
        self._pty_slave_fd = pty_slave_fd
        self._pty_read_fd: ta.Optional[int] = None
        self._pty_reader_task: ta.Optional[asyncio.Task] = None
        self._pty_readable: ta.Optional[asyncio.Future] = None
        self._pty_winsize = pty_winsize

        self._stdin: ta.Optional[asyncio.StreamWriter] = None
        self._read_transports: ta.List[asyncio.BaseTransport] = []
        self._reader_tasks: ta.List[asyncio.Task] = []
        self._open_readers = 0
        self._close_task: ta.Optional[asyncio.Task] = None

        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._returncode: ta.Optional[int] = None
        self._reaped = False

    @property
    def returncode(self) -> ta.Optional[int]:
        return self._returncode

    @property
    def exited(self) -> bool:
        return self._exited.is_set()

    #

    def _add_reader(self, read: ta.Callable[[], ta.Coroutine[ta.Any, ta.Any, None]]) -> asyncio.Task:
        self._open_readers += 1
        task = asyncio.create_task(
            self._run_reader(read),
            name=f'remote-read-{self.id}',
        )
        self._reader_tasks.append(task)
        return task

    async def _run_reader(self, read: ta.Callable[[], ta.Coroutine[ta.Any, ta.Any, None]]) -> None:
        try:
            await read()
        finally:
            # The last reader to finish - at EOF, or torn down - is what ends the output. Announcing that from here,
            # before the task completes, is what lets `_run_close` order its reply after every last byte.
            self._open_readers -= 1
            if self._open_readers == 0 and not self._output_ended.is_set():
                self._output_ended.set()
                await self._service.notify(
                    PROCESS_OUTPUT_END_METHOD,
                    marshal_obj(OutputEndEvent(
                        id=self.id,
                    )),
                )

    async def _connect_reader(self, file: ta.IO, fd: int) -> None:
        reader = await asyncio_open_stream_reader(file)
        transport = reader._transport  # type: ignore[attr-defined]  # noqa
        if transport is not None:
            self._read_transports.append(transport)
        self._add_reader(lambda: self._read_output(reader, fd))

    async def start(self) -> None:
        if self._pty_master_fd is not None:
            read_fd = os.dup(self._pty_master_fd)
            os.set_blocking(read_fd, False)
            self._pty_read_fd = read_fd
            self._pty_reader_task = self._add_reader(lambda: self._read_pty_output(read_fd, 1))

            write_file = os.fdopen(os.dup(self._pty_master_fd), 'wb', 0)
            self._stdin = await asyncio_open_stream_writer(write_file)
        else:
            if self.popen.stdout is not None:
                await self._connect_reader(self.popen.stdout, 1)
            if self.popen.stderr is not None:
                await self._connect_reader(self.popen.stderr, 2)
            if self.popen.stdin is not None:
                self._stdin = await asyncio_open_stream_writer(self.popen.stdin)

        if not self._reader_tasks:
            # Nothing to read: the output is over before it began.
            self._output_ended.set()
            self._service.queue_event(
                PROCESS_OUTPUT_END_METHOD,
                marshal_obj(OutputEndEvent(
                    id=self.id,
                )),
            )

    #

    async def _drain_pty_output(self, fd: int, output_fd: int) -> bool:
        """Forwards whatever is queued on the master; False once the pty is finished (its last slave closed)."""

        while True:
            try:
                data = os.read(fd, _REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except (BlockingIOError, InterruptedError):
                return True
            except OSError:
                # Linux pty masters report EIO when the last slave closes; BSDs return EOF.
                return False
            if not data:
                return False
            await self._service.notify(
                PROCESS_OUTPUT_METHOD,
                marshal_obj(OutputEvent(
                    id=self.id,
                    fd=output_fd,
                    data=data,
                )),
            )

    def _close_pty_slave(self) -> None:
        if self._pty_slave_fd is not None:
            os.close(self._pty_slave_fd)
            self._pty_slave_fd = None

    async def _read_pty_output(self, fd: int, output_fd: int) -> None:
        loop = asyncio.get_running_loop()
        try:
            while True:
                if not await self._drain_pty_output(fd, output_fd):
                    return

                if self.exited and self._pty_slave_fd is not None:
                    # Keep one slave descriptor open until the leader has exited and every byte already queued on the
                    # master has been consumed. Closing the final slave first can discard trailing pty output.
                    self._close_pty_slave()
                    continue

                # Wait for output - or for the exit, which `_poll_exit` announces by resolving this same future.
                readable = self._pty_readable = loop.create_future()

                def on_readable() -> None:
                    if not readable.done():
                        readable.set_result(None)

                loop.add_reader(fd, on_readable)
                try:
                    await readable
                finally:
                    self._pty_readable = None
                    if self._pty_read_fd == fd:
                        loop.remove_reader(fd)

        finally:
            if self._pty_read_fd == fd:
                self._pty_read_fd = None
                os.close(fd)

    async def _read_output(self, reader: asyncio.StreamReader, fd: int) -> None:
        while True:
            try:
                data = await reader.read(_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except OSError:
                return
            if not data:
                return
            await self._service.notify(
                PROCESS_OUTPUT_METHOD,
                marshal_obj(OutputEvent(
                    id=self.id,
                    fd=fd,
                    data=data,
                )),
            )

    #

    def _poll_exit(self) -> None:
        """
        A non-blocking, non-reaping probe of the child, run from the service's SIGCHLD handler: the first to see the
        exit records and announces it. The leader stays a zombie - its pid and pgid ours to signal - until `close` reaps
        it.
        """

        if self._exited.is_set() or self._reaped:
            return
        try:
            returncode = _remote_process_wait(self.popen.pid, nohang=True)
        except ChildProcessError:
            # Reaped behind our back: there is no exit status to be had, and nothing more to observe.
            return
        if returncode is None:
            return
        self._returncode = returncode
        self._exited.set()
        if (readable := self._pty_readable) is not None and not readable.done():
            readable.set_result(None)
        self._service.queue_event(
            PROCESS_EXITED_METHOD,
            marshal_obj(ExitedEvent(
                id=self.id,
                returncode=returncode,
            )),
        )

    def _signal(self, sig: int, process_group: bool) -> None:
        if self._reaped:
            raise ProcessLookupError(self.popen.pid)
        pid = self.popen.pid
        if self.exited:
            # The unreaped leader keeps its pid, and therefore its process-group id, from being reused.
            if process_group:
                try:
                    os.killpg(pid, sig)
                except (PermissionError, ProcessLookupError):
                    pass
            return

        if process_group:
            try:
                os.killpg(pid, sig)
            except ProcessLookupError:
                # No such group yet: the pty bootstrap creates its session right after exec, and a signal can race that
                # setup. Hit the owned pid so it cannot escape, then sweep the group once more in case it came to exist
                # in between - and already has members.
                self._kill_leader(sig)
                try:
                    os.killpg(pid, sig)
                except ProcessLookupError:
                    pass
            except PermissionError:
                # macOS/BSD can return EPERM for a group whose members are all zombies - benign for a process we still
                # own. The confirming probe is unreliable on Darwin, so deliver to the owned leader pid directly rather
                # than risk swallowing a signal that never reached a live leader (whose handlers would then never run).
                self._kill_leader(sig)
        else:
            self._kill_leader(sig)

    def _kill_leader(self, sig: int) -> None:
        """
        Delivers `sig` to the owned leader pid directly - used when the group signal cannot be, or may not have been,
        delivered. ESRCH is benign (already gone); EPERM on our own child is a zombie on macOS/BSD, benign once its exit
        is confirmed and a genuine error otherwise.
        """

        try:
            os.kill(self.popen.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            if not self._is_exited_nowait():
                raise

    def _is_exited_nowait(self) -> bool:
        try:
            return _remote_process_wait(self.popen.pid, nohang=True) is not None
        except ChildProcessError:
            return True
        except OSError:
            return False

    async def signal(self, sig: int, process_group: bool) -> None:
        self._signal(sig, process_group)

    async def write(self, data: bytes) -> None:
        if self._stdin is None or self._stdin.is_closing():
            raise BrokenPipeError('process has no open stdin')
        self._stdin.write(data)
        await self._stdin.drain()

    async def write_eof(self) -> None:
        if self._stdin is None or self._stdin.is_closing():
            return
        try:
            self._stdin.write_eof()
        except (AttributeError, NotImplementedError):
            self._stdin.close()

    async def resize(self, rows: int, cols: int) -> None:
        if self._pty_master_fd is None:
            raise RuntimeError('process does not have a pty')

        import fcntl
        import struct
        import termios

        fcntl.ioctl(self._pty_master_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        self._pty_winsize = (rows, cols)
        if not self.exited:
            try:
                os.killpg(self.popen.pid, signal.SIGWINCH)
            except ProcessLookupError:
                pass
            except PermissionError:
                if not self._is_exited_nowait():
                    raise

    #

    async def _wait_exited(self, timeout: ta.Optional[float]) -> bool:
        if self.exited:
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._exited.wait(), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self.exited
        return True

    async def _wait_output_ended(self, timeout: ta.Optional[float]) -> bool:
        if self._output_ended.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._output_ended.wait(), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self._output_ended.is_set()
        return True

    def _close_streams(self) -> None:
        if self._stdin is not None:
            self._stdin.close()
        for transport in self._read_transports:
            transport.close()
        self._read_transports.clear()
        self._close_pty_slave()
        if (task := self._pty_reader_task) is not None and not task.done():
            task.cancel()
        if (fd := self._pty_read_fd) is not None:
            # Taken out from under the reader: unregister it here too, before the fd number can be reused.
            self._pty_read_fd = None
            asyncio.get_running_loop().remove_reader(fd)
            try:
                os.close(fd)
            except OSError:
                pass
        if self._pty_master_fd is not None:
            try:
                os.close(self._pty_master_fd)
            except OSError:
                pass
            self._pty_master_fd = None

    def _reap(self) -> None:
        if self._reaped:
            return
        _, status = os.waitpid(self.popen.pid, 0)
        self._reaped = True
        if self._returncode is None:
            self._returncode = _remote_waitstatus_to_exitcode(status)
            self._exited.set()
        self.popen.returncode = self._returncode

    async def _run_close(self, policy: ClosePolicySpec) -> CloseResult:
        close_stdin = policy.close_stdin
        first_signal = policy.signal
        grace_s = policy.grace_s
        kill_s = policy.kill_s
        process_group = policy.process_group
        drain_s = policy.drain_s

        if self.exited and not self._reaped and not self._is_exited_nowait():
            # We were told it exited, but a fresh probe of the (long-established, not just-forked) leader finds it still
            # alive - a stale belief. Correct it, so the graceful signal-and-wait below runs: a live process must get
            # its TERM (and the chance to run its handlers) before any KILL.
            self._exited.clear()
            self._returncode = None

        if not self.exited:
            if close_stdin:
                try:
                    await self.write_eof()
                except Exception:  # noqa
                    pass
            self._signal(first_signal, process_group)
            if not await self._wait_exited(grace_s):
                self._signal(signal.SIGKILL, process_group)
                if not await self._wait_exited(kill_s):
                    self._close_streams()
                    raise RuntimeError(f'process {self.id!r} survived SIGKILL for {kill_s}s')

        # Sweep descendants while the unreaped leader still makes its process-group id safe to address.
        if process_group:
            self._signal(first_signal, True)
        if not self._output_ended.is_set():
            await self._wait_output_ended(drain_s)
        if process_group:
            self._signal(signal.SIGKILL, True)

        self._close_streams()
        if self._reader_tasks:
            # Every byte, and the end of output, has been sent once these are done - so the reply below comes after.
            await asyncio.gather(*self._reader_tasks, return_exceptions=True)
        self._reap()
        self._service.finished(self)
        return CloseResult(returncode=check.not_none(self._returncode), state='reaped')

    async def close(self, policy: ClosePolicySpec) -> CloseResult:
        if self._reaped:
            return CloseResult(returncode=check.not_none(self._returncode), state='reaped')
        if self._close_task is None:
            self._close_task = asyncio.create_task(
                self._run_close(policy),
                name=f'remote-close-{self.id}',
            )
        return await asyncio.shield(self._close_task)

    async def _hard_kill(self, timeout: float) -> ta.Optional[int]:
        """
        Last resort once a graceful close has failed: SIGKILLs the group and the leader, closes our ends of its streams,
        and reaps it within `timeout`, so nothing it started outlives the agent. Returns the reaped returncode, or None
        if it could not be reaped in time.
        """

        pid = self.popen.pid
        if not self._reaped:
            # Only while unreaped: the pid, and so its process-group id, is still ours to signal.
            for kill in (os.killpg, os.kill):
                try:
                    kill(pid, signal.SIGKILL)
                except (PermissionError, ProcessLookupError):
                    pass
        self._close_streams()

        deadline = time.monotonic() + timeout
        while not self._reaped:
            try:
                reaped_pid, status = os.waitpid(pid, os.WNOHANG)  # noqa: ASYNC222  # WNOHANG: never blocks
            except ChildProcessError:
                # Reaped behind our back: there is no status left to collect.
                self._reaped = True
                break
            if reaped_pid:
                self._reaped = True
                self._returncode = _remote_waitstatus_to_exitcode(status)
                self._exited.set()
                self.popen.returncode = self._returncode
                break
            if time.monotonic() >= deadline:
                return None
            await asyncio.sleep(.01)

        self._service.finished(self)
        return self._returncode


class _RemoteProcessService:
    _DEFAULT_CLOSE_POLICY: ta.ClassVar[ClosePolicySpec] = ClosePolicySpec(
        signal=int(signal.SIGTERM),
        grace_s=5.,
        kill_s=5.,
        close_stdin=True,
        process_group=True,
        drain_s=1.,
    )

    def __init__(self) -> None:
        super().__init__()

        self._peer: ta.Optional[RpcPeer] = None
        self._processes: ta.Dict[str, _RemoteServerProcess] = {}
        self._next_id = 1
        self._closed = False

        self._sigchld_loop: ta.Optional[asyncio.AbstractEventLoop] = None

        # Exit and end-of-output announcements. They originate in sync code that cannot await a send, so they are queued
        # and sent, in order, by at most one short-lived task.
        self._events: ta.Deque[ta.Tuple[str, ta.Any]] = collections.deque()
        self._event_task: ta.Optional[asyncio.Task] = None

    def set_peer(self, peer: RpcPeer) -> None:
        if self._peer is not None:
            raise RuntimeError('peer already set')
        self._peer = peer

    async def notify(self, method: str, params: ta.Any) -> None:
        if self._peer is None or self._peer.closed:
            return
        try:
            # Fire-and-forget on an ordered stream that the host applies inline, in its receive loop: wire order is
            # delivery order. Awaiting the write is what makes process.close's reply - sent after it - an ordering
            # barrier: by the time the host sees that reply, every preceding output chunk is in its spool.
            await self._peer.notify(method, params)
        except Exception:  # noqa
            # The peer owns the connection failure. Keep draining child pipes until server teardown reaches us.
            pass

    def queue_event(self, method: str, params: ta.Any) -> None:
        self._events.append((method, params))
        if self._event_task is None or self._event_task.done():
            self._event_task = asyncio.create_task(
                self._send_events(),
                name='remote-events',
            )

    async def _send_events(self) -> None:
        while self._events:
            method, params = self._events.popleft()
            await self.notify(method, params)

    #

    def _ensure_sigchld(self) -> None:
        """
        Exits are observed by one SIGCHLD handler probing every unexited child with a non-blocking, non-reaping waitid:
        no thread and no task per child, so nothing to saturate. It is installed before the first child exists, so no
        exit can slip by unnoticed.
        """

        if self._sigchld_loop is not None:
            return
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGCHLD, self._on_sigchld)
        self._sigchld_loop = loop

    def _remove_sigchld(self) -> None:
        if (loop := self._sigchld_loop) is None:
            return
        self._sigchld_loop = None
        try:
            loop.remove_signal_handler(signal.SIGCHLD)
        except (RuntimeError, ValueError):
            pass

    def _on_sigchld(self) -> None:
        # One signal may stand for any number of exits.
        for process in list(self._processes.values()):
            process._poll_exit()  # noqa: SLF001

    #

    def _lookup(self, process_id: str) -> _RemoteServerProcess:
        try:
            return self._processes[process_id]
        except KeyError:
            raise ValueError(f'No such remote process: {process_id!r}') from None

    def finished(self, process: _RemoteServerProcess) -> None:
        if self._processes.get(process.id) is process:
            self._processes.pop(process.id, None)

    @staticmethod
    def _stdio_value(value: str, *, stderr: bool = False) -> ta.Any:
        if value == 'pipe':
            return subprocess.PIPE
        if value == 'devnull':
            return subprocess.DEVNULL
        if stderr and value == 'stdout':
            return subprocess.STDOUT
        raise ValueError(f'Unsupported remote stdio channel: {value!r}')

    @staticmethod
    def _set_pty_winsize(fd: int, rows: int, cols: int) -> None:
        import fcntl
        import struct
        import termios

        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))

    async def spawn(self, params: ta.Any) -> ta.Any:
        if self._closed:
            raise RuntimeError('remote process service is closed')
        p: SpawnParams = unmarshal_obj(params, SpawnParams)
        argv = list(p.argv)
        cwd = p.cwd
        env = dict(p.env) if p.env is not None else None
        name = p.name
        stdio = p.stdio
        kind = stdio.kind

        process_id = f'p{self._next_id}'
        self._next_id += 1

        self._ensure_sigchld()

        master: ta.Optional[int] = None
        slave: ta.Optional[int] = None
        pty_slave_fd: ta.Optional[int] = None
        pty_winsize: ta.Optional[ta.Tuple[int, int]] = None
        try:
            try:
                if kind == 'pipes':
                    stdin = self._stdio_value(check.not_none(stdio.stdin))
                    stdout = self._stdio_value(check.not_none(stdio.stdout))
                    stderr = self._stdio_value(check.not_none(stdio.stderr), stderr=True)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        argv,
                        cwd=cwd,
                        env=env,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                        bufsize=0,
                        start_new_session=True,
                    )

                elif kind == 'pty':
                    rows = check.not_none(stdio.rows)
                    cols = check.not_none(stdio.cols)
                    term = stdio.term
                    if term is not None and (env is None or 'TERM' not in env):
                        env = dict(os.environ if env is None else env)
                        env['TERM'] = term

                    master, slave = os.openpty()
                    self._set_pty_winsize(slave, rows, cols)
                    pty_winsize = (rows, cols)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        [sys.executable, '-c', _REMOTE_PTY_CHILD_CODE, json.dumps(argv)],
                        cwd=cwd,
                        env=env,
                        stdin=slave,
                        stdout=slave,
                        stderr=slave,
                        close_fds=True,
                    )
                    pty_slave_fd = slave
                    slave = None

                else:
                    raise ValueError(f'Invalid remote stdio kind: {kind!r}')

            except BaseException:
                if master is not None:
                    os.close(master)
                raise

        finally:
            if slave is not None:
                os.close(slave)

        process = _RemoteServerProcess(
            self,
            process_id,
            popen,
            created_at=time.time(),
            pty_master_fd=master,
            pty_slave_fd=pty_slave_fd,
            pty_winsize=pty_winsize,
        )
        # Registered before start()'s first suspension point. The SIGCHLD handler is already installed and there is no
        # await between the fork above and here, so a fast exit's signal cannot arrive before the process is findable -
        # no speculative waitid probe of a just-forked child (which some platforms mis-report as already exited) is
        # needed to catch it.
        self._processes[process_id] = process
        try:
            await process.start()
        except BaseException:
            self._processes.pop(process_id, None)
            try:
                os.kill(popen.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(popen.pid, 0)  # noqa: ASYNC222
            popen.returncode = -signal.SIGKILL
            process._close_streams()  # noqa: SLF001
            raise

        return marshal_obj(SpawnResult(
            id=process.id,
            pid=process.popen.pid,
            created_at=process.created_at,
            name=name,
        ))

    async def signal(self, params: ta.Any) -> None:
        p: SignalParams = unmarshal_obj(params, SignalParams)
        await self._lookup(p.id).signal(p.signal, p.process_group)

    async def close(self, params: ta.Any) -> ta.Any:
        p: CloseParams = unmarshal_obj(params, CloseParams)
        return marshal_obj(await self._lookup(p.id).close(p.policy))

    async def write(self, params: ta.Any) -> None:
        p: WriteParams = unmarshal_obj(params, WriteParams)
        await self._lookup(p.id).write(p.data)

    async def write_eof(self, params: ta.Any) -> None:
        p: ProcessRefParams = unmarshal_obj(params, ProcessRefParams)
        await self._lookup(p.id).write_eof()

    async def resize(self, params: ta.Any) -> None:
        p: ResizeParams = unmarshal_obj(params, ResizeParams)
        await self._lookup(p.id).resize(p.rows, p.cols)

    async def _close_at_shutdown(self, process: _RemoteServerProcess) -> None:
        """
        Closes one process as part of agent shutdown, reporting how it went on stderr - nothing else will ever observe
        it. A process whose graceful close fails is not left running past the agent: it is killed outright.
        """

        pid = process.popen.pid
        exited_before = process.exited
        start = time.monotonic()
        try:
            result = await process.close(self._DEFAULT_CLOSE_POLICY)

        except BaseException as e:  # noqa
            _remote_log(
                f'process {process.id} (pid {pid}): close failed after {time.monotonic() - start:.3f}s '
                f'(exited before close: {exited_before}), killing it: {e!r}',
                exc=e,
            )
            returncode = await process._hard_kill(self._DEFAULT_CLOSE_POLICY.kill_s)  # noqa: SLF001
            outcome = f'returncode={returncode}' if returncode is not None else 'NOT reaped'
            _remote_log(f'process {process.id} (pid {pid}): killed, {outcome}')
            if not isinstance(e, Exception):
                raise

        else:
            _remote_log(
                f'process {process.id} (pid {pid}): closed in {time.monotonic() - start:.3f}s '
                f'(exited before close: {exited_before}), returncode={result.returncode}',
            )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._processes:
                await asyncio.gather(*[
                    self._close_at_shutdown(process)
                    for process in list(self._processes.values())
                ], return_exceptions=True)
        finally:
            self._remove_sigchld()
            if (task := self._event_task) is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)


##


class RemoteAgentRpcHandler(RpcHandler):
    def __init__(self) -> None:
        super().__init__()

        self._fs = _RemoteFsService()
        self._processes = _RemoteProcessService()
        self._methods = {
            FS_RESOLVE_PATH_METHOD: self._fs.resolve_path,
            FS_STAT_METHOD: self._fs.stat,
            FS_READ_FILE_METHOD: self._fs.read_file,
            FS_WRITE_FILE_METHOD: self._fs.write_file,
            FS_LIST_DIR_METHOD: self._fs.list_dir,
            FS_GLOB_METHOD: self._fs.glob,
            PROCESS_SPAWN_METHOD: self._processes.spawn,
            PROCESS_SIGNAL_METHOD: self._processes.signal,
            PROCESS_CLOSE_METHOD: self._processes.close,
            PROCESS_WRITE_METHOD: self._processes.write,
            PROCESS_WRITE_EOF_METHOD: self._processes.write_eof,
            PROCESS_RESIZE_METHOD: self._processes.resize,
        }

    def set_peer(self, peer: RpcPeer) -> None:
        self._processes.set_peer(peer)

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None
        return await fn(params)

    async def aclose(self) -> None:
        await self._processes.aclose()


########################################
# main.py


##


async def serve_remote_agent(input: ta.BinaryIO, output: ta.BinaryIO) -> None:  # noqa
    reader = await asyncio_open_stream_reader(input)
    writer = await asyncio_open_stream_writer(output)

    handler = RemoteAgentRpcHandler()
    peer = RpcPeer(AsyncioStreamRpcChannel(reader, writer), handler=handler)
    handler.set_peer(peer)
    try:
        await peer.serve()
    finally:
        await handler.aclose()


def remote_agent_main() -> None:
    runtime = pyremote_bootstrap_finalize()
    asyncio.run(serve_remote_agent(runtime.input, runtime.output))
