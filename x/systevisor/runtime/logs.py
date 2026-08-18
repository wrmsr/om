# ruff: noqa: UP006 UP007 UP037 UP045
import abc
import dataclasses as dc
import enum
import os
import re
import syslog
import typing as ta

from omcore.io.fdio.handlers import FdioHandler
from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorManagerConfig
from ..configs.models import SystevisorOutputConfig
from ..configs.models import SystevisorOutputMode
from ..core.effects import SystevisorApplyLiveConfigEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from .clocks import SystevisorClock
from .events import SystevisorEventBus


_SYSTEVISOR_LOGS_ANSI_ESCAPE_RE = re.compile(
    rb'(?:\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\))',
)
_SYSTEVISOR_LOGS_AUTO_FILE_RE = re.compile(
    r'^systevisor-child-[A-Za-z0-9_.:-]+-[0-9]+-(?:stdout|stderr)\.log(?:\.[1-9][0-9]*)?$',
)


class SystevisorLogStream(enum.Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'


@dc.dataclass(frozen=True)
class SystevisorLogRead:
    requested_offset: int
    start_offset: int
    end_offset: int
    data: bytes
    gap_bytes: int


@dc.dataclass(frozen=True)
class SystevisorLogChunkEvent:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    stream: SystevisorLogStream
    start_offset: int
    end_offset: int
    data: bytes


@dc.dataclass(frozen=True)
class SystevisorLogChannelInfo:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    stream: SystevisorLogStream
    start_offset: int
    end_offset: int
    retired: bool


@dc.dataclass(frozen=True)
class SystevisorLogChannelState:
    state_schema_version: int
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    stream: SystevisorLogStream
    config: SystevisorOutputConfig
    data: bytes
    end_offset: int
    retired: bool
    created_at: float
    last_activity_at: ta.Optional[float]


class SystevisorLogSubscription:
    def __init__(self, manager: 'SystevisorLogManager', subscription_id: int) -> None:
        self._manager = manager
        self._subscription_id = subscription_id
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            self._manager.unsubscribe(self._subscription_id)
            self._closed = True


class SystevisorByteRingBuffer:
    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError(capacity)
        self._capacity = capacity
        self._buffer = bytearray()
        self._end_offset = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def start_offset(self) -> int:
        return self._end_offset - len(self._buffer)

    @property
    def end_offset(self) -> int:
        return self._end_offset

    def append(self, data: bytes) -> ta.Tuple[int, int]:
        start_offset = self._end_offset
        self._end_offset += len(data)
        if self._capacity == 0:
            self._buffer.clear()
        elif len(data) >= self._capacity:
            self._buffer[:] = data[-self._capacity:]
        else:
            self._buffer.extend(data)
            excess = len(self._buffer) - self._capacity
            if excess > 0:
                del self._buffer[:excess]
        return start_offset, self._end_offset

    def resize(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError(capacity)
        self._capacity = capacity
        if capacity == 0:
            self._buffer.clear()
        elif len(self._buffer) > capacity:
            del self._buffer[:-capacity]

    def read(self, offset: int, max_bytes: ta.Optional[int] = None) -> SystevisorLogRead:
        if offset < 0:
            raise ValueError(offset)
        if max_bytes is not None and max_bytes < 0:
            raise ValueError(max_bytes)
        available_start = self.start_offset
        effective_start = min(max(offset, available_start), self._end_offset)
        gap_bytes = max(0, available_start - offset)
        index = effective_start - available_start
        data = bytes(self._buffer[index:])
        if max_bytes is not None:
            data = data[:max_bytes]
        return SystevisorLogRead(
            requested_offset=offset,
            start_offset=effective_start,
            end_offset=effective_start + len(data),
            data=data,
            gap_bytes=gap_bytes,
        )

    def snapshot(self) -> ta.Tuple[bytes, int]:
        return bytes(self._buffer), self._end_offset

    def rehydrate(self, data: bytes, end_offset: int) -> None:
        if self._end_offset or self._buffer:
            raise RuntimeError('ring buffer can only be rehydrated before use')
        if end_offset < len(data) or len(data) > self._capacity:
            raise ValueError('invalid ring buffer handoff state')
        self._buffer[:] = data
        self._end_offset = end_offset


class SystevisorLogSink(Abstract):
    @abc.abstractmethod
    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class SystevisorChildSyslogWriter(Abstract):
    @abc.abstractmethod
    def write(
            self,
            instance_id: SystevisorInstanceId,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            data: bytes,
    ) -> None:
        raise NotImplementedError


class SystevisorPosixChildSyslogWriter(SystevisorChildSyslogWriter):
    def write(
            self,
            instance_id: SystevisorInstanceId,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            data: bytes,
    ) -> None:
        priority = syslog.LOG_INFO if stream is SystevisorLogStream.STDOUT else syslog.LOG_ERR
        text = data.decode('utf-8', errors='replace').replace('\x00', r'\x00')
        syslog.syslog(priority, f'systevisor[{instance_id} run={int(run_id)} {stream.value}]: {text}')


class SystevisorSyslogLogSink(SystevisorLogSink):
    def __init__(
            self,
            writer: SystevisorChildSyslogWriter,
            instance_id: SystevisorInstanceId,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
    ) -> None:
        self._writer = writer
        self._instance_id = instance_id
        self._run_id = run_id
        self._stream = stream

    def write(self, data: bytes) -> None:
        self._writer.write(self._instance_id, self._run_id, self._stream, data)


class SystevisorFdLogSink(SystevisorLogSink):
    def __init__(self, fd: int) -> None:
        self._fd = fd

    def write(self, data: bytes) -> None:
        remaining = data
        while remaining:
            written = os.write(self._fd, remaining)
            remaining = remaining[written:]


class SystevisorRotatingFileLogSink(SystevisorLogSink):
    def __init__(self, config: SystevisorOutputConfig) -> None:
        if config.file is None:
            raise ValueError('file output requires a path')
        self._path = config.file
        self._append = config.append
        self._max_bytes = config.max_bytes
        self._backups = config.backups
        self._fd: ta.Optional[int] = None
        self._size = 0
        self._opened_once = False

    def _open(self) -> None:
        if self._fd is not None:
            return
        flags = os.O_CREAT | os.O_WRONLY
        if self._append or self._opened_once:
            flags |= os.O_APPEND
        else:
            flags |= os.O_TRUNC
        self._fd = os.open(self._path, flags, 0o644)
        self._size = os.fstat(self._fd).st_size
        self._opened_once = True

    def _rotate(self) -> None:
        self.close()
        if self._backups < 1:
            self._fd = os.open(self._path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            self._size = 0
            self._opened_once = True
            return
        last_path = f'{self._path}.{self._backups}'
        try:
            os.unlink(last_path)
        except FileNotFoundError:
            pass
        for index in range(self._backups - 1, 0, -1):
            source = f'{self._path}.{index}'
            destination = f'{self._path}.{index + 1}'
            try:
                os.replace(source, destination)
            except FileNotFoundError:
                pass
        try:
            os.replace(self._path, f'{self._path}.1')
        except FileNotFoundError:
            pass
        self._open()

    def write(self, data: bytes) -> None:
        self._open()
        if self._max_bytes > 0 and self._size > 0 and self._size + len(data) > self._max_bytes:
            self._rotate()
        if self._fd is None:
            raise RuntimeError('log sink failed to open')
        remaining = data
        while remaining:
            written = os.write(self._fd, remaining)
            remaining = remaining[written:]
            self._size += written

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


@dc.dataclass
class SystevisorLogChannel:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    stream: SystevisorLogStream
    config: SystevisorOutputConfig
    ring: SystevisorByteRingBuffer
    sinks: ta.List[SystevisorLogSink] = dc.field(default_factory=list)
    retired: bool = False
    created_at: float = 0.
    last_activity_at: ta.Optional[float] = None


class SystevisorProcessOutputFdioHandler(FdioHandler):
    def __init__(
            self,
            fd: int,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            callback: ta.Callable[[bytes], None],
    ) -> None:
        self._fd = fd
        self._run_id = run_id
        self._stream = stream
        self._callback = callback
        self._closed = False

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def run_id(self) -> SystevisorRunId:
        return self._run_id

    @property
    def stream(self) -> SystevisorLogStream:
        return self._stream

    def close(self) -> None:
        if not self._closed:
            os.close(self._fd)
            self._closed = True

    def readable(self) -> bool:
        return not self._closed

    def on_readable(self) -> None:
        while not self._closed:
            try:
                data = os.read(self._fd, 64 * 1024)
            except BlockingIOError:
                return
            if not data:
                self.close()
                return
            self._callback(data)

    def on_error(self, exc: ta.Optional[BaseException] = None) -> None:
        self.close()


class SystevisorLogManager:
    def __init__(
            self,
            event_bus: SystevisorEventBus,
            clock: SystevisorClock,
            syslog_writer: ta.Optional[SystevisorChildSyslogWriter] = None,
            *,
            default_strip_ansi: bool = False,
    ) -> None:
        self._event_bus = event_bus
        self._clock = clock
        self._syslog_writer = syslog_writer
        self._default_strip_ansi = default_strip_ansi
        self._child_log_directory: ta.Optional[str] = None
        self._channels: ta.Dict[ta.Tuple[SystevisorRunId, SystevisorLogStream], SystevisorLogChannel] = {}
        self._subscriptions: ta.Dict[
            int,
            ta.Tuple[
                ta.Optional[SystevisorRunId],
                ta.Optional[SystevisorLogStream],
                ta.Callable[[SystevisorLogChunkEvent], None],
            ],
        ] = {}
        self._next_subscription_id = 1

    def _make_sinks(
            self,
            run_id: SystevisorRunId,
            instance_id: SystevisorInstanceId,
            stream: SystevisorLogStream,
            config: SystevisorOutputConfig,
            *,
            reopen: bool = False,
    ) -> ta.List[SystevisorLogSink]:
        sinks: ta.List[SystevisorLogSink] = []
        if config.mode is SystevisorOutputMode.FILE:
            file = config.file
            if file is None:
                if self._child_log_directory is None:
                    raise ValueError('automatic file output requires a child log directory')
                file = os.path.join(
                    self._child_log_directory,
                    f'systevisor-child-{instance_id}-{int(run_id)}-{stream.value}.log',
                )
            sinks.append(SystevisorRotatingFileLogSink(dc.replace(
                config,
                file=file,
                append=True if reopen else config.append,
            )))
        elif config.mode is SystevisorOutputMode.STDOUT:
            sinks.append(SystevisorFdLogSink(1 if stream is SystevisorLogStream.STDOUT else 2))
        if config.syslog:
            if self._syslog_writer is None:
                raise RuntimeError('syslog output is not configured')
            sinks.append(SystevisorSyslogLogSink(self._syslog_writer, instance_id, run_id, stream))
        return sinks

    def configure_manager(self, config: SystevisorManagerConfig, *, cleanup: bool) -> None:
        directory = config.child_log_directory
        if directory is not None:
            os.makedirs(directory, mode=0o755, exist_ok=True)
            if not os.path.isdir(directory):
                raise NotADirectoryError(directory)
            directory = os.path.realpath(directory)
        if self._channels and directory != self._child_log_directory:
            raise RuntimeError('child log directory cannot change while log channels exist')
        self._child_log_directory = directory
        if cleanup and config.cleanup_auto_logs and directory is not None:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if _SYSTEVISOR_LOGS_AUTO_FILE_RE.fullmatch(entry.name) and entry.is_file(follow_symlinks=False):
                        os.unlink(entry.path)

    def set_default_strip_ansi(self, enabled: bool) -> None:
        self._default_strip_ansi = enabled

    def register_process(
            self,
            effect: SystevisorSpawnProcessEffect,
            stdout_fd: ta.Optional[int],
            stderr_fd: ta.Optional[int],
    ) -> ta.Sequence[SystevisorProcessOutputFdioHandler]:
        handlers: ta.List[SystevisorProcessOutputFdioHandler] = []
        for stream, output_config, fd in (
                (SystevisorLogStream.STDOUT, effect.spec.unit.stdio.stdout, stdout_fd),
                (SystevisorLogStream.STDERR, effect.spec.unit.stdio.stderr, stderr_fd),
        ):
            if fd is None:
                continue
            channel = SystevisorLogChannel(
                run_id=effect.run_id,
                instance_id=effect.instance_id,
                stream=stream,
                config=output_config,
                ring=SystevisorByteRingBuffer(output_config.back_buffer_bytes),
                sinks=self._make_sinks(effect.run_id, effect.instance_id, stream, output_config),
                created_at=self._clock.monotonic(),
            )
            self._channels[(effect.run_id, stream)] = channel
            def handle_data(
                    data: bytes,
                    run_id: SystevisorRunId = effect.run_id,
                    log_stream: SystevisorLogStream = stream,
            ) -> None:
                self.append(run_id, log_stream, data)

            handlers.append(SystevisorProcessOutputFdioHandler(fd, effect.run_id, stream, handle_data))
        return tuple(handlers)

    def attach_rehydrated_output(
            self,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            fd: int,
    ) -> SystevisorProcessOutputFdioHandler:
        if (run_id, stream) not in self._channels:
            raise RuntimeError(f'cannot attach output without a log channel: {run_id}:{stream.value}')

        def handle_data(data: bytes) -> None:
            self.append(run_id, stream, data)

        return SystevisorProcessOutputFdioHandler(fd, run_id, stream, handle_data)

    def append(self, run_id: SystevisorRunId, stream: SystevisorLogStream, data: bytes) -> None:
        channel = self._channels[(run_id, stream)]
        channel.last_activity_at = self._clock.monotonic()
        strip_ansi = channel.config.strip_ansi
        should_strip_ansi = strip_ansi if strip_ansi is not None else self._default_strip_ansi
        if should_strip_ansi:
            data = _SYSTEVISOR_LOGS_ANSI_ESCAPE_RE.sub(b'', data)
        start_offset, end_offset = channel.ring.append(data)

        retained_sinks: ta.List[SystevisorLogSink] = []
        for sink in channel.sinks:
            try:
                sink.write(data)
            except Exception as exc:  # noqa: BLE001
                sink.close()
                self._event_bus.publish('log.sink_error', {
                    'run_id': run_id,
                    'stream': stream.value,
                    'message': str(exc),
                }, self._clock.monotonic())
            else:
                retained_sinks.append(sink)
        channel.sinks = retained_sinks

        chunk_event = SystevisorLogChunkEvent(
            run_id=run_id,
            instance_id=channel.instance_id,
            stream=stream,
            start_offset=start_offset,
            end_offset=end_offset,
            data=data,
        )
        for subscription_id, (selected_run_id, selected_stream, callback) in tuple(self._subscriptions.items()):
            if selected_run_id is not None and selected_run_id != run_id:
                continue
            if selected_stream is not None and selected_stream is not stream:
                continue
            try:
                callback(chunk_event)
            except Exception as exc:  # noqa: BLE001
                self._subscriptions.pop(subscription_id, None)
                self._event_bus.publish('log.subscriber_error', {
                    'subscription_id': subscription_id,
                    'message': str(exc),
                }, self._clock.monotonic())

        if channel.config.emit_events:
            self._event_bus.publish('process.log', chunk_event, self._clock.monotonic())

    def subscribe(
            self,
            callback: ta.Callable[[SystevisorLogChunkEvent], None],
            *,
            run_id: ta.Optional[SystevisorRunId] = None,
            stream: ta.Optional[SystevisorLogStream] = None,
    ) -> SystevisorLogSubscription:
        subscription_id = self._next_subscription_id
        self._next_subscription_id += 1
        self._subscriptions[subscription_id] = (run_id, stream, callback)
        return SystevisorLogSubscription(self, subscription_id)

    def unsubscribe(self, subscription_id: int) -> None:
        self._subscriptions.pop(subscription_id, None)

    def channels(self) -> ta.Sequence[SystevisorLogChannelInfo]:
        return tuple(
            SystevisorLogChannelInfo(
                run_id=channel.run_id,
                instance_id=channel.instance_id,
                stream=channel.stream,
                start_offset=channel.ring.start_offset,
                end_offset=channel.ring.end_offset,
                retired=channel.retired,
            )
            for _, channel in sorted(
                self._channels.items(),
                key=lambda item: (item[0][0], item[0][1].value),
            )
        )

    def snapshot_states(self) -> ta.Sequence[SystevisorLogChannelState]:
        states: ta.List[SystevisorLogChannelState] = []
        for _, channel in sorted(
                self._channels.items(),
                key=lambda item: (item[0][0], item[0][1].value),
        ):
            data, end_offset = channel.ring.snapshot()
            states.append(SystevisorLogChannelState(
                state_schema_version=1,
                run_id=channel.run_id,
                instance_id=channel.instance_id,
                stream=channel.stream,
                config=channel.config,
                data=data,
                end_offset=end_offset,
                retired=channel.retired,
                created_at=channel.created_at,
                last_activity_at=channel.last_activity_at,
            ))
        return tuple(states)

    def rehydrate(self, states: ta.Iterable[SystevisorLogChannelState]) -> None:
        if self._channels or self._subscriptions:
            raise RuntimeError('log manager can only be rehydrated before use')
        for state in states:
            if state.state_schema_version != 1:
                raise ValueError(f'unsupported log channel schema: {state.state_schema_version}')
            key = (state.run_id, state.stream)
            if key in self._channels:
                raise ValueError(f'duplicate log channel: {state.run_id}:{state.stream.value}')
            ring = SystevisorByteRingBuffer(state.config.back_buffer_bytes)
            ring.rehydrate(state.data, state.end_offset)
            self._channels[key] = SystevisorLogChannel(
                run_id=state.run_id,
                instance_id=state.instance_id,
                stream=state.stream,
                config=state.config,
                ring=ring,
                sinks=self._make_sinks(
                    state.run_id,
                    state.instance_id,
                    state.stream,
                    state.config,
                    reopen=True,
                ),
                retired=state.retired,
                created_at=state.created_at,
                last_activity_at=state.last_activity_at,
            )

    def read(
            self,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            offset: int,
            max_bytes: ta.Optional[int] = None,
    ) -> SystevisorLogRead:
        return self._channels[(run_id, stream)].ring.read(offset, max_bytes)

    def last_activity_at(
            self,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
    ) -> ta.Optional[float]:
        channel = self._channels.get((run_id, stream))
        if channel is None:
            return None
        return channel.last_activity_at if channel.last_activity_at is not None else channel.created_at

    def update_process(self, effect: SystevisorApplyLiveConfigEffect) -> None:
        for stream, output_config in (
                (SystevisorLogStream.STDOUT, effect.spec.unit.stdio.stdout),
                (SystevisorLogStream.STDERR, effect.spec.unit.stdio.stderr),
        ):
            channel = self._channels.get((effect.run_id, stream))
            if channel is None or channel.config == output_config:
                continue
            channel.ring.resize(output_config.back_buffer_bytes)
            for sink in channel.sinks:
                sink.close()
            channel.sinks = self._make_sinks(effect.run_id, effect.instance_id, stream, output_config)
            channel.config = output_config

    def retire_process(self, run_id: SystevisorRunId) -> None:
        for (channel_run_id, _), channel in self._channels.items():
            if channel_run_id == run_id:
                channel.retired = True

    def close(self) -> None:
        self._subscriptions.clear()
        for channel in self._channels.values():
            for sink in channel.sinks:
                sink.close()
            channel.sinks.clear()
