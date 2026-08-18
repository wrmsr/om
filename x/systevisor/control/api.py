# ruff: noqa: UP006 UP007 UP045
import abc
import base64
import dataclasses as dc
import typing as ta
import urllib.parse

from omcore.lite.abstract import Abstract
from omcore.logs.modules import get_module_logger

from ..core.identities import SystevisorRunId
from ..runtime.events import SystevisorBusEvent
from ..runtime.events import SystevisorEventBus
from ..runtime.events import SystevisorEventSubscription
from ..runtime.logs import SystevisorLogChunkEvent
from ..runtime.logs import SystevisorLogManager
from ..runtime.logs import SystevisorLogStream
from ..runtime.logs import SystevisorLogSubscription
from .configs import SystevisorConfigController
from .jsoncodec import SystevisorJsonCodec
from .operations import SystevisorOperationStatus
from .service import SystevisorControlService


_SYSTEVISOR_API_LOG = get_module_logger(globals())


@dc.dataclass(frozen=True)
class SystevisorApiRequest:
    method: str
    target: str
    headers: ta.Mapping[str, str] = dc.field(default_factory=dict)
    body: bytes = b''


@dc.dataclass(frozen=True)
class SystevisorApiResponse:
    status: int
    body: bytes
    content_type: str = 'application/json; charset=utf-8'
    headers: ta.Mapping[str, str] = dc.field(default_factory=dict)


class SystevisorApiStreamSubscription(Abstract):
    @abc.abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class SystevisorApiStream(Abstract):
    content_type: str = 'application/x-ndjson; charset=utf-8'

    @abc.abstractmethod
    def initial(self) -> ta.Sequence[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def subscribe(self, callback: ta.Callable[[bytes], None]) -> SystevisorApiStreamSubscription:
        raise NotImplementedError

    @abc.abstractmethod
    def gap(self, dropped_items: int, dropped_bytes: int) -> bytes:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class SystevisorApiStreamResponse:
    status: int
    stream: SystevisorApiStream
    headers: ta.Mapping[str, str] = dc.field(default_factory=dict)


SystevisorApiResult = ta.Union[SystevisorApiResponse, SystevisorApiStreamResponse]


class SystevisorApiError(Exception):
    def __init__(self, status: int, error_type: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.error_type = error_type
        self.message = message


class SystevisorEventApiStreamSubscription(SystevisorApiStreamSubscription):
    def __init__(self, subscription: SystevisorEventSubscription) -> None:
        self._subscription = subscription

    def close(self) -> None:
        self._subscription.close()


class SystevisorEventApiStream(SystevisorApiStream):
    def __init__(
            self,
            event_bus: SystevisorEventBus,
            json_codec: SystevisorJsonCodec,
            after_sequence: int,
            topics: ta.AbstractSet[str],
    ) -> None:
        self._event_bus = event_bus
        self._json_codec = json_codec
        self._after_sequence = after_sequence
        self._topics = frozenset(topics)

    def _matches(self, event: SystevisorBusEvent) -> bool:
        return not self._topics or event.topic in self._topics

    def _encode(self, event: SystevisorBusEvent) -> bytes:
        return self._json_codec.dump_line(event)

    def initial(self) -> ta.Sequence[bytes]:
        return tuple(
            self._encode(event)
            for event in self._event_bus.journal(self._after_sequence)
            if self._matches(event)
        )

    def subscribe(self, callback: ta.Callable[[bytes], None]) -> SystevisorApiStreamSubscription:
        def on_event(event: SystevisorBusEvent) -> None:
            if event.sequence > self._after_sequence and self._matches(event):
                callback(self._encode(event))

        return SystevisorEventApiStreamSubscription(self._event_bus.subscribe_callback(on_event))

    def gap(self, dropped_items: int, dropped_bytes: int) -> bytes:
        return self._json_codec.dump_line({
            'type': 'stream_gap',
            'dropped_items': dropped_items,
            'dropped_bytes': dropped_bytes,
        })


class SystevisorLogApiStreamSubscription(SystevisorApiStreamSubscription):
    def __init__(self, subscription: SystevisorLogSubscription) -> None:
        self._subscription = subscription

    def close(self) -> None:
        self._subscription.close()


class SystevisorLogApiStream(SystevisorApiStream):
    def __init__(
            self,
            log_manager: SystevisorLogManager,
            json_codec: SystevisorJsonCodec,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            offset: int,
            max_bytes: ta.Optional[int],
    ) -> None:
        self._log_manager = log_manager
        self._json_codec = json_codec
        self._run_id = run_id
        self._stream = stream
        self._offset = offset
        self._max_bytes = max_bytes

    def _encode_chunk(
            self,
            start_offset: int,
            end_offset: int,
            data: bytes,
            *,
            gap_bytes: int = 0,
    ) -> bytes:
        return self._json_codec.dump_line({
            'type': 'log',
            'run_id': self._run_id,
            'stream': self._stream.value,
            'start_offset': start_offset,
            'end_offset': end_offset,
            'gap_bytes': gap_bytes,
            'data_base64': base64.b64encode(data).decode('ascii'),
        })

    def initial(self) -> ta.Sequence[bytes]:
        read = self._log_manager.read(self._run_id, self._stream, self._offset, self._max_bytes)
        if not read.data and not read.gap_bytes:
            return ()
        return (self._encode_chunk(
            read.start_offset,
            read.end_offset,
            read.data,
            gap_bytes=read.gap_bytes,
        ),)

    def subscribe(self, callback: ta.Callable[[bytes], None]) -> SystevisorApiStreamSubscription:
        def on_chunk(chunk: SystevisorLogChunkEvent) -> None:
            callback(self._encode_chunk(chunk.start_offset, chunk.end_offset, chunk.data))

        return SystevisorLogApiStreamSubscription(self._log_manager.subscribe(
            on_chunk,
            run_id=self._run_id,
            stream=self._stream,
        ))

    def gap(self, dropped_items: int, dropped_bytes: int) -> bytes:
        return self._json_codec.dump_line({
            'type': 'stream_gap',
            'run_id': self._run_id,
            'stream': self._stream.value,
            'dropped_items': dropped_items,
            'dropped_bytes': dropped_bytes,
        })


class SystevisorApiApplication:
    def __init__(
            self,
            control: SystevisorControlService,
            config_controller: SystevisorConfigController,
            event_bus: SystevisorEventBus,
            log_manager: SystevisorLogManager,
            json_codec: SystevisorJsonCodec,
    ) -> None:
        self._control = control
        self._config_controller = config_controller
        self._event_bus = event_bus
        self._log_manager = log_manager
        self._json_codec = json_codec

    def _json_response(self, value: ta.Any, status: int = 200) -> SystevisorApiResponse:
        return SystevisorApiResponse(status=status, body=self._json_codec.dumps(value))

    def _error_response(self, error: SystevisorApiError) -> SystevisorApiResponse:
        return self._json_response({
            'status': error.status,
            'error': {
                'type': error.error_type,
                'message': error.message,
            },
        }, error.status)

    @staticmethod
    def _query_int(
            query: ta.Mapping[str, ta.Sequence[str]],
            name: str,
            default: ta.Optional[int] = None,
    ) -> ta.Optional[int]:
        values = query.get(name)
        if not values:
            return default
        try:
            value = int(values[-1])
        except ValueError as exc:
            raise SystevisorApiError(400, 'invalid_parameter', f'{name} must be an integer') from exc
        if value < 0:
            raise SystevisorApiError(400, 'invalid_parameter', f'{name} must be non-negative')
        return value

    @staticmethod
    def _query_bool(
            query: ta.Mapping[str, ta.Sequence[str]],
            name: str,
            default: bool = False,
    ) -> bool:
        values = query.get(name)
        if not values:
            return default
        value = values[-1].lower()
        if value in ('1', 'true', 'yes'):
            return True
        if value in ('0', 'false', 'no'):
            return False
        raise SystevisorApiError(400, 'invalid_parameter', f'{name} must be a boolean')

    def _handle_events(
            self,
            query: ta.Mapping[str, ta.Sequence[str]],
    ) -> SystevisorApiResult:
        after_sequence = ta.cast(int, self._query_int(query, 'after', 0))
        topics = frozenset(query.get('topic', ()))
        stream = SystevisorEventApiStream(self._event_bus, self._json_codec, after_sequence, topics)
        if self._query_bool(query, 'follow'):
            return SystevisorApiStreamResponse(status=200, stream=stream)
        return SystevisorApiResponse(
            status=200,
            body=b''.join(stream.initial()),
            content_type=stream.content_type,
        )

    def _handle_logs(
            self,
            segments: ta.Sequence[str],
            query: ta.Mapping[str, ta.Sequence[str]],
    ) -> SystevisorApiResult:
        if len(segments) != 4:
            raise SystevisorApiError(404, 'not_found', 'log channel not found')
        try:
            run_id = SystevisorRunId(int(segments[2]))
        except ValueError as exc:
            raise SystevisorApiError(400, 'invalid_run_id', 'run id must be an integer') from exc
        try:
            stream_name = SystevisorLogStream(segments[3])
        except ValueError as exc:
            raise SystevisorApiError(400, 'invalid_log_stream', 'log stream must be stdout or stderr') from exc
        offset = ta.cast(int, self._query_int(query, 'offset', 0))
        limit = self._query_int(query, 'limit', 64 * 1024)
        if limit is not None and limit > 8 * 1024 * 1024:
            raise SystevisorApiError(400, 'invalid_parameter', 'limit may not exceed 8388608')
        log_stream = SystevisorLogApiStream(
            self._log_manager,
            self._json_codec,
            run_id,
            stream_name,
            offset,
            limit,
        )
        try:
            initial = log_stream.initial()
        except KeyError as exc:
            raise SystevisorApiError(404, 'log_not_found', 'log channel not found') from exc
        if self._query_bool(query, 'follow'):
            return SystevisorApiStreamResponse(status=200, stream=log_stream)
        return SystevisorApiResponse(
            status=200,
            body=b''.join(initial),
            content_type=log_stream.content_type,
        )

    def _dispatch(self, request: SystevisorApiRequest) -> SystevisorApiResult:
        parsed = urllib.parse.urlsplit(request.target)
        segments = tuple(urllib.parse.unquote(part) for part in parsed.path.split('/') if part)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        method = request.method.upper()

        if method == 'GET' and not segments:
            state = self._control.coordinator.engine.state
            return self._json_response({
                'name': 'systevisor',
                'api_version': 1,
                'config_generation': state.config_generation,
                'shutting_down': state.shutting_down,
            })
        if method == 'GET' and segments == ('v1', 'state'):
            return self._json_response(self._control.coordinator.engine.state)
        if method == 'GET' and segments == ('v1', 'units'):
            state = self._control.coordinator.engine.state
            return self._json_response({'instances': tuple(state.instances.values())})
        if method == 'GET' and segments == ('v1', 'collections'):
            state = self._control.coordinator.engine.state
            return self._json_response({'collections': tuple(state.collections.values())})
        if method == 'GET' and segments == ('v1', 'operations'):
            operations = self._control.operations.list()
            requested_statuses = frozenset(query.get('status', ()))
            if requested_statuses:
                operations = tuple(op for op in operations if op.status.value in requested_statuses)
            return self._json_response({'operations': operations})
        if method == 'GET' and len(segments) == 3 and segments[:2] == ('v1', 'operations'):
            operation = self._control.operations.get(segments[2])
            if operation is None:
                raise SystevisorApiError(404, 'operation_not_found', 'operation not found')
            return self._json_response(operation)
        if method == 'GET' and segments == ('v1', 'config'):
            snapshot = self._config_controller.active_snapshot
            return self._json_response({
                'active': snapshot,
                'last_attempt': self._config_controller.last_attempt,
                'paths': self._config_controller.paths,
                'recursive': self._config_controller.recursive,
            })
        if method == 'GET' and segments == ('v1', 'events'):
            return self._handle_events(query)
        if method == 'GET' and segments == ('v1', 'logs'):
            return self._json_response({'channels': self._log_manager.channels()})
        if method == 'GET' and len(segments) >= 2 and segments[:2] == ('v1', 'logs'):
            return self._handle_logs(segments, query)

        operation = None
        if method == 'POST' and segments == ('v1', 'config', '_check'):
            operation = self._control.check_config()
        elif method == 'POST' and segments == ('v1', 'config', '_reload'):
            operation = self._control.reload_config()
        elif method == 'POST' and segments == ('v1', '_shutdown'):
            operation = self._control.shutdown()
        elif method == 'POST' and len(segments) == 4 and segments[:2] == ('v1', 'units'):
            if segments[3] not in ('_start', '_stop'):
                raise SystevisorApiError(404, 'not_found', 'route not found')
            operation = self._control.set_unit(segments[2], segments[3] == '_start')
        elif method == 'POST' and len(segments) == 4 and segments[:2] == ('v1', 'collections'):
            if segments[3] not in ('_start', '_stop'):
                raise SystevisorApiError(404, 'not_found', 'route not found')
            operation = self._control.set_collection(segments[2], segments[3] == '_start')
        elif method == 'POST' and len(segments) == 4 and segments[:2] == ('v1', 'instances'):
            if segments[3] == '_restart':
                operation = self._control.restart_instance(segments[2])
            elif segments[3] in ('_start', '_stop'):
                operation = self._control.set_instance(segments[2], segments[3] == '_start')
            else:
                raise SystevisorApiError(404, 'not_found', 'route not found')
        if operation is not None:
            status = 202 if operation.status is SystevisorOperationStatus.PENDING else 200
            return self._json_response({'operation': operation}, status)

        if method not in ('GET', 'POST'):
            raise SystevisorApiError(405, 'method_not_allowed', 'method not allowed')
        raise SystevisorApiError(404, 'not_found', 'route not found')

    def handle(self, request: SystevisorApiRequest) -> SystevisorApiResult:
        try:
            if request.body:
                body = self._json_codec.loads(request.body)
                if body is not None and not isinstance(body, dict):
                    raise SystevisorApiError(400, 'invalid_body', 'request JSON body must be an object')
            return self._dispatch(request)
        except SystevisorApiError as error:
            return self._error_response(error)
        except (UnicodeDecodeError, ValueError) as exc:
            return self._error_response(SystevisorApiError(400, 'invalid_request', str(exc)))
        except Exception:  # noqa: BLE001
            _SYSTEVISOR_API_LOG.exception('Unhandled Systevisor API request failure for %s', request.target)
            return self._error_response(SystevisorApiError(
                500,
                'internal_error',
                'internal server error',
            ))
