from .. import _bpe
from . import golden
from .texts import SAMPLES


##


def test_pattern():
    assert _bpe.GPT4_PATTERN == golden.PATTERN


def test_merges():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, golden.VOCAB_SIZE)

    assert tok.get_pattern() == golden.PATTERN
    assert tok.vocab_size == golden.VOCAB_SIZE
    assert [token_bytes for token_bytes, _ in tok.get_mergeable_ranks()[256:]] == golden.MERGES


def test_encoded():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, golden.VOCAB_SIZE)

    assert [tok.encode(text) for text in SAMPLES] == golden.ENCODED
    assert tok.batch_encode(SAMPLES) == golden.ENCODED


def test_chunks():
    # Trained on one text until there is nothing left to merge, every chunk of it is a token of its own - which shows
    # where the pattern split it.
    for text, chunks in zip(SAMPLES, golden.CHUNKS, strict=True):
        tok = _bpe.Tokenizer()
        tok.train_from_iterator([text], 256 + 100_000)
        vocab = [token_bytes for token_bytes, _ in tok.get_mergeable_ranks()]

        assert [vocab[token].decode() for token in tok.encode(text)] == chunks


def test_pattern_chunks():
    for pattern, text, chunks in golden.PATTERN_CHUNKS:
        tok = _bpe.Tokenizer()
        tok.train_from_iterator([text], 256 + 100_000, pattern=pattern)
        vocab = [token_bytes for token_bytes, _ in tok.get_mergeable_ranks()]

        assert [vocab[token].decode() for token in tok.encode(text)] == chunks, pattern
