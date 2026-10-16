# ruff: noqa: UP006 UP007 UP037 UP043 UP045 PT009 PT027 SLF001
import asyncio
import contextlib
import threading
import typing as ta
import unittest

from ..contextmanagers import AsyncClosingManager
from ..contextmanagers import AsyncExitStacked
from ..contextmanagers import ExitStacked
from ..contextmanagers import aclosing
from ..contextmanagers import adefer
from ..contextmanagers import attr_setting
from ..contextmanagers import defer


##


class CmTracker:
    entered = False
    exited = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True


class TestExitStacked(unittest.TestCase):
    def test_exit(self):
        class Foo(ExitStacked):
            def __init__(self):
                super().__init__()
                self.t = CmTracker()

            def _enter_contexts(self):
                self._enter_context(self.t)
                raise RuntimeError('barf')

        foo = Foo()
        with self.assertRaises(RuntimeError):  # noqa
            with foo:
                pass

        self.assertTrue(foo.t.entered)
        self.assertTrue(foo.t.exited)


##


class _Cm:
    """Sync context manager that logs ('enter', name) and ('exit', name, exc_type) into a shared list."""

    def __init__(
            self,
            log: ta.List[tuple],
            name: str,
            *,
            value: ta.Any = None,
            enter_exc: ta.Optional[BaseException] = None,
            exit_exc: ta.Optional[BaseException] = None,
            suppress: bool = False,
    ) -> None:
        self.log = log
        self.name = name
        self.value = value
        self.enter_exc = enter_exc
        self.exit_exc = exit_exc
        self.suppress = suppress

    def __enter__(self):
        self.log.append(('enter', self.name))
        if self.enter_exc is not None:
            raise self.enter_exc
        return self.value

    def __exit__(self, et, e, tb):
        self.log.append(('exit', self.name, et))
        if self.exit_exc is not None:
            raise self.exit_exc
        return self.suppress


class _ACm:
    """Async counterpart of _Cm - yields to the loop on both enter and exit."""

    def __init__(
            self,
            log: ta.List[tuple],
            name: str,
            *,
            value: ta.Any = None,
            enter_exc: ta.Optional[BaseException] = None,
            exit_exc: ta.Optional[BaseException] = None,
            suppress: bool = False,
    ) -> None:
        self.log = log
        self.name = name
        self.value = value
        self.enter_exc = enter_exc
        self.exit_exc = exit_exc
        self.suppress = suppress

    async def __aenter__(self):
        await asyncio.sleep(0)
        self.log.append(('aenter', self.name))
        if self.enter_exc is not None:
            raise self.enter_exc
        return self.value

    async def __aexit__(self, et, e, tb):
        await asyncio.sleep(0)
        self.log.append(('aexit', self.name, et))
        if self.exit_exc is not None:
            raise self.exit_exc
        return self.suppress


##


class _Es(ExitStacked):
    def __init__(
            self,
            on_enter: ta.Optional[ta.Callable[['_Es'], None]] = None,
            on_exit: ta.Optional[ta.Callable[['_Es'], None]] = None,
    ) -> None:
        super().__init__()
        self.on_enter = on_enter
        self.on_exit = on_exit

    def _enter_contexts(self) -> None:
        if self.on_enter is not None:
            self.on_enter(self)

    def _exit_contexts(self) -> None:
        if self.on_exit is not None:
            self.on_exit(self)


class _LockedEs(_Es):
    def __init__(self, *args: ta.Any, **kwargs: ta.Any) -> None:
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    @contextlib.contextmanager
    def _exit_stacked_init_wrapper(self) -> ta.Iterator[None]:
        with self.lock:
            yield


class TestExitStackedLifecycle(unittest.TestCase):
    def test_initial_state_is_new(self):
        es = _Es()
        self.assertEqual(es._exit_stacked_state, 'new')
        self.assertIsNone(es._exit_stack)

    def test_enter_returns_self(self):
        es = _Es()
        with es as v:
            self.assertIs(v, es)

    def test_states_through_normal_lifecycle(self):
        seen = []
        es = _Es(
            on_enter=lambda s: seen.append(('in _enter_contexts', s._exit_stacked_state)),
            on_exit=lambda s: seen.append(('in _exit_contexts', s._exit_stacked_state)),
        )
        seen.append(('before', es._exit_stacked_state))
        with es:
            seen.append(('body', es._exit_stacked_state))
        seen.append(('after', es._exit_stacked_state))
        self.assertEqual(seen, [
            ('before', 'new'),
            ('in _enter_contexts', 'entering'),
            ('body', 'entered'),
            ('in _exit_contexts', 'exiting'),
            ('after', 'exited'),
        ])

    def test_state_property_is_read_only(self):
        es = _Es()
        with self.assertRaises(AttributeError):
            es._exit_stacked_state = 'entered'  # type: ignore

    def test_state_is_per_instance(self):
        a, b = _Es(), _Es()
        with a:
            self.assertEqual(a._exit_stacked_state, 'entered')
            self.assertEqual(b._exit_stacked_state, 'new')
        self.assertEqual(b._exit_stacked_state, 'new')
        with b:
            pass
        self.assertEqual(a._exit_stacked_state, 'exited')
        self.assertEqual(b._exit_stacked_state, 'exited')

    def test_subclass_dunder_state_name_does_not_collide(self):
        # The base's private attr is name-mangled, so a subclass using the same spelling gets its own attribute.
        class Es(_Es):
            __exit_stacked_state = 'mine'

            def mine(self):
                return self.__exit_stacked_state

        es = Es()
        with es:
            self.assertEqual(es._exit_stacked_state, 'entered')
            self.assertEqual(es.mine(), 'mine')


class TestExitStackedContexts(unittest.TestCase):
    def test_enter_context_returns_cm_value(self):
        log: list = []
        got = []
        es = _Es(on_enter=lambda s: got.append(s._enter_context(_Cm(log, 'a', value=420))))
        with es:
            self.assertEqual(got, [420])

    def test_contexts_unwound_lifo_after_exit_contexts(self):
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            s._enter_context(_Cm(log, 'b'))
            s._enter_context(_Cm(log, 'c'))

        es = _Es(on_enter=on_enter, on_exit=lambda s: log.append(('_exit_contexts',)))
        with es:
            log.append(('body',))
        self.assertEqual(log, [
            ('enter', 'a'),
            ('enter', 'b'),
            ('enter', 'c'),
            ('body',),
            ('_exit_contexts',),
            ('exit', 'c', None),
            ('exit', 'b', None),
            ('exit', 'a', None),
        ])

    def test_enter_context_from_body_is_unwound(self):
        log: list = []
        with _Es() as es:
            self.assertEqual(es._enter_context(_Cm(log, 'a', value='v')), 'v')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_enter_context_before_enter_raises(self):
        log: list = []
        es = _Es()
        with self.assertRaises(RuntimeError):
            es._enter_context(_Cm(log, 'a'))
        self.assertEqual(log, [])
        self.assertEqual(es._exit_stacked_state, 'new')

    def test_enter_context_after_exit_raises(self):
        # The stack has already been unwound; anything pushed onto it now would never be exited.
        log: list = []
        es = _Es()
        with es:
            pass
        with self.assertRaises(RuntimeError):
            es._enter_context(_Cm(log, 'late'))
        self.assertEqual(log, [])

    def test_enter_context_after_failed_enter_raises(self):
        log: list = []

        def on_enter(s):
            raise ValueError

        es = _Es(on_enter=on_enter)
        with self.assertRaises(ValueError):
            with es:
                pass
        self.assertEqual(es._exit_stacked_state, 'error')
        with self.assertRaises(RuntimeError):
            es._enter_context(_Cm(log, 'late'))
        self.assertEqual(log, [])


class TestExitStackedReentry(unittest.TestCase):
    def test_nested_reenter_raises_and_preserves_state(self):
        log: list = []
        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        with es:
            with self.assertRaises(RuntimeError) as cm:
                with es:
                    self.fail('nested body must not run')
            self.assertIn("'entered'", str(cm.exception))
            self.assertEqual(es._exit_stacked_state, 'entered')
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_reenter_after_exit_raises(self):
        log: list = []
        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        with es:
            pass
        with self.assertRaises(RuntimeError):
            with es:
                self.fail('body must not run')
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_reenter_after_failed_enter_raises(self):
        calls = []

        def on_enter(s):
            calls.append(1)
            raise ValueError

        es = _Es(on_enter=on_enter)
        with self.assertRaises(ValueError):
            es.__enter__()
        with self.assertRaises(RuntimeError):
            es.__enter__()
        self.assertEqual(calls, [1])
        self.assertEqual(es._exit_stacked_state, 'error')

    def test_exit_without_enter_raises(self):
        es = _Es(on_exit=lambda s: self.fail('_exit_contexts must not run'))
        with self.assertRaises(RuntimeError):
            es.__exit__(None, None, None)
        self.assertEqual(es._exit_stacked_state, 'new')

    def test_double_exit_raises_and_does_not_rerun(self):
        log: list = []
        es = _Es(
            on_enter=lambda s: s._enter_context(_Cm(log, 'a')),
            on_exit=lambda s: log.append(('_exit_contexts',)),
        )
        es.__enter__()
        es.__exit__(None, None, None)
        with self.assertRaises(RuntimeError):
            es.__exit__(None, None, None)
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('_exit_contexts',), ('exit', 'a', None)])


class TestExitStackedErrors(unittest.TestCase):
    def test_enter_contexts_failure_unwinds_and_sets_error(self):
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            s._enter_context(_Cm(log, 'b'))
            raise ValueError('boom')

        es = _Es(on_enter=on_enter, on_exit=lambda s: self.fail('_exit_contexts must not run'))
        with self.assertRaisesRegex(ValueError, 'boom'):
            with es:
                self.fail('body must not run')
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [
            ('enter', 'a'),
            ('enter', 'b'),
            ('exit', 'b', ValueError),
            ('exit', 'a', ValueError),
        ])

    def test_nested_cm_enter_failure_unwinds_earlier_ones(self):
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            s._enter_context(_Cm(log, 'b', enter_exc=KeyError('b')))

        es = _Es(on_enter=on_enter)
        with self.assertRaises(KeyError):
            es.__enter__()
        self.assertEqual(es._exit_stacked_state, 'error')
        # 'b' never finished entering so is never exited.
        self.assertEqual(log, [('enter', 'a'), ('enter', 'b'), ('exit', 'a', KeyError)])

    def test_enter_contexts_base_exception_unwinds(self):
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            raise KeyboardInterrupt

        es = _Es(on_enter=on_enter)
        with self.assertRaises(KeyboardInterrupt):
            es.__enter__()
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', KeyboardInterrupt)])

    def test_enter_contexts_failure_suppressed_by_nested_cm_still_raises(self):
        # Even if a nested cm 'suppresses' the init error, __enter__ must not succeed.
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a', suppress=True))
            raise ValueError

        es = _Es(on_enter=on_enter)
        with self.assertRaises(ValueError):
            es.__enter__()
        self.assertEqual(es._exit_stacked_state, 'error')

    def test_exit_contexts_failure_unwinds_and_sets_error(self):
        log: list = []

        def on_exit(s):
            raise ValueError('exit boom')

        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')), on_exit=on_exit)
        with self.assertRaisesRegex(ValueError, 'exit boom'):
            with es:
                pass
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', ValueError)])

    def test_exit_contexts_failure_chains_body_exception(self):
        log: list = []

        def on_exit(s):
            raise KeyError('exit')

        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')), on_exit=on_exit)
        with self.assertRaises(KeyError) as cm:
            with es:
                raise ValueError('body')
        self.assertIsInstance(cm.exception.__context__, ValueError)
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', KeyError)])

    def test_body_exception_propagates_and_state_is_exited(self):
        # A failure in the with-body is the caller's error, not the object's - it still exits cleanly.
        log: list = []
        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        with self.assertRaisesRegex(ValueError, 'body'):
            with es:
                raise ValueError('body')
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', ValueError)])

    def test_body_exception_suppressed_by_nested_cm(self):
        log: list = []
        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a', suppress=True)))
        with es:
            raise ValueError('swallowed')
        self.assertEqual(es._exit_stacked_state, 'exited')  # type: ignore  # noqa
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', ValueError)])  # noqa

    def test_exit_returns_suppression_flag(self):
        log: list = []
        es = _Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a', suppress=True)))
        es.__enter__()
        try:
            raise ValueError
        except ValueError as e:
            self.assertTrue(es.__exit__(type(e), e, e.__traceback__))

        es2 = _Es()
        es2.__enter__()
        self.assertFalse(es2.__exit__(None, None, None))

    def test_nested_cm_exit_failure_propagates_and_sets_error(self):
        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            s._enter_context(_Cm(log, 'b', exit_exc=KeyError('b exit')))

        es = _Es(on_enter=on_enter)
        with self.assertRaises(KeyError):
            with es:
                pass
        self.assertEqual(es._exit_stacked_state, 'error')
        # 'a' still gets exited, and sees the failure from 'b'.
        self.assertEqual(log, [('enter', 'a'), ('enter', 'b'), ('exit', 'b', None), ('exit', 'a', KeyError)])


class TestExitStackedInitWrapper(unittest.TestCase):
    def test_wrapper_wraps_enter_and_has_no_stack(self):
        log: list = []

        class Es(_Es):
            @contextlib.contextmanager
            def _exit_stacked_init_wrapper(self):
                log.append(('wrapper before', self._exit_stack is None))
                yield
                log.append(('wrapper after',))

        es = Es(on_enter=lambda s: log.append(('_enter_contexts',)))
        with es:
            log.append(('body',))
        self.assertEqual(log, [
            ('wrapper before', True),
            ('_enter_contexts',),
            ('wrapper after',),
            ('body',),
        ])

    def test_wrapper_not_used_on_exit(self):
        calls = []

        class Es(_Es):
            @contextlib.contextmanager
            def _exit_stacked_init_wrapper(self):
                calls.append(1)
                yield

        with Es():
            pass
        self.assertEqual(calls, [1])

    def test_wrapper_failure_before_yield_leaves_object_usable(self):
        # e.g. a lock acquire timing out: nothing was entered, so the object should not be bricked.
        class Es(_Es):
            fail = True

            @contextlib.contextmanager
            def _exit_stacked_init_wrapper(self):
                if self.fail:
                    raise TimeoutError
                yield

        log: list = []
        es = Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        with self.assertRaises(TimeoutError):
            es.__enter__()
        self.assertEqual(es._exit_stacked_state, 'new')
        self.assertEqual(log, [])

        es.fail = False
        with es:
            pass
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_wrapper_swallowing_init_error_does_not_report_entered(self):
        class Es(_Es):
            @contextlib.contextmanager
            def _exit_stacked_init_wrapper(self):
                try:
                    yield
                except ValueError:
                    pass

        log: list = []

        def on_enter(s):
            s._enter_context(_Cm(log, 'a'))
            raise ValueError

        es = Es(on_enter=on_enter)
        with self.assertRaises(RuntimeError):
            with es:
                self.fail('body must not run against an already-unwound stack')
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', ValueError)])

    def test_locked_enter_exit(self):
        log: list = []
        es = _LockedEs(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        with es:
            self.assertFalse(es.lock.locked())
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_racing_enter_does_not_clobber_winner(self):
        # Deterministically simulates a thread switch landing between a racer's 'new' state check and its state write.
        # That window only exists if the check isn't serialized by the init wrapper's lock, so the racer only pauses if
        # it reaches the check without the lock held.
        log: list = []
        racer_checked = threading.Event()
        winner_entered = threading.Event()
        racer: ta.Optional[threading.Thread] = None

        class Es(_LockedEs):
            def _check_exit_stacked_state(self, *valid):
                super()._check_exit_stacked_state(*valid)
                if valid == ('new',) and threading.current_thread() is racer:
                    racer_checked.set()
                    if not self.lock.locked():
                        winner_entered.wait(5.)

        es = Es(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        outcomes: ta.Dict[str, ta.Any] = {}

        def race():
            try:
                outcomes['racer'] = es.__enter__()
            except BaseException as e:  # noqa
                outcomes['racer'] = e

        racer = threading.Thread(target=race)
        racer.start()
        try:
            self.assertTrue(racer_checked.wait(5.))
            try:
                outcomes['main'] = es.__enter__()
            except RuntimeError as e:
                outcomes['main'] = e
        finally:
            winner_entered.set()
            racer.join(5.)
        self.assertFalse(racer.is_alive())

        winners = [k for k, v in outcomes.items() if v is es]
        losers = [k for k, v in outcomes.items() if isinstance(v, RuntimeError)]
        self.assertEqual(len(winners), 1, outcomes)
        self.assertEqual(len(losers), 1, outcomes)

        # The loser's failed attempt must not have touched the winner's state...
        self.assertEqual(es._exit_stacked_state, 'entered')
        # ...so the winner can still exit and unwind its contexts.
        es.__exit__(None, None, None)
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('enter', 'a'), ('exit', 'a', None)])

    def test_concurrent_enters_exactly_one_wins(self):
        n = 8
        barrier = threading.Barrier(n)
        log: list = []
        es = _LockedEs(on_enter=lambda s: s._enter_context(_Cm(log, 'a')))
        results: ta.List[ta.Any] = []
        results_lock = threading.Lock()

        def run():
            barrier.wait()
            try:
                r = es.__enter__()
            except RuntimeError as e:
                r = e  # type: ignore
            with results_lock:
                results.append(r)

        threads = [threading.Thread(target=run) for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(5.)

        self.assertEqual(sum(1 for r in results if r is es), 1)
        self.assertEqual(sum(1 for r in results if isinstance(r, RuntimeError)), n - 1)
        self.assertEqual(log, [('enter', 'a')])


class TestExitStackedSubclassChecks(unittest.TestCase):
    def test_mixin_overriding_enter_rejected(self):
        class M:
            def __enter__(self):
                return self

        with self.assertRaisesRegex(TypeError, '__enter__'):
            class Bad(M, ExitStacked):  # type: ignore  # noqa
                pass

    def test_mixin_overriding_exit_rejected(self):
        class M:
            def __exit__(self, et, e, tb):
                return None

        with self.assertRaisesRegex(TypeError, '__exit__'):
            class Bad(M, ExitStacked):  # type: ignore  # noqa
                pass

    def test_mixin_after_base_still_rejected(self):
        class M:
            def __enter__(self):
                return self

        with self.assertRaises(TypeError):
            class Bad(ExitStacked, M):  # noqa
                pass

    def test_grandchild_of_overriding_subclass_rejected(self):
        class Overrides(ExitStacked):
            def __enter__(self):  # type: ignore
                return self

        with self.assertRaises(TypeError):
            class Bad(Overrides):  # noqa
                pass

    def test_plain_mixins_and_deep_subclasses_allowed(self):
        class M:
            def helper(self):
                return 'helped'

        class A(M, ExitStacked):
            pass

        class B(A):
            pass

        with B() as b:
            self.assertEqual(b.helper(), 'helped')
            self.assertEqual(b._exit_stacked_state, 'entered')

    def test_init_subclass_kwargs_forwarded(self):
        seen = {}

        class Base(ExitStacked):
            def __init_subclass__(cls, *, tag=None, **kwargs):
                super().__init_subclass__(**kwargs)
                seen[cls.__name__] = tag

        class Child(Base, tag='x'):  # noqa
            pass

        self.assertEqual(seen, {'Child': 'x'})

    def test_async_and_sync_override_checks_are_independent(self):
        class M:
            def __enter__(self):
                return self

            def __exit__(self, et, e, tb):
                return None

        # A sync-cm mixin is fine on an *async* exit stacked.
        class Ok(M, AsyncExitStacked):
            pass

        self.assertTrue(issubclass(Ok, AsyncExitStacked))


##


class _AEs(AsyncExitStacked):
    def __init__(
            self,
            on_enter: ta.Optional[ta.Callable[['_AEs'], ta.Awaitable[None]]] = None,
            on_exit: ta.Optional[ta.Callable[['_AEs'], ta.Awaitable[None]]] = None,
    ) -> None:
        super().__init__()
        self.on_enter = on_enter
        self.on_exit = on_exit

    async def _async_enter_contexts(self) -> None:
        if self.on_enter is not None:
            await self.on_enter(self)

    async def _async_exit_contexts(self) -> None:
        if self.on_exit is not None:
            await self.on_exit(self)


class TestAsyncExitStacked(unittest.IsolatedAsyncioTestCase):
    async def test_initial_state_and_enter_returns_self(self):
        es = _AEs()
        self.assertEqual(es._exit_stacked_state, 'new')
        async with es as v:
            self.assertIs(v, es)
            self.assertEqual(es._exit_stacked_state, 'entered')
        self.assertEqual(es._exit_stacked_state, 'exited')

    async def test_states_through_normal_lifecycle(self):
        seen = []

        async def on_enter(s):
            seen.append(('enter', s._exit_stacked_state))

        async def on_exit(s):
            seen.append(('exit', s._exit_stacked_state))

        async with _AEs(on_enter, on_exit):
            pass
        self.assertEqual(seen, [('enter', 'entering'), ('exit', 'exiting')])

    async def test_mixed_sync_and_async_contexts_unwound_lifo(self):
        log: list = []
        got = []

        async def on_enter(s):
            got.append(await s._enter_async_context(_ACm(log, 'a', value=1)))
            got.append(s._enter_context(_Cm(log, 's', value=2)))
            got.append(await s._enter_async_context(_ACm(log, 'b', value=3)))

        async def on_exit(s):
            log.append(('_async_exit_contexts',))

        async with _AEs(on_enter, on_exit):
            log.append(('body',))
        self.assertEqual(got, [1, 2, 3])
        self.assertEqual(log, [
            ('aenter', 'a'),
            ('enter', 's'),
            ('aenter', 'b'),
            ('body',),
            ('_async_exit_contexts',),
            ('aexit', 'b', None),
            ('exit', 's', None),
            ('aexit', 'a', None),
        ])

    async def test_enter_contexts_outside_lifecycle_raise(self):
        log: list = []
        es = _AEs()
        with self.assertRaises(RuntimeError):
            es._enter_context(_Cm(log, 'x'))
        with self.assertRaises(RuntimeError):
            await es._enter_async_context(_ACm(log, 'y'))
        self.assertEqual(log, [])

    async def test_enter_contexts_after_exit_raise(self):
        log: list = []
        es = _AEs()
        async with es:
            pass
        with self.assertRaises(RuntimeError):
            es._enter_context(_Cm(log, 'late'))
        with self.assertRaises(RuntimeError):
            await es._enter_async_context(_ACm(log, 'late'))
        self.assertEqual(log, [])

    async def test_enter_failure_unwinds_and_sets_error(self):
        log: list = []

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a'))
            s._enter_context(_Cm(log, 's'))
            raise ValueError('boom')

        es = _AEs(on_enter)
        with self.assertRaisesRegex(ValueError, 'boom'):
            async with es:
                self.fail('body must not run')
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [
            ('aenter', 'a'),
            ('enter', 's'),
            ('exit', 's', ValueError),
            ('aexit', 'a', ValueError),
        ])

    async def test_exit_failure_unwinds_and_sets_error(self):
        log: list = []

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a'))

        async def on_exit(s):
            raise ValueError('exit boom')

        es = _AEs(on_enter, on_exit)
        with self.assertRaisesRegex(ValueError, 'exit boom'):
            async with es:
                pass
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('aenter', 'a'), ('aexit', 'a', ValueError)])

    async def test_body_exception_propagates_and_state_is_exited(self):
        log: list = []

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a'))

        es = _AEs(on_enter)
        with self.assertRaises(ValueError):
            async with es:
                raise ValueError
        self.assertEqual(es._exit_stacked_state, 'exited')
        self.assertEqual(log, [('aenter', 'a'), ('aexit', 'a', ValueError)])

    async def test_body_exception_suppressed_by_nested_cm(self):
        log: list = []

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a', suppress=True))

        es = _AEs(on_enter)
        async with es:
            raise ValueError
        self.assertEqual(es._exit_stacked_state, 'exited')  # type: ignore

    async def test_reenter_and_double_exit_raise(self):
        es = _AEs()
        async with es:
            with self.assertRaises(RuntimeError):
                async with es:
                    self.fail('nested body must not run')
            self.assertEqual(es._exit_stacked_state, 'entered')
        with self.assertRaises(RuntimeError):
            await es.__aexit__(None, None, None)
        with self.assertRaises(RuntimeError):
            await es.__aenter__()
        self.assertEqual(es._exit_stacked_state, 'exited')

    async def test_exit_without_enter_raises(self):
        es = _AEs()
        with self.assertRaises(RuntimeError):
            await es.__aexit__(None, None, None)
        self.assertEqual(es._exit_stacked_state, 'new')

    async def test_cancel_during_enter_unwinds_and_sets_error(self):
        log: list = []
        started = asyncio.Event()
        never = asyncio.Event()

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a'))
            started.set()
            await never.wait()

        es = _AEs(on_enter)
        task = asyncio.ensure_future(es.__aenter__())
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(es._exit_stacked_state, 'error')
        self.assertEqual(log, [('aenter', 'a'), ('aexit', 'a', asyncio.CancelledError)])

    async def test_concurrent_task_enter_while_entering_raises(self):
        # Two tasks racing on one instance: the second sees 'entering' and fails without disturbing the first.
        log: list = []
        started = asyncio.Event()
        go = asyncio.Event()

        async def on_enter(s):
            await s._enter_async_context(_ACm(log, 'a'))
            started.set()
            await go.wait()

        es = _AEs(on_enter)
        first = asyncio.ensure_future(es.__aenter__())
        await started.wait()
        with self.assertRaises(RuntimeError):
            await es.__aenter__()
        with self.assertRaises(RuntimeError):
            await es.__aexit__(None, None, None)
        self.assertEqual(es._exit_stacked_state, 'entering')
        go.set()
        self.assertIs(await first, es)
        self.assertEqual(es._exit_stacked_state, 'entered')
        await es.__aexit__(None, None, None)
        self.assertEqual(log, [('aenter', 'a'), ('aexit', 'a', None)])

    async def test_init_wrapper_wraps_enter_only(self):
        log: list = []

        class Es(_AEs):
            @contextlib.asynccontextmanager
            async def _async_exit_stacked_init_wrapper(self):
                log.append(('wrapper before', self._exit_stack is None))
                await asyncio.sleep(0)
                yield
                log.append(('wrapper after',))

        async def on_enter(s):
            log.append(('_async_enter_contexts',))

        async with Es(on_enter):
            log.append(('body',))
        self.assertEqual(log, [
            ('wrapper before', True),
            ('_async_enter_contexts',),
            ('wrapper after',),
            ('body',),
        ])

    async def test_init_wrapper_with_asyncio_lock_serializes(self):
        lock = asyncio.Lock()
        log: list = []

        class Es(_AEs):
            @contextlib.asynccontextmanager
            async def _async_exit_stacked_init_wrapper(self):
                async with lock:
                    yield

        async def on_enter(s):
            log.append(('enter', lock.locked()))

        async with Es(on_enter):
            self.assertFalse(lock.locked())
        self.assertEqual(log, [('enter', True)])

    async def test_init_wrapper_failure_before_yield_leaves_object_usable(self):
        class Es(_AEs):
            fail = True

            @contextlib.asynccontextmanager
            async def _async_exit_stacked_init_wrapper(self):
                if self.fail:
                    raise TimeoutError
                yield

        es = Es()
        with self.assertRaises(TimeoutError):
            await es.__aenter__()
        self.assertEqual(es._exit_stacked_state, 'new')
        es.fail = False
        async with es:
            pass
        self.assertEqual(es._exit_stacked_state, 'exited')

    async def test_init_wrapper_swallowing_init_error_does_not_report_entered(self):
        class Es(_AEs):
            @contextlib.asynccontextmanager
            async def _async_exit_stacked_init_wrapper(self):
                try:
                    yield
                except ValueError:
                    pass

        async def on_enter(s):
            raise ValueError

        es = Es(on_enter)
        with self.assertRaises(RuntimeError):
            async with es:
                self.fail('body must not run')
        self.assertEqual(es._exit_stacked_state, 'error')

    def test_mixin_overriding_aenter_rejected(self):
        class M:
            async def __aenter__(self):
                return self

        with self.assertRaisesRegex(TypeError, '__aenter__'):
            class Bad(M, AsyncExitStacked):  # type: ignore  # noqa
                pass

    def test_mixin_overriding_aexit_rejected(self):
        class M:
            async def __aexit__(self, et, e, tb):
                return None

        with self.assertRaisesRegex(TypeError, '__aexit__'):
            class Bad(M, AsyncExitStacked):  # type: ignore  # noqa
                pass


##


class TestDefer(unittest.TestCase):
    def test_runs_on_exit(self):
        calls = []
        with defer(lambda: calls.append('done')):
            self.assertEqual(calls, [])
        self.assertEqual(calls, ['done'])

    def test_passes_args_and_kwargs(self):
        calls = []

        def fn(*args, **kwargs):
            calls.append((args, kwargs))

        with defer(fn, 1, 2, x=3):
            pass
        self.assertEqual(calls, [((1, 2), {'x': 3})])

    def test_yields_bound_callable(self):
        calls = []

        def fn(a):
            calls.append(a)

        with defer(fn, 'v') as f:
            f()
        self.assertEqual(calls, ['v', 'v'])

    def test_yields_fn_itself_without_args(self):
        def fn():
            pass

        with defer(fn) as f:
            self.assertIs(f, fn)

    def test_runs_on_exception_and_propagates(self):
        calls = []
        with self.assertRaises(ValueError):
            with defer(lambda: calls.append(1)):
                raise ValueError
        self.assertEqual(calls, [1])

    def test_lifo_when_nested(self):
        calls = []  # type: ignore
        with defer(calls.append, 'outer'):
            with defer(calls.append, 'inner'):
                pass
        self.assertEqual(calls, ['inner', 'outer'])

    def test_deferred_exception_chains_body_exception(self):
        def fail():
            raise KeyError

        with self.assertRaises(KeyError) as cm:
            with defer(fail):
                raise ValueError
        self.assertIsInstance(cm.exception.__context__, ValueError)


class TestADefer(unittest.IsolatedAsyncioTestCase):
    async def test_awaits_on_exit(self):
        calls = []

        async def fn():
            calls.append('done')

        async with adefer(fn()):
            self.assertEqual(calls, [])
        self.assertEqual(calls, ['done'])

    async def test_awaits_on_exception_and_propagates(self):
        calls = []

        async def fn():
            calls.append('done')

        with self.assertRaises(ValueError):
            async with adefer(fn()):
                raise ValueError
        self.assertEqual(calls, ['done'])

    async def test_accepts_future(self):
        fut = asyncio.get_event_loop().create_future()
        fut.set_result(5)
        async with adefer(fut) as f:
            self.assertIs(f, fut)


##


class TestAttrSetting(unittest.TestCase):
    def test_sets_and_restores_existing_instance_attr(self):
        class C:
            pass

        c = C()
        c.x = 1  # type: ignore
        with attr_setting(c, 'x', 2) as orig:
            self.assertEqual(orig, 1)
            self.assertEqual(c.x, 2)  # type: ignore
        self.assertEqual(c.x, 1)  # type: ignore

    def test_deletes_when_previously_absent(self):
        class C:
            pass

        c = C()
        with attr_setting(c, 'x', 2) as orig:
            self.assertIsNone(orig)
            self.assertEqual(c.x, 2)  # type: ignore
        self.assertFalse(hasattr(c, 'x'))

    def test_yields_default_when_absent(self):
        class C:
            pass

        sentinel = object()
        with attr_setting(C(), 'x', 2, default=sentinel) as orig:
            self.assertIs(orig, sentinel)

    def test_restores_on_exception(self):
        class C:
            pass

        c = C()
        c.x = 1  # type: ignore
        with self.assertRaises(ValueError):
            with attr_setting(c, 'x', 2):
                raise ValueError
        self.assertEqual(c.x, 1)  # type: ignore

    def test_deletes_on_exception_when_previously_absent(self):
        class C:
            pass

        c = C()
        with self.assertRaises(ValueError):
            with attr_setting(c, 'x', 2):
                raise ValueError
        self.assertFalse(hasattr(c, 'x'))

    def test_nested(self):
        class C:
            x = 0

        with attr_setting(C, 'x', 1):
            with attr_setting(C, 'x', 2):
                self.assertEqual(C.x, 2)
            self.assertEqual(C.x, 1)
        self.assertEqual(C.x, 0)

    def test_restores_none_value(self):
        class C:
            pass

        c = C()
        c.x = None  # type: ignore
        with attr_setting(c, 'x', 2, default='dflt') as orig:
            self.assertIsNone(orig)
        self.assertTrue(hasattr(c, 'x'))
        self.assertIsNone(c.x)  # type: ignore

    @unittest.expectedFailure
    def test_class_attr_not_materialized_on_instance(self):
        # Known issue: getattr() sees the class attribute, so on exit it's written back onto the *instance*, leaving a
        # shadowing instance attr that no longer tracks the class.
        class C:
            x = 1

        c = C()
        with attr_setting(c, 'x', 2):
            pass
        self.assertNotIn('x', vars(c))


##


class _AClosable:
    def __init__(self):
        self.closed = 0

    async def aclose(self):
        await asyncio.sleep(0)
        self.closed += 1


class TestAClosing(unittest.IsolatedAsyncioTestCase):
    async def test_alias(self):
        self.assertIs(aclosing, AsyncClosingManager)

    async def test_returns_thing_and_closes(self):
        t = _AClosable()
        async with aclosing(t) as v:
            self.assertIs(v, t)
            self.assertEqual(t.closed, 0)
        self.assertEqual(t.closed, 1)

    async def test_closes_on_exception_and_propagates(self):
        t = _AClosable()
        with self.assertRaises(ValueError):
            async with aclosing(t):
                raise ValueError
        self.assertEqual(t.closed, 1)

    async def test_closes_async_generator_early(self):
        log: list = []

        async def agen():
            try:
                for i in range(10):
                    yield i
            finally:
                log.append('finalized')

        async with aclosing(agen()) as g:
            async for i in g:
                if i == 2:
                    break
        self.assertEqual(log, ['finalized'])
