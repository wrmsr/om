import typing as ta

from ...formats.json.stream.events import BeginArray as JsonBeginArray
from ...formats.json.stream.events import BeginObject as JsonBeginObject
from ...formats.json.stream.events import EndArray as JsonEndArray
from ...formats.json.stream.events import EndObject as JsonEndObject
from ...formats.json.stream.events import Event as JsonEvent
from ...formats.json.stream.events import Key as JsonKey
from ...formats.json.stream.lexing import JsonStreamLexer
from ...formats.json.stream.parsing import JsonStreamParser
from ...formats.json.stream.tokens import SCALAR_VALUE_TYPES
from .errors import JqStructureError
from .events import BeginArray
from .events import BeginObject
from .events import EndArray
from .events import EndObject
from .events import ObjectKey
from .events import Scalar
from .events import StructuralEvent


##


def adapt_json_stream_events(events: ta.Iterable[JsonEvent]) -> ta.Iterator[StructuralEvent]:
    for event in events:
        if event is JsonBeginArray:
            yield BeginArray()
        elif event is JsonEndArray:
            yield EndArray()
        elif event is JsonBeginObject:
            yield BeginObject()
        elif event is JsonEndObject:
            yield EndObject()
        elif isinstance(event, JsonKey):
            yield ObjectKey(event.key)
        elif isinstance(event, SCALAR_VALUE_TYPES):
            yield Scalar(event)
        else:
            raise JqStructureError(f'unknown JSON structural event: {event!r}')


def parse_json_structural_events(chunks: str | ta.Iterable[str]) -> ta.Iterator[StructuralEvent]:
    if isinstance(chunks, str):
        chunk_iterator: ta.Iterable[str] = (chunks,)
    else:
        chunk_iterator = chunks

    lexer = JsonStreamLexer()
    parser = JsonStreamParser()
    with lexer, parser:
        for chunk in chunk_iterator:
            if not chunk:
                continue
            for token in lexer(chunk):
                yield from adapt_json_stream_events(parser(token))
        for token in lexer(''):
            yield from adapt_json_stream_events(parser(token))
