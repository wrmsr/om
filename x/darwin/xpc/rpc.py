"""
A compact NSXPCConnection-like RPC layer over :mod:`ctypes_xpc.core`.

It intentionally uses a tiny dictionary envelope rather than trying to imitate Foundation's private NSXPC wire format.
Both peers can export an object and obtain a dynamic proxy for the remote object.  Calls use libxpc's native reply
channel and return :class:`concurrent.futures.Future` objects.
"""
import asyncio
import concurrent.futures
import dataclasses
import inspect
import re
import threading
import traceback
import typing as ta

from .core import NO_REPLY
from .core import PeerCredentials
from .core import XPCConnection
from .core import XPCEndpoint
from .core import XPCError
from .core import XPCErrorEvent
from .core import XPCMessage
from .core import XPCReentrancyError
from .core import in_xpc_callback
from .core import run_bundled_service
from .core import wait_forever


##


_RPC_MARKER: ta.Final = '__ctypes_xpc_rpc__'
_RPC_VERSION: ta.Final = 1
_METHOD_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]{0,255}$')
_RPC_METHOD_MARKER: ta.Final = '__ctypes_xpc_rpc_method__'


class RPCProtocolError(XPCError):
    """A peer sent an invalid mini-RPC envelope."""


class RemoteError(XPCError):
    """An exception reported by the remote exported object."""

    def __init__(
        self,
        remote_type: str,
        message: str,
        *,
        remote_module: str | None = None,
        remote_traceback: str | None = None,
    ) -> None:
        self.remote_type = remote_type
        self.remote_module = remote_module
        self.remote_message = message
        self.remote_traceback = remote_traceback
        qualified = f'{remote_module}.{remote_type}' if remote_module else remote_type
        super().__init__(f'remote {qualified}: {message}')


def rpc_method(function: ta.Callable[..., ta.Any]) -> ta.Callable[..., ta.Any]:
    """Mark a public method for :meth:`RPCInterface.from_object`."""

    setattr(function, _RPC_METHOD_MARKER, True)
    return function


@dataclasses.dataclass(frozen=True, slots=True, init=False)
class RPCInterface:
    """The explicit method allowlist for an exported or remote object."""

    methods: frozenset[str]

    def __init__(self, methods: ta.Iterable[str]) -> None:
        normalized = frozenset(methods)
        if not normalized:
            raise ValueError('an RPC interface must contain at least one method')
        for method in normalized:
            _validate_method_name(method)
        object.__setattr__(self, 'methods', normalized)

    @classmethod
    def of(cls, *methods: str) -> RPCInterface:
        return cls(methods)

    @classmethod
    def from_object(cls, value: object | type[object]) -> RPCInterface:
        owner = value if isinstance(value, type) else type(value)
        methods: set[str] = set()
        for name, member in inspect.getmembers(owner):
            descriptor = inspect.getattr_static(owner, name)
            target = descriptor
            if isinstance(descriptor, (staticmethod, classmethod)):
                target = descriptor.__func__
            if callable(member) and getattr(target, _RPC_METHOD_MARKER, False):
                methods.add(name)
        return cls(methods)

    def allows(self, method: str) -> bool:
        return method in self.methods


def _validate_method_name(method: object) -> str:
    if not isinstance(method, str) or not _METHOD_PATTERN.fullmatch(method):
        raise ValueError(
            'RPC method names must match [A-Za-z][A-Za-z0-9_]{0,255}; '
            f'got {method!r}',
        )
    return method


class _RemoteMethod:
    __slots__ = (
        '_connection',
        '_method',
        '_oneway',
    )

    def __init__(self, connection: MiniXPCConnection, method: str, oneway: bool) -> None:
        self._connection = connection
        self._method = method
        self._oneway = oneway

    def __call__(self, *args: ta.Any, **kwargs: ta.Any) -> ta.Any:
        if self._oneway:
            self._connection.send_oneway(self._method, *args, **kwargs)
            return None
        return self._connection.call_async(self._method, *args, **kwargs)

    def __repr__(self) -> str:
        kind = 'oneway' if self._oneway else 'request'
        return f'<remote {kind} method {self._method}>'


class RemoteProxy:
    """A dynamic proxy whose methods return standard-library Futures."""

    __slots__ = (
        '_connection',
        '_oneway',
        '_cache',
        '_lock',
    )

    def __init__(self, connection: MiniXPCConnection, *, oneway: bool) -> None:
        self._connection = connection
        self._oneway = oneway
        self._cache: dict[str, _RemoteMethod] = {}
        self._lock = threading.Lock()

    def __getattr__(self, method: str) -> _RemoteMethod:
        if method.startswith('_'):
            raise AttributeError(method)
        with self._lock:
            try:
                return self._cache[method]
            except KeyError:
                self._connection._check_remote_method(method)
                remote_method = _RemoteMethod(self._connection, method, self._oneway)
                self._cache[method] = remote_method
                return remote_method

    def __repr__(self) -> str:
        kind = 'one-way' if self._oneway else 'request/reply'
        return f'RemoteProxy({kind})'


InvalidationHandler: ta.TypeAlias = ta.Callable[['MiniXPCConnection', XPCErrorEvent], None]
InterruptionHandler: ta.TypeAlias = ta.Callable[['MiniXPCConnection', XPCErrorEvent], None]
UnhandledMessageHandler: ta.TypeAlias = ta.Callable[['MiniXPCConnection', XPCMessage], None]


def _safe_xpc_text(value: object) -> str:
    """Make arbitrary exception text encodable as an XPC UTF-8 string."""

    return (
        str(value)
        .replace('\x00', '\uFFFD')
        .encode('utf-8', 'backslashreplace')
        .decode('utf-8')
    )


def _close_awaitable(value: object) -> None:
    """Best-effort cleanup for a coroutine that could not be scheduled."""

    close = getattr(value, 'close', None)
    if callable(close):
        try:
            close()
        except BaseException:
            pass


class MiniXPCConnection:
    """A bidirectional exported-object/remote-proxy connection.

    Calls made through :attr:`remote` return a Future.  Returning a Future from
    an exported method is supported and automatically flattened, which makes
    callback-style two-way RPC straightforward and avoids blocking an XPC event
    handler.
    """

    def __init__(
        self,
        connection: XPCConnection,
        *,
        exported_object: object | None = None,
        exported_interface: RPCInterface | None = None,
        remote_interface: RPCInterface | None = None,
        peer_code_signing_requirement: str | None = None,
        executor: concurrent.futures.Executor | None = None,
        asyncio_loop: asyncio.AbstractEventLoop | None = None,
        include_remote_tracebacks: bool = False,
        max_remote_traceback_chars: int = 16_384,
    ) -> None:
        if (exported_object is None) != (exported_interface is None):
            raise ValueError('exported_object and exported_interface must be set together')
        if max_remote_traceback_chars < 0:
            raise ValueError('max_remote_traceback_chars must be nonnegative')

        super().__init__()

        self._connection = connection
        self._exported_object = exported_object
        self._exported_interface = exported_interface
        self._remote_interface = remote_interface
        self._executor = executor
        self._asyncio_loop = asyncio_loop
        self._include_remote_tracebacks = include_remote_tracebacks
        self._max_remote_traceback_chars = max_remote_traceback_chars
        self._lock = threading.RLock()
        self._closed = False
        self._invalidation_handlers: list[InvalidationHandler] = []
        self._interruption_handlers: list[InterruptionHandler] = []
        self._unhandled_message_handler: UnhandledMessageHandler | None = None

        self.remote = RemoteProxy(self, oneway=False)
        self.remote_oneway = RemoteProxy(self, oneway=True)

        if peer_code_signing_requirement is not None:
            connection.set_peer_code_signing_requirement(peer_code_signing_requirement)
        connection.set_message_handler(self._receive_message, auto_reply=False)
        connection.add_error_handler(self._receive_transport_error)

    @classmethod
    def connect_service(
        cls,
        name: str,
        **kwargs: ta.Any,
    ) -> MiniXPCConnection:
        result = cls(XPCConnection.connect_service(name), **kwargs)
        result.activate()
        return result

    @classmethod
    def connect_mach_service(
        cls,
        name: str,
        *,
        privileged: bool = False,
        **kwargs: ta.Any,
    ) -> MiniXPCConnection:
        result = cls(
            XPCConnection.connect_mach_service(name, privileged=privileged),
            **kwargs,
        )
        result.activate()
        return result

    @classmethod
    def from_endpoint(
        cls,
        endpoint: XPCEndpoint,
        **kwargs: ta.Any,
    ) -> MiniXPCConnection:
        result = cls(XPCConnection.from_endpoint(endpoint), **kwargs)
        result.activate()
        return result

    @property
    def connection(self) -> XPCConnection:
        return self._connection

    @property
    def remote_object_proxy(self) -> RemoteProxy:
        return self.remote

    @property
    def remote_oneway_proxy(self) -> RemoteProxy:
        return self.remote_oneway

    @property
    def closed(self) -> bool:
        return self._closed

    def set_exported_object(
        self,
        exported_object: object,
        exported_interface: RPCInterface,
    ) -> None:
        with self._lock:
            self._exported_object = exported_object
            self._exported_interface = exported_interface

    def clear_exported_object(self) -> None:
        with self._lock:
            self._exported_object = None
            self._exported_interface = None

    def set_unhandled_message_handler(
        self,
        handler: UnhandledMessageHandler | None,
    ) -> None:
        with self._lock:
            self._unhandled_message_handler = handler

    def add_invalidation_handler(self, handler: InvalidationHandler) -> None:
        with self._lock:
            self._invalidation_handlers.append(handler)

    def add_interruption_handler(self, handler: InterruptionHandler) -> None:
        with self._lock:
            self._interruption_handlers.append(handler)

    def activate(self) -> MiniXPCConnection:
        self._connection.activate()
        return self

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._connection.cancel()

    def peer_credentials(self) -> PeerCredentials:
        return self._connection.peer_credentials()

    def _check_remote_method(self, method: str) -> str:
        method = _validate_method_name(method)
        interface = self._remote_interface
        if interface is not None and not interface.allows(method):
            raise AttributeError(f'remote interface does not contain {method!r}')
        return method

    def call_async(
        self,
        method: str,
        *args: ta.Any,
        **kwargs: ta.Any,
    ) -> concurrent.futures.Future[ta.Any]:
        method = self._check_remote_method(method)
        with self._lock:
            if self._closed:
                raise XPCError('mini XPC connection is closed')

        source = self._connection.request_async({
            _RPC_MARKER: _RPC_VERSION,
            'kind': 'call',
            'method': method,
            'args': list(args),
            'kwargs': kwargs,
        })
        result: concurrent.futures.Future[ta.Any] = concurrent.futures.Future()

        def complete(reply_future: concurrent.futures.Future[dict[str, ta.Any]]) -> None:
            try:
                reply = reply_future.result()
                value = self._decode_reply(reply)
            except BaseException as exc:
                if not result.done():
                    result.set_exception(exc)
            else:
                if not result.done():
                    result.set_result(value)

        source.add_done_callback(complete)
        return result

    def call(
        self,
        method: str,
        *args: ta.Any,
        timeout: float | None = None,
        **kwargs: ta.Any,
    ) -> ta.Any:
        if in_xpc_callback():
            raise XPCReentrancyError(
                'blocking mini-XPC calls are forbidden from XPC callbacks; '
                'return/use the Future from call_async() instead',
            )
        return self.call_async(method, *args, **kwargs).result(timeout=timeout)

    def send_oneway(self, method: str, *args: ta.Any, **kwargs: ta.Any) -> None:
        method = self._check_remote_method(method)
        with self._lock:
            if self._closed:
                raise XPCError('mini XPC connection is closed')
        self._connection.send(
            {
                _RPC_MARKER: _RPC_VERSION,
                'kind': 'oneway',
                'method': method,
                'args': list(args),
                'kwargs': kwargs,
            },
        )

    @staticmethod
    def _decode_reply(reply: ta.Mapping[str, ta.Any]) -> ta.Any:
        if reply.get(_RPC_MARKER) != _RPC_VERSION or reply.get('kind') != 'reply':
            raise RPCProtocolError(f'invalid mini-XPC reply envelope: {reply!r}')
        ok = reply.get('ok')
        if ok is True:
            return reply.get('result')
        if ok is not False:
            raise RPCProtocolError("mini-XPC reply has a non-Boolean/missing 'ok' field")
        error = reply.get('error')
        if not isinstance(error, ta.Mapping):
            raise RPCProtocolError('mini-XPC error reply has no error dictionary')
        remote_type = error.get('type', 'Exception')
        message = error.get('message', '')
        remote_module = error.get('module')
        remote_traceback = error.get('traceback')
        if not isinstance(remote_type, str) or not isinstance(message, str):
            raise RPCProtocolError('mini-XPC error reply has invalid type/message fields')
        return_error = RemoteError(
            remote_type,
            message,
            remote_module=remote_module if isinstance(remote_module, str) else None,
            remote_traceback=remote_traceback if isinstance(remote_traceback, str) else None,
        )
        raise return_error

    def _receive_message(self, _low: XPCConnection, message: XPCMessage) -> object:
        try:
            payload = message.payload
        except BaseException:
            message.close()
            raise

        if payload.get(_RPC_MARKER) != _RPC_VERSION:
            with self._lock:
                handler = self._unhandled_message_handler
            if handler is not None:
                handler(self, message)
            else:
                message.close()
            return NO_REPLY

        kind = payload.get('kind')
        if kind not in ('call', 'oneway'):
            self._reply_protocol_error(message, kind, 'invalid RPC message kind')
            return NO_REPLY

        try:
            method = _validate_method_name(payload.get('method'))
            args = payload.get('args', [])
            kwargs = payload.get('kwargs', {})
            if not isinstance(args, list):
                raise RPCProtocolError("RPC 'args' must be an array")
            if not isinstance(kwargs, dict) or not all(isinstance(k, str) for k in kwargs):
                raise RPCProtocolError("RPC 'kwargs' must be a string-keyed dictionary")

            with self._lock:
                exported_object = self._exported_object
                exported_interface = self._exported_interface
            if exported_object is None or exported_interface is None:
                raise RPCProtocolError('this connection exports no object')
            if not exported_interface.allows(method):
                raise RPCProtocolError(f'method {method!r} is not in the exported interface')

            target = getattr(exported_object, method)
            if not callable(target):
                raise RPCProtocolError(f'exported attribute {method!r} is not callable')
        except BaseException as exc:
            if kind == 'call':
                self._reply_exception(message, exc)
            else:
                message.close()
                traceback.print_exception(exc)
            return NO_REPLY

        def invoke() -> ta.Any:
            return target(*args, **kwargs)

        if self._executor is not None:
            try:
                invocation: ta.Any = self._executor.submit(invoke)
            except BaseException as exc:
                if kind == 'call':
                    self._reply_exception(message, exc)
                else:
                    message.close()
                    traceback.print_exception(exc)
                return NO_REPLY
        else:
            try:
                invocation = invoke()
            except BaseException as exc:
                if kind == 'call':
                    self._reply_exception(message, exc)
                else:
                    message.close()
                    traceback.print_exception(exc)
                return NO_REPLY

        if kind == 'oneway':
            self._consume_oneway_result(invocation, message)
        else:
            self._resolve_call_result(invocation, message)
        return NO_REPLY

    def _resolve_call_result(self, value: ta.Any, message: XPCMessage) -> None:
        if isinstance(value, concurrent.futures.Future):
            value.add_done_callback(
                lambda future: self._finish_future_call(
                    ta.cast(concurrent.futures.Future[ta.Any], future),
                    message,
                ),
            )
            return
        if inspect.isawaitable(value):
            if self._asyncio_loop is None:
                _close_awaitable(value)
                self._reply_exception(
                    message,
                    TypeError(
                        'exported method returned an awaitable but no asyncio_loop was configured',
                    ),
                )
                return
            coroutine = _await_value(value)
            try:
                future = asyncio.run_coroutine_threadsafe(coroutine, self._asyncio_loop)
            except BaseException as exc:
                coroutine.close()
                _close_awaitable(value)
                self._reply_exception(message, exc)
                return
            self._resolve_call_result(future, message)
            return
        self._reply_success(message, value)

    def _finish_future_call(
        self,
        future: concurrent.futures.Future[ta.Any],
        message: XPCMessage,
    ) -> None:
        try:
            value = future.result()
        except BaseException as exc:
            self._reply_exception(message, exc)
        else:
            # Flatten futures/awaitables returned by executor jobs or callbacks.
            self._resolve_call_result(value, message)

    def _consume_oneway_result(self, value: ta.Any, message: XPCMessage) -> None:
        message.close()
        if isinstance(value, concurrent.futures.Future):
            value.add_done_callback(self._log_oneway_future)
            return
        if inspect.isawaitable(value):
            if self._asyncio_loop is None:
                _close_awaitable(value)
                traceback.print_exception(
                    TypeError('one-way exported method returned an awaitable but no asyncio_loop was configured'),
                )
                return
            coroutine = _await_value(value)
            try:
                future = asyncio.run_coroutine_threadsafe(coroutine, self._asyncio_loop)
            except BaseException as exc:
                coroutine.close()
                _close_awaitable(value)
                traceback.print_exception(exc)
            else:
                future.add_done_callback(self._log_oneway_future)

    @staticmethod
    def _log_oneway_future(future: concurrent.futures.Future[ta.Any]) -> None:
        try:
            future.result()
        except BaseException as exc:
            traceback.print_exception(exc)

    def _reply_success(self, message: XPCMessage, result: ta.Any) -> None:
        try:
            message.reply(
                {
                    _RPC_MARKER: _RPC_VERSION,
                    'kind': 'reply',
                    'ok': True,
                    'result': result,
                },
            )
        except BaseException as exc:
            # Most commonly the exported method returned a value outside the low-level XPC codec.  Turn that local
            # encoding failure into a proper remote exception rather than leaving the caller hanging.
            self._reply_exception(message, exc)
        else:
            message.close()

    def _reply_exception(self, message: XPCMessage, exception: BaseException) -> None:
        error: dict[str, ta.Any] = {
            'type': _safe_xpc_text(type(exception).__qualname__),
            'module': _safe_xpc_text(type(exception).__module__),
            'message': _safe_xpc_text(exception),
        }
        if self._include_remote_tracebacks and self._max_remote_traceback_chars:
            formatted = ''.join(
                traceback.format_exception(type(exception), exception, exception.__traceback__),
            )
            error['traceback'] = _safe_xpc_text(formatted[-self._max_remote_traceback_chars :])
        try:
            message.reply(
                {
                    _RPC_MARKER: _RPC_VERSION,
                    'kind': 'reply',
                    'ok': False,
                    'error': error,
                },
            )
        except BaseException:
            traceback.print_exc()
        finally:
            message.close()

    def _reply_protocol_error(self, message: XPCMessage, kind: ta.Any, text: str) -> None:
        # Reuse the normal exception path so hostile NULs/lone surrogates in a malformed envelope cannot themselves make
        # the error reply unencodable.
        self._reply_exception(message, RPCProtocolError(f'{text}: {kind!r}'))

    def _receive_transport_error(
        self,
        _low: XPCConnection,
        event: XPCErrorEvent,
    ) -> None:
        if event.kind == 'connection_interrupted':
            with self._lock:
                handlers = tuple(self._interruption_handlers)
        elif event.kind == 'connection_invalid':
            with self._lock:
                self._closed = True
                handlers = tuple(self._invalidation_handlers)
        else:
            return

        for handler in handlers:
            try:
                handler(self, event)
            except BaseException:
                traceback.print_exc()

    def __enter__(self) -> MiniXPCConnection:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._connection!r})'


async def _await_value(value: ta.Any) -> ta.Any:
    return await value


ExportedFactory: ta.TypeAlias = ta.Callable[[MiniXPCConnection], object]
PeerValidator: ta.TypeAlias = ta.Callable[[PeerCredentials], bool]


class MiniXPCMachService:
    """A launchd Mach-service listener that creates one RPC connection per peer."""

    def __init__(
        self,
        name: str,
        exported_factory: ExportedFactory,
        *,
        exported_interface: RPCInterface,
        remote_interface: RPCInterface | None = None,
        peer_validator: PeerValidator | None = None,
        peer_code_signing_requirement: str | None = None,
        privileged: bool = False,
        executor: concurrent.futures.Executor | None = None,
        asyncio_loop: asyncio.AbstractEventLoop | None = None,
        include_remote_tracebacks: bool = False,
    ) -> None:
        super().__init__()

        self._name = name
        self._factory = exported_factory
        self._exported_interface = exported_interface
        self._remote_interface = remote_interface
        self._peer_validator = peer_validator
        self._peer_code_signing_requirement = peer_code_signing_requirement
        self._executor = executor
        self._asyncio_loop = asyncio_loop
        self._include_remote_tracebacks = include_remote_tracebacks
        self._lock = threading.RLock()
        self._connections: set[MiniXPCConnection] = set()
        self._listener = XPCConnection.mach_service_listener(name, privileged=privileged)
        self._listener.set_peer_handler(self._accept_peer)

    @property
    def listener(self) -> XPCConnection:
        return self._listener

    @property
    def connections(self) -> tuple[MiniXPCConnection, ...]:
        with self._lock:
            return tuple(self._connections)

    def start(self) -> MiniXPCMachService:
        self._listener.activate()
        return self

    def _accept_peer(self, _listener: XPCConnection, peer: XPCConnection) -> None:
        if self._peer_validator is not None:
            try:
                accepted = bool(self._peer_validator(peer.peer_credentials()))
            except BaseException:
                traceback.print_exc()
                peer.cancel()
                return
            if not accepted:
                peer.cancel()
                return

        connection = MiniXPCConnection(
            peer,
            remote_interface=self._remote_interface,
            peer_code_signing_requirement=self._peer_code_signing_requirement,
            executor=self._executor,
            asyncio_loop=self._asyncio_loop,
            include_remote_tracebacks=self._include_remote_tracebacks,
        )
        try:
            exported_object = self._factory(connection)
            connection.set_exported_object(exported_object, self._exported_interface)
        except BaseException:
            traceback.print_exc()
            connection.close()
            return

        def discard(
            invalid_connection: MiniXPCConnection,
            _event: XPCErrorEvent,
        ) -> None:
            with self._lock:
                self._connections.discard(invalid_connection)

        connection.add_invalidation_handler(discard)
        with self._lock:
            self._connections.add(connection)
        try:
            connection.activate()
        except BaseException:
            with self._lock:
                self._connections.discard(connection)
            connection.close()
            raise

    def stop(self) -> None:
        with self._lock:
            connections = tuple(self._connections)
            self._connections.clear()
        for connection in connections:
            connection.close()
        self._listener.cancel()

    def run_forever(self) -> None:
        wait_forever()

    def __enter__(self) -> MiniXPCMachService:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()


_BUNDLED_RPC_CONNECTIONS_LOCK = threading.Lock()
_BUNDLED_RPC_CONNECTIONS: set[MiniXPCConnection] = set()


def run_bundled_rpc_service(
    exported_factory: ExportedFactory,
    *,
    exported_interface: RPCInterface,
    remote_interface: RPCInterface | None = None,
    peer_code_signing_requirement: str | None = None,
    executor: concurrent.futures.Executor | None = None,
    asyncio_loop: asyncio.AbstractEventLoop | None = None,
    include_remote_tracebacks: bool = False,
) -> None:
    """Run the mini-RPC layer inside an app-bundled ``xpc_main`` service."""

    def accept(peer: XPCConnection) -> None:
        connection = MiniXPCConnection(
            peer,
            remote_interface=remote_interface,
            peer_code_signing_requirement=peer_code_signing_requirement,
            executor=executor,
            asyncio_loop=asyncio_loop,
            include_remote_tracebacks=include_remote_tracebacks,
        )
        exported_object = exported_factory(connection)
        connection.set_exported_object(exported_object, exported_interface)
        with _BUNDLED_RPC_CONNECTIONS_LOCK:
            _BUNDLED_RPC_CONNECTIONS.add(connection)

        def discard(invalid: MiniXPCConnection, _event: XPCErrorEvent) -> None:
            with _BUNDLED_RPC_CONNECTIONS_LOCK:
                _BUNDLED_RPC_CONNECTIONS.discard(invalid)

        connection.add_invalidation_handler(discard)
        try:
            connection.activate()
        except BaseException:
            with _BUNDLED_RPC_CONNECTIONS_LOCK:
                _BUNDLED_RPC_CONNECTIONS.discard(connection)
            connection.close()
            raise

    run_bundled_service(accept)
