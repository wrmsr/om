import pytest

from ... import quickjs


##


def test_time_limit():
    ctx = quickjs.Context()
    ctx.set_time_limit(0.05)
    with pytest.raises(quickjs.JsInterruptError):
        ctx.eval('for (;;) {}')
    # Disabling the limit restores normal operation.
    ctx.set_time_limit(-1)
    assert ctx.eval('1 + 1') == 2


def test_time_limit_not_hit():
    ctx = quickjs.Context()
    ctx.set_time_limit(60.0)
    assert ctx.eval('let s = 0; for (let i = 0; i < 1000; i++) s += i; s') == 499500


def test_memory_limit():
    ctx = quickjs.Context()
    ctx.set_memory_limit(4 * 1024 * 1024)
    with pytest.raises(quickjs.JsError):
        ctx.eval('const a = []; for (;;) { a.push("x".repeat(4096)); }')


def test_memory_stats():
    ctx = quickjs.Context()
    ctx.eval('globalThis.keep = [1, 2, 3]')
    stats = ctx.memory()
    assert stats['memory_used_size'] > 0
    assert stats['obj_count'] > 0


def test_gc():
    ctx = quickjs.Context()
    ctx.eval('for (let i = 0; i < 100; i++) { let o = {self: null}; o.self = o; }')
    ctx.gc()
    assert ctx.eval('1') == 1


def test_gc_threshold():
    ctx = quickjs.Context()
    ctx.set_gc_threshold(1024 * 1024)
    assert ctx.eval('1') == 1


def test_max_stack_size_validation():
    ctx = quickjs.Context()
    with pytest.raises(ValueError):  # noqa
        ctx.set_max_stack_size(-1)
    with pytest.raises(ValueError):  # noqa
        ctx.set_memory_limit(-1)
