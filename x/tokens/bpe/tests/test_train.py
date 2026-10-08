import pytest

from .. import _bpe
from . import reference
from .texts import SAMPLES
from .texts import make_texts


##


NANOCHAT_PATTERN = _bpe.GPT4_PATTERN.replace('{1,3}', '{1,2}')


def train(texts, vocab_size, *args, **kwargs):
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(texts, vocab_size, *args, **kwargs)
    return tok


@pytest.mark.parametrize('pattern', [
    _bpe.GPT4_PATTERN,
    NANOCHAT_PATTERN,
    r'\w+|\s+',
    r'\S+',
    r'(?s).',
    r'(?s).+',
    r'[a-z]+',
])
@pytest.mark.parametrize('vocab_size', [256, 257, 300, 700])
def test_reference(pattern, vocab_size):
    texts = [*SAMPLES, *make_texts(1, 20, 50)]

    tok = train(texts, vocab_size, pattern=pattern)
    merges = reference.train(pattern, texts, vocab_size)

    assert tok.get_pattern() == pattern
    assert tok.vocab_size == 256 + len(merges)
    assert tok.get_mergeable_ranks() == reference.mergeable_ranks(merges)


def test_untrained():
    tok = _bpe.Tokenizer()

    assert tok.vocab_size == 256
    assert tok.get_pattern() == ''
    assert tok.get_mergeable_ranks() == [(bytes([byte]), byte) for byte in range(256)]


def test_default_pattern():
    assert train(['some text'], 256).get_pattern() == _bpe.GPT4_PATTERN
    assert train(['some text'], 256, pattern=None).get_pattern() == _bpe.GPT4_PATTERN
    assert train(['some text'], 256, 8192, r'\w+').get_pattern() == r'\w+'


def test_merges_in_order_of_count_then_of_pair():
    # 'ab' is the most frequent pair. 'cd' and 'ef' tie, and the lesser pair goes first.
    tok = train(['ab ' * 10 + 'ef ' * 5 + 'cd ' * 5], 259, pattern=r'\w+')
    assert tok.get_mergeable_ranks()[256:] == [(b'ab', 256), (b'cd', 257), (b'ef', 258)]


def test_merges_chain():
    # A merge makes new pairs to merge: of 'aaa', first 'aa', and then that with the 'a' left over.
    tok = train(['aaa'] * 10, 300)
    assert tok.get_mergeable_ranks()[256:] == [(b'aa', 256), (b'aaa', 257)]

    # Seven of them pair off left to right into three 'aa' and an 'a'. The first two 'aa' merge, and that leaves
    # 'aaaa' with 'aa' and 'aa' with 'a' each seen once, of which the second is the lesser pair.
    tok = train(['aaaaaaa'], 300)
    assert tok.get_mergeable_ranks()[256:] == [(b'aa', 256), (b'aaaa', 257), (b'aaa', 258), (b'aaaaaaa', 259)]


def test_stops_when_nothing_is_left_to_merge():
    tok = train(['ab'] * 10, 300)
    assert tok.vocab_size == 257

    assert train([], 300).vocab_size == 256
    assert train(['', 'a', 'b'], 300).vocab_size == 256
    assert train(['abc abc'], 256).vocab_size == 256


def test_merges_stay_within_chunks():
    # This splits into 'ab' and then ' ab' over and over: however often a 'b' is followed by a space, the two are
    # never in the same chunk.
    tok = train(['ab ab ab ab ab ab'], 300)
    assert tok.get_mergeable_ranks()[256:] == [(b'ab', 256), (b' ab', 257)]


def test_retraining_replaces():
    tok = train(['ab ab ab'], 300, pattern=r'\w+')
    assert tok.get_mergeable_ranks()[256:] == [(b'ab', 256)]

    tok.train_from_iterator(['cd cd cd'], 300)
    assert tok.get_pattern() == _bpe.GPT4_PATTERN
    assert tok.get_mergeable_ranks()[256:] == [(b'cd', 256), (b' cd', 257)]


@pytest.mark.parametrize('buffer_size', [1, 2, 7, 8192])
def test_buffer_sizes(buffer_size):
    texts = [*SAMPLES, *make_texts(2, 40, 30)]
    expected = train(texts, 400).get_mergeable_ranks()

    assert train(texts, 400, buffer_size).get_mergeable_ranks() == expected
    assert train(texts, 400, buffer_size=buffer_size).get_mergeable_ranks() == expected


@pytest.mark.parametrize('num_threads', [1, 2, 3, 16])
def test_num_threads(num_threads):
    # Enough text, in enough pieces, that it is in fact shared out between that many threads.
    texts = make_texts(3, 600, 200)
    assert sum(len(text) for text in texts) > 16 * 32 * 1024
    expected = train(texts, 600, num_threads=1).get_mergeable_ranks()

    assert train(texts, 600, num_threads=num_threads).get_mergeable_ranks() == expected
    assert train(texts, 600, 100, num_threads=num_threads).get_mergeable_ranks() == expected
    assert train(texts, 600).get_mergeable_ranks() == expected


def test_iterables():
    texts = make_texts(4, 10, 40)
    expected = train(texts, 350).get_mergeable_ranks()

    assert train(tuple(texts), 350).get_mergeable_ranks() == expected
    assert train(iter(texts), 350).get_mergeable_ranks() == expected
    assert train((text for text in texts), 350).get_mergeable_ranks() == expected
    assert train(dict.fromkeys(texts), 350).get_mergeable_ranks() == expected

    tok = _bpe.Tokenizer()
    tok.train_from_iterator(iterator=texts, vocab_size=350, buffer_size=3, pattern=_bpe.GPT4_PATTERN, num_threads=2)
    assert tok.get_mergeable_ranks() == expected

    # A str is an iterable of strs too, if not a useful one: no chunk of a single letter has a pair in it.
    assert train('abcabcabc', 350).vocab_size == 256


def test_str_subclasses():
    class Text(str):  # noqa
        pass

    texts = make_texts(5, 10, 40)
    expected = train(texts, 350).get_mergeable_ranks()

    assert train([Text(text) for text in texts], 350).get_mergeable_ranks() == expected
