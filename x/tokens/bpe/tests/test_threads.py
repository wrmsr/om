import concurrent.futures as cf
import threading

from .. import _bpe
from .texts import SAMPLES
from .texts import make_texts


##


TIMEOUT = 30


class GatedTexts:
    """An iterator of texts which, on reaching one of them, says that it has and waits to be told to go on."""

    def __init__(self, texts, gate_at):
        self._texts = iter(texts)
        self._gate_at = gate_at
        self._num_taken = 0

        self.reached = threading.Event()
        self.proceed = threading.Event()

    def __iter__(self):
        return self

    def __next__(self):
        if self._num_taken == self._gate_at:
            self.reached.set()
            if not self.proceed.wait(TIMEOUT):
                raise TimeoutError
        self._num_taken += 1
        return next(self._texts)


def train(texts, vocab_size, pattern=None):
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(texts, vocab_size, pattern=pattern)
    return tok


def state(tok):
    return (tok.get_pattern(), tok.vocab_size, tok.get_mergeable_ranks(), tok.batch_encode(SAMPLES))


def test_training_is_swapped_in_whole():
    old_texts = make_texts(1, 20, 50)
    new_texts = [*SAMPLES, *make_texts(2, 20, 50)]
    tok = train(old_texts, 400)
    old_state = state(tok)
    new_state = state(train(new_texts, 500, r'\w+|\s+'))
    assert old_state != new_state

    gated = GatedTexts(new_texts, len(new_texts) // 2)
    with cf.ThreadPoolExecutor(1) as executor:
        future = executor.submit(tok.train_from_iterator, gated, 500, 4, r'\w+|\s+')

        # Half trained, it is still in every way what it was.
        assert gated.reached.wait(TIMEOUT)
        assert state(tok) == old_state

        gated.proceed.set()
        future.result(TIMEOUT)
    assert state(tok) == new_state


def test_training_can_be_reentered():
    tok = train(['ef ef ef'], 300, r'\w+')
    seen = []

    def texts():
        yield 'ab ab ab'
        seen.append(tok.get_mergeable_ranks()[256:])
        tok.train_from_iterator(['cd cd cd'], 300, pattern=r'\w+')
        seen.append(tok.get_mergeable_ranks()[256:])
        seen.append(tok.encode('cd ab'))
        yield 'ab ab'

    tok.train_from_iterator(texts(), 300, 1, r'\w+')

    # The training begun from inside the other finished first, and held until the outer one did.
    assert seen == [
        [(b'ef', 256)],
        [(b'cd', 256)],
        [256, 97, 98],
    ]
    assert tok.get_mergeable_ranks()[256:] == [(b'ab', 256)]


def test_encoding_at_once():
    texts = [*SAMPLES, *make_texts(3, 30, 60)]
    tok = train(texts, 600)
    expected = [tok.encode(text) for text in texts]
    num_threads = 8
    barrier = threading.Barrier(num_threads)

    def work(n):
        barrier.wait(TIMEOUT)
        for _ in range(20):
            assert [tok.encode(text) for text in texts] == expected
            assert tok.batch_encode(texts, num_threads=1 + n % 3) == expected
            assert tok.decode(expected[n]) == texts[n]
            assert tok.vocab_size == 600

    with cf.ThreadPoolExecutor(num_threads) as executor:
        for future in [executor.submit(work, n) for n in range(num_threads)]:
            future.result(TIMEOUT)


def test_training_at_once():
    corpora = [
        (make_texts(4, 20, 50), 400, None),
        ([*SAMPLES, *make_texts(5, 20, 50)], 500, r'\w+|\s+'),
        (make_texts(6, 30, 40), 450, r'\S+|\s+'),
    ]
    states = [state(train(*corpus)) for corpus in corpora]
    num_threads = 6
    barrier = threading.Barrier(num_threads)
    tok = _bpe.Tokenizer()

    def work(n):
        texts, vocab_size, pattern = corpora[n % len(corpora)]
        barrier.wait(TIMEOUT)
        for _ in range(5):
            tok.train_from_iterator(texts, vocab_size, 7, pattern, num_threads=2)

    with cf.ThreadPoolExecutor(num_threads) as executor:
        for future in [executor.submit(work, n) for n in range(num_threads)]:
            future.result(TIMEOUT)

    # Whichever finished last is the one it is left as, and as nothing between any two of them.
    assert state(tok) in states


def test_encoding_while_training():
    corpora = [
        (make_texts(7, 20, 50), 400, None),
        ([*SAMPLES, *make_texts(8, 20, 50)], 500, r'\w+|\s+'),
    ]
    probe = SAMPLES[0] + make_texts(9, 1, 100)[0]
    toks = [train(*corpus) for corpus in corpora]
    ranks = [tok.get_mergeable_ranks() for tok in toks]
    encodings = [tok.encode(probe) for tok in toks]
    patterns = [tok.get_pattern() for tok in toks]

    tok = train(*corpora[0])
    num_readers = 4
    barrier = threading.Barrier(num_readers + 1)
    done = threading.Event()

    def read():
        barrier.wait(TIMEOUT)
        num_reads = 0
        while not done.is_set() or num_reads < 10:
            # Each on its own is of one model or of the other, whichever it was at the time.
            assert tok.encode(probe) in encodings
            assert tok.batch_encode([probe, probe])[1] in encodings
            assert tok.get_mergeable_ranks() in ranks
            assert tok.get_pattern() in patterns
            assert tok.vocab_size in (400, 500)
            num_reads += 1

    def write():
        barrier.wait(TIMEOUT)
        try:
            for n in range(30):
                texts, vocab_size, pattern = corpora[(n + 1) % len(corpora)]
                tok.train_from_iterator(texts, vocab_size, pattern=pattern)
        finally:
            done.set()

    with cf.ThreadPoolExecutor(num_readers + 1) as executor:
        futures = [executor.submit(write), *[executor.submit(read) for _ in range(num_readers)]]
        for future in futures:
            future.result(TIMEOUT)
