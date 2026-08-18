import argparse
import concurrent.futures
import os
import pickle
import shlex
import subprocess
import sys
import sysconfig
import tempfile

from ... import LocalWorkerConfig
from ... import LocalWorkerSpec
from ... import LocalWorkerStartError
from ... import ThreadedLocalWorkerCoordinator
from ...interpreters import SubinterpreterCallTimeoutError
from ...interpreters import SubinterpreterCodeIdentityError
from ...interpreters import SubinterpreterGilError
from ...interpreters import SubinterpreterLocalWorkerRunner
from ...interpreters import SubinterpreterRemoteError
from ...interpreters import SubinterpreterTarget
from . import fixture


##


_EXTENSION_MODULE = '_omcore_daemons_subinterpreter_test'
_TIMEOUT_S = 10.


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _compile_extension(output_dir: str) -> str:
    extension_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    include_dir = sysconfig.get_config_var('INCLUDEPY')
    linker = sysconfig.get_config_var('LDSHARED')
    shared_flags = sysconfig.get_config_var('CCSHARED')
    if not all(isinstance(value, str) and value for value in (extension_suffix, include_dir, linker)):
        raise RuntimeError('Interpreter build configuration cannot compile an extension module')

    source_file = os.path.join(os.path.dirname(__file__), 'extension.c')
    output_file = os.path.join(output_dir, _EXTENSION_MODULE + extension_suffix)
    command = [
        *shlex.split(linker),
        *shlex.split(shared_flags or ''),
        '-I',
        include_dir,
        source_file,
        '-o',
        output_file,
    ]
    subprocess.run(command, check=True)
    return output_file


def _make_worker(
        module_search_path: str,
        *,
        code_identity: str = fixture.CODE_IDENTITY,
) -> LocalWorkerSpec[fixture.TestClient]:
    target = SubinterpreterTarget(
        factory_name=f'{fixture.__name__}.make_test_service',
        code_identity_name=f'{fixture.__name__}.CODE_IDENTITY',
        code_identity=code_identity,
        config_data=pickle.dumps(
            fixture.TestServiceConfig(extension_module=_EXTENSION_MODULE),
            protocol=pickle.HIGHEST_PROTOCOL,
        ),
        module_search_paths=(module_search_path,),
        preload_modules=(_EXTENSION_MODULE,),
        require_gil=True,
    )
    runner = SubinterpreterLocalWorkerRunner(
        target,
        fixture.TestClient,
        max_pending_calls=16,
    )
    return LocalWorkerSpec(
        runner_factory=lambda: runner,
        config=LocalWorkerConfig(
            linger_s=.05,
            drain_timeout_s=_TIMEOUT_S,
        ),
    )


def _run_integration(module_search_path: str) -> None:
    _require(sysconfig.get_config_var('Py_GIL_DISABLED') == 1, 'Integration requires a free-threaded CPython build')
    _require(not sys._is_gil_enabled(), 'Main interpreter unexpectedly started with its GIL enabled')  # noqa
    _require(_EXTENSION_MODULE not in sys.modules, 'Test extension was imported into the main interpreter')

    worker = _make_worker(module_search_path)
    with ThreadedLocalWorkerCoordinator() as coordinator:
        first = coordinator.acquire(worker, timeout=_TIMEOUT_S)
        first_interpreter_id = first.interface.caller.bootstrap_info.interpreter_id
        try:
            bootstrap_info = first.interface.caller.bootstrap_info
            info = first.interface.info()
            _require(bootstrap_info.gil_enabled, 'Extension preload did not enable the subinterpreter GIL')
            _require(info['gil_enabled'], 'Service did not run with its subinterpreter GIL enabled')
            _require(info['interpreter_id'] == first_interpreter_id, 'Bootstrap and service interpreter IDs differ')
            _require(first_interpreter_id != 0, 'Service unexpectedly ran in the main interpreter')
            _require(not sys._is_gil_enabled(), 'Subinterpreter import enabled the main interpreter GIL')  # noqa

            first_count, first_c_thread = first.interface.increment(1)
            _require(first_count == 1, 'Per-interpreter extension state did not start empty')
            _require(first_c_thread == info['thread_ident'], 'Python and C work ran on different worker threads')

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(first.interface.increment, 1) for _ in range(8)]
                concurrent_results = [future.result(_TIMEOUT_S) for future in futures]
            _require(
                sorted(count for count, _ in concurrent_results) == list(range(2, 10)),
                'Concurrent calls were not serialized through one service instance',
            )
            _require(
                all(thread_ident == info['thread_ident'] for _, thread_ident in concurrent_results),
                'Concurrent calls escaped the owning worker thread',
            )

            try:
                first.interface.fail()
            except SubinterpreterRemoteError as exc:
                _require(exc.remote_type == 'builtins.ValueError', 'Remote exception type was not retained')
                _require(exc.message == 'intentional service failure', 'Remote exception message was not retained')
            else:
                raise AssertionError('Remote service exception was not reported')

            try:
                first.interface.unpicklable()
            except SubinterpreterRemoteError as exc:
                _require('pickle' in exc.message.lower(), 'Response serialization failure lost its message')
            else:
                raise AssertionError('Unpicklable service response was not reported')

            next_count, _ = first.interface.increment(1)
            _require(next_count == 10, 'Remote application or serialization failure killed the worker generation')

            try:
                first.interface.sleep(.25, timeout_s=.01)
            except SubinterpreterCallTimeoutError:
                pass
            else:
                raise AssertionError('Slow service call did not time out')
            _require(
                coordinator.inspect(worker).active_count == 2,
                'Timed-out call did not retain its nested runtime activity',
            )

        finally:
            first.close()

        _require(coordinator.wait_stopped(worker, timeout=_TIMEOUT_S), 'First generation did not exit after linger')

        second = coordinator.acquire(worker, timeout=_TIMEOUT_S)
        try:
            second_interpreter_id = second.interface.caller.bootstrap_info.interpreter_id
            _require(second.generation == 2, 'Second acquisition did not start a new generation')
            _require(second_interpreter_id != first_interpreter_id, 'New generation reused the closed interpreter')
            second_count, _ = second.interface.increment(1)
            _require(second_count == 1, 'New interpreter did not receive fresh C module state')
        finally:
            coordinator.request_shutdown(worker)
            second.close()
        _require(coordinator.wait_stopped(worker, timeout=_TIMEOUT_S), 'Second generation did not stop')

        mismatched_worker = _make_worker(
            module_search_path,
            code_identity='definitely-not-the-running-code',
        )
        try:
            coordinator.acquire(mismatched_worker, timeout=_TIMEOUT_S)
        except LocalWorkerStartError as exc:
            _require(
                isinstance(exc.cause, SubinterpreterCodeIdentityError),
                'Code identity mismatch did not fail with its typed cause',
            )
        else:
            raise AssertionError('Mismatched code identity was accepted')

    _require(not sys._is_gil_enabled(), 'Main interpreter GIL was enabled by completed workers')  # noqa
    _require(_EXTENSION_MODULE not in sys.modules, 'Test extension leaked into the main interpreter')


def _run_gil_refusal(module_search_path: str) -> None:
    _require(os.environ.get('PYTHON_GIL') == '0', 'GIL-refusal check requires PYTHON_GIL=0')
    _require(not sys._is_gil_enabled(), 'GIL-refusal main interpreter unexpectedly has its GIL enabled')  # noqa
    _require(_EXTENSION_MODULE not in sys.modules, 'Test extension was imported into the main interpreter')

    worker = _make_worker(module_search_path)
    with ThreadedLocalWorkerCoordinator() as coordinator:
        try:
            coordinator.acquire(worker, timeout=_TIMEOUT_S)
        except LocalWorkerStartError as exc:
            _require(
                isinstance(exc.cause, SubinterpreterGilError),
                'Forced no-GIL mode did not fail with its typed cause',
            )
        else:
            raise AssertionError('GIL-requiring service started under forced no-GIL mode')

    _require(_EXTENSION_MODULE not in sys.modules, 'Test extension leaked into the main interpreter')


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--gil-refusal-path')
    args = parser.parse_args()

    if args.gil_refusal_path is not None:
        _run_gil_refusal(args.gil_refusal_path)
        return

    with tempfile.TemporaryDirectory(prefix='omcore-daemons-subinterpreter-') as temp_dir:
        _compile_extension(temp_dir)
        _run_integration(temp_dir)

        env = dict(os.environ)
        env['PYTHON_GIL'] = '0'
        subprocess.run(
            [
                sys.executable,
                '-m',
                __spec__.name,
                '--gil-refusal-path',
                temp_dir,
            ],
            check=True,
            env=env,
        )

    print('subinterpreter local-worker integration passed')


if __name__ == '__main__':
    _main()
