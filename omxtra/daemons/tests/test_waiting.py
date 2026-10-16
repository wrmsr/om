from ..waiting import FnWait
from ..waiting import SequentialWait
from ..waiting import waiter_for


def test_sequential_waiter_progress():
    calls = []
    first_results = iter([False, True])

    def first():
        calls.append('first')
        return next(first_results)

    def second():
        calls.append('second')
        return True

    waiter = waiter_for(SequentialWait([
        FnWait(first),
        FnWait(second),
    ]))

    assert not waiter.do_wait()
    assert calls == ['first']

    assert waiter.do_wait()
    assert calls == ['first', 'first', 'second']

    assert waiter.do_wait()
    assert calls == ['first', 'first', 'second']
