import concurrent.futures
import concurrent.interpreters
import importlib
import pickle
import queue
import sys
import threading
import traceback
import typing as ta

from .... import check
from .... import dataclasses as dc
from .... import lang
from ...runtime import Activity
from ...runtime import ActivityRejectedError
from ...runtime import ServiceRuntime
from ..workers import LocalWorkerContext
from ..workers import LocalWorkerRunner
from .errors import SubinterpreterCallTimeoutError
from .errors import SubinterpreterCodeIdentityError
from .errors import SubinterpreterExecutionError
from .errors import SubinterpreterGilError
from .errors import SubinterpreterRemoteError
from .errors import SubinterpreterSerializationError
from .errors import SubinterpreterUnavailableError
from .interfaces import SubinterpreterBootstrapInfo
from .interfaces import SubinterpreterCaller
from .interfaces import SubinterpreterService
from .interfaces import SubinterpreterTarget
from .interfaces import validate_max_pending_calls


T = ta.TypeVar('T')


##


_SUBINTERPRETER_SERVICE: SubinterpreterService | None = None


def _initialize_service(
        factory_name: str,
        code_identity_name: str,
        expected_code_identity: str,
        config_data: bytes,
        module_search_paths: tuple[str, ...],
        preload_modules: tuple[str, ...],
        require_gil: bool,
        allow_code_identity_mismatch: bool,
) -> tuple[bool, ta.Any]:
    global _SUBINTERPRETER_SERVICE  # noqa

    check.none(_SUBINTERPRETER_SERVICE)

    sys.path[:0] = module_search_paths

    code_identity_obj = lang.import_attr(code_identity_name)
    if callable(code_identity_obj):
        actual_code_identity = check.non_empty_str(code_identity_obj())
    else:
        actual_code_identity = check.non_empty_str(code_identity_obj)

    if actual_code_identity != expected_code_identity and not allow_code_identity_mismatch:
        return (False, ('code-identity', actual_code_identity))

    for module in preload_modules:
        importlib.import_module(module)

    gil_enabled = sys._is_gil_enabled()  # noqa
    if require_gil and not gil_enabled:
        return (False, ('gil', None))

    factory = check.callable(lang.import_attr(factory_name))
    config = pickle.loads(config_data)  # noqa: S301
    service = check.isinstance(factory(config), SubinterpreterService)
    _SUBINTERPRETER_SERVICE = service

    return (True, (
        concurrent.interpreters.get_current().id,
        gil_enabled,
        actual_code_identity,
    ))


def _dispatch_service(payload: bytes) -> bytes:
    service = check.not_none(_SUBINTERPRETER_SERVICE)

    try:
        method, args, kwargs = pickle.loads(payload)  # noqa: S301
        result = service.dispatch(
            check.non_empty_str(method),
            check.isinstance(args, tuple),
            check.isinstance(kwargs, dict),
        )
        return pickle.dumps((True, result), protocol=pickle.HIGHEST_PROTOCOL)

    except BaseException as exc:  # noqa
        return pickle.dumps((False, (
            f'{type(exc).__module__}.{type(exc).__qualname__}',
            str(exc),
            traceback.format_exc(),
        )), protocol=pickle.HIGHEST_PROTOCOL)


def _finalize_service() -> None:
    global _SUBINTERPRETER_SERVICE  # noqa

    service = check.not_none(_SUBINTERPRETER_SERVICE)
    try:
        service.close()
    finally:
        _SUBINTERPRETER_SERVICE = None


##


@dc.dataclass(frozen=True)
class _CallTask:
    payload: bytes
    future: concurrent.futures.Future[bytes]
    activity: Activity


_STOP = object()


class _ThreadedSubinterpreterCaller(SubinterpreterCaller, lang.Final):
    def __init__(
            self,
            runtime: ServiceRuntime,
            bootstrap_info: SubinterpreterBootstrapInfo,
            *,
            max_pending_calls: int,
    ) -> None:
        super().__init__()

        self._runtime = runtime
        self._bootstrap_info = bootstrap_info
        self._queue: queue.Queue[_CallTask | object] = queue.Queue()
        self._slots = threading.BoundedSemaphore(max_pending_calls)

        self._lock = threading.Lock()
        self._accepting = True
        self._failure: SubinterpreterExecutionError | None = None

    @property
    def bootstrap_info(self) -> SubinterpreterBootstrapInfo:
        return self._bootstrap_info

    def _unavailable_locked(self) -> SubinterpreterUnavailableError:
        if self._failure is not None:
            return SubinterpreterUnavailableError(
                f'Subinterpreter worker failed: {self._failure}',
            )
        return SubinterpreterUnavailableError('Subinterpreter worker is shutting down')

    def begin_shutdown(self) -> bool:
        with self._lock:
            if not self._accepting:
                return False
            self._accepting = False
            self._queue.put(_STOP)
            return True

    def fail(self, exc: SubinterpreterExecutionError) -> None:
        with self._lock:
            self._failure = exc
            self._accepting = False

        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is _STOP:
                continue
            task = ta.cast(_CallTask, item)
            self.complete(task, exc=exc)

    def get(self) -> _CallTask | object:
        return self._queue.get()

    def complete(
            self,
            task: _CallTask,
            *,
            result: bytes | None = None,
            exc: BaseException | None = None,
    ) -> None:
        try:
            if exc is not None:
                task.future.set_exception(exc)
            else:
                task.future.set_result(check.not_none(result))
        finally:
            task.activity.close()
            self._slots.release()

    def invoke(
            self,
            method: str,
            args: tuple[ta.Any, ...] = (),
            kwargs: ta.Mapping[str, ta.Any] | None = None,
            *,
            timeout: lang.TimeoutLike = None,
    ) -> ta.Any:
        check.non_empty_str(method)
        check.isinstance(args, tuple)
        if kwargs is None:
            kwargs = {}
        elif not all(isinstance(key, str) for key in kwargs):
            raise TypeError('Subinterpreter call keyword names must be strings')

        try:
            payload = pickle.dumps(
                (method, args, dict(kwargs)),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except Exception as exc:
            raise SubinterpreterSerializationError(f'Could not serialize subinterpreter call: {exc}') from exc

        timeout_ = lang.Timeout.of(timeout)
        try:
            slot_timeout = timeout_.remaining_or(None)
        except TimeoutError as exc:
            raise SubinterpreterCallTimeoutError('Timed out waiting to submit subinterpreter call') from exc
        if not self._slots.acquire(timeout=slot_timeout):
            raise SubinterpreterCallTimeoutError('Timed out waiting to submit subinterpreter call')

        activity: Activity | None = None
        submitted = False
        try:
            with self._lock:
                if not self._accepting:
                    raise self._unavailable_locked()
                try:
                    activity = self._runtime.activity.acquire()
                except (ActivityRejectedError, RuntimeError) as exc:
                    raise SubinterpreterUnavailableError('Subinterpreter worker is shutting down') from exc

                future: concurrent.futures.Future[bytes] = concurrent.futures.Future()
                self._queue.put(_CallTask(payload, future, activity))
                activity = None
                submitted = True

        finally:
            if activity is not None:
                activity.close()
            if not submitted:
                self._slots.release()

        try:
            response_data = future.result(timeout=timeout_.remaining_or(None))
        except TimeoutError as exc:
            raise SubinterpreterCallTimeoutError('Timed out waiting for subinterpreter call') from exc

        try:
            ok, value = pickle.loads(response_data)  # noqa: S301
        except Exception as exc:
            raise SubinterpreterSerializationError(f'Could not deserialize subinterpreter response: {exc}') from exc

        if ok:
            return value

        remote_type, message, remote_traceback = value
        raise SubinterpreterRemoteError(
            remote_type=remote_type,
            message=message,
            remote_traceback=remote_traceback,
        )


##


@dc.dataclass(frozen=True)
class SubinterpreterLocalWorkerRunner(LocalWorkerRunner[T]):
    target: SubinterpreterTarget
    interface_factory: ta.Callable[[SubinterpreterCaller], T]
    max_pending_calls: int = 64

    def __post_init__(self) -> None:
        check.isinstance(self.target, SubinterpreterTarget)
        check.callable(self.interface_factory)
        validate_max_pending_calls(self.max_pending_calls)

    @staticmethod
    def _execution_error(exc: BaseException) -> SubinterpreterExecutionError:
        return SubinterpreterExecutionError(f'Subinterpreter execution failed: {exc}')

    def _bootstrap(
            self,
            interpreter: concurrent.interpreters.Interpreter,
    ) -> SubinterpreterBootstrapInfo:
        try:
            ok, value = interpreter.call(
                _initialize_service,
                self.target.factory_name,
                self.target.code_identity_name,
                self.target.code_identity,
                self.target.config_data,
                self.target.module_search_paths,
                self.target.preload_modules,
                self.target.require_gil,
                self.target.allow_code_identity_mismatch,
            )
        except BaseException as exc:  # noqa
            raise self._execution_error(exc) from exc
        if not ok:
            kind, detail = value
            if kind == 'code-identity':
                raise SubinterpreterCodeIdentityError(
                    expected=self.target.code_identity,
                    actual=detail,
                )
            if kind == 'gil':
                raise SubinterpreterGilError('Subinterpreter service requires an enabled GIL')
            raise SubinterpreterExecutionError(f'Unknown subinterpreter bootstrap failure: {value!r}')

        interpreter_id, gil_enabled, code_identity = value
        return SubinterpreterBootstrapInfo(
            interpreter_id=interpreter_id,
            gil_enabled=gil_enabled,
            code_identity=code_identity,
        )

    def run(self, ctx: LocalWorkerContext[T]) -> None:
        interpreter: concurrent.interpreters.Interpreter | None = None
        caller: _ThreadedSubinterpreterCaller | None = None
        notifier: threading.Thread | None = None
        service_initialized = False
        failure: BaseException | None = None

        try:
            interpreter = concurrent.interpreters.create()
            bootstrap_info = self._bootstrap(interpreter)
            service_initialized = True

            caller = _ThreadedSubinterpreterCaller(
                ctx.runtime,
                bootstrap_info,
                max_pending_calls=self.max_pending_calls,
            )

            def notify_shutdown() -> None:
                ctx.runtime.shutdown.wait()
                caller.begin_shutdown()

            notifier = threading.Thread(
                target=notify_shutdown,
                name=f'SubinterpreterShutdown-{bootstrap_info.interpreter_id}',
                daemon=True,
            )
            notifier.start()

            ctx.publish(self.interface_factory(caller))

            while True:
                item = caller.get()
                if item is _STOP:
                    break
                task = ta.cast(_CallTask, item)
                try:
                    response = interpreter.call(_dispatch_service, task.payload)
                except BaseException as exc:  # noqa
                    execution_error = self._execution_error(exc)
                    caller.complete(task, exc=execution_error)
                    caller.fail(execution_error)
                    ctx.runtime.shutdown.request(message='subinterpreter-execution-failed')
                    raise execution_error from exc
                else:
                    caller.complete(task, result=response)

        except BaseException as exc:  # noqa
            failure = exc

        finally:
            ctx.runtime.shutdown.request(message='subinterpreter-runner-exiting')
            if caller is not None:
                caller.begin_shutdown()

            if interpreter is not None and service_initialized:
                try:
                    interpreter.call(_finalize_service)
                except BaseException as exc:  # noqa
                    if failure is None:
                        failure = self._execution_error(exc)
                    else:
                        failure.add_note(f'Subinterpreter service finalization also failed: {exc}')

            if interpreter is not None:
                try:
                    interpreter.close()
                except BaseException as exc:  # noqa
                    if failure is None:
                        failure = self._execution_error(exc)
                    else:
                        failure.add_note(f'Subinterpreter close also failed: {exc}')

            if notifier is not None:
                notifier.join()

        if failure is not None:
            raise failure
