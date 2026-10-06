import gc
import importlib.machinery
import importlib.util
import weakref

import pytest

from .. import _pcre2 as pcre2


##


class ReentrantExporter(tuple):  # noqa
    """
    A buffer exporter whose release hook tries to match with the very MatchData holding its buffer.

    It is a tuple of what the hook needs, the MatchData included, and not an object with attributes for them: a tuple
    only lets go of its items when it is freed, so the hook can reach the block whichever of the two the collector
    gets to first.
    """

    def __buffer__(self, flags):
        return memoryview(b'a')

    def __release_buffer__(self, view):
        md, code, subject, log = self
        log.append('released')
        try:
            log.append(code.match(subject, md))
        except RuntimeError as e:
            log.append(str(e))


def test_release_hook_cannot_reenter_a_block_being_collected():
    code = pcre2.compile(b'a')
    other = bytearray(b'a')
    log: list = []

    md = pcre2.MatchData.create(1)
    exporter = ReentrantExporter((md, code, other, log))
    assert code.match(exporter, md) == 1
    assert log == []

    # The block holds the exporter's buffer and the exporter holds the block, so it is the collector which empties the
    # block - with the exporter, and so the block, still there for the hook to find.
    del md, exporter
    gc.collect()

    # Released once, and the match the hook tried refused: let through, it would have had the block release the buffer
    # a second time, and then lose the buffer it took in its place.
    assert log == ['released', 'MatchData is already in use']
    other.extend(b'a')


def test_release_hook_cannot_reenter_a_block_in_use():
    code = pcre2.compile(b'a')
    other = bytearray(b'a')
    log: list = []
    md = pcre2.MatchData.create(1)

    # Matching something else lets go of the exporter's buffer from inside the match.
    assert code.match(ReentrantExporter((md, code, other, log)), md) == 1
    assert code.match(b'ba', md) == 1
    assert log == ['released', 'MatchData is already in use']
    assert md.ovector == (1, 2)
    assert md.next_match() == (2, 0)

    # As does substituting through the block.
    del log[:]
    assert code.match(ReentrantExporter((md, code, other, log)), md) == 1
    assert code.substitute(b'ba', b'x', match_data=md) == (b'bx', 1)
    assert log == ['released', 'MatchData is already in use']

    other.extend(b'a')


##


def fresh_module():
    """Another instance of the extension module, as its multi-phase initialization allows, known only to its caller."""

    loader = importlib.machinery.ExtensionFileLoader(pcre2.__name__, pcre2.__file__)
    spec = importlib.util.spec_from_file_location(pcre2.__name__, pcre2.__file__, loader=loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


OBJECT_MAKERS = {
    'Code': lambda m: m.compile(b'a'),
    'CompileContext': lambda m: m.CompileContext.create(),
    'MatchContext': lambda m: m.MatchContext.create(),
    'MatchData': lambda m: m.MatchData.create(1),
}


@pytest.mark.parametrize('kind', OBJECT_MAKERS)
def test_objects_are_collected(kind):
    obj = OBJECT_MAKERS[kind](pcre2)
    assert type(obj).__name__ == kind
    assert gc.is_tracked(obj)
    assert type(obj) in gc.get_referents(obj)


@pytest.mark.parametrize('kind', OBJECT_MAKERS)
def test_module_holding_its_own_object_is_collected(kind):
    # An object holds its type, and its type the module it came from - so a module holding one of its own objects is a
    # cycle, which only goes away if the object lets the collector see its part in it.
    module = fresh_module()
    assert module is not pcre2
    assert module.Code is not pcre2.Code

    vars(module)['saved'] = OBJECT_MAKERS[kind](module)
    ref = weakref.ref(module)
    del module
    gc.collect()
    assert ref() is None
