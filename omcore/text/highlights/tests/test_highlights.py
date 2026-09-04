import importlib.util

import pytest

from ... import styled as st
from ..base import get_highlighter
from ..base import highlight_code


def _names(lines):
    return {
        ref.name
        for line in lines
        for run in line.runs()
        for ref in run.styles
        if isinstance(ref, st.StyleName)
    }


def test_python_highlighter():
    lines = highlight_code('python', ['def f():', '    return "s"  # c'])
    assert lines is not None
    assert [line.text for line in lines] == ['def f():', '    return "s"  # c']
    names = _names(lines)
    assert 'code.keyword' in names
    assert 'code.def' in names
    assert 'code.string' in names
    assert 'code.comment' in names


def test_python_highlighter_tolerates_garbage():
    lines = highlight_code('python', ['def broken(:', '  "unclosed'])
    assert lines is not None
    assert [line.text for line in lines] == ['def broken(:', '  "unclosed']


def test_python_highlighter_multiline_string():
    lines = highlight_code('python', ['x = """', 'inside', '"""'])
    assert lines is not None
    assert all(run.styles == (st.StyleName('code.string'),) for run in lines[1].runs())


def test_diff_highlighter():
    lines = highlight_code('diff', ['--- a', '+++ b', '@@ -1 +1 @@', '-old', '+new', ' ctx', ''])
    assert lines is not None
    assert [line.style_at(0) if line else () for line in lines] == [
        (st.StyleName('code.diff.meta'),),
        (st.StyleName('code.diff.meta'),),
        (st.StyleName('code.diff.hunk'),),
        (st.StyleName('code.diff.del'),),
        (st.StyleName('code.diff.add'),),
        (),
        (),
    ]


def test_aliases_and_unknown_language():
    assert get_highlighter('py') is get_highlighter('python3')
    assert get_highlighter('patch') is get_highlighter('diff')
    # (Not 'brainfuck' - pygments actually has a lexer for that.)
    assert highlight_code('zz-no-such-lang-zz', ['+++']) is None


def test_pygments_fallback_highlighter():
    if importlib.util.find_spec('pygments') is None:
        pytest.skip('pygments not installed')

    lines = highlight_code('rust', ['fn main() { let x = "s"; } // c'])
    assert lines is not None
    assert lines[0].text == 'fn main() { let x = "s"; } // c'
    names = _names(lines)
    assert 'code.keyword' in names
    assert 'code.string' in names

    # Multi-line + row-count invariant.
    lines = highlight_code('json', ['{', '  "k": 1', '}'])
    assert lines is not None
    assert len(lines) == 3
    assert [line.text for line in lines] == ['{', '  "k": 1', '}']

    # Still None for total nonsense.
    assert highlight_code('no-such-language-zzz', ['x']) is None
