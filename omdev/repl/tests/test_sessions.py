import pytest

from omcore import lang

from ..interpreters import Interpreter
from ..interpreters import Result
from ..interpreters import ResultStatus
from ..languages import JAVASCRIPT_LANGUAGE
from ..languages import PYTHON_LANGUAGE
from ..outputs import ListOutputSink
from ..outputs import ResultOutput
from ..sessions import DuplicateInterpreterError
from ..sessions import NoActiveInterpreterError
from ..sessions import NoSuchInterpreterError
from ..sessions import Session


##


class EchoInterpreter(Interpreter):
    """Writes the source back as its result - enough to tell which interpreter ran."""

    def __init__(self, language, tag):
        super().__init__()

        self._language = language
        self.tag = tag
        self.closed = False

    @property
    def language(self):
        return self._language

    async def execute(self, source, sink):
        sink.write(ResultOutput(f'{self.tag}:{source}'))
        return Result(ResultStatus.OK, lang.just(source))

    async def aclose(self):
        self.closed = True


# mypy narrows member expressions (`session.active_name`) across statements without invalidating them on calls, so state
# is read into fresh locals before being asserted on.


def test_registration_and_switching():
    a = EchoInterpreter(PYTHON_LANGUAGE, 'a')
    b = EchoInterpreter(JAVASCRIPT_LANGUAGE, 'b')

    session = Session()
    names = session.names
    assert names == ()
    active_name = session.active_name
    assert active_name is None
    with pytest.raises(NoActiveInterpreterError):
        session.active  # noqa: B018

    session.add('a', a)
    active = session.active
    assert active is a  # the first registered is active

    session.add('b', b)
    names = session.names
    assert names == ('a', 'b')
    active = session.active
    assert active is a
    assert session.interpreters['b'] is b

    assert session.switch('b') is b
    active_name = session.active_name
    assert active_name == 'b'

    with pytest.raises(NoSuchInterpreterError):
        session.switch('c')
    with pytest.raises(DuplicateInterpreterError):
        session.add('a', a)

    session.add('c', EchoInterpreter(PYTHON_LANGUAGE, 'c'), activate=True)
    active_name = session.active_name
    assert active_name == 'c'


def test_listeners_and_removal():
    a = EchoInterpreter(PYTHON_LANGUAGE, 'a')
    b = EchoInterpreter(PYTHON_LANGUAGE, 'b')
    session = Session({'a': a, 'b': b})

    seen = []
    session.add_listener(lambda s: seen.append(s.active_name))

    session.switch('b')
    session.switch('b')  # no change, no notification
    assert seen == ['b']

    assert session.remove('b') is b
    active_name = session.active_name
    assert active_name == 'a'
    assert seen == ['b', 'a']

    session.remove_listener(session._listeners[0])  # noqa: SLF001
    session.remove('a')
    active_name = session.active_name
    assert active_name is None
    assert seen == ['b', 'a']


def test_execute_delegates_and_close_closes_all():
    a = EchoInterpreter(PYTHON_LANGUAGE, 'a')
    b = EchoInterpreter(PYTHON_LANGUAGE, 'b')
    session = Session({'a': a, 'b': b}, active='b')

    sink = ListOutputSink()
    result = lang.sync_await(session.execute('x', sink))
    assert result.value.must() == 'x'
    assert sink.text() == 'b:x\n'

    lang.sync_await(session.aclose())
    assert a.closed and b.closed
