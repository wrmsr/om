# ruff: noqa: PTH100 PTH118 PTH123 PT009 UP006 UP007 UP036 UP045
import os.path
import runpy
import tempfile
import typing as ta
import unittest

from .utils import systevisor_test_artifact_source


class TestSystevisorAmalgamation(unittest.TestCase):
    _source: ta.ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls._source = systevisor_test_artifact_source()

    def test_runs_without_package_imports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = os.path.join(temp_dir, 'systevisor.py')
            with open(artifact_path, 'w') as artifact_file:
                artifact_file.write(self._source)
            namespace = runpy.run_path(artifact_path, run_name='systevisor_amalgamation_isolated_test')
            self.assertIn(namespace['__package__'], (None, ''))
            self.assertTrue(callable(namespace['systevisor_main']))

    def test_loads_yaml_without_a_third_party_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = os.path.join(temp_dir, 'systevisor.py')
            with open(artifact_path, 'w') as artifact_file:
                artifact_file.write(self._source)
            config_path = os.path.join(temp_dir, 'systevisor.yml')
            with open(config_path, 'w') as config_file:
                config_file.write('units:\n  worker:\n    exec:\n      argv: [/bin/true, "no"]\n')
            namespace = runpy.run_path(artifact_path, run_name='systevisor_amalgamation_yaml_test')

            # A flattened artifact has no package to import the bundled YAML backend relative to, so the loader has to
            # carry it explicitly rather than rely on whatever happens to be installed beside it.
            self.assertEqual(type(namespace['SystevisorYamlConfigLoader'].backend).__name__, 'GoyamlYamlBackend')
            document = namespace['systevisor_load_config_document'](config_path)
            self.assertEqual(document.data['units']['worker']['exec']['argv'], ['/bin/true', 'no'])
