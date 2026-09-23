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
import binascii
import collections
import dataclasses as dc
import functools
import glob as glob_mod
import hashlib
import inspect
import json
import os
import platform
import pwd
import select
import signal
import site
import stat as stat_mod
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import typing as ta
import zlib


########################################


if sys.version_info < (3, 8):
    raise OSError(f'Requires python (3, 8), got {sys.version_info} from {sys.executable}')  # noqa


def __om_amalg__():  # noqa
    return dict(
        src_files=[
            dict(path='../../../omcore/asyncs/asyncio/streams.py', sha1='0f5b4b31c139f08110827b601ff4f0d45489fba2'),
            dict(path='../../../omcore/lite/abstract.py', sha1='a2fc3f3697fa8de5247761e9d554e70176f37aac'),
            dict(path='../../../omcore/lite/check.py', sha1='62b9ccea94c4f7bcef97e7adae8674b8cb11d4af'),
            dict(path='../../../omcore/os/pyremote/core.py', sha1='b0baf1528b4daa0bd392ccdf34b8d34b43d4243d'),
            dict(path='protocol.py', sha1='0820e42ac03ae29bacd92aa6dcae3be20d7b38c6'),
            dict(path='../../core/rpc/errors.py', sha1='9c59beacb63fd0f49b731f8d74b38faefdc90d22'),
            dict(path='../../core/rpc/handlers.py', sha1='123f3c9e2c61649e7d65192cd0f559fefd705a57'),
            dict(path='../../core/rpc/messages.py', sha1='738982ca2b771c5ed2a1498f56cc8201e03533c8'),
            dict(path='../../core/rpc/channels.py', sha1='28b173f12d80f7941550c831c7451c2aaa37259c'),
            dict(path='../../core/rpc/peers.py', sha1='7355153cae5fa40f217d732ba0b6c586506b992c'),
            dict(path='server.py', sha1='069f943bef0b72cd642037cd7a33d6592e84e4af'),
            dict(path='main.py', sha1='12eef0f46ab416d4ccc8ae492388e5466d5f6be1'),
        ],
    )


########################################


# ../../../omcore/lite/abstract.py
T = ta.TypeVar('T')

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


async def asyncio_open_stream_writer(
        f: ta.IO,
        loop: ta.Any = None,
) -> asyncio.StreamWriter:
    if loop is None:
        loop = asyncio.get_running_loop()

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: asyncio.streams.FlowControlMixin(loop=loop),
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

            # Disable timeout
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
# ../protocol.py
"""JSON-compatible values shared by the host adapter and the remote agent payload."""


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


def encode_remote_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def decode_remote_bytes(value: ta.Any) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f'Expected base64 string, got {type(value).__name__}')
    try:
        return base64.b64decode(value.encode('ascii'), validate=True)
    except (UnicodeEncodeError, binascii.Error) as e:
        raise ValueError('Invalid base64 data') from e


def check_remote_dict(
        value: ta.Any,
        required: ta.AbstractSet[str],
        optional: ta.AbstractSet[str] = frozenset(),
) -> ta.Dict[str, ta.Any]:
    if not isinstance(value, dict):
        raise TypeError(f'Expected object, got {type(value).__name__}')
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise ValueError(
            f'Invalid object fields: required {sorted(required)!r}, '
            f'optional {sorted(optional)!r}, got {sorted(keys)!r}',
        )
    return value


def check_remote_str(value: ta.Any, *, non_empty: bool = False) -> str:
    if not isinstance(value, str) or (non_empty and not value):
        raise TypeError(f'Expected {"non-empty " if non_empty else ""}string, got {value!r}')
    return value


def check_remote_optional_str(value: ta.Any) -> ta.Optional[str]:
    if value is None:
        return None
    return check_remote_str(value)


def check_remote_bool(value: ta.Any) -> bool:
    if type(value) is not bool:
        raise TypeError(f'Expected bool, got {value!r}')
    return value


def check_remote_int(value: ta.Any, *, minimum: ta.Optional[int] = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise TypeError(f'Expected integer >= {minimum!r}, got {value!r}')
    return value


def check_remote_optional_int(value: ta.Any, *, minimum: ta.Optional[int] = None) -> ta.Optional[int]:
    if value is None:
        return None
    return check_remote_int(value, minimum=minimum)


def check_remote_float(value: ta.Any, *, minimum: ta.Optional[float] = None) -> float:
    if type(value) not in (int, float):
        raise TypeError(f'Expected number, got {value!r}')
    out = float(value)
    if minimum is not None and out < minimum:
        raise ValueError(f'Expected number >= {minimum!r}, got {value!r}')
    return out


def check_remote_optional_float(value: ta.Any, *, minimum: ta.Optional[float] = None) -> ta.Optional[float]:
    if value is None:
        return None
    return check_remote_float(value, minimum=minimum)


def check_remote_str_list(value: ta.Any, *, non_empty: bool = False) -> ta.List[str]:
    if not isinstance(value, list) or (non_empty and not value):
        raise TypeError(f'Expected {"non-empty " if non_empty else ""}string list, got {value!r}')
    for item in value:
        check_remote_str(item)
    return value


def check_remote_optional_str_dict(value: ta.Any) -> ta.Optional[ta.Dict[str, str]]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f'Expected string object, got {value!r}')
    for key, item in value.items():
        check_remote_str(key, non_empty=True)
        check_remote_str(item)
    return value


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
    remote_type: str
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


@dc.dataclass(frozen=True)
class RpcResultMessage:
    id: int
    result: ta.Any = None


@dc.dataclass(frozen=True)
class RpcErrorMessage:
    id: int
    error: RpcRemoteErrorData


@dc.dataclass(frozen=True)
class RpcCancelMessage:
    id: int


@dc.dataclass(frozen=True)
class RpcNotificationMessage:
    method: str
    params: ta.Any = None


@dc.dataclass(frozen=True)
class RpcPingMessage:
    id: int


@dc.dataclass(frozen=True)
class RpcPongMessage:
    id: int


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


class JsonRpcMessageCodec(RpcMessageCodec):
    @classmethod
    def _to_obj(cls, message: RpcMessage) -> ta.Mapping[str, ta.Any]:
        if isinstance(message, RpcRequestMessage):
            return {'type': 'request', 'id': message.id, 'method': message.method, 'params': message.params}
        if isinstance(message, RpcResultMessage):
            return {'type': 'result', 'id': message.id, 'result': message.result}
        if isinstance(message, RpcErrorMessage):
            return {
                'type': 'error',
                'id': message.id,
                'error': {
                    'code': message.error.code,
                    'type': message.error.remote_type,
                    'message': message.error.message,
                    'traceback': message.error.traceback,
                },
            }
        if isinstance(message, RpcCancelMessage):
            return {'type': 'cancel', 'id': message.id}
        if isinstance(message, RpcNotificationMessage):
            return {'type': 'notification', 'method': message.method, 'params': message.params}
        if isinstance(message, RpcPingMessage):
            return {'type': 'ping', 'id': message.id}
        if isinstance(message, RpcPongMessage):
            return {'type': 'pong', 'id': message.id}
        raise TypeError(message)

    @staticmethod
    def _check_keys(dct: ta.Mapping[str, ta.Any], keys: ta.AbstractSet[str]) -> None:
        actual = set(dct)
        if actual != keys:
            raise RpcProtocolError(f'Invalid RPC message fields: expected {sorted(keys)!r}, got {sorted(actual)!r}')

    @staticmethod
    def _decode_id(value: ta.Any) -> int:
        if type(value) is not int or value <= 0:
            raise RpcProtocolError(f'Invalid RPC message id: {value!r}')
        return value

    @staticmethod
    def _decode_method(value: ta.Any) -> str:
        if not isinstance(value, str) or not value:
            raise RpcProtocolError(f'Invalid RPC method: {value!r}')
        return value

    @classmethod
    def _from_obj(cls, obj: ta.Any) -> RpcMessage:
        if not isinstance(obj, dict):
            raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')

        message_type = obj.get('type')
        if message_type == 'request':
            cls._check_keys(obj, {'type', 'id', 'method', 'params'})
            return RpcRequestMessage(
                cls._decode_id(obj['id']),
                cls._decode_method(obj['method']),
                obj['params'],
            )
        if message_type == 'result':
            cls._check_keys(obj, {'type', 'id', 'result'})
            return RpcResultMessage(cls._decode_id(obj['id']), obj['result'])
        if message_type == 'error':
            cls._check_keys(obj, {'type', 'id', 'error'})
            error = obj['error']
            if not isinstance(error, dict):
                raise RpcProtocolError(f'RPC error must be an object, got {type(error).__name__}')
            cls._check_keys(error, {'code', 'type', 'message', 'traceback'})
            if not isinstance(error['code'], str) or not error['code']:
                raise RpcProtocolError(f'Invalid RPC error code: {error["code"]!r}')
            if not isinstance(error['type'], str) or not error['type']:
                raise RpcProtocolError(f'Invalid RPC error type: {error["type"]!r}')
            if not isinstance(error['message'], str):
                raise RpcProtocolError(f'Invalid RPC error message: {error["message"]!r}')
            if error['traceback'] is not None and not isinstance(error['traceback'], str):
                raise RpcProtocolError(f'Invalid RPC error traceback: {error["traceback"]!r}')
            return RpcErrorMessage(
                cls._decode_id(obj['id']),
                RpcRemoteErrorData(
                    code=error['code'],
                    remote_type=error['type'],
                    message=error['message'],
                    traceback=error['traceback'],
                ),
            )
        if message_type == 'cancel':
            cls._check_keys(obj, {'type', 'id'})
            return RpcCancelMessage(cls._decode_id(obj['id']))
        if message_type == 'notification':
            cls._check_keys(obj, {'type', 'method', 'params'})
            return RpcNotificationMessage(cls._decode_method(obj['method']), obj['params'])
        if message_type == 'ping':
            cls._check_keys(obj, {'type', 'id'})
            return RpcPingMessage(cls._decode_id(obj['id']))
        if message_type == 'pong':
            cls._check_keys(obj, {'type', 'id'})
            return RpcPongMessage(cls._decode_id(obj['id']))
        raise RpcProtocolError(f'Invalid RPC message type: {message_type!r}')

    def encode(self, message: RpcMessage) -> bytes:
        try:
            obj = self._to_obj(message)
            self._from_obj(obj)
            return json.dumps(
                obj,
                allow_nan=False,
                separators=(',', ':'),
            ).encode('utf-8')
        except (RecursionError, TypeError, ValueError) as e:
            raise RpcProtocolError(f'RPC message is not JSON-compatible: {e}') from e

    @staticmethod
    def _reject_json_constant(value: str) -> ta.NoReturn:
        raise ValueError(f'Invalid JSON constant: {value}')

    def decode(self, data: bytes) -> RpcMessage:
        try:
            obj = json.loads(data.decode('utf-8'), parse_constant=self._reject_json_constant)
        except (RecursionError, UnicodeDecodeError, ValueError) as e:
            raise RpcProtocolError(f'Invalid RPC JSON: {e}') from e
        return self._from_obj(obj)


########################################
# ../../../core/rpc/channels.py


##


DEFAULT_RPC_MAX_FRAME_BYTES = 16 * 1024 * 1024

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
    ) -> None:
        super().__init__()

        check.arg(max_frame_bytes > 0)

        self._reader = reader
        self._writer = writer
        self._codec = codec if codec is not None else JsonRpcMessageCodec()
        self._max_frame_bytes = max_frame_bytes

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
            await self._writer.wait_closed()
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
        self._outgoing = {}  # type: ta.Dict[int, asyncio.Future]
        self._pings = {}  # type: ta.Dict[int, asyncio.Future]
        self._incoming = {}  # type: ta.Dict[int, asyncio.Task]
        self._notifications = set()  # type: ta.Set[asyncio.Task]

        self._receive_task = None  # type: ta.Optional[asyncio.Task]
        self._closed_event = asyncio.Event()
        self._closing = False
        self._finished = False
        self._failure = None  # type: ta.Optional[BaseException]
        self._background_failure = None  # type: ta.Optional[BaseException]

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

    def _new_id(self) -> int:
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def _check_running(self) -> None:
        if self._receive_task is None:
            raise RuntimeError('RPC peer has not been started')
        if self._closing or self._finished:
            raise RpcConnectionClosedError('RPC peer is closed')

    def _abort(self, exc: BaseException) -> None:
        if self._background_failure is None:
            self._background_failure = exc
        if self._receive_task is not None and not self._receive_task.done():
            self._receive_task.cancel()

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

    async def start(self) -> None:
        if self._receive_task is not None or self._finished:
            raise RuntimeError('RPC peer has already been started')
        if self._channel.closed:
            raise RpcConnectionClosedError('RPC channel is closed')
        self._receive_task = asyncio.create_task(
            self._run(),
            name='omllm-rpc-receive',
        )

    async def wait_closed(self) -> None:
        if self._receive_task is None and not self._finished:
            raise RuntimeError('RPC peer has not been started')
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

        may_have_sent = False
        try:
            may_have_sent = True
            await self._send(RpcRequestMessage(request_id, method, params))
            return await future

        except asyncio.CancelledError:
            future.cancel()
            if may_have_sent:
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
        response = None  # type: ta.Optional[RpcMessage]
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
            if self._notification_error_handler is not None:
                self._notification_error_handler(message, e)

    async def _dispatch(self, message: RpcMessage) -> None:
        if isinstance(message, RpcRequestMessage):
            if message.id in self._incoming:
                raise RpcProtocolError(f'Duplicate inbound RPC request id: {message.id}')
            if len(self._incoming) + len(self._notifications) >= self._max_in_flight:
                await self._channel.send(RpcErrorMessage(
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
            try:
                future = self._outgoing.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC result id: {message.id}') from None
            if not future.done():
                future.set_result(message.result)
            return

        if isinstance(message, RpcErrorMessage):
            try:
                future = self._outgoing.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC error id: {message.id}') from None
            if not future.done():
                if message.error.code == 'cancelled':
                    future.set_exception(RpcRemoteCancelledError(message.error))
                else:
                    future.set_exception(RpcRemoteError(message.error))
            return

        if isinstance(message, RpcPingMessage):
            await self._channel.send(RpcPongMessage(message.id))
            return

        if isinstance(message, RpcPongMessage):
            try:
                future = self._pings.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC pong id: {message.id}') from None
            if not future.done():
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
            await self._channel.aclose()
        finally:
            current = asyncio.current_task()
            tasks = [
                task
                for task in [*self._incoming.values(), *self._notifications]
                if task is not current and not task.done()
            ]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self._incoming.clear()
            self._notifications.clear()

            for future in [*self._outgoing.values(), *self._pings.values()]:
                if not future.done():
                    future.set_exception(self._connection_error(message))
            self._outgoing.clear()
            self._pings.clear()

            self._closed_event.set()

    async def _run(self) -> None:
        failure = None  # type: ta.Optional[BaseException]
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
            if not self._receive_task.done():
                self._receive_task.cancel()
            await self._receive_task
            await self._closed_event.wait()

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


def _remote_darwin_process_wait(pid: int, *, nohang: bool = False) -> ta.Optional[int]:
    # CPython did not expose os.waitid on macOS until 3.13, although libc and the kernel have long provided it. Keep
    # the child waitable so its pid/pgid remain ours until close deliberately reaps it. The first six siginfo_t fields
    # are fixed-width scalars on Darwin; the tail only reserves enough space for libc to fill the complete structure.
    import ctypes

    class Siginfo(ctypes.Structure):
        _fields_ = [
            ('si_signo', ctypes.c_int),
            ('si_errno', ctypes.c_int),
            ('si_code', ctypes.c_int),
            ('si_pid', ctypes.c_int),
            ('si_uid', ctypes.c_uint),
            ('si_status', ctypes.c_int),
            ('_tail', ctypes.c_ubyte * 104),
        ]

    waitid = ctypes.CDLL(None, use_errno=True).waitid
    waitid.argtypes = (ctypes.c_int, ctypes.c_uint, ctypes.c_void_p, ctypes.c_int)
    waitid.restype = ctypes.c_int

    info = Siginfo()
    options = _REMOTE_DARWIN_WEXITED | _REMOTE_DARWIN_WNOWAIT
    if nohang:
        options |= os.WNOHANG
    ctypes.set_errno(0)
    if waitid(_REMOTE_DARWIN_P_PID, pid, ctypes.byref(info), options):
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    if nohang and not info.si_pid:
        return None
    return _remote_process_returncode(info.si_code, info.si_status)


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
    def _entry(path: str, name: ta.Optional[str] = None) -> ta.Dict[str, ta.Any]:
        return {
            'name': os.path.basename(path) if name is None else name,
            'path': path,
            'is_dir': os.path.isdir(path),
            'is_file': os.path.isfile(path),
            'is_symlink': os.path.islink(path),
        }

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
        obj = check_remote_dict(params, {'path'})
        return self._resolve(check_remote_str(obj['path']))

    async def stat(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        lst = os.lstat(path)
        st = os.stat(path)
        return {
            'path': path,
            'size': st.st_size,
            'is_dir': stat_mod.S_ISDIR(st.st_mode),
            'is_file': stat_mod.S_ISREG(st.st_mode),
            'is_symlink': stat_mod.S_ISLNK(lst.st_mode),
        }

    async def read_file(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        with open(path, 'rb') as f:  # noqa
            data = f.read()
        return {
            'data': encode_remote_bytes(data),
            'digest': _remote_fs_digest(data),
        }

    async def write_file(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path', 'content', 'overwrite', 'expected_digest'})
        path = check_remote_str(obj['path'])
        content = decode_remote_bytes(obj['content'])
        overwrite = check_remote_bool(obj['overwrite'])
        expected_digest = check_remote_optional_str(obj['expected_digest'])

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
                return {'created': True}

            if not overwrite:
                raise FileExistsError(path)
            if not stat_mod.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                self._check_expected_digest(path, expected_digest)

            os.chmod(tmp_path, stat_mod.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            tmp_path = ''
            return {'created': False}

        finally:
            if fd >= 0:
                os.close(fd)
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
            os.rmdir(tmp_dir)

    async def list_dir(self, params: ta.Any) -> ta.List[ta.Dict[str, ta.Any]]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        return [
            {
                'name': entry.name,
                'path': entry.path,
                'is_dir': entry.is_dir(),
                'is_file': entry.is_file(),
                'is_symlink': entry.is_symlink(),
            }
            for entry in os.scandir(path)
        ]

    async def glob(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'pattern', 'root', 'max_results'})
        pattern = check_remote_str(obj['pattern'])
        root = check_remote_str(obj['root'])
        max_results = check_remote_optional_int(obj['max_results'], minimum=0)

        resolved_root = self._resolve(root)
        resolved_glob_root = self._resolve(_remote_glob_root(pattern))
        if not _remote_path_is_under(resolved_glob_root, resolved_root):
            raise ValueError(f'glob root {resolved_glob_root!r} is outside permitted root {resolved_root!r}')

        entries = []  # type: ta.List[ta.Dict[str, ta.Any]]
        has_more = False
        for path in glob_mod.iglob(pattern, recursive=True):
            if not _remote_path_is_under(self._resolve(path), resolved_root):
                continue
            if max_results is not None and len(entries) >= max_results:
                has_more = True
                break
            entries.append(self._entry(path))
        return {'entries': entries, 'has_more': has_more}


##


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
        self._pty_read_fd = None  # type: ta.Optional[int]
        self._pty_reader_task = None  # type: ta.Optional[asyncio.Task]
        self._pty_winsize = pty_winsize

        self._stdin = None  # type: ta.Optional[asyncio.StreamWriter]
        self._read_transports = []  # type: ta.List[asyncio.BaseTransport]
        self._reader_tasks = []  # type: ta.List[asyncio.Task]
        self._output_task = None  # type: ta.Optional[asyncio.Task]
        self._wait_task = None  # type: ta.Optional[asyncio.Task]
        self._close_task = None  # type: ta.Optional[asyncio.Task]

        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._returncode = None  # type: ta.Optional[int]
        self._reaped = False

    @property
    def returncode(self) -> ta.Optional[int]:
        return self._returncode

    @property
    def exited(self) -> bool:
        return self._exited.is_set()

    async def _connect_reader(self, file: ta.IO, fd: int) -> None:
        reader = await asyncio_open_stream_reader(file)
        transport = reader._transport  # type: ignore[attr-defined]  # noqa
        if transport is not None:
            self._read_transports.append(transport)
        self._reader_tasks.append(asyncio.create_task(self._read_output(reader, fd)))

    async def start(self) -> None:
        if self._pty_master_fd is not None:
            read_fd = os.dup(self._pty_master_fd)
            os.set_blocking(read_fd, False)
            self._pty_read_fd = read_fd
            self._pty_reader_task = asyncio.create_task(self._read_pty_output(read_fd, 1))
            self._reader_tasks.append(self._pty_reader_task)

            write_file = os.fdopen(os.dup(self._pty_master_fd), 'wb', 0)
            self._stdin = await asyncio_open_stream_writer(write_file)
        else:
            if self.popen.stdout is not None:
                await self._connect_reader(self.popen.stdout, 1)
            if self.popen.stderr is not None:
                await self._connect_reader(self.popen.stderr, 2)
            if self.popen.stdin is not None:
                self._stdin = await asyncio_open_stream_writer(self.popen.stdin)

        self._output_task = asyncio.create_task(self._run_output(), name=f'remote-output-{self.id}')
        self._wait_task = asyncio.create_task(self._run_wait(), name=f'remote-wait-{self.id}')

    async def _drain_pty_output(self, fd: int, output_fd: int) -> bool:
        while True:
            try:
                data = os.read(fd, _REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except (BlockingIOError, InterruptedError):
                return True
            except OSError:
                # Linux pty masters report EIO when the slave closes; BSDs return EOF.
                return False
            if not data:
                return False
            await self._service.notify(PROCESS_OUTPUT_METHOD, {
                'id': self.id,
                'fd': output_fd,
                'data': encode_remote_bytes(data),
            })

    def _close_pty_slave(self) -> None:
        if self._pty_slave_fd is not None:
            os.close(self._pty_slave_fd)
            self._pty_slave_fd = None

    async def _read_pty_output(self, fd: int, output_fd: int) -> None:
        loop = asyncio.get_running_loop()
        exited_task = asyncio.create_task(self._exited.wait())
        readable = None  # type: ta.Optional[asyncio.Future]
        try:
            while True:
                readable = loop.create_future()

                def on_readable() -> None:
                    if not readable.done():
                        readable.set_result(None)

                loop.add_reader(fd, on_readable)
                try:
                    waiters = [readable]  # type: ta.List[asyncio.Future]
                    if self._pty_slave_fd is not None:
                        waiters.append(exited_task)
                    await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
                finally:
                    loop.remove_reader(fd)
                    if not readable.done():
                        readable.cancel()

                if not await self._drain_pty_output(fd, output_fd):
                    return

                if exited_task.done():
                    # Keep one slave descriptor open until the leader has exited and every byte already queued on the
                    # master has been consumed. Closing the final slave first can discard trailing pty output.
                    self._close_pty_slave()
                    if not await self._drain_pty_output(fd, output_fd):
                        return

        finally:
            if readable is not None:
                loop.remove_reader(fd)
            if not exited_task.done():
                exited_task.cancel()
            if self._pty_read_fd == fd:
                self._pty_read_fd = None
                os.close(fd)

    async def _read_output(self, reader: asyncio.StreamReader, fd: int) -> None:
        while True:
            try:
                data = await reader.read(_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except OSError:
                # Linux pty masters report EIO when the slave closes; BSDs return EOF.
                return
            if not data:
                return
            await self._service.notify(PROCESS_OUTPUT_METHOD, {
                'id': self.id,
                'fd': fd,
                'data': encode_remote_bytes(data),
            })

    async def _run_output(self) -> None:
        try:
            if self._reader_tasks:
                await asyncio.gather(*self._reader_tasks)
        finally:
            self._output_ended.set()
            await self._service.notify(PROCESS_OUTPUT_END_METHOD, {'id': self.id})

    async def _run_wait(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            self._returncode = await loop.run_in_executor(None, _remote_process_wait, self.popen.pid)
        except BaseException:
            if self._reaped:
                return
            raise
        finally:
            if self._returncode is not None:
                self._exited.set()

        await self._service.notify(PROCESS_EXITED_METHOD, {
            'id': self.id,
            'returncode': self._returncode,
        })

    def _signal(self, sig: int, process_group: bool) -> None:
        if self._reaped:
            raise ProcessLookupError(self.popen.pid)
        if self.exited:
            # The unreaped leader keeps its pid, and therefore its process-group id, from being reused.
            if process_group:
                try:
                    os.killpg(self.popen.pid, sig)
                except (PermissionError, ProcessLookupError):
                    pass
            return

        if process_group:
            # The pty bootstrap creates its session immediately after exec, but a signal can race that setup. Hitting
            # the owned pid as well ensures it cannot escape before its pgid exists.
            try:
                os.kill(self.popen.pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError:
                if not self._is_exited_nowait():
                    raise
            try:
                os.killpg(self.popen.pid, sig)
            except ProcessLookupError:
                pass
            except PermissionError:
                if not self._is_exited_nowait():
                    raise
        else:
            try:
                os.kill(self.popen.pid, sig)
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

    async def _wait_exited(self, timeout: ta.Optional[float]) -> bool:
        if self.exited:
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(asyncio.shield(self._exited.wait()), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self.exited
        return True

    async def _wait_output_ended(self, timeout: ta.Optional[float]) -> bool:
        if self._output_ended.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(asyncio.shield(self._output_ended.wait()), timeout)
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
        if self._pty_reader_task is not None and not self._pty_reader_task.done():
            self._pty_reader_task.cancel()
        if self._pty_read_fd is not None:
            try:
                os.close(self._pty_read_fd)
            except OSError:
                pass
            self._pty_read_fd = None
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
            self._returncode = os.waitstatus_to_exitcode(status)
            self._exited.set()
        self.popen.returncode = self._returncode

    async def _run_close(self, policy: ta.Mapping[str, ta.Any]) -> ta.Dict[str, ta.Any]:
        close_stdin = check_remote_bool(policy['close_stdin'])
        first_signal = check_remote_int(policy['signal'], minimum=1)
        grace_s = check_remote_float(policy['grace_s'], minimum=0.)
        kill_s = check_remote_float(policy['kill_s'], minimum=0.)
        process_group = check_remote_bool(policy['process_group'])
        drain_s = check_remote_float(policy['drain_s'], minimum=0.)

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
        if self._output_task is not None:
            await asyncio.gather(self._output_task, return_exceptions=True)
        self._reap()
        self._service.finished(self)
        return {'returncode': self._returncode, 'state': 'reaped'}

    async def close(self, policy: ta.Mapping[str, ta.Any]) -> ta.Dict[str, ta.Any]:
        if self._reaped:
            return {'returncode': self._returncode, 'state': 'reaped'}
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._run_close(policy), name=f'remote-close-{self.id}')
        return await asyncio.shield(self._close_task)


class _RemoteProcessService:
    _DEFAULT_CLOSE_POLICY: ta.ClassVar[ta.Mapping[str, ta.Any]] = {
        'signal': int(signal.SIGTERM),
        'grace_s': 5.,
        'kill_s': 5.,
        'close_stdin': True,
        'process_group': True,
        'drain_s': 1.,
    }

    def __init__(self) -> None:
        super().__init__()

        self._peer = None  # type: ta.Optional[RpcPeer]
        self._processes = {}  # type: ta.Dict[str, _RemoteServerProcess]
        self._next_id = 1
        self._closed = False

    def set_peer(self, peer: RpcPeer) -> None:
        if self._peer is not None:
            raise RuntimeError('peer already set')
        self._peer = peer

    async def notify(self, method: str, params: ta.Any) -> None:
        if self._peer is None or self._peer.closed:
            return
        try:
            # Events are calls rather than fire-and-forget notifications. The acknowledgement makes process.close's
            # response an ordering barrier: by the time the host sees it, every preceding output chunk is in its spool.
            await self._peer.call(method, params)
        except Exception:  # noqa
            # The peer owns the connection failure. Keep draining child pipes until server teardown reaches us.
            pass

    def _lookup(self, process_id: ta.Any) -> _RemoteServerProcess:
        process_id = check_remote_str(process_id, non_empty=True)
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

    async def spawn(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        if self._closed:
            raise RuntimeError('remote process service is closed')
        obj = check_remote_dict(params, {'argv', 'cwd', 'env', 'stdio', 'name'})
        argv = check_remote_str_list(obj['argv'], non_empty=True)
        cwd = check_remote_optional_str(obj['cwd'])
        env = check_remote_optional_str_dict(obj['env'])
        name = check_remote_optional_str(obj['name'])
        stdio = check_remote_dict(obj['stdio'], {'kind'}, {'stdin', 'stdout', 'stderr', 'rows', 'cols', 'term'})
        kind = check_remote_str(stdio['kind'])

        process_id = f'p{self._next_id}'
        self._next_id += 1

        master = None  # type: ta.Optional[int]
        slave = None  # type: ta.Optional[int]
        pty_slave_fd = None  # type: ta.Optional[int]
        pty_winsize = None  # type: ta.Optional[ta.Tuple[int, int]]
        try:
            try:
                if kind == 'pipes':
                    stdin = self._stdio_value(check_remote_str(stdio['stdin']))
                    stdout = self._stdio_value(check_remote_str(stdio['stdout']))
                    stderr = self._stdio_value(check_remote_str(stdio['stderr']), stderr=True)
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
                    rows = check_remote_int(stdio['rows'], minimum=1)
                    cols = check_remote_int(stdio['cols'], minimum=1)
                    term = check_remote_optional_str(stdio['term'])
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
        try:
            await process.start()
            self._processes[process_id] = process
        except BaseException:
            try:
                os.kill(popen.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(popen.pid, 0)  # noqa: ASYNC222
            popen.returncode = -signal.SIGKILL
            process._close_streams()  # noqa: SLF001
            raise

        return {
            'id': process.id,
            'pid': process.popen.pid,
            'created_at': process.created_at,
            'name': name,
        }

    async def signal(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'signal', 'process_group'})
        await self._lookup(obj['id']).signal(
            check_remote_int(obj['signal'], minimum=1),
            check_remote_bool(obj['process_group']),
        )

    async def close(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'id', 'policy'})
        policy = check_remote_dict(
            obj['policy'],
            {'signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s'},
        )
        return await self._lookup(obj['id']).close(policy)

    async def write(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'data'})
        await self._lookup(obj['id']).write(decode_remote_bytes(obj['data']))

    async def write_eof(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id'})
        await self._lookup(obj['id']).write_eof()

    async def resize(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'rows', 'cols'})
        await self._lookup(obj['id']).resize(
            check_remote_int(obj['rows'], minimum=1),
            check_remote_int(obj['cols'], minimum=1),
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._processes:
            await asyncio.gather(*[
                process.close(self._DEFAULT_CLOSE_POLICY)
                for process in list(self._processes.values())
            ], return_exceptions=True)


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
