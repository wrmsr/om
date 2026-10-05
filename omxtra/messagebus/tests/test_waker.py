from ..waker import Waker


def test_wait_times_out_without_a_wake():
    w = Waker()
    try:
        assert not w.wait(0.)
    finally:
        w.close()


def test_wake_then_wait():
    w = Waker()
    try:
        w.wake()
        assert w.wait(0.)
        assert not w.wait(0.)
    finally:
        w.close()


def test_wakes_coalesce():
    w = Waker()
    try:
        for _ in range(1000):
            w.wake()
        assert w.wait(0.)
        assert not w.wait(0.)
    finally:
        w.close()
