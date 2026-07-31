# ruff: noqa: PT009
# @om-lite
import io
import unittest

from ..progressbar import progress_bar


class TestProgressBar(unittest.TestCase):
    def test_progress_bar(self):
        for seq in (range(10), iter(range(10))):
            with self.subTest(seq=seq):
                out = io.StringIO()
                self.assertEqual(
                    list(progress_bar(seq, out=out, no_tty_check=True)),
                    list(range(10)),
                )
                self.assertTrue(out.getvalue())

    def test_empty_progress_bar(self):
        out = io.StringIO()

        self.assertEqual(
            list(progress_bar([], out=out, no_tty_check=True, length=3)),
            [],
        )
        self.assertIn('[███] 0/0', out.getvalue())


if __name__ == '__main__':
    unittest.main()
