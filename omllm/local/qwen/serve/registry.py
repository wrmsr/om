"""
Which chat protocol a checkpoint speaks, by what its tokenizer is seen to have: the families in order, the first that
recognizes the tokenizer, ChatML -- whose formats tell themselves apart by the chat template (chat.py) -- for the
rest. An explicit chat format is one of ChatML's, and is taken as said.
"""
import typing as ta

from omcore import dataclasses as dc

from ..tokenizer import Tokenizer
from .chat import ChatFormat
from .chatml import ChatmlProtocol
from .inkling2 import Inkling2ChatProtocol
from .inkling2 import speaks_inkling2
from .protocols import ChatProtocol


##


@dc.dataclass(frozen=True)
class ChatOptions:
    """
    What a server says about how conversations are rendered. `reasoning_effort` is every protocol's (the effort of a
    request that names none); the rest are ChatML's (chatml.py).
    """

    reasoning_effort: ta.Any = None
    chat_format: ChatFormat | None = None
    open_think: bool | None = None
    preserve_thinking: bool = True


@dc.dataclass(frozen=True)
class ChatProtocolFamily:
    name: str
    speaks: ta.Callable[[Tokenizer], bool]
    make: ta.Callable[[Tokenizer, ChatOptions], ChatProtocol]


def _make_inkling2(tok: Tokenizer, options: ChatOptions) -> ChatProtocol:
    return Inkling2ChatProtocol(tok, reasoning_effort=options.reasoning_effort)


def _make_chatml(tok: Tokenizer, options: ChatOptions) -> ChatProtocol:
    return ChatmlProtocol(
        tok,
        chat_format=options.chat_format,
        open_think=options.open_think,
        preserve_thinking=options.preserve_thinking,
        reasoning_effort=options.reasoning_effort,
    )


CHATML_FAMILY = ChatProtocolFamily('chatml', lambda tok: True, _make_chatml)

CHAT_PROTOCOL_FAMILIES: ta.Sequence[ChatProtocolFamily] = (
    ChatProtocolFamily('inkling2', speaks_inkling2, _make_inkling2),
    CHATML_FAMILY,
)


def chat_protocol_for(tok: Tokenizer, options: ChatOptions | None = None) -> ChatProtocol:
    options = options if options is not None else ChatOptions()

    if options.chat_format is not None:
        return CHATML_FAMILY.make(tok, options)

    for family in CHAT_PROTOCOL_FAMILIES:
        if family.speaks(tok):
            return family.make(tok, options)

    raise ValueError('no chat protocol for this tokenizer')
