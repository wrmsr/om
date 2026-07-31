import io

from ..timers import _get_global_registry
from ..timers import global_timer_context
from ..timers import global_timer_wrap


def test_global_timer_context():
    out = io.StringIO()
    clock = iter([1., 3.5]).__next__
    namespace = {'__name__': 'test_module'}

    with global_timer_context(namespace, 'work', clock=clock, report_out=out):
        pass

    _get_global_registry(namespace).get_timer('work').report()
    assert out.getvalue() == 'test_module::work: 1 calls, 2.500s total\n'


def test_global_timer_wrap_descriptor():
    out = io.StringIO()
    clock = iter([1., 2., 3., 5.]).__next__
    namespace = {'__name__': 'test_module'}

    class Adder:
        @global_timer_wrap(namespace, 'add', clock=clock, report_out=out)
        def add(self, left, right):
            return left + right

    adder = Adder()
    assert adder.add(1, 2) == 3
    assert Adder.add(adder, 3, 4) == 7

    _get_global_registry(namespace).get_timer('add').report()
    assert out.getvalue() == 'test_module::add: 2 calls, 3.000s total\n'
