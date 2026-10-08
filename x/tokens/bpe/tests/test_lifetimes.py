import gc
import importlib.machinery
import importlib.util
import weakref

import pytest

from .. import _bpe
from .texts import SAMPLES


##


class Text(str):  # noqa
    """A str which can be watched for having been let go of, as a plain one cannot."""


def test_texts_are_let_go_of():
    tok = _bpe.Tokenizer()
    texts = [Text(text) for text in SAMPLES]
    refs = [weakref.ref(text) for text in texts]

    tok.train_from_iterator(texts, 300, 3)
    tok.train_from_iterator(iter(texts), 300, pattern=r'\w+')
    tok.batch_encode(texts)
    tok.batch_encode(iter(texts))
    for text in texts:
        tok.encode(text)

    del texts, text
    gc.collect()
    assert all(ref() is None for ref in refs)


@pytest.mark.parametrize('buffer_size', [1, 3, 8192])
def test_texts_are_let_go_of_on_failure(buffer_size):
    tok = _bpe.Tokenizer()
    texts = [Text(text) for text in SAMPLES]
    refs = [weakref.ref(text) for text in texts]

    with pytest.raises(TypeError):
        tok.train_from_iterator([*texts, None], 300, buffer_size)  # type: ignore[list-item]
    with pytest.raises(TypeError):
        tok.batch_encode([*texts, None])  # type: ignore[list-item]

    del texts
    gc.collect()
    assert all(ref() is None for ref in refs)


def test_texts_may_be_taken_away_meanwhile():
    # The list the texts come in is the caller's to change, and here does change, from inside the very call it was
    # passed to - which must go on reading what it was given, and not what has since been freed.
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, 300)
    expected = [tok.encode(text) for text in SAMPLES]

    class Texts(list):  # noqa
        def __iter__(self):
            yield from list.__iter__(self)
            self.clear()
            gc.collect()

    texts = Texts(Text(text) for text in SAMPLES)
    assert tok.batch_encode(texts) == expected
    assert texts == []


def test_texts_may_be_held_by_nothing_else():
    # Texts made as they are asked for, and kept by nobody: all that stands between them and being freed while they
    # are being read is whatever hold is taken of them here.
    tok = _bpe.Tokenizer()
    tok.train_from_iterator(SAMPLES, 300)
    expected = (tok.get_mergeable_ranks(), [tok.encode(text) for text in SAMPLES])

    tok = _bpe.Tokenizer()
    tok.train_from_iterator((Text(text) for text in SAMPLES), 300, 3)
    assert tok.get_mergeable_ranks() == expected[0]
    assert tok.batch_encode(Text(text) for text in SAMPLES) == expected[1]
    assert [tok.encode(Text(text)) for text in SAMPLES] == expected[1]


def test_tokenizers_are_collected():
    tok = _bpe.Tokenizer()
    assert gc.is_tracked(tok)
    assert type(tok) in gc.get_referents(tok)


def fresh_module():
    """Another instance of the extension module, as its multi-phase initialization allows, known only to its caller."""

    loader = importlib.machinery.ExtensionFileLoader(_bpe.__name__, _bpe.__file__)
    spec = importlib.util.spec_from_file_location(_bpe.__name__, _bpe.__file__, loader=loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_module_holding_its_own_tokenizer_is_collected():
    # A tokenizer holds its type, and its type the module it came from - so a module holding one of its own is a
    # cycle, which only goes away if the tokenizer lets the collector see its part in it.
    module = fresh_module()
    assert module is not _bpe
    assert module.Tokenizer is not _bpe.Tokenizer

    tok = module.Tokenizer()
    tok.train_from_iterator(SAMPLES, 300)
    assert tok.encode(SAMPLES[0]) != []

    vars(module)['saved'] = tok
    ref = weakref.ref(module)
    del module, tok
    gc.collect()
    assert ref() is None
