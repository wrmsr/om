import pytest

from .. import _bpe
from . import reference
from .texts import SAMPLES
from .texts import make_text
from .texts import make_texts


##


def train(texts, vocab_size, pattern=None):
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(texts, vocab_size, pattern=pattern)
    return tok


@pytest.mark.parametrize('pattern', [
    _bpe.GPT4_PATTERN,
    r'\w+|\s+',
    r'(?s).+',
])
@pytest.mark.parametrize('vocab_size', [256, 300, 700])
def test_reference(pattern, vocab_size):
    texts = [*SAMPLES, *make_texts(1, 20, 50)]
    tok = train(texts, vocab_size, pattern)
    merges = reference.train(pattern, texts, vocab_size)

    # Text it was trained on, and text it was not.
    for text in [*texts, *make_texts(2, 10, 50)]:
        assert tok.encode(text) == reference.encode(pattern, merges, text)


def test_untrained():
    tok = _bpe.Tokenizer()

    # With no pattern there are no chunks, and so no tokens.
    assert tok.encode('hello') == []
    assert tok.encode('') == []
    assert tok.batch_encode(['hello', '']) == [[], []]


def test_bytes_until_trained_to_merge():
    tok = train(['hello world'], 256)

    assert tok.encode('hello wörld') == list('hello wörld'.encode())
    assert tok.encode('') == []


def test_earliest_merge_first():
    tok = train(['aaa'] * 10, 300)
    assert tok.get_mergeable_ranks()[256:] == [(b'aa', 256), (b'aaa', 257)]

    assert tok.encode('a') == [97]
    assert tok.encode('aa') == [256]
    assert tok.encode('aaa') == [257]

    # 'aa' was learned before 'aaa', so every 'aa' there is to make is made before any 'aaa' is.
    assert tok.encode('aaaa') == [256, 256]
    assert tok.encode('aaaaa') == [256, 257]
    assert tok.encode('aaaaaa') == [256, 256, 256]


def test_unmatched_text_is_left_out():
    tok = train(['ab ab ab'], 300, r'[a-z]+')
    assert tok.get_mergeable_ranks()[256:] == [(b'ab', 256)]

    assert tok.encode('ab, AB, ab!') == [256, 256]
    assert tok.decode(tok.encode('ab, AB, ab!')) == 'abab'


@pytest.mark.parametrize('size', [1, 2, 127, 128, 129, 130, 257, 700])
def test_long_chunks(size):
    # Past a length a chunk is encoded another way, which has to come to the same thing. The pattern here makes a
    # single chunk of anything, and each text is of a kind to keep merging for as long as it goes on.
    pattern = r'(?s).+'
    texts = [
        'a' * 1000,
        'ab' * 500,
        'abc' * 400,
        'aab' * 400,
        make_text(3, 200),
    ]
    tok = train(texts, 400, pattern)
    merges = reference.train(pattern, texts, 400)
    assert tok.get_mergeable_ranks() == reference.mergeable_ranks(merges)

    for text in texts:
        for start in (0, 1, 2, 3):
            piece = text[start:start + size]
            assert tok.encode(piece) == reference.encode(pattern, merges, piece)


def test_long_chunk_of_one_character():
    # What makes encoding one merge at a time, each found by going over the whole chunk, a matter of hours.
    text = 'a' * 1_000_000
    tok = train([text], 300)

    ids = tok.encode(text)
    assert len(ids) < 20
    assert tok.decode(ids) == text


def test_keyword():
    tok = train(['ab ab ab'], 300)

    assert tok.encode(text='ab ab') == tok.encode('ab ab')
    assert tok.batch_encode(texts=['ab ab']) == [tok.encode('ab ab')]


def test_str_subclass():
    class Text(str):  # noqa
        pass

    tok = train(SAMPLES, 300)

    assert tok.encode(Text(SAMPLES[0])) == tok.encode(SAMPLES[0])
    assert tok.batch_encode([Text(SAMPLES[0])]) == [tok.encode(SAMPLES[0])]


def test_round_trip():
    texts = [*SAMPLES, *make_texts(4, 20, 50)]
    tok = train(texts, 600)

    # The default pattern leaves nothing out, so everything comes back.
    for text in [*texts, *make_texts(5, 10, 50)]:
        assert tok.decode(tok.encode(text)) == text


def test_batch_encode():
    texts = [*SAMPLES, *make_texts(6, 20, 50)]
    tok = train(texts, 500)
    expected = [tok.encode(text) for text in texts]

    assert tok.batch_encode(texts) == expected
    assert tok.batch_encode(tuple(texts)) == expected
    assert tok.batch_encode(iter(texts)) == expected
    assert tok.batch_encode(text for text in texts) == expected
    assert tok.batch_encode([]) == []
    assert tok.batch_encode(['']) == [[]]


@pytest.mark.parametrize('num_threads', [None, 1, 2, 3, 16])
def test_batch_encode_num_threads(num_threads):
    # Enough text, in enough pieces, that it is in fact shared out between that many threads.
    texts = make_texts(7, 600, 200)
    assert sum(len(text) for text in texts) > 16 * 32 * 1024
    tok = train(texts[:50], 500)
    expected = [tok.encode(text) for text in texts]

    assert tok.batch_encode(texts, num_threads=num_threads) == expected


def test_whitespace_past_the_probe():
    # A run of spaces is the default pattern at its slowest: slow enough that even in a short text it is more than is
    # tried without detaching, and has to be done over. That must not show.
    pattern = _bpe.GPT4_PATTERN
    texts = [
        ' ' * 700 + 'x',
        ('a' + ' ' * 300) * 3,
        ' ' * 1000,
    ]
    for buffer_size in (1, 8192):
        tok = _bpe.Tokenizer()
        tok.train_from_iterator(texts, 280, buffer_size)
        merges = reference.train(pattern, texts, 280)
        assert tok.get_mergeable_ranks() == reference.mergeable_ranks(merges)

        for text in texts:
            assert tok.encode(text) == reference.encode(pattern, merges, text)
        assert tok.batch_encode(texts[:1]) == [reference.encode(pattern, merges, texts[0])]
