from .... import lang
from .. import readers as gs


def test_prependable_coro_reader():
    def f():
        rdr = gs.PrependableStrCoroReader()

        i = yield from rdr.read(2)
        assert i == 'ab'

        rdr.prepend('c')
        i = yield from rdr.read(3)
        assert i == 'cde'

        rdr.prepend('gh')
        rdr.prepend('f')
        i = yield from rdr.read(2)
        assert i == 'fg'

        i = yield from rdr.read(2)
        assert i == 'hi'

        return 'done'

    cg = lang.capture_coroutine(f())
    assert cg.send() == cg.Yield(2)
    assert cg.send('ab') == cg.Yield(2)
    assert cg.send('de') == cg.Yield(1)
    assert cg.send('i') == cg.Return('done')


def test_prependable_coro_reader_read_none_offset():
    def f():
        rdr = gs.PrependableBytesCoroReader()

        rdr.prepend(b'abcdef')
        i = yield from rdr.read(2)
        assert i == b'ab'

        # Must not replay the two bytes already consumed from the queued chunk.
        i = yield from rdr.read(None)
        assert i == b'cdef'

        return 'done'

    cg = lang.capture_coroutine(f())
    assert cg.send() == cg.Return('done')


def test_prependable_coro_reader_prepend_offset():
    def f():
        rdr = gs.PrependableBytesCoroReader()

        rdr.prepend(b'abcdef', 4)
        i = yield from rdr.read(1)
        assert i == b'e'

        i = yield from rdr.read(None)
        assert i == b'f'

        return 'done'

    cg = lang.capture_coroutine(f())
    assert cg.send() == cg.Return('done')


def test_prependable_coro_reader_read_exact():
    def f():
        rdr = gs.PrependableBytesCoroReader()

        i = yield from rdr.read_exact(2)
        assert i == b'ab'

        try:
            yield from rdr.read_exact(4)
        except EOFError:
            return 'eof'
        raise RuntimeError

    cg = lang.capture_coroutine(f())
    assert cg.send() == cg.Yield(2)
    assert cg.send(b'ab') == cg.Yield(4)
    assert cg.send(b'cd') == cg.Return('eof')
