# ruff: noqa: PT009 UP006 UP007
import unittest

from ..imports import can_import
from ..imports import import_attr


class TesTImportAttr(unittest.TestCase):
    def test_import_attr(self):
        dotted_path = __package__.rpartition('.')[0] + '.imports.import_attr.__name__'
        name = import_attr(dotted_path)
        self.assertEqual(name, 'import_attr')


class TestCanImport(unittest.TestCase):
    def test_can_import(self):
        self.assertTrue(can_import('zlib'))
        self.assertTrue(can_import('importlib.util'))
        self.assertTrue(can_import('.imports', __package__.rpartition('.')[0]))

        self.assertFalse(can_import('no_such_module_here'))
        self.assertFalse(can_import('no_such_package_here.sub'))
        self.assertFalse(can_import('zlib.no_such_submodule'))
