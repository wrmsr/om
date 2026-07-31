# ruff: noqa: PT009
# @om-lite
import unittest

from ..indent import IndentWriter


class TestIndentWriter(unittest.TestCase):
    def test_multiline_write(self):
        writer = IndentWriter(indent='>')

        with writer.indent():
            writer.write('a\nb\nc')

        self.assertEqual(writer.getvalue(), '>a\n>b\n>c')
