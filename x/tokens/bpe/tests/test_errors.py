import pytest

from .. import _bpe
from .texts import SAMPLES


##


def trained():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, 300)
    return tok


def state(tok):
    return (tok.get_pattern(), tok.vocab_size, tok.get_mergeable_ranks(), tok.encode(SAMPLES[0]))


def test_new():
    with pytest.raises(TypeError):
        _bpe.Tokenizer(1)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        _bpe.Tokenizer(pattern='a')  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        class Sub(_bpe.Tokenizer):  # type: ignore[misc]
            pass


def test_vocab_size():
    tok = _bpe.Tokenizer()

    for vocab_size in (-1, 0, 255, 1 << 32, 1 << 62):
        with pytest.raises(ValueError, match='vocab_size'):
            tok.train_from_iterator(['a'], vocab_size)
    with pytest.raises(OverflowError):
        tok.train_from_iterator(['a'], 1 << 80)
    with pytest.raises(TypeError):
        tok.train_from_iterator(['a'], 'big')  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        tok.train_from_iterator(['a'])  # type: ignore[call-arg]

    # As large as is allowed is no more work than there are merges to be had.
    tok.train_from_iterator(['ab ab'], (1 << 32) - 1)
    assert tok.vocab_size == 258


def test_buffer_size():
    tok = _bpe.Tokenizer()

    for buffer_size in (0, -1):
        with pytest.raises(ValueError, match='buffer_size'):
            tok.train_from_iterator(['a'], 300, buffer_size)

    # As is one which could never be filled.
    tok.train_from_iterator(['ab ab'], 300, 1 << 62)
    assert tok.vocab_size == 258


def test_num_threads():
    tok = trained()

    for num_threads in (0, -1, 257, 1 << 40):
        with pytest.raises(ValueError, match='num_threads'):
            tok.train_from_iterator(['a'], 300, num_threads=num_threads)
        with pytest.raises(ValueError, match='num_threads'):
            tok.batch_encode(['a'], num_threads=num_threads)
    with pytest.raises(TypeError):
        tok.train_from_iterator(['a'], 300, num_threads='2')
    with pytest.raises(TypeError):
        tok.train_from_iterator(['a'], 300, 8192, None, 2)
    with pytest.raises(TypeError):
        tok.batch_encode(['a'], 2)


@pytest.mark.parametrize('pattern', [
    '(',
    '[a-',
    r'\p{NotAProperty}',
    '(?<=a+)b',

    # A single byte, which could split a character in two.
    r'\C',
])
def test_bad_pattern(pattern):
    tok = trained()
    before = state(tok)
    texts = iter(SAMPLES)

    with pytest.raises(ValueError, match='Invalid regex pattern'):
        tok.train_from_iterator(texts, 300, pattern=pattern)

    # Found out before anything was taken from the iterator, or done to the tokenizer.
    assert next(texts) == SAMPLES[0]
    assert state(tok) == before


def test_pattern_type():
    tok = _bpe.Tokenizer()

    with pytest.raises(TypeError):
        tok.train_from_iterator(['a'], 300, pattern=b'a')  # type: ignore[arg-type]
    with pytest.raises(UnicodeEncodeError):
        tok.train_from_iterator(['a'], 300, pattern='\ud800')

    # NUL is nothing special, in a pattern or in text.
    tok.train_from_iterator(['a\x00b a\x00b'], 300, pattern='a\x00b')
    assert tok.get_pattern() == 'a\x00b'
    assert tok.get_mergeable_ranks()[256:] == [(b'\x00b', 256), (b'a\x00b', 257)]


def test_not_iterable():
    tok = trained()
    before = state(tok)

    for texts in (None, 1, object()):
        with pytest.raises(TypeError):
            tok.train_from_iterator(texts, 300)
        with pytest.raises(TypeError):
            tok.batch_encode(texts)
    assert state(tok) == before


@pytest.mark.parametrize('buffer_size', [1, 2, 8192])
@pytest.mark.parametrize('bad', [b'bytes', 1, None, ['list']])
def test_not_str(buffer_size, bad):
    tok = trained()
    before = state(tok)

    with pytest.raises(TypeError, match='expected str'):
        tok.train_from_iterator(['some text', 'more text', bad, 'yet more'], 400, buffer_size)
    assert state(tok) == before

    with pytest.raises(TypeError, match='expected str'):
        tok.batch_encode(['some text', bad])
    with pytest.raises(TypeError, match='expected str'):
        tok.encode(bad)


def test_texts_are_not_one_str():
    tok = trained()

    with pytest.raises(TypeError, match='not a str'):
        tok.batch_encode('some text')


def test_surrogates():
    tok = trained()
    before = state(tok)

    # Not text which has a UTF-8 encoding to split.
    with pytest.raises(UnicodeEncodeError):
        tok.encode('a\ud800b')
    with pytest.raises(UnicodeEncodeError):
        tok.batch_encode(['ab', 'a\ud800b'])
    with pytest.raises(UnicodeEncodeError):
        tok.train_from_iterator(['ab', 'a\ud800b'], 300)
    assert state(tok) == before


def test_arguments():
    tok = trained()

    with pytest.raises(TypeError):
        tok.encode()
    with pytest.raises(TypeError):
        tok.encode('a', 'b')
    with pytest.raises(TypeError):
        tok.encode(texts='a')
    with pytest.raises(TypeError):
        tok.encode('a', text='a')
    with pytest.raises(TypeError):
        tok.decode()
    with pytest.raises(TypeError):
        tok.decode([1], [2])
    with pytest.raises(TypeError):
        tok.get_pattern(1)
    with pytest.raises(AttributeError):
        tok.vocab_size = 1


@pytest.mark.parametrize('buffer_size', [1, 3, 8192])
def test_failing_iterator(buffer_size):
    tok = trained()
    before = state(tok)

    def texts():
        yield from SAMPLES[:5]
        raise KeyError('no more')

    with pytest.raises(KeyError, match='no more'):
        tok.train_from_iterator(texts(), 400, buffer_size, r'\w+')
    assert state(tok) == before


def test_match_limit():
    # A pattern may set its own limit on how much matching it may take, and this one sets one which its first branch
    # cannot keep to - as one which backtracks without end will fail to keep to the default.
    pattern = r'(*LIMIT_MATCH=100)(a+)+\d|b+'
    tok = trained()
    before = state(tok)

    for text in ('aaaaaaaaaaaaaaaa', 'aaaaaaaaaaaaaaaa' * 200):
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.train_from_iterator([text], 300, pattern=pattern)
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.train_from_iterator(['bb', text], 300, 1, pattern)
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.train_from_iterator(['bb', text] * 400, 300, pattern=pattern, num_threads=4)
    assert state(tok) == before

    tok.train_from_iterator(['bb bb bb'], 300, pattern=pattern)
    assert tok.encode('bb b') == [256, 98]
    for text in ('aaaaaaaaaaaaaaaa', 'aaaaaaaaaaaaaaaa' * 200):
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.encode(text)
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.batch_encode(['bb', text])
        with pytest.raises(RuntimeError, match='match limit exceeded'):
            tok.batch_encode(['bb', text] * 400, num_threads=4)
