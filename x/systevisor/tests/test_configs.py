import json
import pathlib
import tempfile
import unittest

from x.systevisor.configs.compiling import SystevisorConfigCompiler
from x.systevisor.configs.diagnostics import SystevisorConfigDiagnosticStage
from x.systevisor.configs.models import SystevisorDependencyCondition
from x.systevisor.configs.models import SystevisorRestartMode
from x.systevisor.configs.models import SystevisorScheduleActionKind
from x.systevisor.core.identities import SystevisorInstanceId


class TestSystevisorConfigs(unittest.TestCase):
    def test_split_formats_compile_to_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / '00-manager.toml').write_text(
                '[manager]\nidentifier = "test-systevisor"\n\n[api]\nunix_socket = "/tmp/test.sock"\n',
            )
            (root / '10-db.json').write_text(json.dumps({
                'units': {
                    'db': {
                        'exec': {'argv': ['redis-server', '--port', '0']},
                        'replicas': 2,
                        'restart': {'mode': 'always'},
                        'resources': {'observe': False},
                    },
                },
                'schedules': {
                    'db-cycle': {
                        'cron': '0 3 * * *',
                        'action': {'kind': 'restart', 'target_kind': 'unit', 'target': 'db'},
                    },
                },
            }))
            (root / '20-web.yml').write_text(
                'units:\n'
                '  web:\n'
                '    exec:\n'
                '      argv: [python, -m, example]\n'
                '    dependencies:\n'
                '      requires:\n'
                '        db: running\n'
                'collections:\n'
                '  stack:\n'
                '    units: [db, web]\n',
            )
            (root / 'README.txt').write_text('ignored')

            result = SystevisorConfigCompiler().compile([temp_dir])

        self.assertTrue(result.is_valid, result.diagnostics)
        snapshot = result.snapshot
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(
            set(snapshot.instances),
            {SystevisorInstanceId('db:0'), SystevisorInstanceId('db:1'), SystevisorInstanceId('web:0')},
        )
        self.assertEqual(snapshot.config.units['db'].restart.mode, SystevisorRestartMode.ALWAYS)
        self.assertFalse(snapshot.config.units['db'].resources.observe)
        self.assertEqual(snapshot.config.schedules['db-cycle'].action.kind, SystevisorScheduleActionKind.RESTART)
        self.assertEqual(
            snapshot.config.units['web'].dependencies.requires,
            {'db': SystevisorDependencyCondition.RUNNING},
        )
        self.assertEqual(len(snapshot.source_paths), 3)
        self.assertTrue(any(
            provenance.object_path == ('units', 'web', 'exec', 'argv') and provenance.source.endswith('20-web.yml')
            for provenance in snapshot.provenance
        ))

    def test_duplicate_definition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            for file_name, argv in (('a.json', ['one']), ('b.json', ['two'])):
                (root / file_name).write_text(json.dumps({'units': {'same': {'exec': {'argv': argv}}}}))

            result = SystevisorConfigCompiler().compile([temp_dir])

        self.assertFalse(result.is_valid)
        self.assertEqual(result.diagnostics[0].stage, SystevisorConfigDiagnosticStage.MERGE)
        self.assertEqual(result.diagnostics[0].object_path, ('units', 'same', 'exec', 'argv'))

    def test_unknown_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'config.json'
            path.write_text(json.dumps({'surprise': True}))

            result = SystevisorConfigCompiler().compile([str(path)])

        self.assertFalse(result.is_valid)
        self.assertEqual(result.diagnostics[0].stage, SystevisorConfigDiagnosticStage.UNMARSHAL)

    def test_semantic_errors_are_collected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'config.json'
            path.write_text(json.dumps({
                'units': {
                    'bad name': {
                        'exec': {'argv': []},
                        'replicas': 0,
                        'dependencies': {'requires': {'missing': 'RUNNING'}},
                    },
                },
            }))

            result = SystevisorConfigCompiler().compile([str(path)])

        self.assertFalse(result.is_valid)
        self.assertEqual(
            {diagnostic.code for diagnostic in result.diagnostics},
            {'empty_argv', 'invalid_replicas', 'invalid_unit_name', 'unknown_dependency'},
        )

    def test_ordering_cycle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'config.json'
            path.write_text(json.dumps({
                'units': {
                    'a': {'exec': {'argv': ['a']}, 'dependencies': {'after': ['b']}},
                    'b': {'exec': {'argv': ['b']}, 'dependencies': {'after': ['a']}},
                },
            }))

            result = SystevisorConfigCompiler().compile([str(path)])

        self.assertFalse(result.is_valid)
        self.assertIn('dependency_cycle', {diagnostic.code for diagnostic in result.diagnostics})

    def test_health_and_empty_collection_policies_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'config.json'
            path.write_text(json.dumps({
                'units': {
                    'worker': {
                        'exec': {'argv': ['worker']},
                        'health': [
                            {
                                'name': 'bad-command',
                                'role': 'liveness',
                                'kind': 'command',
                                'argv': ['bad\u0000argument'],
                                'interval_secs': 0,
                            },
                            {
                                'name': 'bad-http',
                                'role': 'readiness',
                                'kind': 'http',
                                'url': 'https://example.com/ready',
                                'expected_statuses': [99],
                            },
                            {
                                'name': 'bad-log',
                                'role': 'liveness',
                                'kind': 'log_activity',
                                'channel': 'combined',
                                'max_quiet_secs': -1,
                            },
                        ],
                    },
                },
                'collections': {'empty': {'units': []}},
            }))

            result = SystevisorConfigCompiler().compile([str(path)])

        self.assertFalse(result.is_valid)
        expected_codes = {
            'empty_collection',
            'invalid_health_argv',
            'invalid_health_log_policy',
            'invalid_health_statuses',
            'invalid_health_timing',
            'unsupported_health_url',
        }
        actual_codes = {diagnostic.code for diagnostic in result.diagnostics}
        self.assertTrue(expected_codes.issubset(actual_codes), actual_codes)

    def test_digest_ignores_source_file_names(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            data = json.dumps({'units': {'service': {'exec': {'argv': ['service']}}}})
            (pathlib.Path(first_dir) / 'a.json').write_text(data)
            (pathlib.Path(second_dir) / 'different.json').write_text(data)

            first = SystevisorConfigCompiler().compile([first_dir])
            second = SystevisorConfigCompiler().compile([second_dir])

        self.assertTrue(first.is_valid)
        self.assertTrue(second.is_valid)
        assert first.snapshot is not None
        assert second.snapshot is not None
        self.assertEqual(first.snapshot.digest, second.snapshot.digest)

    def test_self_update_timing_policy_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'config.json'
            path.write_text(json.dumps({
                'manager': {
                    'self_update': {
                        'probe_timeout_secs': 0,
                        'response_grace_secs': -1,
                    },
                },
            }))

            result = SystevisorConfigCompiler().compile([str(path)])

        self.assertFalse(result.is_valid)
        self.assertIn('invalid_self_update_policy', {item.code for item in result.diagnostics})
