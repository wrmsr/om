from ..languages import BASH_LANGUAGE
from ..languages import JAVASCRIPT_LANGUAGE
from ..languages import PYTHON_LANGUAGE
from ..languages import Completeness


##


def test_python_completeness():
    c = PYTHON_LANGUAGE.check_complete
    assert c('1 + 1') is Completeness.COMPLETE
    assert c('x = 1; y = 2') is Completeness.COMPLETE
    assert c('def f():') is Completeness.INCOMPLETE
    assert c('def f():\n    return 1') is Completeness.INCOMPLETE
    assert c('def f():\n    return 1\n') is Completeness.COMPLETE
    assert c('if x:\n    pass\nelse:\n    pass\n') is Completeness.COMPLETE
    assert c('nope(') is Completeness.INCOMPLETE
    assert c('1 +') is Completeness.INVALID
    assert c(')') is Completeness.INVALID


def test_python_language_descriptor():
    assert PYTHON_LANGUAGE.name == 'python'
    assert PYTHON_LANGUAGE.highlight_name == 'python'
    assert PYTHON_LANGUAGE.prompt == '>>> '
    assert PYTHON_LANGUAGE.continuation_prompt == '... '


def test_javascript_completeness():
    c = JAVASCRIPT_LANGUAGE.check_complete
    assert c('1 + 2') is Completeness.COMPLETE
    assert c('function f() {') is Completeness.INCOMPLETE
    assert c('function f() {\n  return 1\n}') is Completeness.COMPLETE
    assert c('`abc') is Completeness.INCOMPLETE
    assert c('`a\nb`') is Completeness.COMPLETE
    assert c('"abc') is Completeness.COMPLETE  # invalid, never incomplete: the engine reports it
    assert c('"a)b"') is Completeness.COMPLETE
    assert c("'a{'") is Completeness.COMPLETE
    assert c('// (\n1') is Completeness.COMPLETE
    assert c('/* x') is Completeness.INCOMPLETE
    assert c('/* ( */ 1') is Completeness.COMPLETE
    assert c(')') is Completeness.INVALID


def test_javascript_language_descriptor():
    assert JAVASCRIPT_LANGUAGE.name == 'javascript'
    assert JAVASCRIPT_LANGUAGE.display_name == 'js'
    assert JAVASCRIPT_LANGUAGE.prompt == 'js> '


def test_bash_completeness():
    c = BASH_LANGUAGE.check_complete
    assert c('echo hi') is Completeness.COMPLETE
    assert c('echo "hi') is Completeness.INCOMPLETE
    assert c("echo 'hi") is Completeness.INCOMPLETE
    assert c('echo "a\nb"') is Completeness.COMPLETE
    assert c("echo 'it\\'s'") is Completeness.INCOMPLETE  # no escapes in single quotes: a third one opens
    assert c('echo "a \\" b') is Completeness.INCOMPLETE
    assert c('echo one \\') is Completeness.INCOMPLETE
    assert c('echo one \\\ntwo') is Completeness.COMPLETE
    assert c('echo hi # it\'s a comment') is Completeness.COMPLETE
    assert c('echo "#" \'') is Completeness.INCOMPLETE
    assert c('if true; then') is Completeness.COMPLETE  # the shell's to report


def test_bash_language_descriptor():
    assert BASH_LANGUAGE.name == 'bash'
    assert BASH_LANGUAGE.highlight_name == 'bash'
    assert BASH_LANGUAGE.prompt == '$ '
    assert BASH_LANGUAGE.continuation_prompt == '> '
