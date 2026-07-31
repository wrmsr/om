import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...types.context import Context
from ...types.messages import AiMessage
from ...types.options import Options


##


class BackendScriptError(Exception):
    pass


class BackendScriptExhaustedError(BackendScriptError):
    """Raised when a script has no turn available for an invocation."""


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class BackendScriptInvocation:
    invocation_index: int
    context: Context
    options: Options | None


BackendScriptTurnExpectation: ta.TypeAlias = ta.Callable[[BackendScriptInvocation], None]


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class BackendScriptGatePoint:
    """A point immediately before an event emission, plus one point after the final event."""

    invocation_index: int
    emission_index: int


BackendScriptGate: ta.TypeAlias = ta.Callable[[BackendScriptGatePoint], ta.Awaitable[None]]


##


DEFAULT_SCRIPT_CHUNK_SIZE: int = 8


def split_script_text(s: str, chunk_size: int | None) -> ta.Sequence[str]:
    if not s:
        return ()
    if chunk_size is None or chunk_size <= 0 or chunk_size >= len(s):
        return (s,)
    return tuple(s[i:i + chunk_size] for i in range(0, len(s), chunk_size))


##


@ta.final
@dc.dataclass(frozen=True)
class BackendScriptTurn:
    message: AiMessage | None = None

    _: dc.KW_ONLY

    error: BaseException | None = dc.field(default=None, repr=False)

    chunk_size: int | None = DEFAULT_SCRIPT_CHUNK_SIZE

    expect: BackendScriptTurnExpectation | None = dc.field(default=None, repr=False)

    def __post_init__(self) -> None:
        check.arg((self.message is None) != (self.error is None))


@ta.final
@dc.dataclass(frozen=True)
class BackendScript:
    turns: ta.Sequence[BackendScriptTurn]

    _: dc.KW_ONLY

    on_exhausted: ta.Literal['raise', 'repeat_last', 'restart'] = 'raise'

    gate: BackendScriptGate | None = dc.field(default=None, repr=False)


##


class BackendScriptCursor:
    """Mutable consumption state over an immutable script."""

    def __init__(self, script: BackendScript) -> None:
        super().__init__()

        self._script = script
        self._next = 0

    @property
    def script(self) -> BackendScript:
        return self._script

    def next_turn(self) -> BackendScriptTurn:
        turns = self._script.turns

        if (i := self._next) < len(turns):
            self._next = i + 1
            return turns[i]

        if not turns:
            raise BackendScriptExhaustedError

        match self._script.on_exhausted:
            case 'raise':
                raise BackendScriptExhaustedError

            case 'repeat_last':
                return turns[-1]

            case 'restart':
                self._next = 1
                return turns[0]

            case _:
                raise ValueError(self._script.on_exhausted)
