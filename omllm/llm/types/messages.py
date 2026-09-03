# ruff: noqa: UP007
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from .content import TextContent
from .content import TextContentBuilder
from .content import ThinkingContent
from .content import ThinkingContentBuilder
from .content import ToolCall
from .content import ToolCallBuilder


MessageT = ta.TypeVar('MessageT', bound='Message')


##


@dc.dataclass(frozen=True)
@msh.set_polymorphic(naming='snake', suffix_stripping='required')
class Message(lang.Abstract, lang.Sealed):
    pass


class MessageBuilder(lang.Abstract, ta.Generic[MessageT]):
    @abc.abstractmethod
    def build(self) -> MessageT:
        raise NotImplementedError


##


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
class UserMessage(Message):
    content: str | TextContent


@ta.final
class UserMessageBuilder(MessageBuilder[UserMessage]):
    def __init__(self) -> None:
        super().__init__()

        self.content: str | TextContent = ''

    def build(self) -> UserMessage:
        return UserMessage(
            content=self.content,
        )


##


type StopReason = ta.Literal[
    'stop',
    'length',
    'tool_use',
    'error',
]


#


type TokenCostSource = ta.Literal[
    # Billed figures reported by the provider in the response itself.
    'reported',

    # Figures computed locally from static rates (USD per million tokens, the models.dev convention).
    'estimated',
]


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True, default_repr_fn=lang.truthy_repr)
@msh.update_field_options(omit_if=lang.is_none)
class TokenCost:
    """
    A single request's cost in absolute USD (amounts, not rates), broken down mirroring TokenUsage's token counts
    with the same inclusive/overlapping semantics. As with token counts, providers report or imply varying subsets -
    a gross total without a breakdown is better than nothing at all.
    """

    source: TokenCostSource

    # Inclusive prompt-side cost. Cache reads and writes are overlapping details within this value.
    input: float | None = None

    # Inclusive completion-side cost. Reasoning is an overlapping detail within this value.
    output: float | None = None

    # Reasoning cost, when known. This is already included in output.
    reasoning: float | None = None

    # Cost of input tokens read from a prompt cache, when known. This is already included in input.
    cache_read: float | None = None

    # Cost of input tokens written to a prompt cache, when known. This is already included in input.
    cache_write: float | None = None

    # The billed total when reported, or the sum of the inclusive components when estimated.
    total: float | None = None


#


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True, default_repr_fn=lang.truthy_repr)
@msh.update_field_options(omit_if=lang.is_none)
class TokenUsage:
    # Inclusive input total. Cache reads and writes are overlapping details within this value.
    input: int | None = None

    # Inclusive billed output total. Reasoning is an overlapping detail within this value.
    output: int | None = None

    # Billed reasoning output, when reported by the provider. This is already included in output.
    reasoning: int | None = None

    # Input tokens read from a prompt cache. This is already included in input.
    cache_read: int | None = None

    # Input tokens written to a prompt cache. This is already included in input.
    cache_write: int | None = None

    # The provider's authoritative total, or input + output when the provider does not report one.
    total: int | None = None

    # This request's cost, when reported by the provider or computed from static rates.
    cost: TokenCost | None = None


#


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True, default_repr_fn=lang.opt_repr)
class AiMessage(Message):
    content: ta.Sequence[ta.Union[
        TextContent,
        ThinkingContent,
        ToolCall,
    ]]

    stop_reason: StopReason | None = None

    token_usage: TokenUsage | None = None


@ta.final
class AiMessageBuilder(MessageBuilder[AiMessage]):
    def __init__(self) -> None:
        super().__init__()

        self.content: list[ta.Union[
            TextContentBuilder,
            ThinkingContentBuilder,
            ToolCallBuilder,
        ]] = []
        self.stop_reason: StopReason | None = None
        self.token_usage: TokenUsage | None = None

    def build(self) -> AiMessage:
        return AiMessage(
            content=[cb.build() for cb in self.content],
            stop_reason=self.stop_reason,
            token_usage=self.token_usage,
        )


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
class ToolResultMessage(Message):
    tool_call_id: str
    tool_name: str

    content: ta.Sequence[TextContent] = ()

    # Whether the content describes a failure rather than a result. Providers which distinguish the two are told so;
    # for the rest the content alone has to say.
    is_error: bool = False
