import random

import pytest

from ...errors import InvalidBlobKeyError
from ..paths import local_blob_decode_name
from ..paths import local_blob_decode_segment
from ..paths import local_blob_dir_name
from ..paths import local_blob_encode_segment
from ..paths import local_blob_file_name
from ..paths import local_blob_key_to_path


def test_encoding():
    assert local_blob_encode_segment('abc-1_2.x~') == 'abc-1_2.x~'
    assert local_blob_encode_segment('A') == '%41'
    assert local_blob_encode_segment('%') == '%25'
    assert local_blob_encode_segment('caf\u00e9') == 'caf%c3%a9'
    assert local_blob_encode_segment('sp ace') == 'sp ace'
    assert local_blob_file_name('x.file') == 'x.file.file'
    assert local_blob_dir_name('x.dir') == 'x.dir.dir'
    assert local_blob_key_to_path('a/B/c') == (['a.dir', '%42.dir'], 'c.file')


def test_round_trip_random():
    rng = random.Random(42)
    alphabet = 'aAzZ09%._- ~!\u00e9\u00c9\u65e5\U0001f600\ue000'
    for _ in range(2000):
        seg = ''.join(rng.choice(alphabet) for _ in range(rng.randint(1, 12)))
        if seg in ('.', '..'):
            continue
        enc = local_blob_encode_segment(seg)
        assert enc == enc.lower() or not any('A' <= c <= 'Z' for c in enc)
        assert all(0x20 <= ord(c) <= 0x7e for c in enc)
        assert local_blob_decode_segment(enc) == seg
        assert local_blob_decode_name(enc + '.file') == (seg, False)
        assert local_blob_decode_name(enc + '.dir') == (seg, True)


def test_case_distinct():
    names = {local_blob_file_name(s) for s in ['a', 'A', 'aA', 'Aa', 'AA', 'aa']}
    assert len(names) == 6
    assert len({n.lower() for n in names}) == 6


def test_foreign_names():
    for n in [
        'junk',
        'x.tmp',
        '.file',
        '.dir',
        'A.file',  # uppercase is never produced by the encoding
        '%61.file',  # non-canonical 'a'
        '%4.file',
        '%zz.file',
        '%c3.file',  # truncated utf-8
        '..file',  # decodes to '.'
        '...dir',  # decodes to '..'
    ]:
        assert local_blob_decode_name(n) is None, n


def test_limits():
    local_blob_file_name('x' * 250)
    with pytest.raises(InvalidBlobKeyError):
        local_blob_file_name('x' * 251)
    with pytest.raises(InvalidBlobKeyError):
        local_blob_dir_name('X' * 100)
    with pytest.raises(InvalidBlobKeyError):
        local_blob_key_to_path('ok/' + '\u00e9' * 50)
