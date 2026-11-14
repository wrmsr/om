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

That paragraph describes the *legacy* format (`LEGACY`), which is what a checkpoint without a chat template gets. The
checkpoints served here carry templates that say otherwise, and `ChatFormat` is what this module (and the tool grammar)
needs to know of them: `QWEN35` and `QWEN38` describe tools under another preamble with the system message after it,
have the model call them as

    <tool_call>
    <function=name>
    <parameter=key>
    value
    </parameter>
    </function>
    </tool_call>

(a string's value as it is, anything else as JSON), put a reasoning block in the assistant turns that keep their
reasoning even when it is empty, and open the block in the generation prompt. They were established by rendering the
templates as black boxes over many conversations (`tests/chat_oracle.py`, which is also their test); nothing here is
derived from a template's source.
"""
import json
import re
import typing as ta

from omcore import dataclasses as dc

from ..constrain.schemas import schema_only_text
from ..constrain.schemas import schema_takes_text
from ..tokenizer import Tokenizer


##


THINK_OPEN = '<think>\n'  # what a generation prompt ends with when it opens the reasoning block itself


@dc.dataclass(frozen=True)
class ChatFormat:
    """What differs between the chat formats the checkpoints were trained on, as far as rendering and parsing go."""

    name: str

    # how a tool call is written: 'json' -- {"name": ..., "arguments": {...}} -- or 'function' -- <function=name> with
    # one <parameter=key> block per argument
    call_syntax: str = 'json'

    # with thinking on, the generation prompt ends with the opened reasoning block
    open_think: bool = False

    # an assistant turn that keeps its reasoning has the block even when the reasoning is empty (and every turn after
    # the last user query keeps it); False: such a turn has the block only if it has reasoning
    empty_think: bool = False

    # a boolean or null argument is spelled True / False / None when a call is rendered (qwen3.5's template does;
    # either spelling is read back, and the grammar allows the model both)
    python_literals: bool = False


LEGACY = ChatFormat('legacy')
QWEN35 = ChatFormat('qwen3.5', call_syntax='function', open_think=True, empty_think=True, python_literals=True)
QWEN38 = ChatFormat('qwen3.8', call_syntax='function', open_think=True, empty_think=True)

CHAT_FORMATS: ta.Mapping[str, ChatFormat] = {f.name: f for f in (LEGACY, QWEN35, QWEN38)}


def chat_format_for(tok: Tokenizer) -> ChatFormat:
    """
    The format of a checkpoint, from what its chat template is seen to contain: the function-call syntax marks the
    newer formats, and the reasoning-effort switch (`Tokenizer.reasoning_efforts`) qwen3.8's among them. A checkpoint
    without a template gets the legacy format. `tests/chat_oracle.py` says whether the choice renders as the template
    does.
    """

    template = tok.chat_template or ''
    if '<function=' not in template:
        return LEGACY
    return QWEN38 if tok.reasoning_efforts else QWEN35


TOOLS_PREAMBLE = (
    '# Tools\n'
    '\n'
    'You may call one or more functions to assist with the user query.\n'
    '\n'
    'You are provided with function signatures within <tools></tools> XML tags:\n'
    '<tools>'
)

TOOLS_POSTAMBLE = (
    '\n'
    '</tools>\n'
    '\n'
    'For each function call, return a json object with function name and arguments within '
    '<tool_call></tool_call> XML tags:\n'
    '<tool_call>\n'
    '{"name": <function-name>, "arguments": <args-json-object>}\n'
    '</tool_call>'
)


FUNCTION_TOOLS_PREAMBLE = (
    '# Tools\n'
    '\n'
    'You have access to the following functions:\n'
    '\n'
    '<tools>'
)

FUNCTION_TOOLS_POSTAMBLE = (
    '\n'
    '</tools>\n'
    '\n'
    'If you choose to call a function ONLY reply in the following format with NO suffix:\n'
    '\n'
    '<tool_call>\n'
    '<function=example_function_name>\n'
    '<parameter=example_parameter_1>\n'
    'value_1\n'
    '</parameter>\n'
    '<parameter=example_parameter_2>\n'
    'This is the value for the second parameter\n'
    'that can span\n'
    'multiple lines\n'
    '</parameter>\n'
    '</function>\n'
    '</tool_call>\n'
    '\n'
    '<IMPORTANT>\n'
    'Reminder:\n'
    '- Function calls MUST follow the specified format: an inner <function=...></function> block must be nested within '
    '<tool_call></tool_call> XML tags\n'
    '- Required parameters MUST be specified\n'
    '- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT '
    'after\n'
    '- If there is no function call available, answer the question like normal with your current knowledge and do not '
    'tell the user about function calls\n'
    '</IMPORTANT>'
)


def _tojson(x: ta.Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def _text_of(content: ta.Any) -> str:
    """A message's content as text: a string, or the text parts of a list of parts."""

    if isinstance(content, str):
        return content
    if content is None:
        return ''
    return ''.join(
        p.get('text', '')
        for p in content
        if isinstance(p, dict)
        and p.get('type') == 'text'
    )


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
        reasoning_instruction: str | None = None,
        open_think: bool | None = None,
        fmt: ChatFormat = LEGACY,
) -> str:
    """
    The prompt string for an OpenAI-style message list (roles system / user / assistant / tool), in the checkpoint's
    format (`fmt`).
    `reasoning_instruction`: the checkpoint's instruction for the request's reasoning effort
    (`Tokenizer.reasoning_instruction`), which opens the system turn -- a system turn of its own when there would be
    none. `open_think`: with thinking on, end the generation prompt with the opened reasoning block (`THINK_OPEN`), as
    the checkpoints' own templates do: the model then continues inside it, where otherwise it opens the block itself
    -- or does not. None: as the format has it. Whoever reads the generation must know it started there
    (`parse_output` / `StreamParser` / the constraints take the same flag).
    """

    if open_think is None:
        open_think = fmt.open_think

    out: list[str] = []
    msgs = list(messages)

    system: list[str] = []
    if reasoning_instruction:
        system.append(reasoning_instruction)
    own = [_text_of(msgs[0].get('content'))] if msgs and msgs[0].get('role') == 'system' else []
    if fmt.call_syntax == 'function':  # the tools first, the system message after them
        if tools:
            system.append(
                FUNCTION_TOOLS_PREAMBLE + ''.join('\n' + _tojson(t) for t in tools) + FUNCTION_TOOLS_POSTAMBLE,
            )
        system.extend(own)
    else:
        system.extend(own)
        if tools:
            system.append(TOOLS_PREAMBLE + ''.join('\n' + _tojson(t) for t in tools) + TOOLS_POSTAMBLE)
    if system:
        out.append('<|im_start|>system\n' + '\n\n'.join(system) + '<|im_end|>\n')

    # the template keeps reasoning only for assistant turns after the last real user query (tool responses do not
    # count); with preserve_thinking every assistant turn keeps it
    last_query = len(msgs) - 1
    for i in range(len(msgs) - 1, -1, -1):
        m = msgs[i]
        c = m.get('content')
        if (
                m.get('role') == 'user' and
                isinstance(c, str) and
                not (c.startswith('<tool_response>') and c.endswith('</tool_response>'))
        ):
            last_query = i
            break

    for i, m in enumerate(msgs):
        role = m.get('role')

        content = m.get('content')
        if not isinstance(content, str):
            content = '' if content is None else ''.join(
                p.get('text', '')
                for p in content
                if isinstance(p, dict)
                and p.get('type') == 'text'
            )

        if role == 'user' or (role == 'system' and i > 0):
            out.append(f'<|im_start|>{role}\n{content}<|im_end|>\n')

        elif role == 'assistant':
            keep = preserve_thinking or i > last_query
            last = i == len(msgs) - 1
            always = last or preserve_thinking or fmt.empty_think
            out.append(render_assistant_turn(m, with_reasoning=keep and (always or None), fmt=fmt))

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
        elif open_think:
            out.append(THINK_OPEN)

    return ''.join(out)


def _arguments(fn: dict) -> dict:
    """A tool call's arguments as a mapping (OpenAI clients send them as JSON text)."""

    args = fn.get('arguments')
    if isinstance(args, str):
        try:
            args = json.loads(args) if args.strip() else {}
        except json.JSONDecodeError:
            return {}
    return args if isinstance(args, dict) else {}


def _parameter_text(value: ta.Any, fmt: ChatFormat) -> str:
    """An argument's value inside its <parameter> block: a string as it is, anything else as JSON."""

    if isinstance(value, str):
        return value
    if fmt.python_literals and (value is None or isinstance(value, bool)):
        return str(value)
    return _tojson(value)


def render_function_call(fn: dict, fmt: ChatFormat) -> str:
    """One call in the function format, `<tool_call>` through `</tool_call>`."""

    out = ['<tool_call>\n<function=' + str(fn.get('name')) + '>\n']
    for key, value in _arguments(fn).items():
        out.append(f'<parameter={key}>\n{_parameter_text(value, fmt)}\n</parameter>\n')
    out.append('</function>\n</tool_call>')
    return ''.join(out)


def render_assistant_turn(m: dict, with_reasoning: bool | None = True, fmt: ChatFormat = LEGACY) -> str:
    """
    One assistant turn, `<|im_start|>assistant\n` through `<|im_end|>\n`. with_reasoning True renders the think block
    (empty if the message has none), False omits it, None renders it only if there is reasoning (the legacy template's
    rule for non-final turns after the last query).
    """

    content = _text_of(m.get('content'))

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
        fn = tc.get('function', tc)

        if fmt.call_syntax == 'function':
            if j > 0:
                out.append('\n')
            elif content.strip():
                out.append('\n\n')
            out.append(render_function_call(fn, fmt))
            continue

        if (j == 0 and content) or j > 0:
            out.append('\n')

        args = fn.get('arguments')
        if not isinstance(args, str):
            args = _tojson(args)

        out.append('<tool_call>\n{"name": "' + str(fn.get('name')) + '", "arguments": ' + args + '}\n</tool_call>')

    out.append('<|im_end|>\n')

    return ''.join(out)


##


_TOOL_CALL_RE = re.compile(r'<tool_call>\s*(.*?)\s*</tool_call>', re.DOTALL)
_THINK_RE = re.compile(r'<think>(.*?)</think>', re.DOTALL)

_FUNCTION_RE = re.compile(r'\s*<function=([^>\n]*)>', re.DOTALL)
_PARAMETER_RE = re.compile(r'<parameter=([^>\n]*)>\n?(.*?)\n?</parameter>', re.DOTALL)
_PARAMETER_OPEN_RE = re.compile(r'\s*<parameter=([^>\n]*)>\n?')
_PARAMETER_CLOSE = '</parameter>'
_PARAMETER_END = '\n' + _PARAMETER_CLOSE
_PYTHON_LITERALS: ta.Mapping[str, ta.Any] = {'True': True, 'False': False, 'None': None}


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


def _parameter_schemas(tools: ta.Sequence[dict] | None, name: str) -> ta.Mapping[str, ta.Any]:
    for t in tools or ():
        fn = t.get('function', t)
        if fn.get('name') == name:
            params = fn.get('parameters')
            props = params.get('properties') if isinstance(params, dict) else None
            return props if isinstance(props, dict) else {}
    return {}


def parameter_value(raw: str, schema: ta.Any) -> ta.Any:
    """
    A parameter block's text as its argument value: itself for a string parameter; otherwise the JSON it is (True /
    False / None read as well), or -- when it is no JSON, and for a parameter that may be a string -- itself.
    """

    if schema_only_text(schema):
        return raw
    text = raw.strip()
    if text in _PYTHON_LITERALS:
        return _PYTHON_LITERALS[text]
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return raw
    if isinstance(value, str) and schema_takes_text(schema):
        return raw  # (a string parameter is written without quotes: quoted text is text with quotes)
    return value


def _function_call_parts(raw: str, tools: ta.Sequence[dict] | None) -> tuple[str, dict] | None:
    m = _FUNCTION_RE.match(raw)
    if m is None:
        return None
    name = m.group(1).strip()
    schemas = _parameter_schemas(tools, name)
    args = {
        pm.group(1).strip(): parameter_value(pm.group(2), schemas.get(pm.group(1).strip()))
        for pm in _PARAMETER_RE.finditer(raw, m.end())
    }
    return name, args


def _function_call_obj(raw: str, idx: int, tools: ta.Sequence[dict] | None) -> dict | None:
    parts = _function_call_parts(raw, tools)
    if parts is None:
        return None
    return {
        'id': f'call_{idx}',
        'type': 'function',
        'function': {'name': parts[0], 'arguments': _tojson(parts[1])},
    }


def parse_output(
        text: str,
        think_open: bool = False,
        fmt: ChatFormat = LEGACY,
        tools: ta.Sequence[dict] | None = None,
) -> Parsed:
    """
    Split a finished completion into reasoning, tool calls and content. `think_open`: the prompt had opened the
    reasoning block (`render_chat`'s `open_think`), so the completion starts inside it. In the function format a
    parameter's text becomes a value by the declared schema of that parameter (`tools`): see `parameter_value`.
    """

    if think_open:
        text = THINK_OPEN + text

    reasoning = None
    m = _THINK_RE.search(text)
    if m:
        reasoning = m.group(1).strip('\n')
        text = text[:m.start()] + text[m.end():]
    elif '<think>' in text:
        # a block that never closed (the budget ran out mid-thought): all of it is reasoning, as StreamParser has it
        at = text.index('<think>')
        reasoning = text[at + len('<think>'):].strip('\n')
        text = text[:at]
    calls: list[dict] = []
    for mt in _TOOL_CALL_RE.finditer(text):
        if fmt.call_syntax == 'function':
            tc = _function_call_obj(mt.group(1), len(calls), tools)
        else:
            tc = _tool_call_obj(mt.group(1), len(calls))
        if tc is not None:
            calls.append(tc)
    content = _TOOL_CALL_RE.sub('', text).strip('\n')
    return Parsed(content, reasoning, calls)


class StreamParser:
    """
    Incremental version of parse_output for streaming: feed decoded text, get back deltas of ('reasoning', str),
    ('content', str), or, for a tool call, ('tool_call', dict) with the call's id, name and an empty `arguments` as soon
    as the name is known, then ('tool_call', {'index', 'function': {'arguments': piece}}) pieces of the arguments' JSON
    text as it streams (the OpenAI delta shape: clients concatenate the pieces), and nothing more at the closing tag. A
    call whose head never parsed is delivered whole at its closing tag instead. Text that may be the start of a tag is
    held back until it is either a tag or clearly not. `think_open`: the stream starts inside a reasoning block the
    prompt opened.

    In the function format (`fmt`) the arguments are not JSON as the model writes them, so their JSON text is made
    here: the head when `<function=name>` has arrived; a string parameter's `"key": "` at its opening tag and its
    text, JSON-escaped, as it is written (a long file body does not wait for its end); any other parameter's
    `"key": value` when its block closes, typed by the parameter's schema in `tools` as `parse_output` types it; `}`
    at the closing tag -- the pieces concatenate to what `parse_output` gives for the call.
    """

    TAGS = ('<think>', '</think>', '<tool_call>', '</tool_call>')

    def __init__(
            self,
            think_open: bool = False,
            fmt: ChatFormat = LEGACY,
            tools: ta.Sequence[dict] | None = None,
    ) -> None:
        super().__init__()

        self.fmt = fmt
        self.tools = tools

        self.buf = ''

        self.in_think = False
        self.in_call = False

        self.n_calls = 0

        self.skip_nl = False  # drop the newlines the format puts right after <think> and </think>

        self.call_head_done = False  # the current call's name has been delivered; what follows is its arguments
        self.call_args_sent = 0      # characters of the arguments text already delivered
        self.call_args_any = False   # a non-blank argument piece has been delivered
        self.call_text = ''          # the current call's body so far
        self.call_name = ''          # (function format) the current call's function
        self.call_param_open = False  # (function format) inside a string parameter, its text streaming

        if think_open:
            self.feed(THINK_OPEN)  # (delivers nothing: the tag and the newline after it are format)

    def feed(self, text: str) -> list[tuple[str, ta.Any]]:
        self.buf += text
        return self._drain(final=False)

    def finish(self) -> list[tuple[str, ta.Any]]:
        out = self._drain(final=True)
        if self.buf:
            out.append(('reasoning' if self.in_think else 'content', self.buf))
            self.buf = ''
        return out

    _ARGS_RE = re.compile(r'^\s*\{\s*"name"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"arguments"\s*:\s*', re.DOTALL)

    def _stream_call(self, final: bool) -> list[tuple[str, ta.Any]]:
        """
        Deltas for the current call from `call_text`: the head once the name and the arguments key have arrived, then
        the arguments' text as it grows, holding back the trailing run of whitespace / '}' that may be the outer
        object's close; at `final`, whatever remains before that close.
        """

        if self.fmt.call_syntax == 'function':
            return self._stream_function_call(final)

        out: list[tuple[str, ta.Any]] = []
        idx = self.n_calls

        if not self.call_head_done:
            m = self._ARGS_RE.match(self.call_text)
            if m is None:
                if final:  # no parseable head: deliver the whole call the old way, if it parses at all
                    tc = _tool_call_obj(self.call_text.strip(), idx)
                    if tc is not None:
                        out.append(('tool_call', tc))
                        self.n_calls += 1
                return out

            name = json.loads('"' + m.group(1) + '"')

            out.append(('tool_call', {
                'index': idx,
                'id': f'call_{idx}',
                'type': 'function',
                'function': {'name': name, 'arguments': ''},
            }))

            self.call_head_done = True
            self.call_args_sent = m.end()

        text = self.call_text

        if final:
            body = text.rstrip()
            stop = len(body) - 1 if body.endswith('}') else len(body)  # the outer object's close is not an argument
            piece = text[self.call_args_sent:stop].rstrip() if stop > self.call_args_sent else ''
            self.n_calls += 1

        else:
            stop = len(text)
            while stop > self.call_args_sent and text[stop - 1] in ' \t\r\n}':
                stop -= 1
            piece = text[self.call_args_sent:stop]

        if not self.call_args_any and piece:  # whitespace between the key and the value is not an argument
            stripped = piece.lstrip()
            self.call_args_sent += len(piece) - len(stripped)
            piece = stripped
            self.call_args_any = bool(piece)

        if piece:
            out.append(('tool_call', {'index': idx, 'function': {'arguments': piece}}))
            self.call_args_sent = stop

        return out

    def _stream_function_call(self, final: bool) -> list[tuple[str, ta.Any]]:
        """`_stream_call` for the function format: the head, then one piece of arguments JSON per closed parameter."""

        out: list[tuple[str, ta.Any]] = []
        idx = self.n_calls
        text = self.call_text

        if not self.call_head_done:
            m = _FUNCTION_RE.match(text)
            if m is None:
                return out  # (at `final`: a call that never named a function is no call)

            self.call_name = m.group(1).strip()
            out.append(('tool_call', {
                'index': idx,
                'id': f'call_{idx}',
                'type': 'function',
                'function': {'name': self.call_name, 'arguments': ''},
            }))

            self.call_head_done = True
            self.call_args_sent = m.end()

        schemas = _parameter_schemas(self.tools, self.call_name)
        pieces: list[str] = []

        while True:
            if self.call_param_open:
                # inside a string parameter: its text goes out as it comes, JSON-escaped, but for a tail that may be
                # the start of the closing sequence
                end = text.find(_PARAMETER_CLOSE, self.call_args_sent)
                if end < 0:
                    stop = len(text)
                    for n in range(min(len(_PARAMETER_END), stop - self.call_args_sent), 0, -1):
                        if _PARAMETER_END.startswith(text[stop - n:]):
                            stop -= n
                            break
                    if stop > self.call_args_sent:
                        pieces.append(_tojson(text[self.call_args_sent:stop])[1:-1])
                        self.call_args_sent = stop
                    break

                stop = end - 1 if end > self.call_args_sent and text[end - 1] == '\n' else end
                pieces.append(_tojson(text[self.call_args_sent:stop])[1:-1] + '"')
                self.call_args_sent = end + len(_PARAMETER_CLOSE)
                self.call_param_open = False
                continue

            om = _PARAMETER_OPEN_RE.match(text, self.call_args_sent)
            if om is None:
                break
            if om.end() == len(text) and not om.group(0).endswith('\n') and not final:
                break  # (the newline after the tag is format, not value: wait to see it)
            key = om.group(1).strip()
            lead = ('{' if not self.call_args_any else ', ') + _tojson(key) + ': '

            if schema_only_text(schemas.get(key)):
                pieces.append(lead + '"')
                self.call_param_open = True
                self.call_args_any = True
                self.call_args_sent = om.end()
                continue

            # anything else is known only whole: its text is a value by what it turns out to be
            pm = _PARAMETER_RE.match(text, om.start(1) - len('<parameter='))
            if pm is None:
                break
            pieces.append(lead + _tojson(parameter_value(pm.group(2), schemas.get(key))))
            self.call_args_any = True
            self.call_args_sent = pm.end()

        if final:
            pieces.append('}' if self.call_args_any else '{}')
            self.n_calls += 1

        if pieces:
            out.append(('tool_call', {'index': idx, 'function': {'arguments': ''.join(pieces)}}))

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
                    # keep what could still be the start of the closing tag; stream the rest of the arguments
                    keep = 0
                    for n in range(min(len(self.buf), len('</tool_call>') - 1), 0, -1):
                        if '</tool_call>'.startswith(self.buf[-n:]):
                            keep = n
                            break

                    self.call_text += self.buf[:len(self.buf) - keep] if keep else self.buf
                    self.buf = self.buf[len(self.buf) - keep:] if keep else ''
                    out.extend(self._stream_call(final=False))
                    return out

                self.call_text += self.buf[:end]
                self.buf = self.buf[end + len('</tool_call>'):]
                out.extend(self._stream_call(final=True))

                self.in_call = False
                self.call_text = ''
                self.call_head_done = False
                self.call_args_sent = 0
                self.call_args_any = False
                self.call_param_open = False

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
