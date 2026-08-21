"""Result set decoding: turning column definitions and raw row packets into described, converted Python rows."""
import typing as ta

from omcore import dataclasses as dc

from ..constants import FIELD_TYPE
from .messages import ColumnDefinition
from .parsing import parse_text_row


##


# The field types whose values are text under the connection encoding (as opposed to ascii-encoded scalars).
TEXT_TYPES = frozenset({
    FIELD_TYPE.BIT,
    FIELD_TYPE.BLOB,
    FIELD_TYPE.LONG_BLOB,
    FIELD_TYPE.MEDIUM_BLOB,
    FIELD_TYPE.STRING,
    FIELD_TYPE.TINY_BLOB,
    FIELD_TYPE.VAR_STRING,
    FIELD_TYPE.VARCHAR,
    FIELD_TYPE.GEOMETRY,
})

BINARY_CHARSETNR = 63

RowConverter: ta.TypeAlias = ta.Callable[[str], ta.Any]

# Per column: the encoding to decode its bytes with (None to leave as bytes), and an optional value converter.
ColumnCoder: ta.TypeAlias = tuple[str | None, RowConverter | None]


@dc.dataclass(frozen=True)
class ResultSchema:
    """The decoding plan for a result set: its columns and how to turn each column's bytes into a Python value."""

    fields: ta.Sequence[ColumnDefinition]
    coders: ta.Sequence[ColumnCoder]

    @property
    def description(self) -> tuple[tuple[ta.Any, ...], ...]:
        return tuple(f.description() for f in self.fields)


def build_result_schema(
        fields: ta.Sequence[ColumnDefinition],
        *,
        encoding: str,
        use_unicode: bool,
        decoders: ta.Mapping[int, RowConverter | None],
) -> ResultSchema:
    coders: list[ColumnCoder] = []
    for field in fields:
        field_type = field.type_code
        if not use_unicode:
            col_encoding: str | None = None
        elif field_type == FIELD_TYPE.JSON:
            # JSON columns arrive with charset=binary, but should be decoded with the connection encoding.
            col_encoding = encoding
        elif field_type in TEXT_TYPES:
            # A binary charset on a text type means a BINARY / BLOB type, whose value stays bytes.
            col_encoding = None if field.charsetnr == BINARY_CHARSETNR else encoding
        else:
            # Integers, dates, times and other scalars are ascii.
            col_encoding = 'ascii'

        converter = decoders.get(field_type)
        coders.append((col_encoding, converter))

    return ResultSchema(fields, coders)


def decode_row(payload: bytes, schema: ResultSchema) -> tuple[ta.Any, ...]:
    raw = parse_text_row(payload)
    row: list[ta.Any] = []
    for value, (encoding, converter) in zip(raw, schema.coders, strict=False):
        if value is None:
            row.append(None)
            continue
        decoded: ta.Any = value.decode(encoding) if encoding is not None else value
        if converter is not None:
            decoded = converter(decoded)
        row.append(decoded)
    return tuple(row)
