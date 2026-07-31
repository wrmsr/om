# ruff: noqa: PT009
# @om-lite
import io
import unittest

from ..coloring import AnsiTermColoring
from ..coloring import NopTermColoring
from ..coloring import TermColor
from ..coloring import term_coloring


class TestTermColoring(unittest.TestCase):
    def test_implementations(self):
        self.assertEqual(NopTermColoring().red('text'), 'text')
        self.assertEqual(
            AnsiTermColoring().color(TermColor.GREEN, 'text'),
            '\033[32mtext\033[0m',
        )

    def test_selection(self):
        self.assertIsInstance(term_coloring(disabled=True), NopTermColoring)
        self.assertIsInstance(term_coloring(file=io.StringIO()), NopTermColoring)
        self.assertIsInstance(term_coloring(forced=True, disabled=True), AnsiTermColoring)


if __name__ == '__main__':
    unittest.main()
