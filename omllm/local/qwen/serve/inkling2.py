"""
Inkling 2's chat protocol (INKLING.md, "The chat protocol"): a conversation is a run of framed messages,

    <|message_ROLE|> [name] <|content_CHANNEL|> body <|end_message|>

with no generation prompt -- the model opens its own messages -- and a model turn is one or more of them (reasoning
on the thinking channel, the answer on the text channel, a tool call as JSON on its own channel under the tool's
name) ended by <|content_model_end_sampling|>, which is where generation stops; <|end_message|> only ends a message.

Rendering follows the checkpoint's chat template, established by rendering it as a black box over many conversations
(nothing here is derived from its source): tools declared first, in one system message, as compact key-sorted JSON;
the leading system messages; one system message naming the thinking effort as a number; then the turns. A tool call
is `{"name": ..., "args": {...}}` with the arguments' top-level keys sorted. Where this departs on purpose: an
OpenAI client's arguments arrive as JSON text and are parsed (the template refuses them), a tool result that is not
text is written as JSON, and images are refused -- the vision tower is not built.

What a message says is never its framing. The markers are special tokens, and only they are: in a rendered prompt
the text of a message -- a body, a header's name -- is written escaped (`inkling2_escape`), so that a tool result or
a file that quotes `<|end_message|>` ends nothing and a user cannot write a system message, and
`Inkling2ChatProtocol.encode` encodes it as the plain text it is. The other way, the reader is told which of what it
reads were special tokens (`ChatReader.mark`), so a model writing about its own protocol is read as writing text.

Reading is one incremental reader (`Inkling2Reader`); a finished answer is read by the same code, so a streamed
answer's deltas concatenate to what the unstreamed one carries.
"""
import json
import re
import typing as ta

from omcore import check

from ..constrain.framed import FramedJsonConstraint
from ..constrain.framed import FramedPlainConstraint
from ..constrain.framed import FramedToolConstraint
from ..constrain.framed import FrameTokens
from ..constrain.grammar import JsonCallSpelling
from ..constrain.grammar import response_format_schema
from ..tokenizer import Tokenizer
from .chat import Parsed
from .protocols import ChatEvent
from .protocols import ChatProtocol
from .protocols import ChatReader


##


INKLING2_MESSAGE_USER = '<|message_user|>'
INKLING2_MESSAGE_MODEL = '<|message_model|>'
INKLING2_MESSAGE_SYSTEM = '<|message_system|>'
INKLING2_MESSAGE_TOOL = '<|message_tool|>'

INKLING2_CONTENT_TEXT = '<|content_text|>'
INKLING2_CONTENT_THINKING = '<|content_thinking|>'
INKLING2_CONTENT_XML = '<|content_xml|>'
INKLING2_CONTENT_TOOL_JSON = '<|content_invoke_tool_json|>'

INKLING2_END_MESSAGE = '<|end_message|>'
INKLING2_END_SAMPLING = '<|content_model_end_sampling|>'

INKLING2_MESSAGE_PREFIX = '<|message_'
INKLING2_CONTENT_PREFIX = '<|content_'

# what every marker opens with, and so what no message's text may be left holding in a rendered prompt
INKLING2_MARKER_OPEN = '<|'
INKLING2_ESCAPE = '\u241b'

# what a tokenizer must have for its checkpoint to speak this protocol
INKLING2_REQUIRED_TOKENS = (
    INKLING2_MESSAGE_USER,
    INKLING2_MESSAGE_MODEL,
    INKLING2_MESSAGE_SYSTEM,
    INKLING2_CONTENT_TEXT,
    INKLING2_CONTENT_THINKING,
    INKLING2_CONTENT_TOOL_JSON,
    INKLING2_END_MESSAGE,
    INKLING2_END_SAMPLING,
)

# a call's body: {"name": NAME, "args": ARGUMENTS}, ended by its message's end
INKLING2_CALL_SPELLING = JsonCallSpelling(open='{', args_key='"args"', close='')


_UNESCAPE_RE = re.compile(f'{INKLING2_ESCAPE}({INKLING2_ESCAPE})?')


def inkling2_escape(text: str) -> str:
    """
    A message's text as a rendered prompt holds it: an escape between the two characters a marker opens with,
    wherever the text has them, so that it holds no marker; and an escape of the text's own doubled, so that
    `inkling2_unescape` gives the text back whatever it was.
    """

    text = text.replace(INKLING2_ESCAPE, INKLING2_ESCAPE * 2)
    return text.replace(INKLING2_MARKER_OPEN, INKLING2_MARKER_OPEN[0] + INKLING2_ESCAPE + INKLING2_MARKER_OPEN[1:])


def inkling2_unescape(text: str) -> str:
    return _UNESCAPE_RE.sub(lambda m: m.group(1) or '', text)


# The thinking effort a prompt names, by the names clients use. The template's default is 'high'.
INKLING2_EFFORTS: ta.Mapping[str, float] = {
    'none': 0,
    'minimal': 0.1,
    'low': 0.2,
    'medium': 0.7,
    'high': 0.9,
    'xhigh': 0.99,
    'max': 0.99,
}

INKLING2_DEFAULT_EFFORT = 'high'
INKLING2_MAX_EFFORT = 0.99


def inkling2_effort_level(value: ta.Any) -> float:
    """A reasoning effort -- one of the names, or a number in [0, 0.99] -- as the number a prompt states."""

    if value is None:
        return INKLING2_EFFORTS[INKLING2_DEFAULT_EFFORT]

    if isinstance(value, str):
        if value not in INKLING2_EFFORTS:
            raise ValueError(
                f'reasoning_effort must be one of {", ".join(INKLING2_EFFORTS)} or a number in '
                f'[0, {INKLING2_MAX_EFFORT}]: {value!r}',
            )
        return INKLING2_EFFORTS[value]

    if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 <= value <= INKLING2_MAX_EFFORT):
        raise ValueError(f'reasoning_effort must be in [0, {INKLING2_MAX_EFFORT}]: {value!r}')

    return value


def _level_text(level: float) -> str:
    return str(int(level)) if level == int(level) else repr(float(level))


def _json(x: ta.Any, *, sort_keys: bool = False) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'), sort_keys=sort_keys)


def _frame(role: str, channel: str, body: str, name: str = '') -> str:
    return f'{role}{inkling2_escape(name)}{channel}{inkling2_escape(body)}{INKLING2_END_MESSAGE}'


def _text_parts(content: ta.Any) -> list[str] | None:
    """A message's content as the texts it is framed as: one for a string, one per text part; None for no content."""

    if content is None:
        return None
    if isinstance(content, str):
        return [content]

    out = []
    for p in content:
        kind = p.get('type') if isinstance(p, dict) else None
        if kind != 'text':
            raise ValueError(f'unsupported content part {kind!r}: this model is served text-only')
        out.append(str(p.get('text', '')))
    return out


def _tool_declarations(tools: ta.Sequence[dict]) -> str:
    decls = []
    for t in tools:
        fn = t.get('function', t)
        decls.append({
            'description': fn.get('description') or '',
            'name': fn['name'],
            'parameters': fn.get('parameters') or {},
            'type': 'function',
        })
    return _frame(INKLING2_MESSAGE_SYSTEM, INKLING2_CONTENT_XML, _json(decls, sort_keys=True), 'tool_declare')


def _call_arguments(fn: ta.Mapping[str, ta.Any]) -> dict:
    """A tool call's arguments as a mapping (OpenAI clients send them as JSON text)."""

    args = fn.get('arguments')
    if isinstance(args, str):
        try:
            args = json.loads(args) if args.strip() else {}
        except json.JSONDecodeError:
            raise ValueError(f'tool call arguments are not JSON: {args[:80]!r}') from None
    if args is None:
        return {}
    if not isinstance(args, dict):
        raise ValueError('tool call arguments must be an object')  # noqa: TRY004  (a bad request, like the others)
    return args


def render_inkling2_tool_call(fn: ta.Mapping[str, ta.Any]) -> str:
    """One call's message: the tool's name as the header, `{"name", "args"}` as the body, the arguments' keys sorted."""

    name = str(fn.get('name'))
    args = _call_arguments(fn)
    body = '{"name":' + _json(name) + ',"args":' + _json({k: args[k] for k in sorted(args)}) + '}'
    return _frame(INKLING2_MESSAGE_MODEL, INKLING2_CONTENT_TOOL_JSON, body, name)


def render_inkling2_assistant(m: ta.Mapping[str, ta.Any]) -> str:
    """One model turn: its reasoning, its content, its calls -- a message each -- and the end of sampling."""

    out: list[str] = []

    reasoning = m.get('reasoning_content')
    if not isinstance(reasoning, str):
        reasoning = m.get('reasoning')
    if isinstance(reasoning, str) and reasoning:
        out.append(_frame(INKLING2_MESSAGE_MODEL, INKLING2_CONTENT_THINKING, reasoning))

    calls = m.get('tool_calls') or []
    texts = _text_parts(m.get('content'))
    if texts is not None and (len(texts) != 1 or texts[0] or not (out or calls)):
        # (an empty answer is written only when the turn has nothing else)
        out.extend(_frame(INKLING2_MESSAGE_MODEL, INKLING2_CONTENT_TEXT, t) for t in texts)

    for tc in calls:
        out.append(render_inkling2_tool_call(tc.get('function', tc)))

    out.append(INKLING2_END_SAMPLING)
    return ''.join(out)


def render_inkling2(
        messages: ta.Sequence[dict],
        tools: ta.Sequence[dict] | None = None,
        *,
        effort: ta.Any = None,
        continuation: bool = False,
) -> str:
    """
    The prompt for an OpenAI-style message list. `effort`: the thinking effort the prompt states
    (`inkling2_effort_level`). `continuation`: neither the tools nor the effort are written (the conversation these
    messages continue has them).
    """

    out: list[str] = []
    msgs = list(messages)

    lead = 0
    while lead < len(msgs) and msgs[lead].get('role') == 'system':
        lead += 1

    effort_frame = _frame(
        INKLING2_MESSAGE_SYSTEM,
        INKLING2_CONTENT_TEXT,
        f'Thinking effort level: {_level_text(inkling2_effort_level(effort))}',
    )

    if tools and not continuation:
        out.append(_tool_declarations(tools))

    call_names: dict[str, str] = {}  # a call's id -> its tool, for the results that name only the id

    for i, m in enumerate(msgs):
        if i == lead and not continuation:
            out.append(effort_frame)

        role = m.get('role')

        if role == 'system' or role == 'user':
            marker = INKLING2_MESSAGE_SYSTEM if role == 'system' else INKLING2_MESSAGE_USER
            out.extend(_frame(marker, INKLING2_CONTENT_TEXT, t) for t in _text_parts(m.get('content')) or [''])

        elif role == 'assistant':
            for tc in m.get('tool_calls') or []:
                if tc.get('id') is not None:
                    call_names[str(tc['id'])] = str(tc.get('function', tc).get('name'))
            out.append(render_inkling2_assistant(m))

        elif role == 'tool':
            name = m.get('name')
            if not isinstance(name, str):
                name = call_names.get(str(m.get('tool_call_id')), '')
            content = m.get('content')
            if content is not None and not isinstance(content, (str, list)):
                content = _json(content)
            out.extend(
                _frame(INKLING2_MESSAGE_TOOL, INKLING2_CONTENT_TEXT, t, name)
                for t in _text_parts(content) or ['']
            )

        else:
            raise ValueError(f'unknown message role: {role!r}')

    if lead == len(msgs) and not continuation:
        out.append(effort_frame)

    return ''.join(out)


##


_MARKER_RE = re.compile(r'<\|[A-Za-z0-9_]+\|>')

# a call's body up to its arguments: {"name": "...", "args":
_CALL_HEAD_RE = re.compile(r'^\s*\{\s*"name"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"args"\s*:\s*', re.DOTALL)

_SEGMENT_SEPARATOR = '\n\n'


class Inkling2Reader(ChatReader):
    """
    A model turn read as it is generated: its special tokens through `mark`, everything else through `feed` -- which
    reads no marker out of text, whatever the text spells. Thinking messages are reasoning, text messages content (a
    later message of a kind follows the earlier ones after a blank line), and a tool-call message is a call: its head
    goes out when its name is known -- the message's header carries it before the JSON starts -- and its arguments as
    the text of the JSON's `args` value, as it is written. A call whose JSON never took that shape is delivered whole
    when its message ends, if it parses at all. Text outside any message is content.
    """

    def __init__(self) -> None:
        super().__init__()

        self._events: list[ChatEvent] = []  # everything handed back so far: `parsed` is these put together

        self._kind: str | None = None  # None: between messages; 'header'; 'reasoning' | 'content' | 'call'
        self._header = ''
        self._seen = {'reasoning': False, 'content': False}  # a message of the kind has delivered text
        self._fresh = False  # the current message has delivered nothing yet

        self._n_calls = 0
        self._call_text = ''
        self._call_name = ''
        self._call_head_sent = False
        self._call_args_at: int | None = None  # where the arguments' text starts in `_call_text`, once known
        self._call_args_sent = 0
        self._call_args_any = False  # a non-blank piece of the arguments has gone out

    def feed(self, text: str) -> list[ChatEvent]:
        return self._keep(self._take(text) if text else [])

    def mark(self, marker: str) -> list[ChatEvent]:
        return self._keep(self._mark(marker))

    def finish(self) -> list[ChatEvent]:
        out: list[ChatEvent] = []
        if self._kind == 'call':
            out.extend(self._end_call())
        self._kind = None
        return self._keep(out)

    def _keep(self, events: list[ChatEvent]) -> list[ChatEvent]:
        self._events.extend(events)
        return events

    def parsed(self, text: str = '') -> Parsed:
        reasoning: list[str] = []
        content: list[str] = []
        calls: list[dict] = []

        for kind, payload in self._events:
            if kind == 'reasoning':
                reasoning.append(payload)
            elif kind == 'content':
                content.append(payload)
            else:
                i = payload['index']
                if 'id' in payload:
                    calls.append({
                        'id': payload['id'],
                        'type': 'function',
                        'function': {'name': payload['function']['name'], 'arguments': ''},
                    })
                calls[i]['function']['arguments'] += payload['function']['arguments']

        for c in calls:
            c['function']['arguments'] = c['function']['arguments'] or '{}'

        return Parsed(
            ''.join(content),
            ''.join(reasoning) if reasoning else None,
            calls,
        )

    # text

    def _text(self, kind: str, text: str) -> list[ChatEvent]:
        if not text:
            return []
        if self._fresh:
            self._fresh = False
            if self._seen[kind]:
                text = _SEGMENT_SEPARATOR + text
            self._seen[kind] = True
        return [(kind, text)]

    # calls

    def _call_head(self, name: str) -> ChatEvent:
        self._call_head_sent = True
        self._call_name = name
        return ('tool_call', {
            'index': self._n_calls,
            'id': f'call_{self._n_calls}',
            'type': 'function',
            'function': {'name': name, 'arguments': ''},
        })

    def _stream_call(self, final: bool) -> list[ChatEvent]:
        out: list[ChatEvent] = []
        text = self._call_text

        if self._call_args_at is None:
            m = _CALL_HEAD_RE.match(text)
            if m is None:
                return out
            if not self._call_head_sent:
                out.append(self._call_head(json.loads('"' + m.group(1) + '"')))
            self._call_args_at = self._call_args_sent = m.end()

        if final:
            body = text.rstrip()
            stop = len(body) - 1 if body.endswith('}') else len(body)  # the outer object's close is not an argument
            piece = text[self._call_args_sent:stop].rstrip() if stop > self._call_args_sent else ''
        else:
            stop = len(text)
            while stop > self._call_args_sent and text[stop - 1] in ' \t\r\n}':
                stop -= 1
            piece = text[self._call_args_sent:stop]

        if not self._call_args_any and piece:  # whitespace between the key and the value is not an argument
            stripped = piece.lstrip()
            self._call_args_sent += len(piece) - len(stripped)
            piece = stripped
            self._call_args_any = bool(piece)

        if piece:
            out.append(('tool_call', {'index': self._n_calls, 'function': {'arguments': piece}}))
            self._call_args_sent = stop

        return out

    def _end_call(self) -> list[ChatEvent]:
        out = self._stream_call(final=True)

        if self._call_args_at is None:
            # no `{"name", "args"}` head: the whole object at once, if it is one
            try:
                obj = json.loads(self._call_text)
            except json.JSONDecodeError:
                obj = None
            if isinstance(obj, dict):
                name = obj.get('name') if isinstance(obj.get('name'), str) else self._call_name
                args = obj.get('args', obj.get('arguments', {}))
                if name:
                    if not self._call_head_sent:
                        out.append(self._call_head(name))
                    out.append(('tool_call', {
                        'index': self._n_calls,
                        'function': {'arguments': args if isinstance(args, str) else _json(args)},
                    }))

        if self._call_head_sent:
            self._n_calls += 1

        self._call_text = ''
        self._call_name = ''
        self._call_head_sent = False
        self._call_args_at = None
        self._call_args_sent = 0
        self._call_args_any = False
        return out

    # the stream

    def _take(self, text: str) -> list[ChatEvent]:
        kind = self._kind
        if kind == 'header':
            self._header += text
            return []
        if kind == 'call':
            self._call_text += text
            return self._stream_call(final=False)
        if kind is None:
            if not text.strip():
                return []
            self._fresh = True  # (text outside any message: content, as a message of its own)
            return self._text('content', text)
        return self._text(kind, text)

    def _mark(self, marker: str) -> list[ChatEvent]:
        out: list[ChatEvent] = []

        if marker == INKLING2_END_MESSAGE or marker.startswith(INKLING2_MESSAGE_PREFIX):
            if self._kind == 'call':
                out.extend(self._end_call())
            self._kind = 'header' if marker == INKLING2_MESSAGE_MODEL else None
            self._header = ''
            return out

        if self._kind == 'header' and marker.startswith(INKLING2_CONTENT_PREFIX):
            name = self._header.strip()
            self._fresh = True
            if marker == INKLING2_CONTENT_THINKING:
                self._kind = 'reasoning'
            elif marker == INKLING2_CONTENT_TOOL_JSON:
                self._kind = 'call'
                if name:
                    out.append(self._call_head(name))
            else:
                self._kind = 'content'
            return out

        # any other marker is text where it stands
        return self._take(marker)


def parse_inkling2(text: str) -> Parsed:
    """
    A finished model turn's text as reasoning, content and tool calls: what `Inkling2Reader` reads of it, taking
    whatever in the text spells a marker for one -- a reading of text, which cannot tell (the engine reads tokens).
    """

    reader = Inkling2Reader()

    at = 0
    for m in _MARKER_RE.finditer(text):
        reader.feed(text[at:m.start()])
        reader.mark(m.group(0))
        at = m.end()
    reader.feed(text[at:])
    reader.finish()

    return reader.parsed(text)


##


def speaks_inkling2(tok: Tokenizer) -> bool:
    return all(t in tok.special for t in INKLING2_REQUIRED_TOKENS)


class Inkling2ChatProtocol(ChatProtocol):
    def __init__(self, tok: Tokenizer, *, reasoning_effort: ta.Any = None) -> None:
        """
        `reasoning_effort`: the effort a request that names none is rendered at -- a name or a number; None is the
        template's default, 'high'.
        """

        super().__init__()

        missing = [t for t in INKLING2_REQUIRED_TOKENS if t not in tok.special]
        if missing:
            raise ValueError(f'the tokenizer has no {", ".join(missing)}')

        # (what `inkling2_escape` rests on: no special token survives in escaped text)
        unbroken = [t for t in tok.special if INKLING2_MARKER_OPEN not in t]
        if unbroken:
            raise ValueError(f'special tokens that do not open as a marker does: {", ".join(unbroken[:8])}')

        inkling2_effort_level(reasoning_effort)  # (raises on a value that is no effort)

        self._tok = tok
        self._reasoning_effort = reasoning_effort

        self._end = tok.special[INKLING2_END_SAMPLING]
        self._eos = frozenset(
            i
            for i in (
                self._end,
                tok.eos_id,
                tok.special.get('<|endoftext|>'),
            )
            if i is not None
        )

        # the turn as the reader reads it (Inkling2Reader._mark), by id
        sp = tok.special
        self._frames = FrameTokens(
            open_model=sp[INKLING2_MESSAGE_MODEL],
            boundaries=frozenset(
                i for t, i in sp.items() if t == INKLING2_END_MESSAGE or t.startswith(INKLING2_MESSAGE_PREFIX)
            ),
            end_message=sp[INKLING2_END_MESSAGE],
            channels=frozenset(i for t, i in sp.items() if t.startswith(INKLING2_CONTENT_PREFIX)) - self._eos,
            thinking=sp[INKLING2_CONTENT_THINKING],
            text=sp[INKLING2_CONTENT_TEXT],
            call=sp[INKLING2_CONTENT_TOOL_JSON],
            ends=self._eos,
        )

    @property
    def name(self) -> str:
        return 'inkling2'

    @property
    def eos_ids(self) -> ta.AbstractSet[int]:
        return self._eos

    def reasoning_effort(self, value: ta.Any) -> tuple[ta.Any, bool | None]:
        if value is None:
            return None, None
        level = inkling2_effort_level(value)
        return value, (False if level == 0 else None)

    def _effort(self, enable_thinking: bool, reasoning_effort: ta.Any) -> ta.Any:
        """The effort a prompt states: the request's, else none with thinking off, else the server's."""

        if reasoning_effort is not None:
            return reasoning_effort
        if not enable_thinking:
            return 'none'
        return self._reasoning_effort

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
        return render_inkling2(
            messages,
            tools,
            effort=self._effort(enable_thinking, reasoning_effort),
            continuation=continuation,
        )

    def encode(self, text: str) -> list[int]:
        """
        A rendered prompt's ids: its markers the special tokens they are, and what lies between them -- a message's
        text, escaped by the renderer -- unescaped and encoded as plain text, in which nothing is a special token.
        """

        tok = self._tok
        ids: list[int] = []
        if tok.add_bos and tok.bos_id is not None:  # (as Tokenizer.encode)
            ids.append(tok.bos_id)
        for chunk in check.not_none(tok.special_re).split(text):
            if not chunk:
                continue
            sid = tok.special.get(chunk)
            if sid is not None:
                ids.append(sid)
            else:
                ids.extend(tok.encode(inkling2_unescape(chunk), add_bos=False, parse_special=False))
        return ids

    def generation_prompt(self, rendered: str) -> str:
        return ''

    def answer_prefix(self, *, enable_thinking: bool = True) -> str:
        return ''

    # answers

    def reader(self, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> ChatReader:
        return Inkling2Reader()

    def parse(self, text: str, tools: ta.Sequence[dict] | None = None, *, enable_thinking: bool = True) -> Parsed:
        return parse_inkling2(text)

    def constraint(
            self,
            tools: ta.Sequence[dict] | None,
            tool_choice: ta.Any,
            response_format: ta.Any,
            *,
            enable_thinking: bool = True,
    ) -> ta.Any:
        """
        Tools present: a call's message names a declared tool and carries JSON of its parameters, and tool_choice
        'none' / 'required' / a named function forbids or forces one. Without tools, response_format json_object /
        json_schema holds the answer to one JSON value; with neither, a turn is still held to messages that are not
        calls. And with thinking off there is no message of reasoning, whatever else is held: the prompt can only
        state an effort of 0, at which the model still writes one (constrain/framed.py).
        """

        if tools:
            return FramedToolConstraint(
                self._tok,
                self._frames,
                tools,
                INKLING2_CALL_SPELLING,
                tool_choice or 'auto',
                thinking=enable_thinking,
            )

        schema = response_format_schema(response_format)
        if schema is not None:
            return FramedJsonConstraint(self._tok, self._frames, schema, thinking=enable_thinking)

        return FramedPlainConstraint(self._tok, self._frames, thinking=enable_thinking)

    def check(self, tools: ta.Sequence[dict] | None, tool_choice: ta.Any, response_format: ta.Any) -> None:
        pass  # (every request has its grammar: `constraint`)

    # the conversation continued

    def answer_segment(self, msg: dict) -> str:
        return render_inkling2_assistant(msg)

    def close_answer(self, out_ids: ta.Sequence[int]) -> list[int]:
        ids = list(out_ids)
        if not ids or ids[-1] != self._end:
            ids.append(self._end)
        return ids

    def describe(self) -> dict[str, ta.Any]:
        return {
            'chat_format': self.name,
            'open_think': False,
            'reasoning_effort': (
                self._reasoning_effort if self._reasoning_effort is not None else INKLING2_DEFAULT_EFFORT
            ),
        }
