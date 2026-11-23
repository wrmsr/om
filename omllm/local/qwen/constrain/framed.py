"""
Constrained decoding for a chat protocol of framed messages (Inkling 2's: serve/inkling2.py), on the acceptor and
token masks of constrain/grammar.py.

There a model's turn is a run of messages, each opened by one token, then a header -- empty, or a tool's name -- then a
token naming the message's channel, then the body, then the token that ends it; another token ends the turn. All of
those are single special tokens, so where a turn stands is read off the ids (`FrameTokens`; nothing is detected in
text), exactly as the protocol's reader reads it off the markers. What is held:

- **A tool call** -- a message on the call channel -- has a declared tool's name for its header, and for its body

      {"name": that name, <args key>: JSON of that tool's parameters}

  and nothing after it but the end of the message: the header is held to the declared names a token at a time, the
  call channel is offered only once it is one of them, and the body runs under the acceptor. So a call that comes out
  names a real tool, twice and the same, with arguments of the declared types and every required key present.
- `tool_choice` 'none' never offers the call channel. 'required' / a named function: the turn's messages are, at
  most, one of reasoning and then a call; nothing ends the turn before a call is complete. After it, a 'required'
  turn is the model's own again; a named function's turn ends there -- that call is the answer, and a model that
  wanted another tool would otherwise go on calling the one it is allowed.
- **JSON mode** (`FramedJsonConstraint`): at most one message of reasoning, then one text message whose body is one
  JSON value of the schema, then the end of the turn.
- **Thinking off** (every controller's `thinking`): the reasoning channel is not offered, so the turn has no message
  of reasoning. A protocol whose prompt can only state an effort needs this to make "off" mean off: at effort 0 the
  released Inkling 2 Mini still opens one.
- **No tools** (`FramedPlainConstraint`, what a turn is held to when nothing above applies): a message has no header
  and is not a call. Without it the same model, refused its reasoning, called a tool nobody had declared.

Outside those, nothing is restricted: what a text or a reasoning message says is the model's own.

Layout whitespace is rationed (`max_blank`): JSON allows any amount of it between tokens, and a model whose next
choice the grammar has just refused -- a code fence before the value, a closing brace before a required key -- will
take the whitespace it is still offered, again and again, to the length limit. After `max_blank` whitespace tokens
in a row outside a string no more are offered, so the model moves on; what it writes is as valid, less indented at
worst. Inside strings whitespace is content and is left alone.

One thing is not held, here or in the ChatML controllers: the protocol's reader works on decoded text, so a marker
spelled out in ordinary tokens inside a body reads as the marker.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ..tokenizer import Tokenizer
from .grammar import Acceptor
from .grammar import Constraint
from .grammar import JsonCallSpelling
from .grammar import State
from .grammar import TokenMasks
from .grammar import Vocab
from .grammar import compiled_calls
from .grammar import compiled_json
from .grammar import tool_choice_function


##


@dc.dataclass(frozen=True)
class FrameTokens:
    """The ids a framed-message protocol's turn is read by."""

    open_model: int                # opens a message of the model's: its header follows
    boundaries: ta.AbstractSet[int]  # whatever ends the message under way: the end of a message, any message's opener
    end_message: int
    channels: ta.AbstractSet[int]  # every channel marker: ends a header, the body follows
    thinking: int                  # the channels a controller tells apart: reasoning,
    text: int                      # the answer,
    call: int                      # a tool call
    ends: ta.AbstractSet[int]      # the end of the turn (where generation stops)


class _FrameSets:
    """The token sets every request's controller needs of a vocabulary and its frame tokens, found once."""

    _shared: ta.ClassVar[dict[tuple[int, FrameTokens], _FrameSets]] = {}

    @classmethod
    def of(cls, vocab: Vocab, frames: FrameTokens) -> _FrameSets:
        key = (id(vocab), frames)
        got = cls._shared.get(key)
        if got is None or got.vocab is not vocab:
            if len(cls._shared) >= 8:
                cls._shared.pop(next(iter(cls._shared)))
            got = cls._shared[key] = cls(vocab, frames)
        return got

    def __init__(self, vocab: Vocab, frames: FrameTokens) -> None:
        super().__init__()

        self.vocab = vocab
        everything = frozenset(range(vocab.n))
        self.unended = everything - frames.ends      # anything that does not end the turn
        self.uncalled = everything - {frames.call}   # anything that does not open a call
        self.unthought = everything - {frames.thinking}  # ... a message of reasoning
        self.plain = self.uncalled & self.unthought      # ... either
        self.open_model = frozenset([frames.open_model])
        self.end_message = frozenset([frames.end_message])
        self.text = frozenset([frames.text])
        self.thinking_or_text = frozenset([frames.thinking, frames.text])
        self.ends = frozenset(frames.ends)
        self.other_channels = frozenset(frames.channels) - {frames.call} - frames.ends
        self.other_channels_unthought = self.other_channels - {frames.thinking}
        self.memo: dict[ta.Any, frozenset[int]] = {}

    def continuing(self, names: ta.Iterable[bytes], header: bytes) -> frozenset[int]:
        """The tokens that take `header` further toward one of `names` without passing it."""

        out: set[int] = set()
        for nb in names:
            if not nb.startswith(header):
                continue
            node: dict | None = self.vocab.root
            for c in nb[len(header):]:
                node = check.not_none(node).get(c)
                if node is None:
                    break
                tid = node.get(-1)
                if tid is not None:
                    out.add(tid)
        return frozenset(out)


class _FramedConstraint(Constraint):
    """Where a turn stands in the framing, as the protocol's reader tracks it; the two controllers below share it."""

    tok: Tokenizer
    frames: FrameTokens
    max_blank: int

    def _start(self) -> None:
        self.vocab = Vocab.for_tokenizer(self.tok)
        self.sets = _FrameSets.of(self.vocab, self.frames)
        self.kind: str | None = None  # None: between messages; 'header'; 'reasoning' | 'content' | 'call'
        self.header = b''
        self.messages = 0  # the model's messages opened so far
        self.state: State | None = None  # the acceptor's, inside the body it holds
        self.blank = 0  # the whitespace tokens that body has just run, outside a string
        self.done = False  # the turn has ended
        self.violations = 0

    def clone(self) -> ta.Any:
        c = object.__new__(type(self))
        c.__dict__.update(self.__dict__)
        return c

    def feed(self, token_id: int) -> None:
        fr = self.frames

        if self.done:
            return

        if token_id in fr.ends:
            self.done = True
            return

        if token_id in fr.boundaries:
            self._leave(token_id)
            self.kind = 'header' if token_id == fr.open_model else None
            self.header = b''
            self.state = None
            if self.kind == 'header':
                self.messages += 1
            return

        if self.kind == 'header':
            if token_id in fr.channels:
                self.blank = 0
                self.kind = self._enter(token_id)
            else:
                self.header += self.vocab.bytes[token_id]
            return

        if self.state is not None:
            self._body(token_id)

    def _advance(self, acc: Acceptor, token_id: int) -> State:
        st = check.not_none(self.state)
        blank = token_id in self.vocab.ws_tokens and not acc.in_text(st)
        self.blank = self.blank + 1 if blank else 0
        for c in self.vocab.bytes[token_id]:
            st = acc.advance(st, c)
            if not st:
                break
        return st

    def _held(self, acc: Acceptor, masks: TokenMasks) -> frozenset[int]:
        """What the acceptor allows next -- without more layout whitespace, once `max_blank` tokens of it have run."""

        st = check.not_none(self.state)
        out = masks.allowed(st)
        if self.blank < self.max_blank or acc.in_text(st):
            return out

        # (the same object for the same set, as the masks' own are: a device mask is cached by it)
        key = ('unblank', out)
        got = self.sets.memo.get(key)
        if got is None:
            got = self.sets.memo[key] = out - self.vocab.ws_tokens
        return got

    def _enter(self, channel: int) -> str:
        """A header has ended at `channel`: the kind of body that follows (and `state`, where the acceptor holds it)."""

        raise NotImplementedError

    def _body(self, token_id: int) -> None:
        """A token of a body the acceptor holds."""

        raise NotImplementedError

    def _leave(self, boundary: int) -> None:
        """The message under way, if any, has ended."""


@dc.dataclass()
class FramedToolConstraint(_FramedConstraint):
    """
    Tool calls in a framed-message protocol (the module docstring has what is held). The same protocol as
    grammar.ToolConstraint: feed it every generated token, ask it what the next one may be.
    """

    tok: Tokenizer
    frames: FrameTokens
    tools: ta.Sequence[dict]
    spelling: JsonCallSpelling    # how the protocol spells a call's body (its `close` empty: the message's end is it)
    tool_choice: ta.Any = 'auto'  # 'auto' | 'none' | 'required' | {'type': 'function', 'function': {'name': ..}}
    thinking: bool = True         # reasoning may be written (a forced call waits for at most one message of it)
    max_blank: int = 2            # whitespace tokens in a row between a call's JSON tokens

    def __post_init__(self) -> None:
        self._start()

        only = tool_choice_function(self.tool_choice)
        self.forced = self.tool_choice == 'required' or only is not None
        self.single = only is not None  # the one call is the turn
        self.acc: Acceptor | None = None
        self.masks: TokenMasks | None = None
        self.names: dict[bytes, str] = {}  # the tools a call may name, by the bytes of a header that names them
        if self.tool_choice != 'none':
            self.acc, self.masks = compiled_calls(self.tools, only, self.vocab, 'json', self.spelling)
            self.names = {n.encode(): n for n in sorted(self.acc.functions)}
        self.names_key = tuple(self.names)
        self.calls = 0

    @property
    def _waiting(self) -> bool:
        """A call is owed and none is complete yet: nothing but reasoning and that call may come."""

        return self.forced and self.calls == 0

    def allowed(self) -> frozenset[int] | None:
        sets = self.sets

        if self.done:
            return None

        if self.kind == 'call':
            st = check.not_none(self.state)
            if Acceptor.is_complete(st):
                return sets.end_message
            return self._held(check.not_none(self.acc), check.not_none(self.masks))

        if self.single and self.calls:
            return sets.ends if self.kind is None else sets.end_message

        if self.kind == 'header':
            return self._header_set()

        if not self._waiting:
            return None

        if self.kind is None:
            return sets.open_model
        return sets.unended

    def _header_set(self) -> frozenset[int] | None:
        sets = self.sets
        uncalled = sets.uncalled if self.thinking else sets.plain

        if self.acc is None:
            return uncalled

        header = self.header
        if not any(n.startswith(header) for n in self.names):
            # (not on the way to a tool's name -- only an unconstrained draft gets here: no call can come of it)
            return uncalled

        key = (self.names_key, header, self._waiting, self.thinking, self.messages == 1)
        got = sets.memo.get(key)
        if got is not None:
            return got

        out = set(sets.continuing(self.names, header))
        if header:
            if header in self.names:
                out.add(self.frames.call)
        elif not self._waiting:
            out |= sets.other_channels if self.thinking else sets.other_channels_unthought
        elif self.thinking and self.messages == 1:
            out.add(self.frames.thinking)

        res = sets.memo[key] = frozenset(out)
        return res

    def _enter(self, channel: int) -> str:
        fr = self.frames

        if channel == fr.thinking:
            return 'reasoning'

        if channel != fr.call:
            return 'content'

        name = self.names.get(self.header)
        if self.acc is None or name is None:
            self.violations += 1  # (an unconstrained draft)
            return 'content'

        self.state = self.acc.initial((name,))
        return 'call'

    def _body(self, token_id: int) -> None:
        acc = check.not_none(self.acc)
        if Acceptor.is_complete(check.not_none(self.state)):
            st: State = frozenset()  # (nothing follows a complete call but the end of its message)
        else:
            st = self._advance(acc, token_id)

        if not st:
            # the token broke the grammar (only possible unconstrained: a draft the verify step rejects before it is
            # ever committed)
            self.violations += 1
            self.kind = 'content'
            self.state = None
            return

        self.state = st
        if acc.is_complete(st):
            self.calls += 1


@dc.dataclass()
class FramedJsonConstraint(_FramedConstraint):
    """
    JSON mode (`response_format`) in a framed-message protocol: at most one message of reasoning, then one text
    message whose body is one JSON value of `schema` (`{}` for any value), then the end of the turn.
    """

    tok: Tokenizer
    frames: FrameTokens
    schema: ta.Any = None
    thinking: bool = True
    max_blank: int = 2  # whitespace tokens in a row around the value's JSON tokens

    def __post_init__(self) -> None:
        self._start()

        self.acc, self.masks = compiled_json(self.schema if self.schema is not None else {}, self.vocab)
        self.answered = False  # the value's message has ended

    def allowed(self) -> frozenset[int] | None:
        sets = self.sets

        if self.done:
            return None

        if self.answered:
            return sets.ends

        if self.kind is None:
            return sets.open_model

        if self.kind == 'header':
            if self.thinking and self.messages == 1 and not self.header:
                return sets.thinking_or_text
            return sets.text

        if self.state is None:
            return sets.unended  # reasoning

        out = self._held(self.acc, self.masks)
        if self.acc.can_end(self.state):
            key = ('ending', out)
            got = sets.memo.get(key)
            if got is None:
                got = sets.memo[key] = out | sets.end_message
            return got
        return out

    def _enter(self, channel: int) -> str:
        if channel == self.frames.thinking:
            return 'reasoning'
        self.state = self.acc.initial()
        return 'content'

    def _body(self, token_id: int) -> None:
        st = self._advance(self.acc, token_id)
        if not st:
            self.violations += 1  # (an unconstrained draft: restart, it never commits)
            st = self.acc.initial()
        self.state = st

    def _leave(self, boundary: int) -> None:
        if self.state is not None and boundary == self.frames.end_message and self.acc.can_end(self.state):
            self.answered = True


@dc.dataclass()
class FramedPlainConstraint(_FramedConstraint):
    """
    A turn with no tools declared and no format asked for: each message is opened on a channel that is neither a
    call nor, with `thinking` off, reasoning; the rest is the model's.
    """

    tok: Tokenizer
    frames: FrameTokens
    thinking: bool = True
    max_blank: int = 0  # (no body is held)

    def __post_init__(self) -> None:
        self._start()

    def allowed(self) -> frozenset[int] | None:
        if self.kind == 'header' and not self.done:
            return self.sets.other_channels if self.thinking else self.sets.other_channels_unthought
        return None

    def _enter(self, channel: int) -> str:
        return 'reasoning' if channel == self.frames.thinking else 'content'
