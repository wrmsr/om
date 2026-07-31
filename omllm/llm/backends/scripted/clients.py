import abc
import io
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json
from omcore.http import all as http

from .caching import PromptCacheSimulator
from .http import CanScriptedHttpTurn
from .http import RecordedHttpRequest
from .http import ScriptedHttpError
from .http import ScriptedHttpException
from .http import ScriptedHttpGate
from .http import ScriptedHttpGatePoint
from .http import ScriptedHttpRawResponse
from .http import ScriptedHttpResponse
from .http import ScriptedHttpTurn
from .http import ScriptedHttpValidationError
from .http import ScriptedRenderedHttpResponse
from .http import ScriptedUsage


##


class _ScriptedBytesReader:
    def __init__(
            self,
            data: bytes,
            *,
            invocation_index: int,
            chunk_size: int,
            gate: ScriptedHttpGate | None,
    ) -> None:
        super().__init__()

        self._reader = io.BytesIO(data)
        self._invocation_index = invocation_index
        self._chunk_size = chunk_size
        self._gate = gate

        self._chunk_index = 0
        self._finished = False

    async def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True

        if self._gate is not None:
            await self._gate(ScriptedHttpGatePoint(
                invocation_index=self._invocation_index,
                chunk_index=self._chunk_index,
            ))

    async def read1(self, n: int = -1, /) -> lang.Bytes:
        if n == 0:
            return b''

        remaining = len(self._reader.getbuffer()) - self._reader.tell()
        if remaining <= 0:
            await self._finish()
            return b''

        if self._gate is not None:
            await self._gate(ScriptedHttpGatePoint(
                invocation_index=self._invocation_index,
                chunk_index=self._chunk_index,
            ))

        read_size = remaining
        if self._chunk_size > 0:
            read_size = min(read_size, self._chunk_size)
        if n >= 0:
            read_size = min(read_size, n)

        data = self._reader.read1(read_size)
        self._chunk_index += 1
        return data

    async def read(self, n: int = -1, /) -> lang.Bytes:
        if n == 0:
            return b''

        chunks: list[bytes] = []
        remaining = n

        while remaining != 0:
            chunk = await self.read1(remaining)
            if not chunk:
                break
            chunks.append(bytes(chunk))
            if remaining > 0:
                remaining -= len(chunk)

        return b''.join(chunks)


##


class BaseScriptedHttpClient(http.AsyncHttpClient, lang.Abstract):
    def __init__(
            self,
            responses: ta.Iterable[CanScriptedHttpTurn] = (),
            *,
            require_auth: bool = True,
            byte_chunk_size: int = 17,
            simulate_cache: bool = False,
            gate: ScriptedHttpGate | None = None,
    ) -> None:
        super().__init__()

        self._responses = [self._coerce_turn(response) for response in responses]
        self._require_auth = require_auth
        self._byte_chunk_size = byte_chunk_size
        self._simulate_cache = simulate_cache
        self._gate = gate

        self._cache_simulator = PromptCacheSimulator()

        self._requests: list[RecordedHttpRequest] = []
        self._invocations = 0
        self._response_counter = 0

    @staticmethod
    def _coerce_turn(response: CanScriptedHttpTurn) -> ScriptedHttpTurn:
        if isinstance(response, ScriptedHttpTurn):
            return response
        return ScriptedHttpTurn(result=response)

    @property
    def requests(self) -> ta.Sequence[RecordedHttpRequest]:
        return tuple(self._requests)

    def clear_requests(self) -> None:
        self._requests.clear()

    def clear_cache(self) -> None:
        self._cache_simulator.clear()

    def set_responses(self, responses: ta.Iterable[CanScriptedHttpTurn]) -> None:
        self._responses = [self._coerce_turn(response) for response in responses]

    def append_responses(self, *responses: CanScriptedHttpTurn) -> None:
        self._responses.extend(self._coerce_turn(response) for response in responses)

    def pending_response_count(self) -> int:
        return len(self._responses)

    @abc.abstractmethod
    def _validate_request(
            self,
            request: http.HttpClientRequest,
            headers: http.HttpHeaders,
            payload: ta.Mapping[str, ta.Any],
    ) -> ScriptedHttpValidationError | None:
        raise NotImplementedError

    @abc.abstractmethod
    def _render_error(
            self,
            *,
            status: int,
            error_type: str,
            message: str,
    ) -> ScriptedRenderedHttpResponse:
        raise NotImplementedError

    @abc.abstractmethod
    def _render_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        raise NotImplementedError

    def _cache_key_and_prompt(self, request: RecordedHttpRequest) -> tuple[str | None, str]:
        return None, ''

    def _make_response(
            self,
            request: http.HttpClientRequest,
            rendered: ScriptedRenderedHttpResponse,
            *,
            invocation_index: int,
            use_gate: bool = True,
    ) -> http.AsyncStreamHttpClientResponse:
        if isinstance(body := rendered.body, str):
            body = body.encode('utf-8')

        byte_chunk_size = rendered.byte_chunk_size
        if byte_chunk_size is None:
            byte_chunk_size = self._byte_chunk_size

        return http.AsyncStreamHttpClientResponse(
            request=request,
            status=rendered.status,
            headers=http.HttpHeaders.of(rendered.headers),
            _stream=_ScriptedBytesReader(
                body,
                invocation_index=invocation_index,
                chunk_size=byte_chunk_size,
                gate=self._gate if use_gate else None,
            ),
        )

    def _make_validation_error_response(
            self,
            request: http.HttpClientRequest,
            error: ScriptedHttpValidationError,
    ) -> http.AsyncStreamHttpClientResponse:
        return self._make_response(
            request,
            self._render_error(
                status=error.status,
                error_type=error.error_type,
                message=error.message,
            ),
            invocation_index=self._invocations,
            use_gate=False,
        )

    def _resolve_usage(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
    ) -> ScriptedUsage | None:
        usage = response.usage
        if not self._simulate_cache:
            return usage

        cache_key, prompt = self._cache_key_and_prompt(request)
        simulated = self._cache_simulator.check(cache_key, prompt)
        return dc.replace(
            usage if usage is not None else ScriptedUsage(),
            uncached_input_tokens=simulated.uncached_input_tokens,
            cache_read_tokens=simulated.cache_read_tokens,
            cache_write_tokens=simulated.cache_write_tokens,
        )

    async def _stream_request(
            self,
            ctx: http.HttpClientContext,
            req: http.HttpClientRequest,
    ) -> http.AsyncStreamHttpClientResponse:
        if req.method_or_default.upper() != 'POST':
            return self._make_validation_error_response(req, ScriptedHttpValidationError(
                status=405,
                error_type='invalid_request_error',
                message='scripted endpoints require POST',
            ))

        headers = http.HttpHeaders.of(req.headers)
        if 'application/json' not in headers.single.get('content-type', ''):
            return self._make_validation_error_response(req, ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing application/json content-type',
            ))

        try:
            body = req.data.decode('utf-8') if isinstance(req.data, bytes) else req.data
            payload = check.isinstance(json.loads(body or ''), ta.Mapping)
        except (UnicodeDecodeError, json.DecodeError, TypeError, ValueError):
            return self._make_validation_error_response(req, ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='invalid JSON body',
            ))

        if (error := self._validate_request(req, headers, payload)) is not None:
            return self._make_validation_error_response(req, error)

        invocation_index = self._invocations
        self._invocations += 1

        recorded = RecordedHttpRequest(
            invocation_index=invocation_index,
            url=req.url,
            headers=headers,
            payload=payload,
            request=req,
        )
        self._requests.append(recorded)

        if not self._responses:
            return self._make_response(
                req,
                self._render_error(
                    status=500,
                    error_type='scripted_error',
                    message='no scripted responses remaining',
                ),
                invocation_index=invocation_index,
            )

        turn = self._responses.pop(0)
        if turn.expect is not None:
            turn.expect(recorded)

        result = turn.result

        if isinstance(result, ScriptedHttpException):
            raise result.error

        if isinstance(result, ScriptedHttpError):
            if result.body is not None:
                rendered = ScriptedRenderedHttpResponse(
                    status=result.status,
                    headers={'content-type': 'application/json'},
                    body=result.body,
                )
            else:
                rendered = self._render_error(
                    status=result.status,
                    error_type=result.error_type,
                    message=result.message,
                )
            return self._make_response(
                req,
                rendered,
                invocation_index=invocation_index,
            )

        if isinstance(result, ScriptedHttpRawResponse):
            return self._make_response(
                req,
                ScriptedRenderedHttpResponse(
                    status=result.status,
                    headers=result.headers,
                    body=result.body,
                    byte_chunk_size=result.byte_chunk_size,
                ),
                invocation_index=invocation_index,
            )

        if not isinstance(result, ScriptedHttpResponse):
            raise TypeError(result)

        self._response_counter += 1
        rendered = self._render_response(
            recorded,
            result,
            self._resolve_usage(recorded, result),
            self._response_counter,
        )
        return self._make_response(
            req,
            rendered,
            invocation_index=invocation_index,
        )
