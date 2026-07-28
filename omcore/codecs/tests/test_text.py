import pytest

from ... import check
from ..text import UTF8
from ..text import TextEncodingComboCodec
from ..text import TextEncodingOptions


def test_text():
    assert UTF8.new().encode('hi') == b'hi'
    assert UTF8.new(TextEncodingOptions(errors='ignore')).encode('hi') == b'hi'

    te = check.not_none(UTF8.new_incremental)().encode_incremental()
    assert te.feed('hi') == (b'hi',)
    assert te.feed('') == ()
    assert te.finish() == ()
    assert te.eof

    td = check.not_none(UTF8.new_incremental)().decode_incremental()
    assert td.feed(b'hi') == ('hi',)
    assert td.feed(b'') == ()
    assert td.finish() == ()
    assert td.eof

    assert UTF8.new().encode('☃') == b'\xe2\x98\x83'

    td = check.not_none(UTF8.new_incremental)().decode_incremental()
    assert td.feed(b'\xe2') == ()
    assert td.feed(b'\x98') == ()
    assert td.feed(b'\x83') == ('☃',)
    assert td.finish() == ()


def test_text_incremental_final_flush():
    # A truncated multi-byte sequence surfaces at finish(), where final=True raises for strict errors.
    td = check.not_none(UTF8.new_incremental)().decode_incremental()
    assert td.feed(b'\xe2\x98') == ()
    with pytest.raises(UnicodeDecodeError):
        td.finish()


def test_text_incremental_decode_unused_data():
    # The still-undecoded tail is snapshotted before the final decode, so it survives a strict-errors raise.
    td = TextEncodingComboCodec.lookup('utf-8').decode_incremental()
    assert td.feed(b'hi\xe2\x98') == ('hi',)
    with pytest.raises(UnicodeDecodeError):
        td.finish()
    assert td.unused_data == b'\xe2\x98'


def test_text_incremental_decode_unused_data_lenient():
    # With a lenient handler the tail is consumed per the handler *and* reported raw.
    td = TextEncodingComboCodec.lookup('utf-8', TextEncodingOptions(errors='replace')).decode_incremental()
    assert td.feed(b'hi\xe2\x98') == ('hi',)
    assert td.finish() == ('�',)
    assert td.eof
    assert td.unused_data == b'\xe2\x98'


def test_text_incremental_decode_unused_data_empty():
    td = TextEncodingComboCodec.lookup('utf-8').decode_incremental()
    assert td.feed(b'hi') == ('hi',)
    assert td.finish() == ()
    assert td.unused_data == b''
