# ruff: noqa: PYI034 UP006 UP007 UP037 UP045
"""
A small zero-dependency RESP2 Redis client built as a non-HTTP pipeline example.

Run it with ``./python -m omcore.io.pipelines.tests.redis``. By default the entrypoint starts a private,
persistence-disabled Redis subprocess; ``--redis-address HOST:PORT`` instead uses an existing server. It sends the same
representative command sequence through the sync and asyncio stream drivers.
"""
import argparse
import asyncio
import collections
import dataclasses as dc
import shutil
import socket
import subprocess
import tempfile
import time
import typing as ta

from ...streambufs.segmented import SegmentedByteStreamBuffer
from ...streambufs.types import ByteStreamBuffer
from ...streambufs.types import ByteStreamBufferView
from ..bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages
from ..drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ..drivers.sync import SyncSocketIoPipelineDriver
from ..errors import IncompleteDecodingIoPipelineError


RedisCommandArg = ta.Union[str, bytes, bytearray, memoryview, int]  # ta.TypeAlias
RedisValue = ta.Any  # ta.TypeAlias


##
# Protocol messages


class RedisClientError(Exception):
    pass


class RedisProtocolError(RedisClientError):
    pass


class RedisReplyError(RedisClientError):
    pass


class RedisConnectionClosedError(RedisClientError):
    pass


@dc.dataclass(frozen=True)
class RedisCommand:
    args: ta.Tuple[bytes, ...]

    def __post_init__(self) -> None:
        if not self.args:
            raise ValueError('Redis commands must have at least one argument')


@dc.dataclass(frozen=True)
class RedisResponse:
    value: RedisValue


@dc.dataclass(frozen=True)
class _RedisRequest:
    request_id: int
    command: RedisCommand


@dc.dataclass(frozen=True)
class _RedisResult:
    request_id: int
    value: RedisValue = None
    error: ta.Optional[BaseException] = None


##
# RESP2 codec


class RedisCommandEncoderIoPipelineHandler(IoPipelineHandler):
    """Encode Redis commands as RESP2 arrays of bulk strings."""

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not isinstance(msg, RedisCommand):
            ctx.feed_out(msg)
            return

        buf = SegmentedByteStreamBuffer()
        buf.write(b'*' + str(len(msg.args)).encode('ascii') + b'\r\n')
        for arg in msg.args:
            buf.write(b'$' + str(len(arg)).encode('ascii') + b'\r\n')
            buf.write(arg)
            buf.write(b'\r\n')

        ctx.feed_out(buf.split_to(len(buf)))


class _RespArrayState:
    def __init__(self, length: int) -> None:
        super().__init__()

        self.remaining = length
        self.items: ta.List[RedisValue] = []


class RedisResponseDecoderIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """
    Incrementally decode RESP2 replies.

    Bulk-string bodies are split out as stream-buffer views. They are only materialized as ``bytes`` at the public
    client boundary, so parsing and nested-array assembly do not require concatenating the transport read buffer.
    """

    def __init__(self, *, max_buffer_size: ta.Optional[int] = 64 * 1024 * 1024) -> None:
        super().__init__(max_buffer_size=max_buffer_size)

        self._bulk_length: ta.Optional[int] = None
        self._arrays: ta.List[_RespArrayState] = []

    @staticmethod
    def _parse_length(payload: bytes, kind: str) -> int:
        try:
            return int(payload)
        except ValueError:
            raise RedisProtocolError(f'invalid RESP {kind} length: {payload!r}') from None

    def _accept_value(self, value: RedisValue, out: ta.List[ta.Any]) -> None:
        while self._arrays:
            state = self._arrays[-1]
            state.items.append(value)
            state.remaining -= 1
            if state.remaining:
                return

            self._arrays.pop()
            value = state.items

        out.append(RedisResponse(value))

    def _parse_buffer(self, buf: ByteStreamBuffer, out: ta.List[ta.Any]) -> None:
        while True:
            if (bulk_length := self._bulk_length) is not None:
                if len(buf) < bulk_length + 2:
                    return

                bulk = buf.split_to(bulk_length)
                if buf.coalesce(2).tobytes() != b'\r\n':
                    raise RedisProtocolError('RESP bulk string is missing its trailing CRLF')
                buf.advance(2)
                self._bulk_length = None
                self._accept_value(bulk, out)
                continue

            line_end = buf.find(b'\r\n')
            if line_end < 0:
                return

            line = bytes(buf.split_to(line_end).tobytes())
            buf.advance(2)
            if not line:
                raise RedisProtocolError('empty RESP header line')

            prefix = line[:1]
            payload = line[1:]

            if prefix == b'+':
                self._accept_value(payload, out)

            elif prefix == b'-':
                self._accept_value(RedisReplyError(payload.decode('utf-8', errors='replace')), out)

            elif prefix == b':':
                try:
                    value = int(payload)
                except ValueError:
                    raise RedisProtocolError(f'invalid RESP integer: {payload!r}') from None
                self._accept_value(value, out)

            elif prefix == b'$':
                length = self._parse_length(payload, 'bulk string')
                if length == -1:
                    self._accept_value(None, out)
                elif length < 0:
                    raise RedisProtocolError(f'invalid RESP bulk string length: {length}')
                else:
                    self._bulk_length = length

            elif prefix == b'*':
                length = self._parse_length(payload, 'array')
                if length == -1:
                    self._accept_value(None, out)
                elif length < 0:
                    raise RedisProtocolError(f'invalid RESP array length: {length}')
                elif not length:
                    self._accept_value([], out)
                else:
                    self._arrays.append(_RespArrayState(length))

            else:
                raise RedisProtocolError(f'unsupported RESP2 type prefix: {prefix!r}')

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        if not final:
            self._parse_buffer(buf, out)
            return

        # BufferedBytesToMessageDecoderIoPipelineHandler intentionally supplies an empty final buffer. Finish checking
        # this decoder's retained cumulation as well as its already-consumed array/bulk framing state.
        final_buf = self._buf if self._buf is not None else buf  # noqa
        self._parse_buffer(final_buf, out)
        if len(final_buf) or self._bulk_length is not None or self._arrays:
            raise IncompleteDecodingIoPipelineError('incomplete RESP reply at end of input')
        self._buf = None  # noqa


##
# Application protocol handler


class RedisClientIoPipelineHandler(IoPipelineHandler):
    """Correlate outbound client requests with Redis's ordered inbound replies."""

    def __init__(self) -> None:
        super().__init__()

        self._pending: ta.Deque[_RedisRequest] = collections.deque()

    def _fail_pending(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        while self._pending:
            req = self._pending.popleft()
            ctx.feed_out(_RedisResult(req.request_id, error=exc))

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _RedisRequest):
            self._pending.append(msg)
            ctx.feed_out(msg.command)
            return

        if isinstance(msg, RedisResponse):
            if not self._pending:
                raise RedisProtocolError('received an unsolicited Redis reply')

            req = self._pending.popleft()
            if isinstance(msg.value, RedisReplyError):
                ctx.feed_out(_RedisResult(req.request_id, error=msg.value))
            else:
                ctx.feed_out(_RedisResult(req.request_id, value=msg.value))
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self._fail_pending(ctx, msg.exc)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._fail_pending(ctx, RedisConnectionClosedError('Redis closed the connection before replying'))
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)


def make_redis_client_pipeline_spec() -> IoPipeline.Spec:
    return IoPipeline.Spec([
        RedisCommandEncoderIoPipelineHandler(),
        RedisResponseDecoderIoPipelineHandler(),
        RedisClientIoPipelineHandler(),
    ])


##
# Clients


class BaseRedisClient:
    """The driver-independent command and result side of the Redis client."""

    def __init__(self, driver: ta.Any) -> None:
        super().__init__()

        self._driver = driver
        self._next_request_id = 0
        self._executing = False

    @staticmethod
    def _encode_arg(arg: RedisCommandArg) -> bytes:
        if isinstance(arg, str):
            return arg.encode('utf-8')
        if isinstance(arg, int):
            return str(arg).encode('ascii')
        if isinstance(arg, bytes):
            return arg
        if isinstance(arg, (bytearray, memoryview)):
            return bytes(arg)
        raise TypeError(arg)

    @staticmethod
    def _materialize_value(value: RedisValue) -> RedisValue:
        if isinstance(value, ByteStreamBufferView):
            return value.tobytes()
        if isinstance(value, list):
            return [BaseRedisClient._materialize_value(item) for item in value]
        return value

    def _begin_execute(self, args: ta.Tuple[RedisCommandArg, ...]) -> _RedisRequest:
        if self._executing:
            raise RedisClientError('concurrent execute calls on one client are not supported')

        request_id = self._next_request_id
        self._next_request_id += 1
        req = _RedisRequest(request_id, RedisCommand(tuple(self._encode_arg(arg) for arg in args)))
        self._executing = True
        try:
            self._driver.enqueue(req)
        except BaseException:
            self._executing = False
            raise
        return req

    def _finish_execute(self, req: _RedisRequest, msg: ta.Any) -> RedisValue:
        if isinstance(msg, IoPipelineMessages.Error):
            raise msg.exc
        if isinstance(msg, BaseException):
            raise msg
        if not isinstance(msg, _RedisResult):
            raise RedisClientError(f'unexpected pipeline output: {msg!r}')
        if msg.request_id != req.request_id:
            raise RedisClientError(
                f'out-of-order Redis result: expected request {req.request_id}, got {msg.request_id}',
            )
        if msg.error is not None:
            raise msg.error
        return self._materialize_value(msg.value)


class RedisClient(BaseRedisClient):
    """Synchronous Redis client over a synchronous pipeline driver."""

    def execute(self, *args: RedisCommandArg) -> RedisValue:
        req = self._begin_execute(args)
        try:
            while True:
                if (msg := self._driver.next()) is not None:
                    return self._finish_execute(req, msg)
        finally:
            self._executing = False

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> 'RedisClient':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class AsyncRedisClient(BaseRedisClient):
    """
    Asynchronous Redis client over an asynchronous pipeline driver.

    This class has no asyncio dependency: its driver's awaitable ``next`` and ``close`` methods determine which async
    runtime and transport implementation actually power it.
    """

    async def execute(self, *args: RedisCommandArg) -> RedisValue:
        req = self._begin_execute(args)
        try:
            while True:
                if (msg := await self._driver.next()) is not None:
                    return self._finish_execute(req, msg)
        finally:
            self._executing = False

    async def close(self) -> None:
        await self._driver.close()

    async def __aenter__(self) -> 'AsyncRedisClient':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


##
# End-to-end demonstration


class _RedisServer:
    def __init__(self, executable: str) -> None:
        super().__init__()

        self._executable = executable
        self._temp_dir: ta.Optional[tempfile.TemporaryDirectory] = None
        self._process: ta.Optional[subprocess.Popen] = None
        self._log_path: ta.Optional[str] = None
        self._port: ta.Optional[int] = None

    @staticmethod
    def _reserve_port() -> int:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            return ta.cast(ta.Tuple[str, int], sock.getsockname())[1]

    def _read_log(self) -> str:
        if self._log_path is None:
            return ''
        try:
            with open(self._log_path) as f:
                return f.read().strip()
        except OSError:
            return ''

    def __enter__(self) -> int:
        temp_dir = self._temp_dir = tempfile.TemporaryDirectory(prefix='omcore-redis-')
        port = self._port = self._reserve_port()
        self._log_path = f'{temp_dir.name}/redis.log'

        self._process = process = subprocess.Popen([
            self._executable,
            '--bind', '127.0.0.1',
            '--port', str(port),
            '--protected-mode', 'yes',
            '--save', '',
            '--appendonly', 'no',
            '--daemonize', 'no',
            '--dir', temp_dir.name,
            '--logfile', self._log_path,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        deadline = time.monotonic() + 5.
        while True:
            if process.poll() is not None:
                log = self._read_log()
                self.__exit__(None, None, None)
                raise RuntimeError(f'redis-server exited during startup{f": {log}" if log else ""}')

            try:
                with socket.create_connection(('127.0.0.1', port), timeout=.05):
                    return port
            except OSError:
                if time.monotonic() >= deadline:
                    log = self._read_log()
                    self.__exit__(None, None, None)
                    raise TimeoutError(f'timed out starting redis-server{f": {log}" if log else ""}') from None
                time.sleep(.01)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if (process := self._process) is not None:
            self._process = None
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5.)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5.)

        if (temp_dir := self._temp_dir) is not None:
            self._temp_dir = None
            temp_dir.cleanup()


def _run_sync_demo(port: int, *, host: str = '127.0.0.1') -> ta.Mapping[str, RedisValue]:
    with socket.create_connection((host, port)) as sock:
        client = RedisClient(SyncSocketIoPipelineDriver(make_redis_client_pipeline_spec(), sock))
        try:
            client.execute('DEL', 'omcore:redis:sync:value', 'omcore:redis:sync:counter')
            results = {
                'PING': client.execute('PING'),
                'SET': client.execute('SET', 'omcore:redis:sync:value', b'hello\x00pipeline'),
                'GET': client.execute('GET', 'omcore:redis:sync:value'),
                'INCR': client.execute('INCR', 'omcore:redis:sync:counter'),
                'INCRBY': client.execute('INCRBY', 'omcore:redis:sync:counter', 41),
                'MGET': client.execute(
                    'MGET',
                    'omcore:redis:sync:value',
                    'omcore:redis:sync:counter',
                    'omcore:redis:sync:missing',
                ),
            }
            client.execute('DEL', 'omcore:redis:sync:value', 'omcore:redis:sync:counter')
        finally:
            client.close()

    assert results == {
        'PING': b'PONG',
        'SET': b'OK',
        'GET': b'hello\x00pipeline',
        'INCR': 1,
        'INCRBY': 42,
        'MGET': [b'hello\x00pipeline', b'42', None],
    }
    return results


async def _run_async_demo(port: int, *, host: str = '127.0.0.1') -> ta.Mapping[str, RedisValue]:
    reader, writer = await asyncio.open_connection(host, port)
    driver = PollAsyncioStreamIoPipelineDriver(make_redis_client_pipeline_spec(), reader, writer)
    client = AsyncRedisClient(driver)
    try:
        await client.execute('DEL', 'omcore:redis:async:value', 'omcore:redis:async:counter')
        results = {
            'PING': await client.execute('PING'),
            'SET': await client.execute('SET', 'omcore:redis:async:value', b'hello\x00async pipeline'),
            'GET': await client.execute('GET', 'omcore:redis:async:value'),
            'INCR': await client.execute('INCR', 'omcore:redis:async:counter'),
            'INCRBY': await client.execute('INCRBY', 'omcore:redis:async:counter', 41),
            'MGET': await client.execute(
                'MGET',
                'omcore:redis:async:value',
                'omcore:redis:async:counter',
                'omcore:redis:async:missing',
            ),
        }
        await client.execute('DEL', 'omcore:redis:async:value', 'omcore:redis:async:counter')
    finally:
        await client.close()

    assert results == {
        'PING': b'PONG',
        'SET': b'OK',
        'GET': b'hello\x00async pipeline',
        'INCR': 1,
        'INCRBY': 42,
        'MGET': [b'hello\x00async pipeline', b'42', None],
    }
    return results


def _print_results(kind: str, results: ta.Mapping[str, RedisValue]) -> None:
    print(f'{kind} client:')
    for command, value in results.items():
        print(f'  {command:<6} -> {value!r}')


def _parse_redis_address(value: str) -> ta.Tuple[str, int]:
    host, sep, port_string = value.rpartition(':')
    if not sep or not host or not port_string:
        raise argparse.ArgumentTypeError('Redis address must have HOST:PORT format')

    if host.startswith('['):
        if not host.endswith(']'):
            raise argparse.ArgumentTypeError('bracketed Redis host is missing its closing bracket')
        host = host[1:-1]
        if not host:
            raise argparse.ArgumentTypeError('Redis host must not be empty')

    try:
        port = int(port_string)
    except ValueError:
        raise argparse.ArgumentTypeError(f'invalid Redis port: {port_string!r}') from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f'Redis port is out of range: {port}')

    return host, port


def _run_demos(host: str, port: int) -> None:
    print(f'using redis at {host}:{port}')
    _print_results('sync', _run_sync_demo(port, host=host))
    _print_results('async', asyncio.run(_run_async_demo(port, host=host)))


def _main() -> None:
    parser = argparse.ArgumentParser(description='Run the omcore pipeline Redis client demonstration')
    parser.add_argument(
        '--redis-address',
        type=_parse_redis_address,
        metavar='HOST:PORT',
        help='use an existing Redis server instead of starting a subprocess',
    )
    parser.add_argument(
        '--redis-server',
        help='redis-server executable used by the subprocess fallback (default: search PATH)',
    )
    args = parser.parse_args()

    if args.redis_address is not None:
        _run_demos(*args.redis_address)
        return

    redis_server = args.redis_server or shutil.which('redis-server')
    if redis_server is None:
        parser.error('redis-server was not found; pass --redis-server')

    with _RedisServer(redis_server) as port:
        _run_demos('127.0.0.1', port)


if __name__ == '__main__':
    _main()
