import threading

import pytest

from ... import quickjs


##


def test_parallel_distinct_contexts():
    n = 4
    barrier = threading.Barrier(n)
    results = [None] * n
    errors = []

    def work(i):
        try:
            ctx = quickjs.Context()
            barrier.wait()
            results[i] = ctx.eval('function fib(n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); } fib(18)')
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert results == [2584] * n


def test_shared_context_serialized():
    ctx = quickjs.Context()
    ctx.eval('globalThis.counter = 0')
    n = 8
    iters = 50
    barrier = threading.Barrier(n)
    errors = []

    def work():
        try:
            barrier.wait()
            for _ in range(iters):
                ctx.eval('counter += 1')
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=work) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert ctx.eval('counter') == n * iters


def test_shared_context_callables_from_threads():
    ctx = quickjs.Context()
    ctx.set('double', lambda x: x * 2)
    n = 4
    barrier = threading.Barrier(n)
    results = [None] * n
    errors = []

    def work(i):
        try:
            barrier.wait()
            results[i] = ctx.eval(f'double({i})')
        except Exception as e:  # noqa
            errors.append(e)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert results == [i * 2 for i in range(n)]


def test_interrupt_from_other_thread():
    ctx = quickjs.Context()
    started = threading.Event()
    ctx.set('signal_started', started.set)
    raised = []

    def run():
        try:
            ctx.eval('signal_started(); for (;;) {}')
        except quickjs.JsInterruptError as e:
            raised.append(e)

    t = threading.Thread(target=run)
    t.start()
    assert started.wait(timeout=60)
    ctx.interrupt()
    t.join(timeout=60)
    assert not t.is_alive()
    assert len(raised) == 1

    # The context remains usable afterwards.
    assert ctx.eval('1 + 1') == 2


def test_stale_interrupt_does_not_poison_next_eval():
    ctx = quickjs.Context()
    ctx.interrupt()
    assert ctx.eval('1 + 1') == 2


def test_eval_releases_interpreter_to_other_threads():
    # While one thread is stuck inside JS, other Python threads must keep running (the evaluating thread
    # detaches from the interpreter). The loop is terminated by interrupt(), not by a time limit, so the
    # test is deterministic.
    ctx = quickjs.Context()
    other = quickjs.Context()
    started = threading.Event()
    ctx.set('signal_started', started.set)

    def run():
        with pytest.raises(quickjs.JsInterruptError):
            ctx.eval('signal_started(); for (;;) {}')

    t = threading.Thread(target=run)
    t.start()
    assert started.wait(timeout=60)
    # This runs while the other thread is still inside JS_Eval.
    assert other.eval('40 + 2') == 42
    ctx.interrupt()
    t.join(timeout=60)
    assert not t.is_alive()


def test_object_wrappers_dropped_from_other_thread():
    ctx = quickjs.Context()
    objs = [ctx.eval('({v: %d})' % i) for i in range(50)]  # noqa
    done = threading.Event()

    def drop():
        objs.clear()
        done.set()

    t = threading.Thread(target=drop)
    t.start()
    for i in range(50):
        ctx.eval('1 + %d' % i)  # noqa
    assert done.wait(timeout=60)
    t.join(timeout=60)
    assert ctx.eval('1 + 1') == 2
