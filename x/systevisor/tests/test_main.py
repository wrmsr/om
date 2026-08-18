# ruff: noqa: PT009 UP006 UP007 UP045
import json
import pathlib
import tempfile
import unittest

from x.systevisor.main import systevisor_main


class TestSystevisorMain(unittest.TestCase):
    def test_run_executes_only_selected_oneshot_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            unrelated_marker = root / 'unrelated-ran'
            config_path = root / 'systevisor.json'
            config_path.write_text(json.dumps({
                'units': {
                    'selected': {
                        'exec': {'argv': ['/bin/true']},
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
