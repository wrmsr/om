import pytest

from .. import bytes as bytes_codecs


@pytest.mark.parametrize('codec', [
    bytes_codecs.ASCII85,
    bytes_codecs.BASE16,
    bytes_codecs.BASE32,
    bytes_codecs.BASE64,
    bytes_codecs.BASE85,
    bytes_codecs.BASE32_HEX,
    bytes_codecs.BASE64_HEX,
    bytes_codecs.BASE64_URLSAFE,
    bytes_codecs.HEX,
])
def test_bytes_codec_roundtrip(codec):
    value = bytes(range(256))
    instance = codec.new()

    assert instance.decode(instance.encode(value)) == value
