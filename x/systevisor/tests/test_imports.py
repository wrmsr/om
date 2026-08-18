import importlib
import unittest


_SYSTEVISOR_TEST_IMPORT_MODULES = (
    'x.systevisor',
    'x.systevisor.configs',
    'x.systevisor.control',
    'x.systevisor.control.api',
    'x.systevisor.control.client',
    'x.systevisor.control.configs',
    'x.systevisor.control.http',
    'x.systevisor.control.inject',
    'x.systevisor.control.plane',
    'x.systevisor.core',
    'x.systevisor.main',
    'x.systevisor.platforms',
    'x.systevisor.runtime',
)


class TestSystevisorImports(unittest.TestCase):
    def test_package_imports(self) -> None:
        for module_name in _SYSTEVISOR_TEST_IMPORT_MODULES:
            with self.subTest(module_name=module_name):
                importlib.import_module(module_name)
