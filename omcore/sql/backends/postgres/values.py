import typing as ta

from ...dtypes.codecs import BaseDtypeCodec


##


class PostgresDtypeCodec(BaseDtypeCodec):
    """og8000 already speaks the canonical forms: uuids, tz-aware timestamps, bools, and bytes come back as such."""

    def decode_json(self, v: ta.Any) -> ta.Any:
        # As do json documents, parsed - so a str here is a document which is one, not the text of one to be read.
        return v
