from omcore.text import styled as st
from omcore.text.highlights import PythonHighlighter

from ....minitui.docs.highlighting import IncrementalHighlighter
from ...languages import JAVASCRIPT_LANGUAGE
from ...languages import PYTHON_LANGUAGE
from ..highlighting import RetaggedHighlighter
from ..highlighting import get_language_highlighter


##


def test_retagging():
    hl = RetaggedHighlighter(PythonHighlighter(), 'repl.')
    (line,) = hl.highlight(['def f(): pass'])
    names = {span.style.name for span in line.spans if isinstance(span.style, st.StyleName)}
    assert names == {'repl.code.keyword', 'repl.code.def'}
    assert line.text == 'def f(): pass'


def test_language_highlighters():
    for language in (PYTHON_LANGUAGE, JAVASCRIPT_LANGUAGE):
        hl = get_language_highlighter(language)
        assert isinstance(hl, IncrementalHighlighter)  # the wrapper always is; edits reach the inner one if it is
        assert isinstance(hl, RetaggedHighlighter)
    # Fresh instances: tree-sitter highlighters carry incremental state.
    assert get_language_highlighter(PYTHON_LANGUAGE) is not get_language_highlighter(PYTHON_LANGUAGE)
