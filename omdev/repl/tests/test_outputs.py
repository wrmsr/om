from ..outputs import ErrorOutput
from ..outputs import ListOutputSink
from ..outputs import ResultOutput
from ..outputs import StdoutOutput
from ..outputs import TextOutputSink
from ..outputs import output_text


##


def test_output_text():
    assert output_text(StdoutOutput('a\n')) == 'a\n'
    assert output_text(StdoutOutput('a')) == 'a'
    assert output_text(ResultOutput('1')) == '1\n'
    assert output_text(ResultOutput('1\n')) == '1\n'
    assert output_text(ErrorOutput('Traceback\n  x\nE: y')) == 'Traceback\n  x\nE: y\n'


def test_list_sink():
    sink = ListOutputSink()
    sink.write(StdoutOutput('a\n'))
    sink.write(ResultOutput('1'))
    assert sink.outputs == (StdoutOutput('a\n'), ResultOutput('1'))
    assert sink.text() == 'a\n1\n'
    sink.clear()
    assert sink.outputs == ()


def test_text_sink():
    out: list = []
    sink = TextOutputSink(out.append)
    sink.write(StdoutOutput('a\n'))
    sink.write(ErrorOutput('E'))
    assert out == ['a\n', 'E\n']
