"""
The wire protocol: everything the browser is shown, as a closed family of events. Each is marshaled as a json object
tagged by a snake-cased `type` field - `UserMessageFeedEvent` as `"type": "user_message"` - with unset fields omitted.

The events are deliberately close to what is displayed rather than to what happened: the browser folds them into its
view without knowing anything of agents or tools. Fields typed `WebText` carry `WebTextRenderer` output.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ..texts import WebText


##


def _feed_event_options(cls):
    return msh.update_object_options(
        field_defaults=msh.FieldOptions(omit_if=lang.is_none),
    )(cls)


@msh.set_polymorphic(
    type_tagging=msh.FieldTypeTagging('type'),
    naming='snake',
    suffix_stripping='required',
)
@dc.dataclass(frozen=True)
class FeedEvent(lang.Abstract, lang.Sealed):
    pass


##
# Submissions - one line of input from the user, and what came of it


SubmissionKind: ta.TypeAlias = ta.Literal['prompt', 'command']


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class SubmissionStartFeedEvent(FeedEvent):
    id: str
    kind: SubmissionKind
    text: str

    # Whether it holds the session for itself while it runs, as everything but a command allowed while busy does.
    exclusive: bool = True


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class SubmissionEndFeedEvent(FeedEvent):
    id: str

    # For a prompt, its run's end reason - `completed`, `cancelled`, ... - and for a command its result - `success` or
    # `failure`. Either may also end as `error`, having raised.
    status: str

    error: str | None = None


##
# Conversation


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class UserMessageFeedEvent(FeedEvent):
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class CommandEchoFeedEvent(FeedEvent):
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class RunStartFeedEvent(FeedEvent):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class RunEndFeedEvent(FeedEvent):
    # The run's `AgentEndReason`, lowercased.
    reason: str

    error: str | None = None


#


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class AiTextDeltaFeedEvent(FeedEvent):
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class AiTextEndFeedEvent(FeedEvent):
    # The block's whole text, which the deltas before it add up to.
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class AiTextFeedEvent(FeedEvent):
    """A whole block of model text at once - unstreamed output, or a transcript being replayed."""

    text: str


#


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ThinkingStartFeedEvent(FeedEvent):
    """The model has begun thinking - which some models do without a word of it reaching the deltas."""


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ThinkingDeltaFeedEvent(FeedEvent):
    text: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ThinkingEndFeedEvent(FeedEvent):
    text: str


##
# Tools


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ToolStartFeedEvent(FeedEvent):
    # Identifies the call's card for the events after this one.
    key: str

    name: str

    summary: WebText | None = None

    # The call's arguments, as json.
    args: ta.Any = None

    # The card of the call this one runs beneath - a subagent's call, beneath the call which spawned the subagent - and
    # what ran it there.
    parent: str | None = None
    via: str | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ToolOutputFeedEvent(FeedEvent):
    key: str
    text: str

    stream: str | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ToolEndFeedEvent(FeedEvent):
    key: str

    ok: bool

    # A line of facts about the result - an exit code, a subagent's run.
    note: str | None = None

    result: WebText | None = None

    # Whether the result is something the user should see without asking - a diff an edit made, say.
    show: bool | None = None


#


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class PermissionAskFeedEvent(FeedEvent):
    id: str

    # The card of the call asking, when there is one.
    key: str | None = None

    tool: str
    target: str
    rule: str

    preview: WebText | None = None


PermissionOutcome: ta.TypeAlias = ta.Literal['allow', 'deny', 'aborted']


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class PermissionAnswerFeedEvent(FeedEvent):
    id: str
    outcome: PermissionOutcome


##
# Status


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class UsageFeedEvent(FeedEvent):
    """The token usage of the turn just ended."""

    input: int = 0
    input_cached: int = 0
    input_cache_write: int = 0
    output: int = 0
    reasoning: int = 0


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ContextFeedEvent(FeedEvent):
    """How full the model's context window is."""

    input: int

    limit: int | None = None

    estimated: bool | None = None


##
# Everything else


NoticeLevel: ta.TypeAlias = ta.Literal['debug', 'info', 'warn', 'error']


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class NoticeFeedEvent(FeedEvent):
    """A word from the harness itself, rather than from the model or a command - a retry, say, or a run cut short."""

    text: str

    level: NoticeLevel = 'info'


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class TextFeedEvent(FeedEvent):
    """Text displayed through the `ui.TextDisplayer` - command output, in the main."""

    text: WebText


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@_feed_event_options
class ShutdownFeedEvent(FeedEvent):
    pass
