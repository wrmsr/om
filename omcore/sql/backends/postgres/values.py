from ...dtypes.codecs import BaseDtypeCodec


##


class PostgresDtypeCodec(BaseDtypeCodec):
    """og8000 already speaks the canonical forms: uuids, tz-aware timestamps, bools, and bytes come back as such."""
