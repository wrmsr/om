import concurrent.futures as cf
import contextlib
import typing as ta


T = ta.TypeVar('T')
P = ta.ParamSpec('P')


##


class ImmediateExecutor(cf.Executor):
    def __init__(self, *, immediate_exceptions: bool = False) -> None:
        super().__init__()

        self._immediate_exceptions = immediate_exceptions
        self._shutdown = False

    def submit(
            self,
            fn: ta.Callable[P, T],
            /,
            *args: P.args,
            **kwargs: P.kwargs,
    ) -> cf.Future[T]:
        if self._shutdown:
            raise RuntimeError('cannot schedule new futures after shutdown')

        future: ta.Any = cf.Future()
        future.set_running_or_notify_cancel()
        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except BaseException as e:
            if self._immediate_exceptions:
                raise
            future.set_exception(e)
        return future

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        self._shutdown = True


@contextlib.contextmanager
def new_executor(
        max_workers: int | None = None,
        cls: type[cf.Executor] = cf.ThreadPoolExecutor,
        *,
        immediate_exceptions: bool = False,
        **kwargs: ta.Any,
) -> ta.Generator[cf.Executor]:
    if max_workers == 0:
        with ImmediateExecutor(
                immediate_exceptions=immediate_exceptions,
        ) as exe:
            yield exe

    else:
        with cls(  # type: ignore
                max_workers,
                **kwargs,
        ) as exe:
            yield exe
