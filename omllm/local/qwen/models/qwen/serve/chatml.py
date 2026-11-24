"""
The Qwen checkpoints' chat formats (chat.py: ChatML turns, `<think>` blocks, `<tool_call>` in either call syntax) as
a chat protocol.
"""
import typing as ta

from ....constrain.grammar import JsonConstraint
from ....constrain.grammar import ToolConstraint
from ....constrain.grammar import response_format_schema
from ....serve.protocols import ChatEvent
from ....serve.protocols import ChatProtocol
from ....serve.protocols import ChatReader
from ....serve.protocols import Parsed
from ....tokenizer import Tokenizer
from .chat import ChatFormat
from .chat import StreamParser
from .chat import chat_format_for
from .chat import parse_output
from .chat import render_assistant_turn
from .chat import render_chat
from .templates import DEFAULT_REASONING_EFFORT
from .templates import REASONING_EFFORT_INSTRUCTIONS
from .templates import reasoning_instruction
from .templates import takes_reasoning_effort


##


# OpenAI's names for reasoning efforts the checkpoint's template (tokenizer.py) does not have, as the nearest it does
REASONING_EFFORT_ALIASES: ta.Mapping[str, str] = {
    'minimal': 'low',
    'high': 'xhigh',
    'max': 'xhigh',
}


def reasoning_effort_of(value: ta.Any) -> tuple[str | None, bool | None]:
    """
    A request's `reasoning_effort` as (the template's level or None, whether it settles thinking or None): the
    template's own levels as they are, OpenAI's other names as the nearest of them, 'none' as thinking off. Anything
    else is the client's mistake.
    """

    if value is None:
        return None, None
    v = str(value).lower()
    if v == 'none':
        return None, False
    v = REASONING_EFFORT_ALIASES.get(v, v)
    if v not in REASONING_EFFORT_INSTRUCTIONS:
        raise ValueError(
            f'reasoning_effort must be one of {", ".join(REASONING_EFFORT_INSTRUCTIONS)} '
            f'(or none, {", ".join(REASONING_EFFORT_ALIASES)}): {value!r}',
        )
    return v, None


class _ChatmlReader(ChatReader):
    def __init__(self, parser: StreamParser, parse: ta.Callable[[str], Parsed]) -> None:
        super().__init__()

        self._parser = parser
        self._parse = parse

    def feed(self, text: str) -> list[ChatEvent]:
        return self._parser.feed(text)

    def finish(self) -> list[ChatEvent]:
        return self._parser.finish()

    def parsed(self, text: str) -> Parsed:
        return self._parse(text)  # (the finished text read whole, as it always was: `parse_output`)


class ChatmlProtocol(ChatProtocol):
    def __init__(
            self,
            tok: Tokenizer,
            *,
            chat_format: ChatFormat | None = None,
            open_think: bool | None = None,
            preserve_thinking: bool = True,
            reasoning_effort: str | None = None,
    ) -> None:
        """
        `chat_format`: the format requests are rendered in, tool calls constrained to and answers parsed from
        (chat.py's `ChatFormat`); None is the checkpoint's own, as its chat template shows it (`chat_format_for`) --
        the legacy format for a checkpoint without one.

        `reasoning_effort`: the level a request that names none is rendered at, for a checkpoint whose chat template
        takes one (`takes_reasoning_effort`); None is the template's own default, its highest.

        `open_think`: with thinking on, the generation prompt ends with the opened reasoning block (`render_chat`) and
        the answer is read as starting inside it; None is as the chat format has it.

        `preserve_thinking`: reasoning is kept in every rendered assistant turn, which keeps the rendered history --
        and an exact-prefix cache -- stable; False renders it the stock template's way.
        """

        super().__init__()

        reasoning_instruction(tok, reasoning_effort)  # (raises on a level the template does not have)

        self._tok = tok
        self._format = chat_format if chat_format is not None else chat_format_for(tok)
        self._open_think = self._format.open_think if open_think is None else open_think
        self._preserve_thinking = preserve_thinking
        self._reasoning_effort = reasoning_effort

        self._im_end = tok.special.get('<|im_end|>')
        self._eos = frozenset(
            i
            for i in (
                tok.eos_id,
                self._im_end,
                tok.special.get('<|endoftext|>'),
            )
            if i is not None
        )

    @property
    def name(self) -> str:
        return self._format.name

    @property
    def format(self) -> ChatFormat:
        return self._format

    @property
    def open_think(self) -> bool:
        return self._open_think

    @property
    def eos_ids(self) -> ta.AbstractSet[int]:
        return self._eos

    def reasoning_effort(self, value: ta.Any) -> tuple[ta.Any, bool | None]:
        return reasoning_effort_of(value)

    def _opened(self, enable_thinking: bool) -> bool:
        """Whether the prompt ends inside the reasoning block."""

        return self._open_think and enable_thinking

    # prompts

    def render(
            self,
            messages: ta.Sequence[dict],
            tools: ta.Sequence[dict] | None = None,
            *,
            enable_thinking: bool = True,
            reasoning_effort: ta.Any = None,
            continuation: bool = False,
    ) -> str:
        instruction: str | None = None
        if not continuation:
            instruction = reasoning_instruction(self._tok, reasoning_effort or self._reasoning_effort, enable_thinking)

        return render_chat(
            messages,
            tools,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
            preserve_thinking=self._preserve_thinking,
            reasoning_instruction=instruction,
            open_think=self._open_think,
            fmt=self._format,
        )

    def encode(self, text: str) -> list[int]:
        return self._tok.encode(text)

    def generation_prompt(self, rendered: str) -> str:
        return rendered[rendered.rfind('<|im_start|>assistant'):]

    def answer_prefix(self, *, enable_thinking: bool = True) -> str:
        return '<think>\n' if self._opened(enable_thinking) else ''

    # answers

    def reader(self, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> ChatReader:
        return _ChatmlReader(
            StreamParser(self._opened(enable_thinking), self._format, tools),
            lambda text: self.parse(text, tools, enable_thinking=enable_thinking),
        )

    def parse(self, text: str, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> Parsed:
        return parse_output(text, think_open=self._opened(enable_thinking), fmt=self._format, tools=tools)

    def constraint(
            self,
            tools: ta.Sequence[dict] | None,
            tool_choice: ta.Any,
            response_format: ta.Any,
            *,
            enable_thinking: bool = True,
    ) -> ta.Any:
        """
        Tools present: every tool call the model opens is grammar-constrained to the declared schemas, in the call
        syntax of the chat format, and tool_choice 'none' / 'required' / a named function forbids or forces one
        (constrain/grammar.py). Without tools, response_format json_object / json_schema constrains the content to
        one JSON value instead.
        """

        opened = self._opened(enable_thinking)

        if tools:
            return ToolConstraint(
                self._tok,
                tools,
                tool_choice or 'auto',
                thinking=enable_thinking,
                think_open=opened,
                syntax=self._format.call_syntax,
            )

        schema = response_format_schema(response_format)
        if schema is not None:
            return JsonConstraint(self._tok, schema, thinking=enable_thinking, think_open=opened)

        return None

    def check(self, tools: ta.Sequence[dict] | None, tool_choice: ta.Any, response_format: ta.Any) -> None:
        pass  # (every request has its grammar: `constraint`)

    # the conversation continued

    def answer_segment(self, msg: dict) -> str:
        # (as `render_chat` will render this turn when it comes back: with its reasoning block, which in the newer
        # formats is there even when empty)
        always = self._preserve_thinking or self._format.empty_think
        return render_assistant_turn(msg, with_reasoning=True if always else None, fmt=self._format)

    def close_answer(self, out_ids: ta.Sequence[int]) -> list[int]:
        ids = list(out_ids)
        if self._im_end is not None and (not ids or ids[-1] != self._im_end):
            ids.append(self._im_end)
        ids.extend(self._tok.encode('\n'))
        return ids

    def describe(self) -> dict[str, ta.Any]:
        effort = self._reasoning_effort or (DEFAULT_REASONING_EFFORT if takes_reasoning_effort(self._tok) else None)
        return {
            'chat_format': self._format.name,
            'open_think': self._open_think,
            'reasoning_effort': effort,
        }
