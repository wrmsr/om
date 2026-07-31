import typing as ta

from omcore import dataclasses as dc
from omcore.http import all as http

from ...types.content import TextContent
from ...types.content import ThinkingContent
from ...types.content import ToolCall
from ...types.messages import StopReason


##


type ScriptedHttpContent = TextContent | ThinkingContent | ToolCall


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedUsage:
    uncached_input_tokens: int = 10
    output_tokens: int = 5
    reasoning_tokens: int | None = None

    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    total_tokens: int | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpResponse:
    content: ta.Sequence[ScriptedHttpContent] = ()

    stop_reason: StopReason | None = None
    usage: ScriptedUsage | None = dc.field(default_factory=ScriptedUsage)

    response_id: str | None = None
    model: str | None = None

    chunk_chars: int = 7

    def resolved_stop_reason(self) -> StopReason:
        if self.stop_reason is not None:
            return self.stop_reason
        if any(isinstance(content, ToolCall) for content in self.content):
            return 'tool_use'
        return 'stop'


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpError:
    status: int = 500
    error_type: str = 'scripted_error'
    message: str = 'scripted error'
    body: bytes | str | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpRawResponse:
    body: bytes | str

    status: int = 200
    headers: http.CanHttpHeaders | None = None
    byte_chunk_size: int | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpException:
    error: BaseException


type ScriptedHttpResult = (
    ScriptedHttpResponse |
    ScriptedHttpError |
    ScriptedHttpRawResponse |
    ScriptedHttpException
)


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class RecordedHttpRequest:
    invocation_index: int

    url: str
    headers: http.HttpHeaders
    payload: ta.Mapping[str, ta.Any]

    request: http.HttpClientRequest = dc.field(repr=False)


ScriptedHttpExpectation: ta.TypeAlias = ta.Callable[[RecordedHttpRequest], None]


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpTurn:
    result: ScriptedHttpResult
    expect: ScriptedHttpExpectation | None = dc.field(default=None, repr=False)


type CanScriptedHttpTurn = ScriptedHttpResult | ScriptedHttpTurn


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpGatePoint:
    """A point before a response byte chunk, plus one point after the final chunk."""

    invocation_index: int
    chunk_index: int


ScriptedHttpGate: ta.TypeAlias = ta.Callable[[ScriptedHttpGatePoint], ta.Awaitable[None]]


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedHttpValidationError:
    status: int
    error_type: str
    message: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScriptedRenderedHttpResponse:
    body: bytes | str

    status: int = 200
    headers: http.CanHttpHeaders | None = None
    byte_chunk_size: int | None = None
