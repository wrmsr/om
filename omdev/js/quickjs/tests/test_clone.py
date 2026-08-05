import gc
import threading

from ... import quickjs


##


# Deliberately places the RegExp first so every later shared reference crosses the patched JS_ReadRegExp
# registration path, and aliases an object through both plain properties and a Map.
_TEMPLATE_CODE = (
    '(function() {'
    '    var shared = {v: 1};'
    '    var o = {'
    '        re: /ab+c/gi,'
    '        x: shared,'
    '        x2: shared,'
    '        m: new Map([["k", shared]]),'
    '        arr: [1, "two", 3.5, null, true],'
    '        big: 2n ** 70n,'
    '    };'
    '    o.self = o;'
    '    return o;'
    '})()'
)

_CHECKS = [
    'r.self === r',
    'r.x2 === r.x',
    'r.m.get("k") === r.x',
    'r.re instanceof RegExp && r.re.flags === "gi" && r.re.test("xABBc")',
    'r.arr.length === 5 && r.arr[1] === "two" && r.arr[3] === null',
    'r.big === 2n ** 70n',
]


def _verify(ctx):
    for check in _CHECKS:
        assert ctx.eval(check) is True, check


def test_clone_into_fresh_context():
    src = quickjs.Context()
    blob = src.eval(_TEMPLATE_CODE).serialize()

    dst = quickjs.Context()
    dst.set('r', dst.deserialize(blob))
    _verify(dst)


def test_clone_independence():
    src = quickjs.Context()
    src.eval('globalThis.o = ' + _TEMPLATE_CODE)
    blob = src.get('o').serialize()

    dst = quickjs.Context()
    dst.set('r', dst.deserialize(blob))
    dst.eval('r.x.v = 999; r.arr.push("extra")')

    assert dst.eval('r.x.v') == 999
    assert src.eval('o.x.v') == 1
    assert src.eval('o.arr.length') == 5


def test_clone_outlives_source_context():
    src = quickjs.Context()
    blob = src.eval(_TEMPLATE_CODE).serialize()
    del src
    gc.collect()

    dst = quickjs.Context()
    dst.set('r', dst.deserialize(blob))
    _verify(dst)


def test_fanout_one_blob_many_contexts():
    src = quickjs.Context()
    blob = src.eval(_TEMPLATE_CODE).serialize()

    for _ in range(8):
        ctx = quickjs.Context()
        ctx.set('r', ctx.deserialize(blob))
        _verify(ctx)


def test_fanout_threaded():
    src = quickjs.Context()
    blob = src.eval(_TEMPLATE_CODE).serialize()

    n = 4
    barrier = threading.Barrier(n)
    oks = [False] * n
    errors = []

    def work(i):
        try:
            ctx = quickjs.Context()
            barrier.wait()
            ctx.set('r', ctx.deserialize(blob))
            _verify(ctx)
            oks[i] = True
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert oks == [True] * n
