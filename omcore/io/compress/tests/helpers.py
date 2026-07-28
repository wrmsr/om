import typing as ta

from .... import lang
from ...transforms.funcs import run_stream_transform
from ...transforms.types import ByteStreamTransform


def run_transform_chunked(t: ByteStreamTransform[ta.Any], data: lang.Bytes, *, chunk_size: int = 13) -> bytes:
    return b''.join(run_stream_transform(t, (data[i:i + chunk_size] for i in range(0, len(data), chunk_size))))
