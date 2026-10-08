import _thread
import contextlib
import itertools
import signal

import pytest

from .. import _bpe
from .texts import SAMPLES


##


class SignalledError(Exception):
    pass


@contextlib.contextmanager
def handling(signum, handler):
    before = signal.signal(signum, handler)
    try:
        yield
    finally:
        signal.signal(signum, before)


def interrupt(signum, frame):
    raise SignalledError


def signalling(signum):
    """
    An iterator of nothing, which in being found empty has a signal arrive. No Python code is run in doing so, so the
    interpreter does not get to act on the signal there and then: it is left for whatever is iterating to notice.
    """

    return filter(None, map(_thread.interrupt_main, [signum]))


def trained():
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, 300)
    return tok


def state(tok):
    return (tok.get_pattern(), tok.vocab_size, tok.get_mergeable_ranks(), tok.encode(SAMPLES[0]))


def test_between_buffers():
    tok = trained()
    before = state(tok)
    texts = iter(['aa aa', 'bb bb', 'cc cc'])

    with handling(signal.SIGUSR1, interrupt):
        with pytest.raises(SignalledError):
            tok.train_from_iterator(itertools.chain(signalling(signal.SIGUSR1), texts), 300, 1)

    # It stopped at the end of the buffer the signal arrived in the filling of, having taken no more and changed
    # nothing.
    assert next(texts) == 'bb bb'
    assert state(tok) == before


def test_while_merging():
    tok = trained()
    before = state(tok)

    # Here the signal arrives as the iterator is found to have nothing more, with everything already taken from it.
    with handling(signal.SIGUSR1, interrupt):
        with pytest.raises(SignalledError):
            tok.train_from_iterator(itertools.chain(['aa aa aa'], signalling(signal.SIGUSR1)), 300)

    assert state(tok) == before


def test_handled_and_carried_on_from():
    handled: list = []
    expected = _bpe.Tokenizer()
    expected.train_from_iterator(['aa aa', 'bb bb', 'cc cc'], 300)

    # A signal whose handler does not raise is no reason to stop.
    for texts in (
        itertools.chain(signalling(signal.SIGUSR1), ['aa aa', 'bb bb', 'cc cc']),
        itertools.chain(['aa aa', 'bb bb', 'cc cc'], signalling(signal.SIGUSR1)),
    ):
        del handled[:]
        tok = _bpe.Tokenizer()
        with handling(signal.SIGUSR1, lambda signum, frame: handled.append(signum)):
            tok.train_from_iterator(texts, 300, 1)
            assert handled == [signal.SIGUSR1]
        assert tok.get_mergeable_ranks() == expected.get_mergeable_ranks()
