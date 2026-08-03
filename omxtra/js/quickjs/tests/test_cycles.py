import gc

from ... import quickjs


##


class _Sentinel:
    def __init__(self, log):
        self.log = log

    def __del__(self):
        self.log.append('deleted')


def test_context_callable_cycle_collected():
    log = []
    sentinel = _Sentinel(log)
    ctx = quickjs.Context()
    # Context -> callables -> closure -> (ctx, sentinel): a cycle only the GC can break.
    ctx.set('f', lambda: (ctx, sentinel))  # noqa
    assert ctx.eval('typeof f') == 'function'

    del ctx
    del sentinel
    gc.collect()
    assert log == ['deleted']


def test_context_object_cycle_collected():
    log = []
    sentinel = _Sentinel(log)
    ctx = quickjs.Context()
    obj = ctx.eval('({})')
    # Context -> callables -> closure -> (Object -> Context, sentinel).
    ctx.set('f', lambda: (obj, sentinel))  # noqa

    del ctx
    del obj
    del sentinel
    gc.collect()
    assert log == ['deleted']


def test_object_outlives_context_reference():
    ctx = quickjs.Context()
    obj = ctx.eval('({v: 7})')
    del ctx
    # The wrapper keeps its context alive.
    assert obj['v'] == 7


def test_many_contexts_created_and_dropped():
    for _ in range(50):
        ctx = quickjs.Context()
        ctx.set('cb', lambda: 1)
        obj = ctx.eval('({a: [1, 2, 3]})')
        assert obj['a'][0] == 1
        del ctx
        del obj
    gc.collect()
