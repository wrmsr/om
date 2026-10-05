# ruff: noqa: PT009 SLF001 UP006 UP007 UP045
import argparse
import json
import os
import pathlib
import tempfile
import time
import unittest

from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager

from ..core.states import SystevisorProcessState
from ..main import SystevisorMainServerContext
from ..main import _systevisor_main_report_failure
from ..main import _systevisor_main_supervise
from ..main import systevisor_main
from ..runtime.processes import SystevisorProcessManager
from .utils import true_bin


class SystevisorTestMainFailingFdioHandler(FdioHandler):
    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return False

    def close(self) -> None:
        pass

    def next_deadline(self) -> float:
        return time.monotonic()

    def on_timeout(self) -> None:
        raise RuntimeError('reactor handler failed')


class TestSystevisorMain(unittest.TestCase):
    def test_run_executes_only_selected_oneshot_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            unrelated_marker = root / 'unrelated-ran'
            config_path = root / 'systevisor.json'
            config_path.write_text(json.dumps({
                'units': {
                    'selected': {
                        'exec': {'argv': [true_bin()]},
                        'kind': 'oneshot',
                        'autostart': False,
                        'restart': {'start_secs': 0},
                    },
                    'unrelated': {
                        'exec': {'argv': ['/bin/sh', '-c', f'touch {unrelated_marker}']},
                        'kind': 'oneshot',
                        'autostart': True,
                        'restart': {'start_secs': 0},
                    },
                },
                'collections': {
                    'selected': {'units': ['selected']},
                },
            }))

            result = systevisor_main([
                'run',
                'selected',
                '--config',
                str(config_path),
                '--state-directory',
                str(root / 'state'),
            ])

            self.assertEqual(result, 0)
            self.assertFalse(unrelated_marker.exists())

    def test_run_rejects_unknown_collection_without_starting_autostart_units(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            marker = root / 'ran'
            config_path = root / 'systevisor.json'
            config_path.write_text(json.dumps({
                'units': {
                    'worker': {
                        'exec': {'argv': ['/bin/sh', '-c', f'touch {marker}']},
                        'autostart': True,
                    },
                },
                'collections': {
                    'known': {'units': ['worker']},
                },
            }))

            result = systevisor_main(['run', 'missing', '--config', str(config_path)])

            self.assertEqual(result, 2)
            self.assertFalse(marker.exists())

    def test_runtime_failure_stops_children_before_the_manager_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            config_path = root / 'systevisor.json'
            config_path.write_text(json.dumps({
                'units': {
                    'worker': {
                        'exec': {'argv': ['/bin/sleep', '60']},
                        'restart': {'start_secs': 0},
                    },
                },
            }))
            context = SystevisorMainServerContext(argparse.Namespace(
                config=[str(config_path)],
                recursive=False,
                state_directory=str(root / 'state'),
            ))
            try:
                self.assertTrue(context.start(context.compile()).attempt.applied)
                coordinator = context.coordinator
                assert coordinator is not None
                deadline = time.monotonic() + 10.
                while not all(
                        instance.process_state is SystevisorProcessState.RUNNING
                        for instance in coordinator.engine.state.instances.values()
                ):
                    self.assertLess(time.monotonic(), deadline)
                    coordinator.poll(timeout=.1)
                process_manager = context._injector.provide(SystevisorProcessManager)
                pids = [state.pid for state in process_manager.snapshot_states()]
                self.assertEqual(len(pids), 1)

                context._injector.provide(FdioManager).register(SystevisorTestMainFailingFdioHandler())
                with self.assertRaisesRegex(RuntimeError, 'reactor handler failed') as raised:
                    _systevisor_main_supervise(context)
                self.assertEqual(_systevisor_main_report_failure(context.codec, raised.exception, supervising=True), 70)
                self.assertTrue(process_manager.has_processes())
            finally:
                context.close()

            self.assertFalse(process_manager.has_processes())
            with self.assertRaises(ChildProcessError):
                os.waitpid(pids[0], os.WNOHANG)
