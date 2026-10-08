# @om-precheck-allow-any-unicode
import pytest

from .. import _bpe
from .texts import SAMPLES


##


def test_untrained():
    tok = _bpe.Tokenizer()

    assert tok.decode([]) == ''
    assert tok.decode([104, 105]) == 'hi'
    assert tok.decode([0xE4, 0xB8, 0xAD]) == '中'
    assert tok.decode(ids=[104, 105]) == 'hi'


def test_trained():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(['aaa'] * 10, 300)

    assert tok.decode([256]) == 'aa'
    assert tok.decode([257]) == 'aaa'
    assert tok.decode([257, 98, 256]) == 'aaabaa'


def test_iterables():
    tok = _bpe.Tokenizer()

    assert tok.decode((104, 105)) == 'hi'
    assert tok.decode(iter([104, 105])) == 'hi'
    assert tok.decode(b'hi') == 'hi'
    assert tok.decode(range(97, 100)) == 'abc'


def test_unknown_token():
    tok = _bpe.Tokenizer()

    for ids in ([256], [300], [-1], [104, 1 << 40], [1 << 80], [-(1 << 80)]):
        with pytest.raises(ValueError, match='Unknown token id'):
            tok.decode(ids)

    tok.train_from_iterator(['ab ab ab'], 257, pattern=r'\w+')
    assert tok.decode([256]) == 'ab'
    with pytest.raises(ValueError, match='Unknown token id: 257'):
        tok.decode([257])


def test_not_tokens():
    tok = _bpe.Tokenizer()

    for ids in (['a'], [1.5], [None], 'hi', '', 104, None):
        with pytest.raises(TypeError):
            tok.decode(ids)  # type: ignore[arg-type]


def test_not_utf8():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, 400)

    # Tokens are bytes, and need not end where characters do.
    ids = tok.encode('中')
    assert tok.decode(ids) == '中'
    with pytest.raises(UnicodeDecodeError):
        tok.decode([0xE4])
    with pytest.raises(UnicodeDecodeError):
        tok.decode([0xFF])
