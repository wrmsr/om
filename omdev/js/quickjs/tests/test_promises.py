import pytest

from ... import quickjs


##


def test_resolved_promise():
    ctx = quickjs.Context()
    p = ctx.eval('Promise.resolve(42)')
    assert p.promise_state() == 'fulfilled'
    assert p.promise_result() == 42


def test_rejected_promise():
    ctx = quickjs.Context()
    p = ctx.eval('Promise.reject(new Error("bad"))')
    assert p.promise_state() == 'rejected'
    with pytest.raises(quickjs.JsError, match='bad'):
        p.promise_result()


def test_pending_promise():
    ctx = quickjs.Context()
    p = ctx.eval('new Promise(() => {})')
    assert p.promise_state() == 'pending'
    with pytest.raises(RuntimeError):
        p.promise_result()


def test_non_promise():
    ctx = quickjs.Context()
    obj = ctx.eval('({})')
    assert obj.promise_state() is None
    with pytest.raises(TypeError):
        obj.promise_result()


def test_async_function():
    ctx = quickjs.Context()
    p = ctx.eval('(async () => { const v = await Promise.resolve(6); return v * 7; })()')
    assert p.promise_state() == 'pending'
    assert ctx.has_pending_jobs() is True
    assert ctx.execute_pending_jobs() > 0
    assert p.promise_state() == 'fulfilled'
    assert p.promise_result() == 42


def test_execute_pending_job_single():
    ctx = quickjs.Context()
    assert ctx.execute_pending_job() is False
    ctx.eval('Promise.resolve(1).then(v => { globalThis.seen = v; })')
    assert ctx.execute_pending_job() is True
    assert ctx.eval('seen') == 1


def test_promise_then_python_callback():
    ctx = quickjs.Context()
    results: list = []
    ctx.set('report', results.append)
    ctx.eval('Promise.resolve("done").then(report)')
    ctx.execute_pending_jobs()
    assert results == ['done']


def test_module_eval():
    ctx = quickjs.Context()
    p = ctx.eval('globalThis.out = 40 + 2; export {};', module=True)
    assert isinstance(p, quickjs.Object)
    ctx.execute_pending_jobs()
    assert p.promise_state() == 'fulfilled'
    assert ctx.get('out') == 42


def test_module_top_level_await():
    ctx = quickjs.Context()
    p = ctx.eval('globalThis.r = await Promise.resolve(5);', module=True)
    ctx.execute_pending_jobs()
    assert p.promise_state() == 'fulfilled'
    assert ctx.get('r') == 5


def test_module_error():
    ctx = quickjs.Context()
    p = ctx.eval('throw new Error("module boom")', module=True)
    ctx.execute_pending_jobs()
    assert p.promise_state() == 'rejected'
    with pytest.raises(quickjs.JsError, match='module boom'):
        p.promise_result()
