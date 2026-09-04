import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from ...core.eventbus import EventSubscriber
from .contexts import Context
from .inboxes import TurnInbox
from .messages import Message


if ta.TYPE_CHECKING:
    from .events import Event
    from .states import State


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class LlmRetryConfig:
    """Exponential backoff for LLM calls which fail transiently. Being present at all is what enables retries."""

    max_retries: int = 3

    initial_delay_s: float = 1.
    max_delay_s: float = 30.
    multiplier: float = 2.

    def delay_s(self, attempts: int, *, retry_after_s: float | None = None) -> float:
        """The delay before the next attempt, given the number made so far. A provider's own asked-for delay wins."""

        delay = min(self.initial_delay_s * (self.multiplier ** max(attempts - 1, 0)), self.max_delay_s)
        if retry_after_s is not None:
            delay = max(delay, retry_after_s)
        return delay


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnConfig:
    llm_options: llm.Options | None = None

    # The most LLM calls one prompt may make. Reaching it with tool calls still pending leaves them unexecuted and ends
    # the run with AgentEndReason.MAX_TURNS. None is unbounded.
    max_turns: int | None = None

    # When present, LLM calls failing with llm.TransientBackendError are retried with backoff. Absent, they fail the
    # run.
    llm_retry: LlmRetryConfig | None = None

    max_concurrent_tool_calls: int | None = dc.xfield(None, validate=lambda v: v != 0)

    # How long the run's terminal publish may take. It is shielded, so a cancellation landing in it waits for every
    # subscriber; past this it is cut short instead, and the run finishes without the subscribers still in it. None is
    # unbounded.
    cancel_timeout_s: float | None = dc.xfield(None, validate=lambda v: v is None or v > 0)

    # Whether steering which arrives mid-batch cuts the batch short: the tool calls not yet executed get an error result
    # saying the user interjected, and the model sees the steering right away. For there to be calls not yet executed,
    # this runs a message's tool calls one at a time. Off, they run concurrently and the batch finishes first.
    steering_skips_pending_tool_calls: bool = False


##


class AgentEndReason(enum.Enum):
    # The model ended its turn on its own.
    COMPLETED = enum.auto()

    # The model's output was cut off by a token limit. Any tool calls in it were not executed.
    LENGTH = enum.auto()

    # The configured turn limit was reached with tool calls still pending. They were not executed.
    MAX_TURNS = enum.auto()

    # An LLM call, or the loop itself, raised. The transcript up to the failure is kept.
    FAILED = enum.auto()

    # The run's task was cancelled. The transcript up to the cancellation is kept.
    CANCELLED = enum.auto()


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnParams:
    in_state: State
    new_messages: ta.Sequence[Message]

    subscriber: EventSubscriber[Event] | None = None

    inbox: TurnInbox | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnResult:
    config: TurnConfig
    context: Context

    # Everything the run appended, the prompt included, in order.
    new_messages: ta.Sequence[Message] = ()

    reason: AgentEndReason = AgentEndReason.COMPLETED
    error: BaseException | None = None


##


class TurnRunner(lang.Abstract):
    @abc.abstractmethod
    def run_turn(self, params: TurnParams) -> ta.Awaitable[TurnResult]:
        """
        Runs one prompt to its end. Returns for every outcome the loop itself decides - including a failure, which is
        reported through the result's reason and error rather than raised - and raises only when the run's own task is
        cancelled, or on a non-Exception BaseException.
        """

        raise NotImplementedError
