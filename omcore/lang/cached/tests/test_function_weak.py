"""
Weak instance binding: bound wrappers hold their instance weakly by default - plus a strong *pin* released at the
first successful store, keeping temporary-instance one-liners (`Obj().meth()`) alive through their call - so warmed
cached-method-bearing instances are reclaimed by pure refcounting. The instance is dereferenced only on the miss path
- warm hits never touch it - so an escaped wrapper outliving its instance still serves already-cached keys but raises
ReferenceError on any further miss. `strong_instance=True` restores full bound-method-style pinning; non-weakrefable
instances silently fall back to it.
"""
import contextlib
import gc
import weakref

import pytest

from ..function import cached_function


##


@contextlib.contextmanager
def _no_gc():
    was = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        yield
    finally:
        if was:
            gc.enable()


class Nullary:
    calls = 0

    @cached_function
    def calc(self):
        self.calls += 1
        return 420


class Inline:
    calls = 0

    @cached_function
    def add(self, x: int):
        self.calls += 1
        return x + 1


##


def test_temporary_instance_one_liners():
    # LOAD_ATTR drops the temporary's last strong ref before the call - the bind-time pin carries it through:
    with _no_gc():
        assert Nullary().calc() == 420
        assert Inline().add(1) == 2


def test_unwarmed_bind_pins_until_first_compute():
    # The pin means a bound-but-never-called wrapper keeps its instance (and cycles with it) until the first store -
    # the deliberate cost of keeping one-liners alive. The cycle remains collectable by the gc as always.
    with _no_gc():
        n = Nullary()
        w = n.calc  # bind, no call

        r = weakref.ref(n)
        del n
        assert r() is not None  # pinned

        assert w() == 420  # first store releases the pin...
        assert r() is None  # ...and nothing else held it


def test_instances_collect_without_gc():
    with _no_gc():
        n = Nullary()
        assert n.calc() == 420
        i = Inline()
        assert i.add(1) == 2

        refs = (weakref.ref(n), weakref.ref(i))
        del n, i
        assert all(r() is None for r in refs)


def test_escaped_wrapper_hits_serve_misses_raise():
    with _no_gc():
        i = Inline()
        w = i.add
        assert w(1) == 2

        del i
        assert w(1) == 2  # already-cached key still serves
        with pytest.raises(ReferenceError):
            w(9)  # a miss needs the instance


def test_escaped_nullary_warm_value_survives():
    with _no_gc():
        n = Nullary()
        w = n.calc
        assert w() == 420

        del n
        assert w() == 420  # the slot value is the whole cache - no instance needed


def test_alive_semantics_unchanged():
    i = Inline()
    assert i.add(1) == 2
    assert i.add(1) == 2
    assert i.add(2) == 3
    assert i.calls == 2
    assert i.add is i.__dict__['add']  # install still happens


def test_reset_recomputes_while_alive():
    n = Nullary()
    assert n.calc() == 420
    n.__dict__['calc'].reset()
    assert n.calc() == 420
    assert n.calls == 2


def test_unbound_route():
    i = Inline()
    assert Inline.add(i, 3) == 4
    assert i.add(3) == 4
    assert i.calls == 1


##


class Pinned:
    @cached_function(strong_instance=True)
    def calc(self):
        return 7


def test_strong_instance_opt_out():
    with _no_gc():
        p = Pinned()
        w = p.calc
        assert w() == 7

        r = weakref.ref(p)
        del p
        assert r() is not None  # bound-method-style pinning
        assert w() == 7


class Slotted:
    __slots__ = ('__dict__',)  # has a __dict__ but no __weakref__ slot

    @cached_function
    def calc(self):
        return 9


def test_non_weakrefable_falls_back_to_pinning():
    with _no_gc():
        s = Slotted()
        w = s.calc
        assert w() == 9

        del s
        assert w() == 9  # fell back to a strong holder - legacy behavior preserved


##


class ClsScoped:
    @cached_function
    @classmethod
    def calc(cls):
        return 11


def test_classmethod_scope_unaffected():
    assert ClsScoped.calc() == 11
    assert ClsScoped.calc() == 11


class Reducible:
    @cached_function
    def calc(self):
        return 13


def test_reduce_dead_instance_raises():
    with _no_gc():
        r = Reducible()
        w = r.calc
        assert w() == 13

        assert w.__reduce__()  # alive: reducible
        del r
        with pytest.raises(ReferenceError):
            w.__reduce__()
