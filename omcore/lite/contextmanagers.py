# ruff: noqa: UP007 UP043 UP045
import contextlib
import functools
import sys
import typing as ta


T = ta.TypeVar('T')
ExitStackedT = ta.TypeVar('ExitStackedT', bound='ExitStacked')
AsyncExitStackedT = ta.TypeVar('AsyncExitStackedT', bound='AsyncExitStacked')


##


ExitStackedState = ta.Literal[  # ta.TypeAlias  # om-amalg-typing-no-move  # noqa
    'new',

    'entering',
    'entered',

    'exiting',
    'exited',

    'error',
]


class _BaseExitStacked(ta.Generic[T]):
    _exit_stack: ta.Optional[T] = None

    #

    @classmethod
    def _exit_stacked_check_methods(cls, es_cls, methods: ta.Sequence[str]) -> None:
        for a in methods:
            for b in cls.__bases__:
                if b is es_cls:
                    continue
                try:
                    fn = getattr(b, a)
                except AttributeError:
                    pass
                else:
                    if fn is not getattr(es_cls, a):
                        raise TypeError(f'{es_cls.__name__} subclass {cls} must not override {a} via {b}')

    #

    __exit_stacked_state: ExitStackedState = 'new'

    @property
    def _exit_stacked_state(self) -> ExitStackedState:
        return self.__exit_stacked_state  # noqa

    def _check_exit_stacked_state(self, *valid: ExitStackedState) -> None:
        if self.__exit_stacked_state not in valid:
            raise RuntimeError(f'ExitStacked current state {self.__exit_stacked_state!r} in valid state set {valid!r}')

    def _set_exit_stacked_state(self, new: ExitStackedState) -> None:
        self.__exit_stacked_state = new

    def _exit_stacked_state_transition(self, start: ExitStackedState, end: ExitStackedState) -> ta.ContextManager[None]:
        return _ExitStackedStateTransition(self, start, end)


class _ExitStackedStateTransition:
    def __init__(self, obj: _BaseExitStacked, start: ExitStackedState, end: ExitStackedState) -> None:
        self._obj, self._start, self._end = obj, start, end

    def __enter__(self) -> None:
        self._obj._set_exit_stacked_state(self._start)  # noqa

    def __exit__(self, et, e, tb):
        if e is None:
            self._obj._set_exit_stacked_state(self._end)  # noqa
        else:
            self._obj._set_exit_stacked_state('error')


#


class ExitStacked(_BaseExitStacked[contextlib.ExitStack]):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        cls._exit_stacked_check_methods(ExitStacked, ('__enter__', '__exit__'))

    @contextlib.contextmanager
    def _exit_stacked_init_wrapper(self) -> ta.Iterator[None]:
        """
        Overridable wrapper around __enter__ which deliberately does not have access to an _exit_stack yet. Intended for
        things like wrapping __enter__ in a lock.
        """

        yield

    @ta.final
    def __enter__(self: ExitStackedT) -> ExitStackedT:
        """
        Final because any contexts entered during this init must be exited if any exception is thrown, and user
        overriding would likely interfere with that. Override `_enter_contexts` for such init.
        """

        self._check_exit_stacked_state('new')
        with self._exit_stacked_state_transition('entering', 'entered'):
            with self._exit_stacked_init_wrapper():
                if self._exit_stack is not None:
                    raise RuntimeError

                es = self._exit_stack = contextlib.ExitStack()
                es.__enter__()

                try:
                    self._enter_contexts()
                except BaseException:  # noqa
                    es.__exit__(*sys.exc_info())
                    raise

                return self

    @ta.final
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._check_exit_stacked_state('entered')
        with self._exit_stacked_state_transition('exiting', 'exited'):
            if (es := self._exit_stack) is None:
                return None

            try:
                self._exit_contexts()
            except BaseException:  # noqa
                es.__exit__(*sys.exc_info())
                raise

            return es.__exit__(exc_type, exc_val, exc_tb)

    def _enter_contexts(self) -> None:
        pass

    def _exit_contexts(self) -> None:
        pass

    @ta.final
    def _enter_context(self, cm: ta.ContextManager[T]) -> T:
        if (es := self._exit_stack) is None:
            raise RuntimeError
        return es.enter_context(cm)


#


class AsyncExitStacked(_BaseExitStacked[contextlib.AsyncExitStack]):
    def __init_subclass__(cls, **kwargs: ta.Any) -> None:
        super().__init_subclass__(**kwargs)

        cls._exit_stacked_check_methods(AsyncExitStacked, ('__aenter__', '__aexit__'))

    @contextlib.asynccontextmanager
    async def _async_exit_stacked_init_wrapper(self) -> ta.AsyncGenerator[None, None]:
        yield

    @ta.final
    async def __aenter__(self: AsyncExitStackedT) -> AsyncExitStackedT:
        self._check_exit_stacked_state('new')
        with self._exit_stacked_state_transition('entering', 'entered'):
            async with self._async_exit_stacked_init_wrapper():
                if self._exit_stack is not None:
                    raise RuntimeError

                es = self._exit_stack = contextlib.AsyncExitStack()
                await es.__aenter__()

                try:
                    await self._async_enter_contexts()
                except BaseException:  # noqa
                    await es.__aexit__(*sys.exc_info())
                    raise

                return self

    @ta.final
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._check_exit_stacked_state('entered')
        with self._exit_stacked_state_transition('exiting', 'exited'):
            if (es := self._exit_stack) is None:
                return None

            try:
                await self._async_exit_contexts()
            except BaseException:  # noqa
                await es.__aexit__(*sys.exc_info())
                raise

            return await es.__aexit__(exc_type, exc_val, exc_tb)

    async def _async_enter_contexts(self) -> None:
        pass

    async def _async_exit_contexts(self) -> None:
        pass

    @ta.final
    def _enter_context(self, cm: ta.ContextManager[T]) -> T:
        if (es := self._exit_stack) is None:
            raise RuntimeError
        return es.enter_context(cm)

    @ta.final
    async def _enter_async_context(self, cm: ta.AsyncContextManager[T]) -> T:
        if (es := self._exit_stack) is None:
            raise RuntimeError
        return await es.enter_async_context(cm)


##


@contextlib.contextmanager
def defer(fn: ta.Callable, *args: ta.Any, **kwargs: ta.Any) -> ta.Generator[ta.Callable, None, None]:
    if args or kwargs:
        fn = functools.partial(fn, *args, **kwargs)
    try:
        yield fn
    finally:
        fn()


@contextlib.asynccontextmanager
async def adefer(fn: ta.Awaitable) -> ta.AsyncGenerator[ta.Awaitable, None]:
    try:
        yield fn
    finally:
        await fn


##


@contextlib.contextmanager
def attr_setting(obj, attr, val, *, default=None):  # noqa
    not_set = object()
    orig = getattr(obj, attr, not_set)
    try:
        setattr(obj, attr, val)
        if orig is not not_set:
            yield orig
        else:
            yield default
    finally:
        if orig is not_set:
            delattr(obj, attr)
        else:
            setattr(obj, attr, orig)


##


class AsyncClosingManager(contextlib.AbstractAsyncContextManager):
    def __init__(self, thing):
        self.thing = thing

    async def __aenter__(self):
        return self.thing

    async def __aexit__(self, *exc_info):
        await self.thing.aclose()


aclosing = AsyncClosingManager
