"""
Constrained decoding for tool calls.

Once the model has opened a `<tool_call>`, every following token is restricted to those that keep the text a valid
prefix of

    \\n{"name": "<a declared function>", "arguments": <JSON matching that function's parameters>}\\n</tool_call>

so a tool call that comes out is always well-formed, names a real tool, and carries arguments of the declared types with
every required key present. `tool_choice` builds on the same machinery: "none" forbids opening a call, "required" (or a
named function) forces one as soon as the model is out of its reasoning block.

How: `Acceptor` is a prefix acceptor over bytes for that language, compiled from the tools' JSON schemas -- a small NFA
whose states are tuples of frames (literals, string / number / object / array parsers, each knowing its schema),
immutable and hashable. `Vocab` is a byte trie over the tokenizer. The allowed tokens in a state are the trie's complete
tokens reachable while the acceptor stays alive, found by walking the trie against the acceptor; the result is memoised
per state, and the common "inside a free string" state short-circuits to a precomputed set of plain tokens plus a walk
over only the tokens that contain a quote, a backslash or a control byte. In practice a state's mask is computed once
and reused for the rest of the call.

`ToolConstraint` is what the generation loops talk to: it watches generated tokens (bytes, so it works whether
`<tool_call>` is one token or several), tracks reasoning blocks, enters and leaves the acceptor, and hands back the
allowed set for the next token (or None for "anything"). The model's own sampler applies that as a logit mask; under
speculative decoding the verify rows get the mask for their own position, so a draft that breaks the grammar is rejected
like any other mismatch and the correction is drawn from the masked distribution. `JsonConstraint` is the same
controller for `response_format` (JSON mode): the content after the reasoning block must be one JSON value matching the
given schema (any value for `json_object`), and then only the end-of-turn tokens are allowed.

Supported schema features: object (properties, required, additionalProperties), string (enum, minLength / maxLength
ignored), integer, number, boolean, null, array (items), anyOf / oneOf, const, and `{}` / no type for any JSON value.
Whitespace is allowed where JSON allows it.
"""
import json
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .tokenizer import Tokenizer


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


Frame = tuple
Stack = tuple  # of Frame, top last
State = frozenset  # of Stack (the NFA's alternatives); empty = dead

WS = frozenset(b' \t\n\r')
DIGITS = frozenset(b'0123456789')
ESCAPES = frozenset(b'"\\/bfnrtu')
HEX = frozenset(b'0123456789abcdefABCDEF')


def _lit(text: str) -> Frame:
    return ('lit', text, 0)


def _ws() -> Frame:
    return ('ws',)


class Acceptor:
    """Prefix acceptor for one tool-call body (after `<tool_call>`), compiled from the tools' schemas."""

    OPEN = '\n{'
    NAME_KEY = '"name"'
    ARGS_KEY = '"arguments"'
    CLOSE = '\n</tool_call>'

    def __init__(
            self,
            tools: ta.Sequence[dict] = (),
            only: str | None = None,
            value_schema: ta.Any = None,
    ) -> None:
        """
        Tool-call bodies for `tools` (optionally just the function `only`), or, with `value_schema`, one bare JSON value
        of that schema (`{}` for any) -- JSON mode.
        """

        self.schemas: list[ta.Any] = []  # id -> schema (dict) ; shared across frames to keep them small
        self._ids: dict[str, int] = {}
        self.functions: dict[str, int] = {}  # name -> schema id of its parameters

        self.value_sid: int | None = None

        if value_schema is not None:
            self.value_sid = self._schema_id(value_schema if isinstance(value_schema, dict) else {})

        else:
            for t in tools:
                fn = t.get('function', t)
                name = str(fn.get('name'))

                if only is not None and name != only:
                    continue

                params = fn.get('parameters')
                if not isinstance(params, dict):
                    params = {'type': 'object', 'properties': {}}

                self.functions[name] = self._schema_id(params)

            if not self.functions:
                why = f' (tool_choice {only!r} not declared)' if only else ''
                raise ValueError('no tools to constrain to' + why)

        self._memo: dict[State, frozenset[int]] = {}

    def _schema_id(self, schema: ta.Any) -> int:
        key = json.dumps(schema, sort_keys=True)
        i = self._ids.get(key)
        if i is None:
            i = self._ids[key] = len(self.schemas)
            self.schemas.append(schema)
        return i

    # states

    def initial(self) -> State:
        if self.value_sid is not None:
            return frozenset([(
                _ws(),
                ('value', self.value_sid),
                _ws(),
            )])

        return frozenset([(
            _lit(self.CLOSE),
            _lit('}'),
            _ws(),
            ('argsvalue',),  # replaced by the chosen function's parameter schema once the name is known
            _ws(),
            _lit(':'),
            _ws(),
            _lit(self.ARGS_KEY),
            _ws(),
            _lit(','),
            _ws(),
            _lit('"'),
            ('name', tuple(sorted(self.functions)), 0),
            _lit('"'),
            _ws(),
            _lit(':'),
            _ws(),
            _lit(self.NAME_KEY),
            _ws(),
            _lit(self.OPEN),
        )])

    @staticmethod
    def is_complete(state: State) -> bool:
        return any(len(st) == 0 for st in state)

    @staticmethod
    def can_end(state: State) -> bool:
        """
        Whether some alternative could stop here with no more bytes: its remaining frames are all zero-width (optional
        whitespace) or a number that is already complete -- a bare top-level number has no closing byte.
        """

        for st in state:
            ok = True

            for fr in st:
                if fr[0] == 'ws':
                    continue

                if fr[0] == 'num' and fr[2] in ('int0', 'int', 'frac', 'exp'):
                    continue

                ok = False
                break

            if ok:
                return True

        return False

    @staticmethod
    def is_dead(state: State) -> bool:
        return len(state) == 0

    # advancing

    def advance(self, state: State, b: int) -> State:
        out: set[Stack] = set()
        for st in state:
            for nst in self._advance_stack(st, b):
                out.add(nst)
        return frozenset(out)

    def _advance_stack(self, st: Stack, b: int) -> list[Stack]:
        """
        Every stack that can result from consuming byte b (frames that cannot consume it pop first, so an optional
        whitespace frame or a 'number may end here' frame hands the byte to the frame below).
        """

        if not st:
            return []

        fr = st[-1]
        rest = st[:-1]
        kind = fr[0]

        if kind == 'lit':
            text = fr[1]
            i = fr[2]
            if ord(text[i]) != b:
                return []
            i += 1
            return [rest if i == len(text) else (*rest, ('lit', text, i))]

        if kind == 'ws':
            if b in WS:
                return [st]
            return self._advance_stack(rest, b)  # zero-width: hand the byte on

        if kind == 'name':
            opts = fr[1]
            i = fr[2]
            outs: list[Stack] = []
            alive = tuple(o for o in opts if len(o) > i and ord(o[i]) == b)
            if alive:
                outs.append((*rest, ('name', alive, i + 1)))
            for o in opts:
                if len(o) == i:  # this name is complete: the byte belongs to what follows, with its schema chosen
                    outs.extend(self._advance_stack(self._bind_args(rest, o), b))
            return outs

        if kind == 'keyname':  # an object key being matched against the declared property names
            opts = fr[1]
            i = fr[2]
            outs = []
            alive = tuple(o for o in opts if len(o) > i and ord(o[i]) == b)
            if alive:
                outs.append((*rest, ('keyname', alive, i + 1)))
            if b == ord('"'):  # a complete key: the obj frame below learns which one
                obj = rest[-1]
                for o in opts:
                    if len(o) == i:
                        outs.append((*rest[:-1], ('obj', obj[1], 'colon', obj[3], o)))
            return outs

        if kind == 'keystr':  # a free (undeclared) object key; no escapes, must not be a declared property
            text = fr[1]
            if b == ord('"'):
                obj = rest[-1]
                props = self.schemas[obj[1]].get('properties') or {}
                return [] if text in props else [rest]
            if b == ord('\\') or b < 0x20:
                return []
            return [(*rest, ('keystr', text + chr(b)))]

        if kind == 'argsvalue':
            raise AssertionError('arguments schema not bound')

        if kind == 'value':
            return self._start_value(rest, self.schemas[fr[1]], b)

        if kind == 'any':
            return self._start_value(rest, {}, b)

        if kind == 'str':
            return self._advance_str(rest, fr, b)

        if kind == 'num':
            return self._advance_num(rest, fr, b)

        if kind == 'obj':
            return self._advance_obj(rest, fr, b)

        if kind == 'arr':
            return self._advance_arr(rest, fr, b)

        raise AssertionError(kind)

    def _bind_args(self, rest: Stack, name: str) -> Stack:
        sid = self.functions[name]
        out = []
        for f in rest:
            out.append(('value', sid) if f[0] == 'argsvalue' else f)
        return tuple(out)

    # values

    def _start_value(self, rest: Stack, schema: ta.Any, b: int) -> list[Stack]:
        if not isinstance(schema, dict):
            schema = {}

        if 'anyOf' in schema or 'oneOf' in schema:
            outs: list[Stack] = []
            for alt in schema.get('anyOf') or schema.get('oneOf') or []:
                outs.extend(self._start_value(rest, alt, b))
            return outs

        if 'const' in schema:
            return self._advance_stack((*rest, _lit(json.dumps(schema['const'], ensure_ascii=False))), b)

        if 'enum' in schema:
            outs = []
            for val in schema['enum']:
                outs.extend(self._advance_stack((*rest, _lit(json.dumps(val, ensure_ascii=False))), b))
            return outs

        t = schema.get('type')

        if isinstance(t, list):
            outs = []
            for tt in t:
                sub = dict(schema)
                sub['type'] = tt
                outs.extend(self._start_value(rest, sub, b))
            return outs

        if t is None:  # any JSON value
            outs = []
            for tt in ('object', 'array', 'string', 'number', 'boolean', 'null'):
                sub = dict(schema)
                sub['type'] = tt
                outs.extend(self._start_value(rest, sub, b))
            return outs

        if t == 'string':
            return [(*rest, ('str', 0, 0))] if b == ord('"') else []

        if t in ('number', 'integer'):
            return self._start_num(rest, t == 'integer', b)

        if t == 'boolean':
            outs = []
            for lit in ('true', 'false'):
                outs.extend(self._advance_stack((*rest, _lit(lit)), b))
            return outs

        if t == 'null':
            return self._advance_stack((*rest, _lit('null')), b)

        if t == 'object':
            if b != ord('{'):
                return []
            return [(*rest, ('obj', self._schema_id(schema), 'first', frozenset(), None))]

        if t == 'array':
            if b != ord('['):
                return []
            return [(*rest, ('arr', self._schema_id(schema), 'first'))]

        raise ValueError(f'unsupported schema type {t!r}')

    @staticmethod
    def _advance_str(rest: Stack, fr: Frame, b: int) -> list[Stack]:
        esc = fr[1]
        hexleft = fr[2]

        if hexleft:
            return [(*rest, ('str', 0, hexleft - 1))] if b in HEX else []

        if esc:
            if b not in ESCAPES:
                return []
            return [(*rest, ('str', 0, 4 if b == ord('u') else 0))]

        if b == ord('"'):
            return [rest]

        if b == ord('\\'):
            return [(*rest, ('str', 1, 0))]

        if b < 0x20:
            return []

        return [(*rest, fr)]

    def _start_num(self, rest: Stack, integer: bool, b: int) -> list[Stack]:
        if b == ord('-'):
            return [(*rest, ('num', integer, 'sign'))]

        if b == ord('0'):
            return [(*rest, ('num', integer, 'int0'))]

        if b in DIGITS:
            return [(*rest, ('num', integer, 'int'))]

        return []

    def _advance_num(self, rest: Stack, fr: Frame, b: int) -> list[Stack]:
        integer = fr[1]
        phase = fr[2]
        complete = phase in ('int0', 'int', 'frac', 'exp')
        outs: list[Stack] = []

        if phase == 'sign':
            if b == ord('0'):
                outs.append((*rest, ('num', integer, 'int0')))

            elif b in DIGITS:
                outs.append((*rest, ('num', integer, 'int')))

        elif phase in ('int0', 'int'):
            if phase == 'int' and b in DIGITS:
                outs.append((*rest, fr))

            if not integer and b == ord('.'):
                outs.append((*rest, ('num', integer, 'frac0')))

            if not integer and b in (ord('e'), ord('E')):
                outs.append((*rest, ('num', integer, 'exp0')))

        elif phase == 'frac0':
            if b in DIGITS:
                outs.append((*rest, ('num', integer, 'frac')))

        elif phase == 'frac':
            if b in DIGITS:
                outs.append((*rest, fr))

            if b in (ord('e'), ord('E')):
                outs.append((*rest, ('num', integer, 'exp0')))

        elif phase == 'exp0':
            if b in (ord('+'), ord('-')):
                outs.append((*rest, ('num', integer, 'exp1')))

            elif b in DIGITS:
                outs.append((*rest, ('num', integer, 'exp')))

        elif phase == 'exp1':
            if b in DIGITS:
                outs.append((*rest, ('num', integer, 'exp')))

        elif phase == 'exp':
            if b in DIGITS:
                outs.append((*rest, fr))

        if complete:  # the number may end here; the byte belongs to what follows
            outs.extend(self._advance_stack(rest, b))

        return outs

    def _advance_obj(self, rest: Stack, fr: Frame, b: int) -> list[Stack]:
        """('obj', schema id, phase, keys seen, current key): phases first / key (expect a key), colon, value, after."""

        sid = fr[1]
        phase = fr[2]
        seen = fr[3]
        key = fr[4]

        schema = self.schemas[sid]
        props = schema.get('properties') or {}
        required = frozenset(schema.get('required') or [])
        extra = schema.get('additionalProperties', True)

        if b in WS:
            return [(*rest, fr)]

        if phase in ('first', 'key'):
            if phase == 'first' and b == ord('}'):
                return [rest] if required <= seen else []

            if b != ord('"'):
                return []

            remaining = tuple(sorted(k for k in props if k not in seen))
            outs: list[Stack] = []

            if remaining:  # a declared key, matched like a name; its closing quote completes it
                outs.append((*rest, ('obj', sid, 'colon', seen, None), ('keyname', remaining, 0)))

            if extra:  # any other key: its text is tracked so a declared name cannot sneak in through this branch
                outs.append((*rest, ('obj', sid, 'colon', seen, '*'), ('keystr', '')))

            return outs

        if phase == 'colon':
            if b == ord(':'):
                return [(*rest, ('obj', sid, 'value', seen, key))]

            return []

        if phase == 'value':
            vs = props.get(key) if key in props else (extra if isinstance(extra, dict) else {})
            after = ('obj', sid, 'after', seen | ({key} if key in props else set()), None)
            return self._start_value((*rest, after), vs, b)

        if phase == 'after':  # ',' (only if another key can follow) or '}'
            if b == ord(','):
                if not extra and not any(k not in seen for k in props):
                    return []  # every declared key is used and no others are allowed: nothing could follow

                return [(*rest, ('obj', sid, 'key', seen, None))]

            if b == ord('}'):
                return [rest] if required <= seen else []

            return []

        raise AssertionError(phase)

    def _advance_arr(self, rest: Stack, fr: Frame, b: int) -> list[Stack]:
        sid = fr[1]
        phase = fr[2]
        items = self.schemas[sid].get('items', {})

        if phase == 'first':
            if b in WS:
                return [(*rest, fr)]

            if b == ord(']'):
                return [rest]

            return self._start_value((*rest, ('arr', sid, 'after')), items, b)

        if phase == 'value':
            if b in WS:
                return [(*rest, fr)]

            return self._start_value((*rest, ('arr', sid, 'after')), items, b)

        if phase == 'after':
            if b in WS:
                return [(*rest, fr)]

            if b == ord(','):
                return [(*rest, ('arr', sid, 'value'))]

            if b == ord(']'):
                return [rest]

            return []

        raise AssertionError(phase)


##


class Vocab:
    """A byte trie over a tokenizer's tokens (special tokens excluded except the ones a tool call needs)."""

    _shared: dict[int, Vocab] = {}  # noqa

    @classmethod
    def for_tokenizer(cls, tok: Tokenizer) -> Vocab:
        """One trie per tokenizer object (a few seconds to build for a 248k vocabulary)."""

        v = cls._shared.get(id(tok))
        if v is None or v.tok is not tok:
            v = cls._shared[id(tok)] = cls(tok)
        return v

    def __init__(self, tok: Tokenizer, keep_special: ta.Iterable[str] = ('</tool_call>',)) -> None:
        super().__init__()

        self.tok = tok
        self.n = len(tok.tokens)
        keep = set(keep_special)
        self.root: dict = {}  # byte -> node; a node is a dict with an optional key -1 -> token id
        self.plain: set[int] = set()  # tokens that are fine anywhere inside a JSON string
        self.special_root: dict = {}  # trie over the tokens that are not plain
        self.bytes: list[bytes] = []

        for i in range(self.n):
            b = tok.token_bytes(i)
            self.bytes.append(b)

            if i in tok.special_ids and tok.tokens[i] not in keep:
                continue

            if not b:
                continue

            self._insert(self.root, b, i)

            if all(c >= 0x20 and c not in (0x22, 0x5C) for c in b) and tok.tokens[i] not in keep:
                self.plain.add(i)
            else:
                self._insert(self.special_root, b, i)

        self.plain_frozen = frozenset(self.plain)

    @staticmethod
    def _insert(root: dict, b: bytes, i: int) -> None:
        node = root
        for c in b:
            node = node.setdefault(c, {})
        node[-1] = i


class TokenMasks:
    """Allowed-token sets per acceptor state, memoised."""

    def __init__(self, acc: Acceptor, vocab: Vocab) -> None:
        super().__init__()

        self.acc = acc
        self.vocab = vocab
        self.memo: dict[State, frozenset[int]] = {}

    def allowed(self, state: State) -> frozenset[int]:
        got = self.memo.get(state)
        if got is not None:
            return got

        if all(st and st[-1] == ('str', 0, 0) for st in state):
            # inside a string, nothing escaped: every plain token continues it; only the others need checking
            out = set(self.vocab.plain)
            self._walk(state, self.vocab.special_root, out)

        else:
            out = set()
            self._walk(state, self.vocab.root, out)

        res = frozenset(out)
        self.memo[state] = res
        return res

    def _walk(self, state: State, node: dict, out: set[int]) -> None:
        for b, child in node.items():
            if b == -1:
                continue

            nst = self.acc.advance(state, b)
            if not nst:
                continue

            tid = child.get(-1)
            if tid is not None:
                out.add(tid)

            self._walk(nst, child, out)


##


_COMPILED: dict[tuple[str, str | None, int], tuple[Acceptor, TokenMasks]] = {}


def _compiled(tools: ta.Sequence[dict], only: str | None, vocab: Vocab) -> tuple[Acceptor, TokenMasks]:
    """
    The acceptor and its memoised masks for a tool set, shared across requests: an agent sends the same tools every
    turn, and the expensive states (free strings) are then computed once per process.
    """

    key = (json.dumps(tools, sort_keys=True), only, id(vocab))
    got = _COMPILED.get(key)
    if got is None:
        if len(_COMPILED) >= 16:
            _COMPILED.pop(next(iter(_COMPILED)))
        acc = Acceptor(tools, only)
        got = _COMPILED[key] = (acc, TokenMasks(acc, vocab))
    return got


@dc.dataclass()
class ToolConstraint:
    """
    The generation-side controller: feed it every generated token, ask it what the next one may be.

    Modes: 'free' (anything, unless tool_choice forces or forbids a call), 'call' (inside the acceptor), and back to
    'free' when a call completes. Detection is on bytes, so `<tool_call>` may be one token or several, and the reasoning
    block (`<think>` ... `</think>`) is tracked so that a forced call waits until reasoning is over.
    """

    tok: Tokenizer
    tools: ta.Sequence[dict]
    tool_choice: ta.Any = 'auto'  # 'auto' | 'none' | 'required' | {'type': 'function', 'function': {'name': ..}}
    thinking: bool = True         # the generation may start with a reasoning block

    def __post_init__(self) -> None:
        only = None
        if isinstance(self.tool_choice, dict):
            only = str((self.tool_choice.get('function') or {}).get('name') or self.tool_choice.get('name'))
        self.forced = self.tool_choice == 'required' or only is not None
        self.vocab = Vocab.for_tokenizer(self.tok)
        self.acc: Acceptor | None = None
        self.masks: TokenMasks | None = None
        if self.tool_choice != 'none':
            self.acc, self.masks = _compiled(self.tools, only, self.vocab)
        self.mode = 'free'
        self.state: State | None = None
        self.tail = b''  # last bytes of free text, for tag detection
        self.in_think = False
        self.calls = 0
        self.violations = 0
        self._ws_tokens = frozenset(
            i
            for i in range(self.vocab.n)
            if self.vocab.bytes[i]
            and all(c in WS for c in self.vocab.bytes[i])
        )
        self._tag_memo: dict[tuple[bool, bytes], frozenset[int]] = {}

    def clone(self) -> ToolConstraint:
        """A cheap copy for speculative lookahead (states are immutable; the memo is shared)."""

        c = object.__new__(ToolConstraint)
        c.__dict__.update(self.__dict__)
        return c

    OPEN_TAG = b'<tool_call>'

    def _pending_tag(self) -> bytes:
        """
        The longest suffix of the free text that is a proper prefix of '<tool_call>' (the tag may arrive in several
        tokens).
        """

        for n in range(min(len(self.tail), len(self.OPEN_TAG) - 1), 0, -1):
            if self.tail.endswith(self.OPEN_TAG[:n]):
                return self.OPEN_TAG[:n]
        return b''

    def _tag_set(self, forced: bool) -> frozenset[int]:
        """
        forced: tokens that continue / complete the tag (plus whitespace before it starts); otherwise all tokens except
        those that would complete it. Memoised per pending prefix.
        """

        pend = self._pending_tag()
        key = (forced, pend)

        got = self._tag_memo.get(key)
        if got is not None:
            return got

        tag = self.OPEN_TAG
        out: set[int] = set()

        for i in range(self.vocab.n):
            b = self.vocab.bytes[i]
            if not b:
                continue

            joined = pend + b
            completes = tag in joined

            if forced:
                if completes or tag.startswith(joined) or (not pend and i in self._ws_tokens):
                    out.add(i)

            elif not completes:
                out.add(i)

        res = frozenset(out)
        self._tag_memo[key] = res
        return res

    def allowed(self) -> frozenset[int] | None:
        """The ids the next token may take, or None for no restriction."""

        if self.mode == 'call':
            return check.not_none(self.masks).allowed(check.not_none(self.state))

        if self.tool_choice == 'none':
            return self._tag_set(False)

        if self.forced and self.calls == 0 and not self.in_think:
            return self._tag_set(True)

        return None

    def feed(self, token_id: int) -> None:
        b = self.vocab.bytes[token_id]

        if self.mode == 'call':
            acc = check.not_none(self.acc)
            st = check.not_none(self.state)

            for c in b:
                st = acc.advance(st, c)
                if not st:
                    break

            if not st:
                # the token broke the grammar (only possible unconstrained, e.g. a draft the verify step rejects before
                # it is ever committed, or thinking-mode text that looked like a call): back to free text
                self.violations += 1
                self.mode = 'free'
                self.state = None
                self.tail = b''
                return

            if acc.is_complete(st):
                self.calls += 1
                self.mode = 'free'
                self.state = None
                self.tail = b''

            else:
                self.state = st

            return

        self.tail = (self.tail + b)[-24:]

        if self.thinking:
            if self.tail.endswith(b'<think>'):
                self.in_think = True

            elif self.tail.endswith(b'</think>'):
                self.in_think = False

        if self.acc is not None and self.tail.endswith(b'<tool_call>'):
            self.mode = 'call'
            self.state = self.acc.initial()
            self.in_think = False


@dc.dataclass()
class JsonConstraint:
    """
    JSON mode (`response_format`): after the reasoning block, if any, the content is one JSON value of `schema` (`{}`
    for any value) and then the turn ends. Same protocol as ToolConstraint: feed every generated token, ask for the
    allowed set. Once the value can end, the end-of-turn ids are allowed too (and once it has ended, only they are).
    """

    tok: Tokenizer
    schema: ta.Any = None
    thinking: bool = True

    def __post_init__(self) -> None:
        self.vocab = Vocab.for_tokenizer(self.tok)
        self.acc = Acceptor(value_schema=self.schema if self.schema is not None else {})
        self.masks = TokenMasks(self.acc, self.vocab)
        self.state: State | None = None  # None until the value starts (after the reasoning block)
        self.done = False
        self.in_think = False
        self.started = False
        self.tail = b''
        self.end_ids = frozenset(
            i
            for i in self.tok.special_ids
            if self.tok.tokens[i] in ('<|im_end|>', '<|endoftext|>')
            or i == self.tok.eos_id
        )
        self._think_set: frozenset[int] | None = None

    def clone(self) -> JsonConstraint:
        c = object.__new__(JsonConstraint)
        c.__dict__.update(self.__dict__)
        return c

    def _think_tokens(self) -> frozenset[int]:
        """Inside the reasoning block anything goes except an end of turn; memoised."""

        if self._think_set is None:
            self._think_set = frozenset(i for i in range(self.vocab.n) if i not in self.end_ids)
        return self._think_set

    def allowed(self) -> frozenset[int] | None:
        if self.done:
            return self.end_ids

        if self.in_think:
            return self._think_tokens()

        if not self.started and self.thinking and not self.tail:
            # the very first token: a reasoning block may open, or the value may start
            return self._think_open() | self.masks.allowed(self.acc.initial())

        st = self.state if self.state is not None else self.acc.initial()
        out = self.masks.allowed(st)
        if self.acc.can_end(st):
            out = out | self.end_ids

        return out

    def _think_open(self) -> frozenset[int]:
        got = getattr(self, '_think_open_set', None)
        if got is None:
            got = self._think_open_set = frozenset(
                i
                for i in range(self.vocab.n)
                if b'<think>'.startswith(self.vocab.bytes[i])
                and self.vocab.bytes[i]
            )
        return got

    def feed(self, token_id: int) -> None:
        if self.done:
            return

        if token_id in self.end_ids:
            self.done = True
            return

        b = self.vocab.bytes[token_id]
        if self.in_think:
            self.tail = (self.tail + b)[-16:]

            if self.tail.endswith(b'</think>'):
                self.in_think = False
                self.tail = b''

            return

        if not self.started:
            self.tail = (self.tail + b)[-16:]

            if b'<think>'.startswith(self.tail):
                if self.tail == b'<think>':
                    self.in_think = True
                    self.tail = b''

                return

            self.started = True
            self.tail = b''

            st = self.acc.initial()

        else:
            st = self.state if self.state is not None else self.acc.initial()

        for c in b:
            st = self.acc.advance(st, c)
            if not st:
                break

        self.state = st or self.acc.initial()  # a violation (unconstrained draft): restart, never commits

        if st and self.acc.is_complete(st):
            self.done = True


class MaskCache:
    """
    Allowed-token sets as device logit masks ([V] float32, 1 allowed / 0 not), cached by the set object: the acceptor
    memoises its sets, so inside a string the same object comes back every step and nothing is rebuilt or re-uploaded.
    """

    def __init__(self, ops: ta.Any, vocab_size: int) -> None:
        super().__init__()

        self.ops = ops
        self.n = vocab_size
        self.cache: dict[int, tuple[frozenset[int], ta.Any]] = {}

    def mask(self, allowed: frozenset[int] | None) -> ta.Any:
        if allowed is None:
            return None

        got = self.cache.get(id(allowed))
        if got is not None and got[0] is allowed:
            return got[1]

        m = np.zeros(self.n, dtype=np.float32)
        m[list(allowed)] = 1.0

        t = self.ops.array(m, self.ops.dtype('f32'))

        if len(self.cache) > 4096:
            self.cache.clear()
        self.cache[id(allowed)] = (allowed, t)

        return t

    def rows(self, sets: ta.Sequence[frozenset[int] | None]) -> ta.Any:
        """A [T, V] mask for T positions (None rows are all ones), or None if nothing is restricted."""

        if all(s is None for s in sets):
            return None

        ones = None
        rows = []

        for s in sets:
            if s is None:
                if ones is None:
                    ones = self.ops.zeros((self.n,), self.ops.dtype('f32')) + 1

                rows.append(ones)

            else:
                rows.append(self.mask(s))

        return self.ops.stack(rows, 0)
