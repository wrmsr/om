"""
Qwen3.5's chat format, rendered and parsed by hand (no Jinja): the parts of the checkpoint's chat template that an
OpenAI-style tool-calling loop exercises.

Rendering follows the template: an optional system message; with `tools`, the `# Tools` block with each function schema
as JSON inside `<tools>` and the `<tool_call>` instructions, all inside the system turn; user turns; assistant turns
with `<think>` reasoning, content and `<tool_call>` JSON blocks; tool results as `<tool_response>` blocks grouped into
one user turn; then the generation prompt, with an empty think block when thinking is off.

One deliberate deviation, on by default (`preserve_thinking`): the stock template strips the reasoning of every
assistant turn before the last user query, which rewrites the rendered history on every turn and defeats an exact-prefix
cache. Keeping every turn's reasoning (ninfer's `--preserve-thinking`) leaves the prefix stable;
`preserve_thinking=False` reproduces the template's behaviour.

Parsing turns generated text back into OpenAI shapes: `<think>...</think>` -> reasoning_content, `<tool_call>` JSON
blocks -> tool_calls, the rest -> content. `StreamParser` does the same incrementally for streaming.
"""
import json
import re
import typing as ta

from omcore import dataclasses as dc


##


TOOLS_PREAMBLE = (
    '# Tools\n\n'
    'You may call one or more functions to assist with the user query.\n\n'
    'You are provided with function signatures within <tools></tools> XML tags:\n<tools>'
)

TOOLS_POSTAMBLE = (
    '\n</tools>\n\n'
    'For each function call, return a json object with function name and arguments within '
    '<tool_call></tool_call> XML tags:\n<tool_call>\n'
    '{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call>'
)


def _tojson(x: ta.Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def _split_think(content: str) -> tuple[str, str]:
    """('reasoning', 'content') from an assistant message body that may carry a <think> block."""

    if '</think>' not in content:
        return '', content
    head = content.split('</think>', maxsplit=1)[0]
    reasoning = head.rstrip('\n').split('<think>')[-1].lstrip('\n')
    rest = content.rsplit('</think>', maxsplit=1)[-1].lstrip('\n')
    return reasoning, rest


def render_chat(
        messages: ta.Sequence[dict],
        tools: ta.Sequence[dict] | None = None,
        add_generation_prompt: bool = True,
        enable_thinking: bool = True,
        preserve_thinking: bool = True,
) -> str:
    """The prompt string for an OpenAI-style message list (roles system / user / assistant / tool)."""

    out: list[str] = []
    msgs = list(messages)
    if tools:
        out.append('<|im_start|>system\n')
        if msgs and msgs[0].get('role') == 'system':
            out.append(str(msgs[0].get('content') or '') + '\n\n')
        out.append(TOOLS_PREAMBLE)
        for t in tools:
            out.append('\n' + _tojson(t))
        out.append(TOOLS_POSTAMBLE + '<|im_end|>\n')
    elif msgs and msgs[0].get('role') == 'system':
        out.append('<|im_start|>system\n' + str(msgs[0].get('content') or '') + '<|im_end|>\n')

    # the template keeps reasoning only for assistant turns after the last real user query (tool responses do
    # not count); with preserve_thinking every assistant turn keeps it
    last_query = len(msgs) - 1
    for i in range(len(msgs) - 1, -1, -1):
        m = msgs[i]
        c = m.get('content')
        if m.get('role') == 'user' and isinstance(c, str) and not (
            c.startswith('<tool_response>') and c.endswith('</tool_response>')
        ):
            last_query = i
            break

    for i, m in enumerate(msgs):
        role = m.get('role')
        content = m.get('content')
        if not isinstance(content, str):
            content = '' if content is None else ''.join(
                p.get('text', '') for p in content if isinstance(p, dict) and p.get('type') == 'text'
            )
        if role == 'user' or (role == 'system' and i > 0):
            out.append(f'<|im_start|>{role}\n{content}<|im_end|>\n')
        elif role == 'assistant':
            keep = preserve_thinking or i > last_query
            last = i == len(msgs) - 1
            out.append(render_assistant_turn(m, with_reasoning=keep and (last or preserve_thinking or None)))
        elif role == 'tool':
            if i == 0 or msgs[i - 1].get('role') != 'tool':
                out.append('<|im_start|>user')
            out.append('\n<tool_response>\n' + content + '\n</tool_response>')
            if i == len(msgs) - 1 or msgs[i + 1].get('role') != 'tool':
                out.append('<|im_end|>\n')
    if add_generation_prompt:
        out.append('<|im_start|>assistant\n')
        if not enable_thinking:
            out.append('<think>\n\n</think>\n\n')
    return ''.join(out)


def render_assistant_turn(m: dict, with_reasoning: bool | None = True) -> str:
    """
    One assistant turn, `<|im_start|>assistant\n` through `<|im_end|>\n`. with_reasoning True renders the think block
    (empty if the message has none), False omits it, None renders it only if there is reasoning (the template's rule for
    non-final turns after the last query).
    """

    content = m.get('content')
    if not isinstance(content, str):
        content = '' if content is None else ''.join(
            p.get('text', '') for p in content if isinstance(p, dict) and p.get('type') == 'text'
        )
    reasoning = m.get('reasoning_content')
    if not isinstance(reasoning, str):
        reasoning, content = _split_think(content)
    out: list[str] = []
    if with_reasoning or (with_reasoning is None and reasoning):
        r = reasoning.strip('\n')
        c = content.lstrip('\n')
        out.append(f'<|im_start|>assistant\n<think>\n{r}\n</think>\n\n{c}')
    else:
        out.append(f'<|im_start|>assistant\n{content}')
    for j, tc in enumerate(m.get('tool_calls') or []):
        if (j == 0 and content) or j > 0:
            out.append('\n')
        fn = tc.get('function', tc)
        args = fn.get('arguments')
        if not isinstance(args, str):
            args = _tojson(args)
        out.append('<tool_call>\n{"name": "' + str(fn.get('name')) + '", "arguments": ' + args + '}\n</tool_call>')
    out.append('<|im_end|>\n')
    return ''.join(out)


##


_TOOL_CALL_RE = re.compile(r'<tool_call>\s*(.*?)\s*</tool_call>', re.DOTALL)
_THINK_RE = re.compile(r'<think>(.*?)</think>', re.DOTALL)


@dc.dataclass()
class Parsed:
    content: str
    reasoning: str | None
    tool_calls: list[dict]  # OpenAI shape: {id, type: 'function', function: {name, arguments (JSON string)}}


def _tool_call_obj(raw: str, idx: int) -> dict | None:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or 'name' not in obj:
        return None
    args = obj.get('arguments', {})
    return {
        'id': f'call_{idx}',
        'type': 'function',
        'function': {'name': str(obj['name']), 'arguments': args if isinstance(args, str) else _tojson(args)},
    }


def parse_output(text: str) -> Parsed:
    """Split a finished completion into reasoning, tool calls and content."""

    reasoning = None
    m = _THINK_RE.search(text)
    if m:
        reasoning = m.group(1).strip('\n')
        text = text[:m.start()] + text[m.end():]
    calls: list[dict] = []
    for i, mt in enumerate(_TOOL_CALL_RE.finditer(text)):
        tc = _tool_call_obj(mt.group(1), i)
        if tc is not None:
            calls.append(tc)
    content = _TOOL_CALL_RE.sub('', text).strip('\n')
    return Parsed(content, reasoning, calls)


class StreamParser:
    """
    Incremental version of parse_output for streaming: feed decoded text, get back deltas of ('reasoning', str),
    ('content', str) or ('tool_call', dict) as soon as they are unambiguous. Text that may be the start of a tag
    is held back until it is either a tag or clearly not.
    """

    TAGS = ('<think>', '</think>', '<tool_call>', '</tool_call>')

    def __init__(self) -> None:
        self.buf = ''
        self.in_think = False
        self.in_call = False
        self.n_calls = 0
        self.skip_nl = False  # drop the newlines the format puts right after <think> and </think>

    def feed(self, text: str) -> list[tuple[str, ta.Any]]:
        self.buf += text
        return self._drain(final=False)

    def finish(self) -> list[tuple[str, ta.Any]]:
        out = self._drain(final=True)
        if self.buf:
            out.append(('reasoning' if self.in_think else 'content', self.buf))
            self.buf = ''
        return out

    def _drain(self, final: bool) -> list[tuple[str, ta.Any]]:
        out: list[tuple[str, ta.Any]] = []
        while self.buf:
            if self.skip_nl:
                stripped = self.buf.lstrip('\n')
                if not stripped and not final:
                    self.buf = ''
                    return out
                if stripped != self.buf or stripped:
                    self.buf = stripped
                    if stripped:
                        self.skip_nl = False
                if not self.buf:
                    return out
            if self.in_call:
                end = self.buf.find('</tool_call>')
                if end < 0:
                    return out
                tc = _tool_call_obj(self.buf[:end].strip(), self.n_calls)
                if tc is not None:
                    out.append(('tool_call', tc))
                    self.n_calls += 1
                self.buf = self.buf[end + len('</tool_call>'):]
                self.in_call = False
                continue
            lt = self.buf.find('<')
            if lt < 0:
                out.append(('reasoning' if self.in_think else 'content', self.buf))
                self.buf = ''
                return out
            if lt > 0:
                out.append(('reasoning' if self.in_think else 'content', self.buf[:lt]))
                self.buf = self.buf[lt:]
            tag = next((t for t in self.TAGS if self.buf.startswith(t)), None)
            if tag is None:
                if not final and any(t.startswith(self.buf[:len(t)]) for t in self.TAGS):
                    return out  # could still become a tag
                out.append(('reasoning' if self.in_think else 'content', self.buf[:1]))
                self.buf = self.buf[1:]
                continue
            self.buf = self.buf[len(tag):]
            if tag == '<think>':
                self.in_think = True
                self.skip_nl = True
            elif tag == '</think>':
                self.in_think = False
                self.skip_nl = True
            elif tag == '<tool_call>':
                self.in_call = True
            # a stray '</tool_call>' outside a call is dropped
        return out
