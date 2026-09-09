# @om-recommended-import-alias "isb"
from ... import lang as _lang


with _lang.auto_proxy_init(
        globals(),
        update_exports=True,
):
    ##

    from .adapters import (  # noqa
        ByteStreamBufferBytesReaderAdapter as BufferBytesReaderAdapter,
        ByteStreamBufferWriterAdapter as BufferWriterAdapter,
        BytesIoByteStreamBuffer as BytesIoBuffer,
    )

    from .direct import (  # noqa
        DirectByteStreamBufferView as DirectBufferView,
        DirectByteStreamBuffer as DirectBuffer,

        empty_byte_stream_buffer_view as empty_buffer_view,
    )

    from .framing import (  # noqa
        LongestMatchDelimiterByteStreamFrameDecoder as LongestMatchDelimiterFrameDecoder,
        LengthFieldByteStreamFrameDecoder as LengthFieldFrameDecoder,
    )

    from .linear import (  # noqa
        LinearByteStreamBuffer as LinearBuffer,
    )

    from .reading import (  # noqa
        ByteStreamBufferReader as BufferReader,
    )

    from .scanning import (  # noqa
        ScanningByteStreamBuffer as ScanningBuffer,
    )

    from .segmented import (  # noqa
        SegmentedByteStreamBufferView as SegmentedBufferView,
        SegmentedByteStreamBuffer as SegmentedBuffer,

        byte_stream_buffer_view_from_segments as buffer_view_from_segments,
    )


##


from .errors import (  # noqa
    ByteStreamBufferError as BufferError,  # noqa

    NeedMoreDataByteStreamBufferError as NeedMoreDataBufferError,

    LimitByteStreamBufferError as LimitBufferError,
    BufferTooLargeByteStreamBufferError as BufferTooLargeBufferError,
    FrameTooLargeByteStreamBufferError as FrameTooLargeBufferError,

    StateByteStreamBufferError as StateBufferError,
    OutstandingReserveByteStreamBufferError as OutstandingReserveBufferError,
    NoOutstandingReserveByteStreamBufferError as NoOutstandingReserveBufferError,
)

from .types import (  # noqa
    BytesLike,

    ByteStreamBufferView as BufferView,
    ByteStreamBuffer as Buffer,
    MutableByteStreamBuffer as MutableBuffer,
)

from .utils import (  # noqa
    ByteStreamBuffers as Buffers,
)

#

NeedMoreData = NeedMoreDataBufferError

BufferTooLarge = BufferTooLargeBufferError
FrameTooLarge = FrameTooLargeBufferError

OutstandingReserve = OutstandingReserveBufferError
NoOutstandingReserve = NoOutstandingReserveBufferError

#

can_bytes = Buffers.can_bytes
to_bytes = Buffers.to_bytes
bytes_len = Buffers.bytes_len
iter_segments = Buffers.iter_segments
split = Buffers.split
