# ruff: noqa: UP006 UP007 UP045
# @om-lite
from ....lite.check import check
from ..chunking import IoPipelineHttpObjectChunker
from ..compression.compressors import IoPipelineHttpObjectCompressor
from ..encoders import IoPipelineHttpObjectEncoder
from ..objects import IoPipelineHttpMessageHead
from ..responses import IoPipelineHttpResponseHead
from ..responses import IoPipelineHttpResponseObjects


##


class IoPipelineHttpResponseEncoder(IoPipelineHttpResponseObjects, IoPipelineHttpObjectEncoder):
    def _encode_head_line(self, head: IoPipelineHttpMessageHead) -> bytes:
        head = check.isinstance(head, IoPipelineHttpResponseHead)
        version_str = f'HTTP/{head.version.major}.{head.version.minor}'
        # latin-1, matching the parser's decoding of the reason phrase - see the encoder's _encode_headers
        return f'{version_str} {head.status} {head.reason}\r\n'.encode('latin-1')


##


class IoPipelineHttpResponseChunker(IoPipelineHttpResponseObjects, IoPipelineHttpObjectChunker):
    pass


##


class IoPipelineHttpResponseCompressor(IoPipelineHttpResponseObjects, IoPipelineHttpObjectCompressor):
    pass
