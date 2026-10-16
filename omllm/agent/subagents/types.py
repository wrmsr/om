"""
The seam between the subagent tool and whatever actually stands a subagent up: the tool asks a `SubagentRunner` to run
one, and gets back what it said. How the subagent is built - by hand, or as an injector scope of its own - is the
runner's business. The parameters are explicit fields, deliberately: each new thing a subagent needs from its parent is
added here, in the open, rather than reached for through a context object.
"""
import abc
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import typedvalues as tv

from ..types.lifecycle import UsageLedger
from ..types.messages import Message
from ..types.progress import ToolProgressSink
from ..types.tools import ToolEnvironment
from ..types.turns import AgentEndReason
from .profiles import SubagentProfile


##


class SubagentRunId(tv.UniqueScalarTypedValue[uuid.UUID], final=True):
    def __post_init__(self) -> None:
        check.isinstance(self.v, uuid.UUID)


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SubagentRunParams:
    profile: SubagentProfile

    prompt: str

    # The parent's tool environment: the subagent works in the same place, in a process scope of its own under the
    # parent's.
    env: ToolEnvironment | None = None

    # Where the subagent's events go, wrapped, for whoever is watching the parent. None when nobody is.
    progress: ToolProgressSink | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SubagentRunResult:
    run_id: SubagentRunId

    # The text of the subagent's final message, or empty where it had none.
    text: str

    reason: AgentEndReason = AgentEndReason.COMPLETED
    error: BaseException | None = None

    usage: UsageLedger | None = None

    # LLM calls made.
    num_turns: int = 0

    # The subagent's whole transcript, the prompt included. For display only.
    messages: ta.Sequence[Message] = ()


##


class SubagentRunner(lang.Abstract):
    @abc.abstractmethod
    def run_subagent(self, params: SubagentRunParams) -> ta.Awaitable[SubagentRunResult]:
        """
        Runs a subagent on the prompt to its end, and returns what came of it. Like a turn, every outcome the subagent
        decides for itself - a failure included - is reported through the result; only the caller's own cancellation
        raises out.
        """

        raise NotImplementedError
