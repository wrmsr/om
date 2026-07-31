# ruff: noqa: PT009
# @om-lite
import os
import tempfile
import unittest

from ..temp import temp_named_file_context


class TestTemp(unittest.TestCase):
    def test_temp_named_file_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            with temp_named_file_context(root_dir=td) as f:
                path = f.name
                self.assertTrue(os.path.isfile(path))

            self.assertFalse(os.path.exists(path))
