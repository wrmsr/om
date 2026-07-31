from ..targets import FnTarget
from ..targets import NameTarget
from ..targets import Target
from ..targets import target_runner_for


def test_target_of():
    fn = lambda: None

    assert Target.of('pkg.mod') == NameTarget('pkg.mod')
    assert Target.of(fn) == FnTarget(fn)


def test_fn_target_runner_chains_returned_target():
    calls = []

    def inner():
        calls.append('inner')

    def outer():
        calls.append('outer')
        return inner

    target_runner_for(FnTarget(outer)).run()

    assert calls == ['outer', 'inner']
