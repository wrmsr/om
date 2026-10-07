import builtins
import io

import pytest

from ...outputs import ListOutputSink
from ...outputs import StdoutOutput
from ..builtins import Quitter
from ..builtins import SinkPrint
from ..builtins import current_sink
from ..builtins import current_sink_setting
from ..builtins import make_builtins


##


def test_print_goes_to_the_current_sink():
    sink = ListOutputSink()
    p = SinkPrint(lambda: None)
    assert current_sink() is None
    with current_sink_setting(sink):
        assert current_sink() is sink
        p('a', 1, sep='-', end='!')
        p()
    assert current_sink() is None
    assert sink.outputs == (StdoutOutput('a-1!'), StdoutOutput('\n'))


def test_print_falls_back_to_the_default_sink():
    default = ListOutputSink()
    p = SinkPrint(lambda: default)
    p('later')
    assert default.text() == 'later\n'


def test_print_with_no_sink_at_all_is_the_real_print(capsys):
    p = SinkPrint(lambda: None)
    p('real')
    assert capsys.readouterr().out == 'real\n'


def test_print_honors_an_explicit_file():
    sink = ListOutputSink()
    buf = io.StringIO()
    with current_sink_setting(sink):
        SinkPrint(lambda: None)('x', file=buf)
    assert buf.getvalue() == 'x\n'
    assert sink.outputs == ()


def test_quitter():
    q = Quitter('exit')
    assert 'exit()' in repr(q)
    with pytest.raises(SystemExit) as ei:
        q(3)
    assert ei.value.code == 3


def test_make_builtins_is_a_copy():
    p = SinkPrint(lambda: None)
    b = make_builtins(p)
    assert b['print'] is p
    assert isinstance(b['exit'], Quitter)
    assert b['len'] is len
    assert builtins.print is not p  # the real module is untouched

    restricted = make_builtins(p, base={'len': len})
    assert set(restricted) == {'len', 'print', 'exit', 'quit'}
