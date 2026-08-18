"""A small, dependency-free ctypes wrapper around macOS's public C XPC API.

The module intentionally wraps the classic ``<xpc/xpc.h>`` interface rather
than Foundation's NSXPCConnection.  It is lazy: importing it on a non-macOS
host is allowed, but using an XPC operation raises :class:`XPCUnavailableError`.

The interesting part is callback support.  libxpc accepts Objective-C Blocks,
not ordinary C function pointers.  ``_Block`` below constructs a no-capture,
global Block literal using the public Apple/Clang Blocks ABI and points its
invoke slot at a ``ctypes.CFUNCTYPE`` trampoline.
"""

from __future__ import annotations

import concurrent.futures
import ctypes
import ctypes.util
import dataclasses
import datetime as dt
import os
import sys
import threading
import traceback
import uuid as uuid_mod
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import Final
from typing import cast


__all__ = [
    'NO_REPLY',
    'PeerCredentials',
    'UInt64',
    'XPCConnection',
    'XPCConnectionError',
    'XPCDate',
    'XPCDecodeError',
    'XPCEncodeError',
    'XPCEndpoint',
    'XPCError',
    'XPCErrorEvent',
    'XPCFileDescriptor',
    'XPCMessage',
    'XPCNoReplyExpected',
    'XPCObject',
    'XPCReentrancyError',
    'XPCUnavailableError',
    'decode_xpc',
    'encode_xpc',
    'in_xpc_callback',
    'run_bundled_service',
    'wait_forever',
]


# ---------------------------------------------------------------------------
# Exceptions and small value types


class XPCError(RuntimeError):
    """Base class for wrapper-level XPC failures."""


class XPCUnavailableError(XPCError):
    """The XPC runtime is unavailable (normally because this is not macOS)."""


class XPCEncodeError(XPCError, TypeError):
    """A Python value cannot be represented by this wrapper's XPC codec."""


class XPCDecodeError(XPCError, ValueError):
    """An XPC value could not be decoded."""


class XPCNoReplyExpected(XPCError):
    """The incoming dictionary was not sent with a native XPC reply context."""


class XPCReentrancyError(XPCError):
    """A blocking request was attempted from an XPC callback."""


@dataclasses.dataclass(frozen=True, slots=True)
class XPCErrorEvent:
    """A transport/runtime event delivered by libxpc."""

    kind: str
    description: str


class XPCConnectionError(XPCError):
    """An asynchronous or synchronous XPC operation failed."""

    def __init__(self, event: XPCErrorEvent) -> None:
        self.event = event
        super().__init__(f'{event.kind}: {event.description}')


class UInt64(int):
    """An ``int`` subclass that forces XPC's unsigned 64-bit representation."""

    def __new__(cls, value: int) -> "UInt64":
        value = int(value)
        if not 0 <= value <= 0xFFFF_FFFF_FFFF_FFFF:
            raise OverflowError('UInt64 value must be in [0, 2**64 - 1]')
        return cast('UInt64', int.__new__(cls, value))


@dataclasses.dataclass(frozen=True, slots=True)
class XPCDate:
    """An exact XPC date: signed nanoseconds relative to the Unix epoch."""

    nanoseconds_since_epoch: int

    def __post_init__(self) -> None:
        if not -(1 << 63) <= self.nanoseconds_since_epoch < (1 << 63):
            raise OverflowError('XPCDate must fit in a signed 64-bit integer')

    @classmethod
    def from_datetime(cls, value: dt.datetime) -> "XPCDate":
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('XPC datetime values must be timezone-aware')
        value = value.astimezone(dt.timezone.utc)
        epoch = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
        delta = value - epoch
        seconds = delta.days * 86_400 + delta.seconds
        return cls(seconds * 1_000_000_000 + delta.microseconds * 1_000)

    def to_datetime(self) -> dt.datetime:
        seconds, nanoseconds = divmod(self.nanoseconds_since_epoch, 1_000_000_000)
        return (
            dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
            + dt.timedelta(seconds=seconds, microseconds=nanoseconds // 1_000)
        )


class XPCFileDescriptor:
    """A POSIX file descriptor value suitable for transfer through XPC.

    Decoded descriptors are duplicates owned by this object.  For an outgoing
    descriptor, pass ``owns=False`` (the default) if the caller retains normal
    ownership of the original descriptor.
    """

    __slots__ = ('_fd', '_owns')

    def __init__(self, fd: int, *, owns: bool = False) -> None:
        fd = int(fd)
        if fd < 0:
            raise ValueError('file descriptor must be nonnegative')
        self._fd = fd
        self._owns = bool(owns)

    @property
    def closed(self) -> bool:
        return self._fd < 0

    def fileno(self) -> int:
        if self.closed:
            raise ValueError('I/O operation on closed XPCFileDescriptor')
        return self._fd

    def detach(self) -> int:
        fd = self.fileno()
        self._fd = -1
        self._owns = False
        return fd

    def close(self) -> None:
        if self._fd >= 0 and self._owns:
            fd = self._fd
            self._fd = -1
            self._owns = False
            os.close(fd)
        elif self._fd >= 0:
            self._fd = -1

    def __enter__(self) -> "XPCFileDescriptor":
        self.fileno()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except BaseException:
            pass

    def __repr__(self) -> str:
        state = 'closed' if self.closed else f'fd={self._fd}, owns={self._owns}'
        return f'{type(self).__name__}({state})'


@dataclasses.dataclass(frozen=True, slots=True)
class PeerCredentials:
    pid: int
    euid: int
    egid: int
    service_name: str | None
    audit_session_id: int | None = None


class _NoReply:
    __slots__ = ()

    def __repr__(self) -> str:
        return 'NO_REPLY'


NO_REPLY: Final = _NoReply()


# ---------------------------------------------------------------------------
# Lazy native bindings


_XPC = ctypes.c_void_p
_DISPATCH_QUEUE = ctypes.c_void_p


class _LibXPC:
    def __init__(self) -> None:
        if sys.platform != 'darwin':
            raise XPCUnavailableError('libxpc is available only on Apple platforms')
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            raise XPCUnavailableError('this wrapper supports 64-bit macOS only')

        self.xpc = self._load_library(
            ctypes.util.find_library('xpc'),
            '/usr/lib/system/libxpc.dylib',
            'libxpc.dylib',
        )
        self.system = self._load_library(
            ctypes.util.find_library('System'),
            '/usr/lib/libSystem.B.dylib',
            'libSystem.B.dylib',
        )

        self._bind_objects()
        self._bind_connections()
        self._bind_dispatch_and_blocks()
        self._load_error_globals()

    @staticmethod
    def _load_library(*names: str | None) -> ctypes.CDLL:
        errors: list[str] = []
        for name in names:
            if not name:
                continue
            try:
                return ctypes.CDLL(name, mode=ctypes.RTLD_GLOBAL, use_errno=True)
            except OSError as exc:
                errors.append(f'{name!r}: {exc}')
        raise XPCUnavailableError('could not load a required macOS library: ' + '; '.join(errors))

    @staticmethod
    def _bind(
        library: ctypes.CDLL,
        name: str,
        restype: Any,
        argtypes: list[Any],
        *,
        required: bool = True,
    ) -> Any:
        try:
            fn = getattr(library, name)
        except AttributeError:
            if required:
                raise XPCUnavailableError(
                    f'required native symbol {name!r} is unavailable',
                ) from None
            return None
        fn.restype = restype
        fn.argtypes = argtypes
        return fn

    def _bind_objects(self) -> None:
        b = self._bind
        x = self.xpc

        self.xpc_retain = b(x, 'xpc_retain', _XPC, [_XPC])
        self.xpc_release = b(x, 'xpc_release', None, [_XPC])
        self.xpc_get_type = b(x, 'xpc_get_type', ctypes.c_void_p, [_XPC])
        self.xpc_type_get_name = b(
            x, 'xpc_type_get_name', ctypes.c_char_p, [ctypes.c_void_p],
        )
        self.xpc_copy_description = b(x, 'xpc_copy_description', ctypes.c_void_p, [_XPC])
        self.xpc_equal = b(x, 'xpc_equal', ctypes.c_bool, [_XPC, _XPC])

        self.xpc_null_create = b(x, 'xpc_null_create', _XPC, [])
        self.xpc_bool_create = b(x, 'xpc_bool_create', _XPC, [ctypes.c_bool])
        self.xpc_bool_get_value = b(x, 'xpc_bool_get_value', ctypes.c_bool, [_XPC])
        self.xpc_int64_create = b(x, 'xpc_int64_create', _XPC, [ctypes.c_int64])
        self.xpc_int64_get_value = b(x, 'xpc_int64_get_value', ctypes.c_int64, [_XPC])
        self.xpc_uint64_create = b(x, 'xpc_uint64_create', _XPC, [ctypes.c_uint64])
        self.xpc_uint64_get_value = b(x, 'xpc_uint64_get_value', ctypes.c_uint64, [_XPC])
        self.xpc_double_create = b(x, 'xpc_double_create', _XPC, [ctypes.c_double])
        self.xpc_double_get_value = b(x, 'xpc_double_get_value', ctypes.c_double, [_XPC])
        self.xpc_string_create = b(x, 'xpc_string_create', _XPC, [ctypes.c_char_p])
        self.xpc_string_get_string_ptr = b(
            x, 'xpc_string_get_string_ptr', ctypes.c_char_p, [_XPC],
        )
        self.xpc_data_create = b(
            x, 'xpc_data_create', _XPC, [ctypes.c_void_p, ctypes.c_size_t],
        )
        self.xpc_data_get_bytes_ptr = b(
            x, 'xpc_data_get_bytes_ptr', ctypes.c_void_p, [_XPC],
        )
        self.xpc_data_get_length = b(x, 'xpc_data_get_length', ctypes.c_size_t, [_XPC])
        self.xpc_date_create = b(x, 'xpc_date_create', _XPC, [ctypes.c_int64])
        self.xpc_date_get_value = b(x, 'xpc_date_get_value', ctypes.c_int64, [_XPC])
        self.xpc_uuid_create = b(
            x, 'xpc_uuid_create', _XPC, [ctypes.POINTER(ctypes.c_uint8)],
        )
        self.xpc_uuid_get_bytes = b(
            x, 'xpc_uuid_get_bytes', ctypes.POINTER(ctypes.c_uint8), [_XPC],
        )
        self.xpc_fd_create = b(x, 'xpc_fd_create', _XPC, [ctypes.c_int])
        self.xpc_fd_dup = b(x, 'xpc_fd_dup', ctypes.c_int, [_XPC])

        self.xpc_array_create = b(
            x,
            'xpc_array_create',
            _XPC,
            [ctypes.POINTER(_XPC), ctypes.c_size_t],
        )
        self.xpc_array_get_count = b(x, 'xpc_array_get_count', ctypes.c_size_t, [_XPC])
        self.xpc_array_get_value = b(
            x, 'xpc_array_get_value', _XPC, [_XPC, ctypes.c_size_t],
        )

        self.xpc_dictionary_create = b(
            x,
            'xpc_dictionary_create',
            _XPC,
            [ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(_XPC), ctypes.c_size_t],
        )
        self.xpc_dictionary_set_value = b(
            x, 'xpc_dictionary_set_value', None, [_XPC, ctypes.c_char_p, _XPC],
        )
        self.xpc_dictionary_get_count = b(
            x, 'xpc_dictionary_get_count', ctypes.c_size_t, [_XPC],
        )
        self.xpc_dictionary_get_value = b(
            x, 'xpc_dictionary_get_value', _XPC, [_XPC, ctypes.c_char_p],
        )
        self.xpc_dictionary_apply = b(
            x, 'xpc_dictionary_apply', ctypes.c_bool, [_XPC, ctypes.c_void_p],
        )
        self.xpc_dictionary_create_reply = b(
            x, 'xpc_dictionary_create_reply', _XPC, [_XPC],
        )

        self.xpc_endpoint_create = b(x, 'xpc_endpoint_create', _XPC, [_XPC])

    def _bind_connections(self) -> None:
        b = self._bind
        x = self.xpc

        self.xpc_connection_create = b(
            x,
            'xpc_connection_create',
            _XPC,
            [ctypes.c_char_p, _DISPATCH_QUEUE],
        )
        self.xpc_connection_create_mach_service = b(
            x,
            'xpc_connection_create_mach_service',
            _XPC,
            [ctypes.c_char_p, _DISPATCH_QUEUE, ctypes.c_uint64],
        )
        self.xpc_connection_create_from_endpoint = b(
            x, 'xpc_connection_create_from_endpoint', _XPC, [_XPC],
        )
        self.xpc_connection_set_event_handler = b(
            x, 'xpc_connection_set_event_handler', None, [_XPC, ctypes.c_void_p],
        )
        self.xpc_connection_resume = b(x, 'xpc_connection_resume', None, [_XPC])
        self.xpc_connection_suspend = b(x, 'xpc_connection_suspend', None, [_XPC])
        self.xpc_connection_cancel = b(x, 'xpc_connection_cancel', None, [_XPC])
        self.xpc_connection_send_message = b(
            x, 'xpc_connection_send_message', None, [_XPC, _XPC],
        )
        self.xpc_connection_send_message_with_reply = b(
            x,
            'xpc_connection_send_message_with_reply',
            None,
            [_XPC, _XPC, _DISPATCH_QUEUE, ctypes.c_void_p],
        )
        self.xpc_connection_send_message_with_reply_sync = b(
            x, 'xpc_connection_send_message_with_reply_sync', _XPC, [_XPC, _XPC],
        )
        self.xpc_connection_get_pid = b(
            x, 'xpc_connection_get_pid', ctypes.c_int, [_XPC],
        )
        self.xpc_connection_get_euid = b(
            x, 'xpc_connection_get_euid', ctypes.c_uint32, [_XPC],
        )
        self.xpc_connection_get_egid = b(
            x, 'xpc_connection_get_egid', ctypes.c_uint32, [_XPC],
        )
        self.xpc_connection_get_name = b(
            x, 'xpc_connection_get_name', ctypes.c_char_p, [_XPC],
        )
        self.xpc_connection_get_asid = b(
            x,
            'xpc_connection_get_asid',
            ctypes.c_int32,
            [_XPC],
            required=False,
        )
        self.xpc_connection_set_peer_code_signing_requirement = b(
            x,
            'xpc_connection_set_peer_code_signing_requirement',
            ctypes.c_int,
            [_XPC, ctypes.c_char_p],
            required=False,
        )
        self.xpc_main = b(x, 'xpc_main', None, [ctypes.c_void_p], required=False)

    def _bind_dispatch_and_blocks(self) -> None:
        self.free = self._bind(self.system, 'free', None, [ctypes.c_void_p])
        self.dispatch_get_global_queue = self._bind(
            self.system,
            'dispatch_get_global_queue',
            _DISPATCH_QUEUE,
            [ctypes.c_long, ctypes.c_ulong],
        )
        self.reply_queue = self.dispatch_get_global_queue(0, 0)
        if not self.reply_queue:
            raise XPCUnavailableError('dispatch_get_global_queue returned NULL')

        libraries: list[ctypes.CDLL] = [ctypes.CDLL(None), self.system]
        try:
            libraries.append(
                self._load_library(
                    '/usr/lib/system/libsystem_blocks.dylib',
                    'libsystem_blocks.dylib',
                ),
            )
        except XPCUnavailableError:
            pass

        self.global_block_isa = 0
        for library in libraries:
            try:
                symbol = ctypes.c_char.in_dll(library, '_NSConcreteGlobalBlock')
            except ValueError:
                continue
            self.global_block_isa = ctypes.addressof(symbol)
            break
        if not self.global_block_isa:
            raise XPCUnavailableError('could not resolve _NSConcreteGlobalBlock')

    def _load_error_globals(self) -> None:
        self.error_globals: dict[str, int] = {}
        for kind, symbol_name in (
            ('connection_interrupted', '_xpc_error_connection_interrupted'),
            ('connection_invalid', '_xpc_error_connection_invalid'),
            ('termination_imminent', '_xpc_error_termination_imminent'),
            ('peer_code_signing_requirement', '_xpc_error_peer_code_signing_requirement'),
        ):
            try:
                symbol = ctypes.c_char.in_dll(self.xpc, symbol_name)
            except ValueError:
                continue
            self.error_globals[kind] = ctypes.addressof(symbol)


_LIB_LOCK = threading.Lock()
_LIB: _LibXPC | None = None


def _lib() -> _LibXPC:
    global _LIB
    if _LIB is None:
        with _LIB_LOCK:
            if _LIB is None:
                _LIB = _LibXPC()
    return _LIB


def _pointer_value(value: int | ctypes.c_void_p | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    return int(value.value or 0)


def _require_pointer(value: int | ctypes.c_void_p | None, what: str) -> int:
    ptr = _pointer_value(value)
    if not ptr:
        # Most XPC create/copy APIs do not promise errno, and consulting the
        # thread's previous errno here can produce a confidently wrong error.
        raise XPCError(f'{what} returned NULL')
    return ptr


# ---------------------------------------------------------------------------
# Objective-C Block ABI bridge


class _BlockDescriptor(ctypes.Structure):
    _fields_ = [
        ('reserved', ctypes.c_ulong),
        ('size', ctypes.c_ulong),
    ]


class _BlockLiteral(ctypes.Structure):
    _fields_ = [
        ('isa', ctypes.c_void_p),
        ('flags', ctypes.c_int),
        ('reserved', ctypes.c_int),
        ('invoke', ctypes.c_void_p),
        ('descriptor', ctypes.c_void_p),
    ]


_BLOCK_IS_GLOBAL: Final = 1 << 28
_BLOCK_10_6_TRANSITIONAL: Final = 1 << 29


class _Block:
    """A no-capture global Objective-C Block backed by a ctypes callback."""

    __slots__ = ('_callback', '_descriptor', '_literal', '_python_callback')

    def __init__(
        self,
        restype: Any,
        argtypes: Sequence[Any],
        callback: Callable[..., Any],
        *,
        error_result: Any = None,
    ) -> None:
        lib = _lib()
        self._python_callback = callback

        callback_type = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)

        def invoke(_block_pointer: int, *args: Any) -> Any:
            try:
                return callback(*args)
            except BaseException:
                traceback.print_exc()
                return error_result

        self._callback = callback_type(invoke)
        self._descriptor = _BlockDescriptor(0, ctypes.sizeof(_BlockLiteral))
        self._literal = _BlockLiteral(
            lib.global_block_isa,
            _BLOCK_IS_GLOBAL | _BLOCK_10_6_TRANSITIONAL,
            0,
            ctypes.cast(self._callback, ctypes.c_void_p).value,
            ctypes.addressof(self._descriptor),
        )

    @property
    def pointer(self) -> int:
        return ctypes.addressof(self._literal)


# ---------------------------------------------------------------------------
# Raw object ownership and codec


class XPCObject:
    """An owned reference to an otherwise unsupported/raw XPC object."""

    __slots__ = ('_ptr', '_type_name', '_description', '_lock')

    def __init__(
        self,
        pointer: int | ctypes.c_void_p,
        *,
        retain: bool = True,
        expected_type: str | None = None,
    ) -> None:
        ptr = _require_pointer(pointer, 'XPC object')
        lib = _lib()
        if retain:
            _require_pointer(lib.xpc_retain(ptr), 'xpc_retain')

        # From this point on, this wrapper owns exactly one reference whether
        # that reference was supplied by a create/copy API (retain=False) or
        # acquired above (retain=True).  Release it on every constructor error.
        try:
            type_name = _type_name(ptr)
            if expected_type is not None and type_name != expected_type:
                raise TypeError(
                    f'expected XPC type {expected_type!r}, got {type_name!r}',
                )
        except BaseException:
            lib.xpc_release(ptr)
            raise

        self._ptr = ptr
        self._type_name = type_name
        self._description: str | None = None
        self._lock = threading.RLock()

    @property
    def closed(self) -> bool:
        with self._lock:
            return not self._ptr

    @property
    def pointer(self) -> int:
        with self._lock:
            if not self._ptr:
                raise XPCError('XPC object is closed')
            return self._ptr

    @property
    def type_name(self) -> str:
        return self._type_name

    @property
    def description(self) -> str:
        with self._lock:
            if self._description is None:
                if not self._ptr:
                    raise XPCError('XPC object is closed')
                self._description = _copy_description(self._ptr)
            return self._description

    def retain_pointer(self) -> int:
        with self._lock:
            if not self._ptr:
                raise XPCError('XPC object is closed')
            return _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')

    def close(self) -> None:
        with self._lock:
            ptr, self._ptr = self._ptr, 0
        if ptr:
            _lib().xpc_release(ptr)

    def __enter__(self) -> "XPCObject":
        self.pointer
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except BaseException:
            pass

    def __repr__(self) -> str:
        with self._lock:
            if not self._ptr:
                return f'{type(self).__name__}(closed, type={self._type_name!r})'
            return (
                f'{type(self).__name__}(type={self._type_name!r}, '
                f'{self.description})'
            )


class XPCEndpoint(XPCObject):
    """An owned XPC endpoint that can be embedded in another XPC message."""

    def __init__(self, pointer: int | ctypes.c_void_p, *, retain: bool = True) -> None:
        super().__init__(pointer, retain=retain, expected_type='endpoint')


class _OwnedPointer:
    __slots__ = ('pointer',)

    def __init__(self, pointer: int | ctypes.c_void_p) -> None:
        self.pointer = _require_pointer(pointer, 'XPC object creation')

    def close(self) -> None:
        ptr, self.pointer = self.pointer, 0
        if ptr:
            _lib().xpc_release(ptr)

    def __enter__(self) -> int:
        return self.pointer

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


def _type_name(pointer: int | ctypes.c_void_p) -> str:
    lib = _lib()
    type_pointer = lib.xpc_get_type(pointer)
    if not type_pointer:
        raise XPCDecodeError('xpc_get_type returned NULL')
    name = lib.xpc_type_get_name(type_pointer)
    if not name:
        raise XPCDecodeError('xpc_type_get_name returned NULL')
    return name.decode('ascii', 'replace')


def _copy_description(pointer: int | ctypes.c_void_p) -> str:
    lib = _lib()
    description_pointer = _pointer_value(lib.xpc_copy_description(pointer))
    if not description_pointer:
        return '<no XPC description>'
    try:
        return ctypes.string_at(description_pointer).decode('utf-8', 'replace')
    finally:
        lib.free(description_pointer)


def _decode_error(pointer: int | ctypes.c_void_p) -> XPCErrorEvent:
    ptr = _pointer_value(pointer)
    lib = _lib()
    kind = 'unknown_error'
    for candidate, global_pointer in lib.error_globals.items():
        if ptr == global_pointer or lib.xpc_equal(ptr, global_pointer):
            kind = candidate
            break
    return XPCErrorEvent(kind=kind, description=_copy_description(ptr))


def _encode_text(value: str, *, what: str) -> bytes:
    if '\x00' in value:
        raise XPCEncodeError(f'{what} cannot contain NUL')
    try:
        return value.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise XPCEncodeError(f'{what} is not UTF-8 encodable: {value!r}') from exc


def _encode_key(key: object) -> bytes:
    if not isinstance(key, str):
        raise XPCEncodeError(
            f'XPC dictionary keys must be str, got {type(key).__name__}',
        )
    return _encode_text(key, what='XPC dictionary key')


def _encode_mapping(value: Mapping[str, Any]) -> int:
    lib = _lib()
    items = list(value.items())
    if not items:
        return _require_pointer(lib.xpc_dictionary_create(None, None, 0), 'xpc_dictionary_create')

    keys: list[bytes] = []
    pointers: list[int] = []
    try:
        for key, item in items:
            keys.append(_encode_key(key))
            pointers.append(_encode(item))

        key_array = (ctypes.c_char_p * len(keys))(*keys)
        value_array = (_XPC * len(pointers))(*pointers)
        return _require_pointer(
            lib.xpc_dictionary_create(key_array, value_array, len(items)),
            'xpc_dictionary_create',
        )
    finally:
        for pointer in pointers:
            lib.xpc_release(pointer)


def _encode_array(value: Sequence[Any]) -> int:
    lib = _lib()
    if not value:
        return _require_pointer(lib.xpc_array_create(None, 0), 'xpc_array_create')

    pointers: list[int] = []
    try:
        pointers.extend(_encode(item) for item in value)
        value_array = (_XPC * len(pointers))(*pointers)
        return _require_pointer(
            lib.xpc_array_create(value_array, len(pointers)),
            'xpc_array_create',
        )
    finally:
        for pointer in pointers:
            lib.xpc_release(pointer)


def _encode(value: Any) -> int:
    lib = _lib()

    if value is None:
        return _require_pointer(lib.xpc_null_create(), 'xpc_null_create')
    if isinstance(value, bool):
        return _require_pointer(lib.xpc_bool_create(value), 'xpc_bool_create')
    if isinstance(value, UInt64):
        return _require_pointer(lib.xpc_uint64_create(int(value)), 'xpc_uint64_create')
    if isinstance(value, int):
        if -(1 << 63) <= value < (1 << 63):
            return _require_pointer(lib.xpc_int64_create(value), 'xpc_int64_create')
        if 0 <= value <= 0xFFFF_FFFF_FFFF_FFFF:
            return _require_pointer(lib.xpc_uint64_create(value), 'xpc_uint64_create')
        raise XPCEncodeError(f"integer is outside XPC's 64-bit range: {value}")
    if isinstance(value, float):
        return _require_pointer(lib.xpc_double_create(value), 'xpc_double_create')
    if isinstance(value, str):
        return _require_pointer(
            lib.xpc_string_create(_encode_text(value, what='XPC string')),
            'xpc_string_create',
        )
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if raw:
            buffer = ctypes.create_string_buffer(raw, len(raw))
            return _require_pointer(
                lib.xpc_data_create(ctypes.addressof(buffer), len(raw)),
                'xpc_data_create',
            )
        return _require_pointer(lib.xpc_data_create(None, 0), 'xpc_data_create')
    if isinstance(value, XPCDate):
        return _require_pointer(
            lib.xpc_date_create(value.nanoseconds_since_epoch),
            'xpc_date_create',
        )
    if isinstance(value, dt.datetime):
        return _encode(XPCDate.from_datetime(value))
    if isinstance(value, uuid_mod.UUID):
        uuid_array = (ctypes.c_uint8 * 16).from_buffer_copy(value.bytes)
        return _require_pointer(lib.xpc_uuid_create(uuid_array), 'xpc_uuid_create')
    if isinstance(value, XPCFileDescriptor):
        pointer = lib.xpc_fd_create(value.fileno())
        return _require_pointer(pointer, 'xpc_fd_create')
    if isinstance(value, XPCObject):
        return value.retain_pointer()
    if isinstance(value, Mapping):
        return _encode_mapping(cast(Mapping[str, Any], value))
    if isinstance(value, (list, tuple)):
        return _encode_array(value)

    raise XPCEncodeError(
        'unsupported XPC value type '
        f'{type(value).__module__}.{type(value).__qualname__}',
    )


def encode_xpc(value: Any) -> XPCObject:
    """Encode a Python value and return an owned raw XPC object."""

    return XPCObject(_encode(value), retain=False)


def _decode(pointer: int | ctypes.c_void_p) -> Any:
    ptr = _require_pointer(pointer, 'XPC value')
    lib = _lib()
    type_name = _type_name(ptr)

    if type_name == 'null':
        return None
    if type_name == 'bool':
        return bool(lib.xpc_bool_get_value(ptr))
    if type_name == 'int64':
        return int(lib.xpc_int64_get_value(ptr))
    if type_name == 'uint64':
        return UInt64(lib.xpc_uint64_get_value(ptr))
    if type_name == 'double':
        return float(lib.xpc_double_get_value(ptr))
    if type_name == 'string':
        raw = lib.xpc_string_get_string_ptr(ptr)
        if raw is None:
            raise XPCDecodeError('xpc_string_get_string_ptr returned NULL')
        try:
            return raw.decode('utf-8', 'strict')
        except UnicodeDecodeError as exc:
            raise XPCDecodeError('XPC string is not valid UTF-8') from exc
    if type_name == 'data':
        length = int(lib.xpc_data_get_length(ptr))
        if not length:
            return b''
        data_pointer = _pointer_value(lib.xpc_data_get_bytes_ptr(ptr))
        if not data_pointer:
            raise XPCDecodeError('nonempty XPC data object has a NULL byte pointer')
        return ctypes.string_at(data_pointer, length)
    if type_name == 'date':
        return XPCDate(int(lib.xpc_date_get_value(ptr)))
    if type_name == 'uuid':
        uuid_pointer = lib.xpc_uuid_get_bytes(ptr)
        if not uuid_pointer:
            raise XPCDecodeError('xpc_uuid_get_bytes returned NULL')
        return uuid_mod.UUID(bytes=ctypes.string_at(uuid_pointer, 16))
    if type_name == 'fd':
        ctypes.set_errno(0)
        fd = int(lib.xpc_fd_dup(ptr))
        if fd < 0:
            errno = ctypes.get_errno() or 5
            raise OSError(errno, os.strerror(errno), 'xpc_fd_dup')
        return XPCFileDescriptor(fd, owns=True)
    if type_name == 'array':
        count = int(lib.xpc_array_get_count(ptr))
        return [_decode(lib.xpc_array_get_value(ptr, index)) for index in range(count)]
    if type_name == 'dictionary':
        result: dict[str, Any] = {}
        caught: list[BaseException] = []

        def apply(key: bytes | None, item_pointer: int) -> bool:
            try:
                if key is None:
                    raise XPCDecodeError('XPC dictionary yielded a NULL key')
                try:
                    decoded_key = key.decode('utf-8', 'strict')
                except UnicodeDecodeError as exc:
                    raise XPCDecodeError(
                        'XPC dictionary key is not valid UTF-8',
                    ) from exc
                result[decoded_key] = _decode(item_pointer)
                return True
            except BaseException as exc:
                caught.append(exc)
                return False

        block = _Block(
            ctypes.c_bool,
            [ctypes.c_char_p, _XPC],
            apply,
            error_result=False,
        )
        complete = bool(lib.xpc_dictionary_apply(ptr, block.pointer))
        if caught:
            raise caught[0]
        if not complete:
            raise XPCDecodeError('xpc_dictionary_apply stopped before completing')
        return result
    if type_name == 'endpoint':
        return XPCEndpoint(ptr, retain=True)
    if type_name == 'error':
        return _decode_error(ptr)

    return XPCObject(ptr, retain=True)


def decode_xpc(value: XPCObject | int | ctypes.c_void_p) -> Any:
    """Decode a raw XPC object into Python values and ownership wrappers."""

    pointer = value.pointer if isinstance(value, XPCObject) else value
    return _decode(pointer)


def _set_dictionary_items(pointer: int, value: Mapping[str, Any]) -> None:
    lib = _lib()
    for key, item in value.items():
        encoded_key = _encode_key(key)
        item_pointer = _encode(item)
        try:
            lib.xpc_dictionary_set_value(pointer, encoded_key, item_pointer)
        finally:
            lib.xpc_release(item_pointer)


# ---------------------------------------------------------------------------
# Connections and messages


_CALLBACK_STATE = threading.local()


def in_xpc_callback() -> bool:
    return bool(getattr(_CALLBACK_STATE, 'depth', 0))


class _CallbackScope:
    def __enter__(self) -> None:
        _CALLBACK_STATE.depth = getattr(_CALLBACK_STATE, 'depth', 0) + 1

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        depth = getattr(_CALLBACK_STATE, 'depth', 1) - 1
        if depth:
            _CALLBACK_STATE.depth = depth
        else:
            try:
                del _CALLBACK_STATE.depth
            except AttributeError:
                pass


class XPCMessage:
    """An incoming XPC dictionary, retained so a reply may be sent later."""

    __slots__ = (
        '_connection',
        '_ptr',
        '_payload',
        '_replying',
        '_replied',
        '_lock',
    )

    def __init__(self, connection: "XPCConnection", pointer: int | ctypes.c_void_p) -> None:
        ptr = _require_pointer(pointer, 'incoming XPC message')
        _require_pointer(_lib().xpc_retain(ptr), 'xpc_retain')
        self._connection = connection
        self._ptr = ptr
        self._payload: dict[str, Any] | None = None
        self._replying = False
        self._replied = False
        self._lock = threading.Lock()

    @property
    def closed(self) -> bool:
        with self._lock:
            return not self._ptr

    @property
    def pointer(self) -> int:
        """Return the borrowed native message pointer while this object is open."""

        with self._lock:
            if not self._ptr:
                raise XPCError('XPC message is closed')
            return self._ptr

    def retain_pointer(self) -> int:
        """Return a native pointer carrying one new XPC reference.

        The caller owns that reference and must eventually pass it to
        ``xpc_release``.  This is useful when composing the wrapper with another
        public API that accepts the original incoming XPC message.
        """

        with self._lock:
            if not self._ptr:
                raise XPCError('XPC message is closed')
            return _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')

    @property
    def payload(self) -> dict[str, Any]:
        with self._lock:
            if self._payload is not None:
                return self._payload
            if not self._ptr:
                raise XPCError('XPC message is closed')
            decoded = _decode(self._ptr)
            if not isinstance(decoded, dict):
                raise XPCDecodeError('incoming XPC message is not a dictionary')
            self._payload = decoded
            return decoded

    def reply(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise TypeError('an XPC reply must be a mapping/dictionary')

        with self._lock:
            if self._replied:
                raise XPCError('this XPC message has already been replied to')
            if self._replying:
                raise XPCError('this XPC message is already being replied to')
            if not self._ptr:
                raise XPCError('XPC message is closed')
            reply_pointer = _pointer_value(_lib().xpc_dictionary_create_reply(self._ptr))
            if not reply_pointer:
                raise XPCNoReplyExpected('sender did not attach an XPC reply context')
            self._replying = True

        try:
            _set_dictionary_items(reply_pointer, cast(Mapping[str, Any], payload))
            self._connection._send_raw(reply_pointer)
        except BaseException:
            # In particular, permit a caller to replace an unencodable success
            # value with an error reply.  xpc_connection_send_message is void,
            # so a successful native send cannot subsequently report failure.
            with self._lock:
                self._replying = False
            raise
        else:
            with self._lock:
                self._replying = False
                self._replied = True
        finally:
            _lib().xpc_release(reply_pointer)

    def close(self) -> None:
        with self._lock:
            ptr, self._ptr = self._ptr, 0
        if ptr:
            _lib().xpc_release(ptr)

    def __enter__(self) -> "XPCMessage":
        if not self._ptr:
            raise XPCError('XPC message is closed')
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except BaseException:
            pass


MessageHandler = Callable[['XPCConnection', XPCMessage], Mapping[str, Any] | _NoReply | None]
ErrorHandler = Callable[['XPCConnection', XPCErrorEvent], None]
PeerHandler = Callable[['XPCConnection', 'XPCConnection'], None]
UnexpectedEventHandler = Callable[['XPCConnection', Any], None]


class XPCConnection:
    """A client, listener, or accepted peer connection."""

    MACH_SERVICE_LISTENER: Final = 1 << 0
    MACH_SERVICE_PRIVILEGED: Final = 1 << 1

    _active_lock = threading.Lock()
    _active: dict[int, 'XPCConnection'] = {}

    def __init__(
        self,
        pointer: int | ctypes.c_void_p,
        *,
        retain: bool = False,
        role: str = 'connection',
    ) -> None:
        ptr = _require_pointer(pointer, 'XPC connection')
        if retain:
            _require_pointer(_lib().xpc_retain(ptr), 'xpc_retain')

        self._ptr = ptr
        self._role = role
        self._lock = threading.RLock()
        self._event_block: _Block | None = None
        self._message_handler: MessageHandler | None = None
        self._auto_reply = False
        self._error_handlers: list[ErrorHandler] = []
        self._peer_handler: PeerHandler | None = None
        self._unexpected_event_handler: UnexpectedEventHandler | None = None
        self._pending_reply_blocks: dict[int, _Block] = {}
        self._activated = False
        self._suspend_count = 0
        self._cancel_requested = False
        self._invalid = False
        self._released = False
        self._peer_code_signing_requirement_set = False

    @classmethod
    def connect_service(cls, name: str) -> "XPCConnection":
        """Connect to an app-bundled XPC service by bundle identifier."""

        encoded = cls._encode_service_name(name)
        pointer = _lib().xpc_connection_create(encoded, None)
        return cls(pointer, role='service-client')

    @classmethod
    def connect_mach_service(
        cls,
        name: str,
        *,
        privileged: bool = False,
    ) -> "XPCConnection":
        """Connect to a Mach service advertised by a launchd job."""

        flags = cls.MACH_SERVICE_PRIVILEGED if privileged else 0
        pointer = _lib().xpc_connection_create_mach_service(
            cls._encode_service_name(name), None, flags,
        )
        return cls(pointer, role='mach-client')

    @classmethod
    def mach_service_listener(
        cls,
        name: str,
        *,
        privileged: bool = False,
    ) -> "XPCConnection":
        """Claim a launchd-advertised Mach service as its listener."""

        flags = cls.MACH_SERVICE_LISTENER
        if privileged:
            flags |= cls.MACH_SERVICE_PRIVILEGED
        pointer = _lib().xpc_connection_create_mach_service(
            cls._encode_service_name(name), None, flags,
        )
        return cls(pointer, role='mach-listener')

    @classmethod
    def anonymous_listener(cls) -> "XPCConnection":
        """Create an anonymous listener; call :meth:`endpoint` to export it."""

        pointer = _lib().xpc_connection_create(None, None)
        return cls(pointer, role='anonymous-listener')

    @classmethod
    def from_endpoint(cls, endpoint: XPCEndpoint) -> "XPCConnection":
        pointer = _lib().xpc_connection_create_from_endpoint(endpoint.pointer)
        return cls(pointer, role='endpoint-client')

    @staticmethod
    def _encode_service_name(name: str) -> bytes:
        if not isinstance(name, str) or not name:
            raise ValueError('XPC service name must be a nonempty string')
        if '\x00' in name:
            raise ValueError('XPC service name cannot contain NUL')
        try:
            return name.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError(
                f'XPC service name is not UTF-8 encodable: {name!r}',
            ) from exc

    @property
    def role(self) -> str:
        return self._role

    @property
    def active(self) -> bool:
        with self._lock:
            return self._activated and not self._invalid

    @property
    def invalid(self) -> bool:
        with self._lock:
            return self._invalid

    @property
    def pointer(self) -> int:
        with self._lock:
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            return self._ptr

    def retain_pointer(self) -> int:
        with self._lock:
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            return _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')

    def _retained_reference(self, *, require_active: bool = False) -> _OwnedPointer:
        """Return a temporary native retain acquired under the state lock.

        The connection-invalid callback may run on another dispatch thread and
        release this wrapper's owned reference.  Every native operation that
        outlives the Python state lock therefore takes a temporary retain first.
        """

        with self._lock:
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            if require_active and not self._activated:
                raise XPCError('activate() must be called before using the connection')
            if self._invalid:
                raise XPCError('XPC connection is invalid')
            return _OwnedPointer(
                _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain'),
            )

    def set_message_handler(
        self,
        handler: MessageHandler | None,
        *,
        auto_reply: bool = False,
    ) -> "XPCConnection":
        """Install the Python dictionary-message handler.

        With ``auto_reply=True``, a returned mapping is sent through the native
        reply channel.  Returning ``None`` or :data:`NO_REPLY` sends no reply.
        """

        with self._lock:
            self._message_handler = handler
            self._auto_reply = bool(auto_reply)
        return self

    def add_error_handler(self, handler: ErrorHandler) -> "XPCConnection":
        with self._lock:
            self._error_handlers.append(handler)
        return self

    def set_peer_handler(self, handler: PeerHandler | None) -> "XPCConnection":
        with self._lock:
            self._peer_handler = handler
        return self

    def set_unexpected_event_handler(
        self, handler: UnexpectedEventHandler | None,
    ) -> "XPCConnection":
        with self._lock:
            self._unexpected_event_handler = handler
        return self

    def set_peer_code_signing_requirement(
        self,
        requirement: str,
    ) -> "XPCConnection":
        """Require the remote peer to satisfy an Apple code requirement.

        This wraps ``xpc_connection_set_peer_code_signing_requirement``, which
        is public on macOS 12 and later.  Configure it before :meth:`activate`;
        the native API treats installing multiple peer requirements on one
        connection as a programming error, so this wrapper permits one call.
        """

        if not isinstance(requirement, str):
            raise TypeError('code-signing requirement must be str')
        if not requirement:
            raise ValueError('code-signing requirement must be nonempty')
        encoded = _encode_text(requirement, what='code-signing requirement')

        with self._lock:
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            if self._invalid or self._cancel_requested:
                raise XPCError(
                    'cannot configure a canceled/invalid XPC connection',
                )
            if self._activated:
                raise XPCError(
                    'peer code-signing requirement must be set before activate()',
                )
            if self._peer_code_signing_requirement_set:
                raise XPCError(
                    'a peer code-signing requirement is already installed',
                )

            function = getattr(
                _lib(),
                'xpc_connection_set_peer_code_signing_requirement',
                None,
            )
            if function is None:
                raise XPCUnavailableError(
                    'xpc_connection_set_peer_code_signing_requirement is '
                    'unavailable; it requires macOS 12 or later',
                )

            error = int(function(self._ptr, encoded))
            if error:
                try:
                    description = os.strerror(error)
                except ValueError:
                    description = f'native error {error}'
                raise OSError(
                    error,
                    'xpc_connection_set_peer_code_signing_requirement: '
                    + description,
                )
            self._peer_code_signing_requirement_set = True
        return self

    def _ensure_event_block(self) -> None:
        with self._lock:
            if self._event_block is not None:
                return
            block = _Block(None, [_XPC], self._handle_event)
            _lib().xpc_connection_set_event_handler(self.pointer, block.pointer)
            self._event_block = block

    def activate(self) -> "XPCConnection":
        """Install the native callback and perform the initial resume."""

        self._ensure_event_block()
        with self._lock:
            if self._invalid or self._cancel_requested:
                raise XPCError('cannot activate a canceled/invalid XPC connection')
            if self._activated:
                return self
            self._activated = True
            self._suspend_count = 0
            pointer = _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')
            with self._active_lock:
                self._active[self._ptr] = self
        try:
            _lib().xpc_connection_resume(pointer)
        finally:
            _lib().xpc_release(pointer)
        return self

    def suspend(self) -> None:
        with self._lock:
            if not self._activated or self._invalid:
                raise XPCError('cannot suspend an inactive XPC connection')
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            pointer = _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')
            self._suspend_count += 1
        try:
            _lib().xpc_connection_suspend(pointer)
        finally:
            _lib().xpc_release(pointer)

    def resume(self) -> None:
        with self._lock:
            if not self._activated or self._invalid:
                raise XPCError('cannot resume an inactive XPC connection')
            if self._suspend_count <= 0:
                raise XPCError('resume would be unbalanced; use activate() initially')
            if not self._ptr or self._released:
                raise XPCError('XPC connection has been released')
            pointer = _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')
            self._suspend_count -= 1
        try:
            _lib().xpc_connection_resume(pointer)
        finally:
            _lib().xpc_release(pointer)

    def cancel(self) -> None:
        release_immediately = False
        suspend_count = 0
        with self._lock:
            if self._cancel_requested or self._invalid or self._released:
                return
            pointer = _require_pointer(_lib().xpc_retain(self._ptr), 'xpc_retain')
            self._cancel_requested = True
            if not self._activated:
                # Rejected listener peers must still be explicitly canceled,
                # even though they were never resumed/activated.  With no event
                # handler active there will be no final invalidation callback,
                # so release our reference immediately after cancellation.
                self._invalid = True
                release_immediately = True
            else:
                # A canceled connection still needs balanced suspension state
                # so libxpc can deliver its terminal invalidation event.
                suspend_count, self._suspend_count = self._suspend_count, 0

        lib = _lib()
        try:
            lib.xpc_connection_cancel(pointer)
            for _ in range(suspend_count):
                lib.xpc_connection_resume(pointer)

            if release_immediately:
                with self._lock:
                    self._release_owned_reference_locked()
        finally:
            lib.xpc_release(pointer)

    close = cancel

    def __enter__(self) -> "XPCConnection":
        return self.activate()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.cancel()

    def endpoint(self) -> XPCEndpoint:
        with self._retained_reference() as connection_pointer:
            pointer = _lib().xpc_endpoint_create(connection_pointer)
        return XPCEndpoint(pointer, retain=False)

    def peer_credentials(self) -> PeerCredentials:
        with self._retained_reference() as pointer:
            lib = _lib()
            raw_name = lib.xpc_connection_get_name(pointer)
            get_asid = getattr(lib, 'xpc_connection_get_asid', None)
            return PeerCredentials(
                pid=int(lib.xpc_connection_get_pid(pointer)),
                euid=int(lib.xpc_connection_get_euid(pointer)),
                egid=int(lib.xpc_connection_get_egid(pointer)),
                service_name=raw_name.decode('utf-8', 'replace') if raw_name else None,
                audit_session_id=int(get_asid(pointer)) if get_asid is not None else None,
            )

    def _send_raw(self, message_pointer: int | ctypes.c_void_p) -> None:
        with self._retained_reference(require_active=True) as connection_pointer:
            _lib().xpc_connection_send_message(connection_pointer, message_pointer)

    def send(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise TypeError('top-level XPC messages must be mappings/dictionaries')
        with _OwnedPointer(_encode_mapping(cast(Mapping[str, Any], payload))) as pointer:
            self._send_raw(pointer)

    def request_async(
        self, payload: Mapping[str, Any],
    ) -> concurrent.futures.Future[dict[str, Any]]:
        """Send a native XPC request and return a standard-library Future."""

        if not isinstance(payload, Mapping):
            raise TypeError('top-level XPC messages must be mappings/dictionaries')
        future: concurrent.futures.Future[dict[str, Any]] = concurrent.futures.Future()
        holder: dict[str, _Block] = {}

        def receive_reply(reply_pointer: int) -> None:
            block = holder['block']
            try:
                type_name = _type_name(reply_pointer)
                if type_name == 'error':
                    exception: BaseException = XPCConnectionError(_decode_error(reply_pointer))
                    if not future.done():
                        future.set_exception(exception)
                    return
                decoded = _decode(reply_pointer)
                if not isinstance(decoded, dict):
                    raise XPCDecodeError(
                        f'XPC reply must be a dictionary, got {type(decoded).__name__}',
                    )
                if not future.done():
                    future.set_result(decoded)
            except BaseException as exc:
                if not future.done():
                    future.set_exception(exc)
            finally:
                with self._lock:
                    self._pending_reply_blocks.pop(id(block), None)
                    self._release_if_terminal_locked()

        block = _Block(None, [_XPC], receive_reply)
        holder['block'] = block
        with self._lock:
            self._pending_reply_blocks[id(block)] = block

        try:
            with _OwnedPointer(_encode_mapping(cast(Mapping[str, Any], payload))) as pointer:
                with self._retained_reference(require_active=True) as connection_pointer:
                    _lib().xpc_connection_send_message_with_reply(
                        connection_pointer,
                        pointer,
                        _lib().reply_queue,
                        block.pointer,
                    )
        except BaseException:
            with self._lock:
                self._pending_reply_blocks.pop(id(block), None)
                self._release_if_terminal_locked()
            raise

        return future

    def request(
        self,
        payload: Mapping[str, Any],
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Send a request and block outside of XPC callbacks for its reply."""

        if in_xpc_callback():
            raise XPCReentrancyError(
                'blocking for an XPC reply from an XPC callback can deadlock; '
                'use request_async() and return from the callback',
            )
        return self.request_async(payload).result(timeout=timeout)

    def request_sync_native(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Call libxpc's synchronous request primitive directly.

        This has no timeout and is forbidden inside an XPC callback.  The normal
        :meth:`request` method is generally preferable because it uses the async
        native API and a Python Future.
        """

        if in_xpc_callback():
            raise XPCReentrancyError(
                'xpc_connection_send_message_with_reply_sync is unsafe from an event handler',
            )
        with _OwnedPointer(_encode_mapping(payload)) as message_pointer:
            with self._retained_reference(require_active=True) as connection_pointer:
                reply_pointer = _require_pointer(
                    _lib().xpc_connection_send_message_with_reply_sync(
                        connection_pointer, message_pointer,
                    ),
                    'xpc_connection_send_message_with_reply_sync',
                )
        try:
            if _type_name(reply_pointer) == 'error':
                raise XPCConnectionError(_decode_error(reply_pointer))
            result = _decode(reply_pointer)
            if not isinstance(result, dict):
                raise XPCDecodeError('native synchronous reply was not a dictionary')
            return result
        finally:
            _lib().xpc_release(reply_pointer)

    def _handle_event(self, event_pointer: int) -> None:
        with _CallbackScope():
            type_name = _type_name(event_pointer)
            if type_name == 'connection':
                self._handle_peer(event_pointer)
                return
            if type_name == 'dictionary':
                self._handle_message(event_pointer)
                return
            if type_name == 'error':
                self._handle_error(_decode_error(event_pointer))
                return

            value = _decode(event_pointer)
            with self._lock:
                handler = self._unexpected_event_handler
            if handler is not None:
                handler(self, value)

    def _handle_peer(self, peer_pointer: int) -> None:
        with self._lock:
            handler = self._peer_handler
        peer = XPCConnection(peer_pointer, retain=True, role='peer')
        if handler is None:
            peer.cancel()
            return
        try:
            handler(self, peer)
        except BaseException:
            traceback.print_exc()
            peer.cancel()
            return
        if not peer._activated and not peer._cancel_requested:
            # libxpc requires every delivered peer to be accepted or rejected.
            peer.cancel()

    def _handle_message(self, message_pointer: int) -> None:
        with self._lock:
            handler = self._message_handler
            auto_reply = self._auto_reply
        if handler is None:
            return

        message = XPCMessage(self, message_pointer)
        try:
            result = handler(self, message)
            if auto_reply and result is not None and result is not NO_REPLY:
                message.reply(result)
        except BaseException:
            traceback.print_exc()

    def _handle_error(self, event: XPCErrorEvent) -> None:
        with self._lock:
            if event.kind == 'connection_invalid':
                self._invalid = True
            handlers = tuple(self._error_handlers)

        for handler in handlers:
            try:
                handler(self, event)
            except BaseException:
                traceback.print_exc()

        if event.kind == 'connection_invalid':
            with self._lock:
                self._release_if_terminal_locked()

    def _release_if_terminal_locked(self) -> None:
        # Apple does not impose an ordering between the connection's terminal
        # event and error deliveries to outstanding reply handlers.  A global
        # Block literal is not copied by BlocksRuntime, so its Python-owned
        # storage must remain pinned until every native reply callback ran.
        if self._invalid and not self._pending_reply_blocks:
            self._release_owned_reference_locked()

    def _release_owned_reference_locked(self) -> None:
        if self._released:
            return
        self._released = True
        pointer, self._ptr = self._ptr, 0
        if pointer:
            with self._active_lock:
                self._active.pop(pointer, None)
            _lib().xpc_release(pointer)

    def __del__(self) -> None:
        try:
            with self._lock:
                if not self._activated and not self._released:
                    # Newly created connections begin suspended.  Cancel before
                    # dropping our last reference rather than merely releasing a
                    # never-activated connection in suspended state.
                    self._cancel_requested = True
                    _lib().xpc_connection_cancel(self._ptr)
                    self._invalid = True
                    self._release_owned_reference_locked()
                elif self._activated and not self._cancel_requested and not self._invalid:
                    # Active connections are normally kept alive by _active.  This
                    # branch is mainly defensive during interpreter shutdown.
                    _lib().xpc_connection_cancel(self._ptr)
        except BaseException:
            pass

    def __repr__(self) -> str:
        with self._lock:
            return (
                f'{type(self).__name__}(role={self._role!r}, '
                f'active={self._activated}, invalid={self._invalid}, '
                f'pointer=0x{self._ptr:x})'
            )


_BUNDLED_MAIN_BLOCK: _Block | None = None
_BUNDLED_PEERS: set[XPCConnection] = set()


def run_bundled_service(peer_handler: Callable[[XPCConnection], None]) -> None:
    """Enter ``xpc_main`` for an app-bundled low-level XPC service.

    This never normally returns.  It must not be used by a launchd job whose
    plist advertises ``MachServices``; such jobs use
    :meth:`XPCConnection.mach_service_listener` instead.
    """

    global _BUNDLED_MAIN_BLOCK
    lib = _lib()
    if lib.xpc_main is None:
        raise XPCUnavailableError('xpc_main is unavailable')

    def accept(peer_pointer: int) -> None:
        peer = XPCConnection(peer_pointer, retain=True, role='bundled-peer')
        _BUNDLED_PEERS.add(peer)

        def discard_on_invalid(_connection: XPCConnection, event: XPCErrorEvent) -> None:
            if event.kind == 'connection_invalid':
                _BUNDLED_PEERS.discard(peer)

        peer.add_error_handler(discard_on_invalid)
        try:
            peer_handler(peer)
        except BaseException:
            traceback.print_exc()
            peer.cancel()
        if not peer._activated and not peer._cancel_requested:
            peer.cancel()

    _BUNDLED_MAIN_BLOCK = _Block(None, [_XPC], accept)
    lib.xpc_main(_BUNDLED_MAIN_BLOCK.pointer)
    raise RuntimeError('xpc_main unexpectedly returned')


def wait_forever(stop_event: threading.Event | None = None) -> None:
    """Keep the process alive while libdispatch invokes XPC callbacks."""

    event = stop_event if stop_event is not None else threading.Event()
    try:
        while not event.wait(3_600):
            pass
    except KeyboardInterrupt:
        return
