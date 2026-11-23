"""
A chat protocol: how a checkpoint's conversations are written and read -- the prompt a list of messages renders to,
where a turn ends, how the generated text divides into reasoning, content and tool calls, and what a grammar may hold
a tool call or a JSON answer to. The serving engine (serving.py) is written against this; a family of checkpoints
supplies one: Qwen's ChatML formats (chatml.py over chat.py), Inkling 2's framed messages (inkling2.py). Which one a
checkpoint speaks is seen from its tokenizer (registry.py).
"""
import abc
import typing as ta

from omcore import lang

from .chat import Parsed


ChatEvent: ta.TypeAlias = tuple[str, ta.Any]  # ('reasoning' | 'content', text) or ('tool_call', OpenAI delta)


##


class ChatReader(lang.Abstract):
    """
    One answer read as it is generated: fed decoded text, it hands back deltas -- ('reasoning', str), ('content', str),
    or ('tool_call', dict): a call's id and name with empty arguments as soon as the name is known, then pieces of the
    arguments' JSON text (the OpenAI delta shape: clients concatenate them). Text that may be the start of a marker
    is held back until it is one or clearly is not.
    """

    @abc.abstractmethod
    def feed(self, text: str) -> list[ChatEvent]:
        raise NotImplementedError

    @abc.abstractmethod
    def finish(self) -> list[ChatEvent]:
        raise NotImplementedError


class ChatProtocol(lang.Abstract):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def eos_ids(self) -> ta.AbstractSet[int]:
        """The tokens that end a turn: generation stops at one, and it is not part of the answer's text."""

        raise NotImplementedError

    @abc.abstractmethod
    def reasoning_effort(self, value: ta.Any) -> tuple[ta.Any, bool | None]:
        """
        A request's `reasoning_effort` as (the level `render` takes or None for the default, whether it settles
        thinking or None). Raises ValueError for a value the protocol has no reading of.
        """

        raise NotImplementedError

    # prompts

    @abc.abstractmethod
    def render(
            self,
            messages: ta.Sequence[dict],
            tools: ta.Sequence[dict] | None = None,
            *,
            enable_thinking: bool = True,
            reasoning_effort: ta.Any = None,
            continuation: bool = False,
    ) -> str:
        """
        The prompt for an OpenAI-style message list (roles system / user / assistant / tool), up to where the model
        answers. `continuation`: the messages go on a conversation already rendered -- no preamble of the
        conversation's own (the reasoning-effort instruction, the tools) is written again.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def generation_prompt(self, rendered: str) -> str:
        """The tail of a rendered prompt that already belongs to the answer's turn (its opening), '' when none does."""

        raise NotImplementedError

    @abc.abstractmethod
    def answer_prefix(self, *, enable_thinking: bool = True) -> str:
        """What of the answer the prompt has written already, so the generation continues it ('' for nothing)."""

        raise NotImplementedError

    # answers

    @abc.abstractmethod
    def reader(self, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> ChatReader:
        raise NotImplementedError

    @abc.abstractmethod
    def parse(self, text: str, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> Parsed:
        """A finished answer's text (the end-of-turn token not in it) as reasoning, content and tool calls."""

        raise NotImplementedError

    @abc.abstractmethod
    def constraint(
            self,
            tools: ta.Sequence[dict] | None,
            tool_choice: ta.Any,
            response_format: ta.Any,
            *,
            enable_thinking: bool = True,
    ) -> ta.Any:
        """
        The grammar a request's answer is decoded under (a constrain.grammar constraint), or None: tool calls held to
        the declared schemas and `tool_choice`, or the content to a JSON value (`response_format`).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def check(self, tools: ta.Sequence[dict] | None, tool_choice: ta.Any, response_format: ta.Any) -> None:
        """
        Raises ValueError for what the protocol cannot hold a generation to (a forced call, JSON mode, where it has
        no grammar for them): asked before a request is queued, so the client is told rather than served without it.
        """

        raise NotImplementedError

    # the conversation continued: what keeps a later request's ids an extension of this one's

    @abc.abstractmethod
    def answer_segment(self, msg: dict) -> str:
        """How an assistant message renders when it comes back in a later request's history, whole."""

        raise NotImplementedError

    @abc.abstractmethod
    def close_answer(self, out_ids: ta.Sequence[int]) -> list[int]:
        """A generated answer's ids, ended as a turn is ended inside a rendered conversation."""

        raise NotImplementedError

    @abc.abstractmethod
    def describe(self) -> dict[str, ta.Any]:
        """How requests are rendered, for the log and /health."""

        raise NotImplementedError
