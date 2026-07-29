import typing as ta

from .... import dataclasses as dc
from .errors import JsonStreamError
from .events import BeginArray
from .events import BeginObject
from .events import EndArray
from .events import EndObject
from .events import Event
from .events import Key
from .tokens import CONST_IDENT_VALUES
from .tokens import VALUE_TOKEN_KINDS
from .tokens import Position
from .tokens import Token


_ParserState: ta.TypeAlias = ta.Literal[
    'VALUE',
    'VALUE_REQUIRED',
    'OBJECT_BODY',
    'OBJECT_BODY_REQUIRED',
    'AFTER_KEY',
    'AFTER_PAIR',
    'AFTER_ELEMENT',

    # Terminal states: 'DEAD' is entered when a call raises - further calls return nothing and close is quiet, matching
    # the dead-generator behavior of the GenMachine implementation this replaced. 'CLOSED' is entered by close.
    'DEAD',
    'CLOSED',
]


##


@dc.dataclass()
class JsonStreamParseError(JsonStreamError):
    message: str

    pos: Position | None = None


class JsonStreamParserClosedError(JsonStreamError):
    pass


class JsonStreamObject(list):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({super().__repr__()})'


class JsonStreamParser:
    """
    A plain, non-suspending state machine consuming `Token`s one at a time via `__call__` and returning any `Event`s
    produced. `close` must be called after the final token - an incomplete document raises from there.
    """

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        allow_trailing_commas: bool = False

        allow_ident_values: bool = False

        allow_extended_idents: bool = False

    def __init__(
            self,
            config: Config = Config(),
    ) -> None:
        super().__init__()

        self._config = config

        self._stack: list[ta.Literal['OBJECT', 'KEY', 'ARRAY']] = []
        self._state: _ParserState = 'VALUE'
        self._key: ta.Any = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}@{id(self):x}<{self._state}>'

    #

    @property
    def state(self) -> _ParserState:
        return self._state

    @property
    def closed(self) -> bool:
        return self._state == 'CLOSED' or self._state == 'DEAD'

    def close(self) -> None:
        state = self._state
        self._state = 'CLOSED'

        if state == 'CLOSED' or state == 'DEAD':
            return

        if state == 'VALUE' or state == 'VALUE_REQUIRED':
            if self._stack:
                raise JsonStreamParseError('Expected value')
        elif state == 'OBJECT_BODY' or state == 'OBJECT_BODY_REQUIRED':
            raise JsonStreamParseError('Expected object body')
        elif state == 'AFTER_KEY':
            raise JsonStreamParseError('Expected key')
        else:
            raise JsonStreamParseError('Expected continuation')

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #

    def _emit_value(self, v: Event) -> tuple[Event, ...]:
        if not (stack := self._stack):
            self._state = 'VALUE'
            return (v,)

        tt = stack[-1]
        if tt == 'KEY':
            stack.pop()
            if not stack or stack[-1] != 'OBJECT':
                raise JsonStreamParseError('Unexpected key')

            self._state = 'AFTER_PAIR'
            return (v,)

        elif tt == 'ARRAY':
            self._state = 'AFTER_ELEMENT'
            return (v,)

        else:
            raise JsonStreamParseError(f'Unexpected value: {v!r}')

    def _end_object(self) -> tuple[Event, ...]:
        if not (stack := self._stack) or stack.pop() != 'OBJECT':
            raise JsonStreamParseError('Unexpected end object')

        return self._emit_value(EndObject)

    def _end_array(self) -> tuple[Event, ...]:
        if not (stack := self._stack) or stack.pop() != 'ARRAY':
            raise JsonStreamParseError('Unexpected end array')

        return self._emit_value(EndArray)

    #

    def _on_value(self, tok: Token, required: bool) -> tuple[Event, ...]:
        if (kind := tok.kind) in VALUE_TOKEN_KINDS:
            return self._emit_value(tok.value)

        elif kind == 'IDENT':
            try:
                # IDENT token values are always strs
                cv = CONST_IDENT_VALUES[tok.value]  # type: ignore[index]
            except KeyError:
                if not self._config.allow_ident_values:
                    raise JsonStreamParseError('Expected value', tok.position) from None
                return self._emit_value(tok.value)
            return self._emit_value(cv)

        elif kind == 'LBRACE':
            self._stack.append('OBJECT')
            self._state = 'OBJECT_BODY'
            return (BeginObject,)

        elif kind == 'LBRACKET':
            self._stack.append('ARRAY')
            self._state = 'VALUE'
            return (BeginArray,)

        elif required:
            raise JsonStreamParseError('Expected value', tok.position)

        elif kind == 'RBRACKET':
            return self._end_array()

        else:
            raise JsonStreamParseError('Expected value', tok.position)

    def _on_object_body(self, tok: Token, required: bool) -> tuple[Event, ...]:
        if (kind := tok.kind) == 'STRING' or (self._config.allow_extended_idents and kind == 'IDENT'):
            self._key = tok.value
            self._state = 'AFTER_KEY'
            return ()

        elif required:
            raise JsonStreamParseError('Expected value', tok.position)

        elif kind == 'RBRACE':
            return self._end_object()

        else:
            raise JsonStreamParseError('Expected value', tok.position)

    def _on_after_key(self, tok: Token) -> tuple[Event, ...]:
        if tok.kind != 'COLON':
            raise JsonStreamParseError('Expected colon', tok.position)

        k = self._key
        self._key = None

        self._stack.append('KEY')
        self._state = 'VALUE'
        return (Key(k),)

    def _on_after_pair(self, tok: Token) -> tuple[Event, ...]:
        if (kind := tok.kind) == 'COMMA':
            self._state = 'OBJECT_BODY' if self._config.allow_trailing_commas else 'OBJECT_BODY_REQUIRED'
            return ()

        elif kind == 'RBRACE':
            return self._end_object()

        else:
            raise JsonStreamParseError('Expected continuation', tok.position)

    def _on_after_element(self, tok: Token) -> tuple[Event, ...]:
        if (kind := tok.kind) == 'COMMA':
            self._state = 'VALUE' if self._config.allow_trailing_commas else 'VALUE_REQUIRED'
            return ()

        elif kind == 'RBRACKET':
            return self._end_array()

        else:
            raise JsonStreamParseError('Expected continuation', tok.position)

    #

    def __call__(self, tok: Token) -> ta.Sequence[Event]:
        if (kind := tok.kind) == 'SPACE' or kind == 'COMMENT':
            return ()

        try:
            if (state := self._state) == 'VALUE':
                return self._on_value(tok, False)

            elif state == 'OBJECT_BODY':
                return self._on_object_body(tok, False)

            elif state == 'AFTER_KEY':
                return self._on_after_key(tok)

            elif state == 'AFTER_PAIR':
                return self._on_after_pair(tok)

            elif state == 'AFTER_ELEMENT':
                return self._on_after_element(tok)

            elif state == 'VALUE_REQUIRED':
                return self._on_value(tok, True)

            elif state == 'OBJECT_BODY_REQUIRED':
                return self._on_object_body(tok, True)

            elif state == 'DEAD':
                return ()

            else:
                raise JsonStreamParserClosedError

        except JsonStreamParseError:
            self._state = 'DEAD'
            raise
