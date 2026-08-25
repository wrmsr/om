import io

import pytest

from ...errors import DatabaseError
from ...errors import InterfaceError
from .. import messages as msgs
from ..codes import DescribeKind
from ..codes import TransactionStatus
from ..session import ProtocolSession
from ..session import Step


def new_session(**kwargs):
    kwargs.setdefault('user', b'postgres')
    kwargs.setdefault('startup_params', {'user': b'postgres'})
    return ProtocolSession(**kwargs)


##
# Startup


def test_startup_cleartext_password():
    s = new_session(password=b'pw')
    op = s.startup()

    assert op.start() == Step([msgs.StartupMessage({'user': b'postgres'})])
    assert s.handle(msgs.AuthenticationCleartextPassword()) == Step([msgs.PasswordMessage(b'pw')])
    assert s.handle(msgs.AuthenticationOk()) == Step()
    assert s.handle(msgs.ParameterStatus('client_encoding', 'LATIN1')) == Step()
    assert s.handle(msgs.BackendKeyData(1, 2)) == Step()
    assert not op.done
    assert s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE)) == Step()
    assert op.done
    assert op.result() is None

    assert s.client_encoding == 'iso8859-1'
    assert s.parameter_statuses == {'client_encoding': 'LATIN1'}
    assert s.backend_key_data == msgs.BackendKeyData(1, 2)
    assert s.transaction_status == TransactionStatus.IDLE
    assert s.current is None


def test_startup_md5_password():
    s = new_session(password=b'pw')
    op = s.startup()
    op.start()
    step = s.handle(msgs.AuthenticationMd5Password(b'abcd'))
    assert step == Step([msgs.PasswordMessage(b'md51a01e1ce09d1d76da9cfc6327e4c3ccd')])


def test_startup_password_required():
    s = new_session()
    op = s.startup()
    op.start()
    s.handle(msgs.AuthenticationCleartextPassword())
    assert op.done
    with pytest.raises(InterfaceError, match='no password was provided'):
        op.result()


def test_startup_unsupported_auth():
    s = new_session(password=b'pw')
    op = s.startup()
    op.start()
    s.handle(msgs.AuthenticationOther(7, b''))
    with pytest.raises(InterfaceError, match='Authentication method 7 not supported'):
        op.result()


def test_startup_error():
    s = new_session(password=b'pw')
    op = s.startup()
    op.start()
    s.handle(msgs.ErrorResponse({'S': 'FATAL', 'C': '28P01', 'M': 'password authentication failed'}))
    assert op.done
    with pytest.raises(DatabaseError) as ei:
        op.result()
    assert ei.value.args[0]['C'] == '28P01'


##
# Queries


def test_execute_simple():
    s = new_session()
    op = s.execute_simple('select 1 as x')

    assert op.start() == Step([msgs.Query('select 1 as x')])
    assert s.handle(msgs.RowDescription([msgs.FieldDescription('x', 0, 0, 23, 4, -1, 0)])) == Step()
    assert s.handle(msgs.DataRow([b'1'])) == Step()
    assert s.handle(msgs.DataRow([None])) == Step()
    assert s.handle(msgs.CommandComplete('SELECT 2')) == Step()
    assert s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE)) == Step()

    ctx = op.result()
    assert ctx.rows == [[1], [None]]
    assert ctx.row_count == 2
    assert [c['name'] for c in ctx.columns] == ['x']


def test_execute_simple_error_is_raised_after_ready():
    s = new_session()
    op = s.execute_simple('select nope')
    op.start()
    s.handle(msgs.ErrorResponse({'S': 'ERROR', 'C': '42703', 'M': 'nope'}))
    assert not op.done
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    assert op.done
    with pytest.raises(DatabaseError):
        op.result()


def test_execute_unnamed_round_trips():
    s = new_session()
    op = s.execute_unnamed('select $1', (42,), (23,))

    assert op.start() == Step([msgs.Parse('', 'select $1', (23,)), msgs.Flush(), msgs.Sync()])
    s.handle(msgs.ParseComplete())
    assert s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE)) == Step([
        msgs.Describe(DescribeKind.STATEMENT, ''), msgs.Flush(), msgs.Sync(),
    ])
    s.handle(msgs.ParameterDescription((23,)))
    s.handle(msgs.RowDescription([msgs.FieldDescription('?column?', 0, 0, 23, 4, -1, 0)]))
    assert s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE)) == Step([
        msgs.Bind('', '', ('42',)), msgs.Flush(), msgs.Execute(''), msgs.Flush(), msgs.Sync(),
    ])
    s.handle(msgs.BindComplete())
    s.handle(msgs.DataRow([b'42']))
    s.handle(msgs.CommandComplete('SELECT 1'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))

    assert op.result().rows == [[42]]


def test_prepare_and_execute_named():
    s = new_session()
    op = s.prepare_statement('select $1::int')
    assert op.start() == Step([
        msgs.Parse('og8000_statement_0', 'select $1::int', ()),
        msgs.Flush(),
        msgs.Describe(DescribeKind.STATEMENT, 'og8000_statement_0'),
        msgs.Flush(),
        msgs.Sync(),
    ])
    s.handle(msgs.ParseComplete())
    s.handle(msgs.ParameterDescription((23,)))
    s.handle(msgs.RowDescription([msgs.FieldDescription('int4', 0, 0, 23, 4, -1, 0)]))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    name, columns, input_funcs = op.result()
    assert name == 'og8000_statement_0'

    op2 = s.execute_named(name, ('7',), columns, input_funcs, 'select $1::int')
    assert op2.start() == Step([
        msgs.Bind('', name, ('7',)), msgs.Flush(), msgs.Execute(''), msgs.Flush(), msgs.Sync(),
    ])
    s.handle(msgs.BindComplete())
    s.handle(msgs.DataRow([b'7']))
    s.handle(msgs.CommandComplete('SELECT 1'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    assert op2.result().rows == [[7]]

    op3 = s.close_prepared_statement(name)
    assert op3.start() == Step([msgs.Close(DescribeKind.STATEMENT, name), msgs.Flush(), msgs.Sync()])
    s.handle(msgs.CloseComplete())
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    assert op3.result() is None

    assert s.prepare_statement('select 2').start().messages[0] == msgs.Parse('og8000_statement_0', 'select 2', ())


def test_one_operation_at_a_time():
    s = new_session()
    s.execute_simple('select 1').start()
    with pytest.raises(InterfaceError, match='already in progress'):
        s.execute_simple('select 2')


def test_failed_transaction_block():
    s = new_session()
    s.execute_simple('select 1').start()
    s.handle(msgs.ReadyForQuery(TransactionStatus.IN_FAILED_TRANSACTION))

    op = s.execute_simple('select 2')
    op.start()
    s.handle(msgs.CommandComplete('SELECT 1'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IN_FAILED_TRANSACTION))
    with pytest.raises(InterfaceError, match='in failed transaction block'):
        op.result()

    op = s.execute_simple('rollback')
    op.start()
    s.handle(msgs.CommandComplete('ROLLBACK'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    assert op.result().row_count == -1


##
# COPY


def test_copy_in_from_stream():
    s = new_session()
    op = s.execute_unnamed('copy t from stdin', stream=io.BytesIO(b'1\t2\n'))
    op.start()
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.BindComplete())

    step = s.handle(msgs.CopyInResponse(False, (0, 0)))
    assert step == Step([msgs.CopyData(b'1\t2\n')], more=True)
    assert s.resume() == Step([msgs.CopyDone(), msgs.Sync()])

    s.handle(msgs.CommandComplete('COPY 1'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    assert op.result().row_count == 1


def test_copy_in_from_iterable_of_strs():
    s = new_session()
    op = s.execute_unnamed('copy t from stdin', stream=['1\t2\n', '3\t4\n'])
    op.start()
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))

    assert s.handle(msgs.CopyInResponse(False, (0, 0))) == Step([msgs.CopyData(b'1\t2\n')], more=True)
    assert s.resume() == Step([msgs.CopyData(b'3\t4\n')], more=True)
    assert s.resume() == Step([msgs.CopyDone(), msgs.Sync()])


def test_copy_out_to_text_stream():
    out = io.StringIO()
    s = new_session()
    op = s.execute_unnamed('copy t to stdout', stream=out)
    op.start()
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.CopyOutResponse(False, (0,)))
    s.handle(msgs.CopyData(b'caf\xc3\xa9\n'))
    s.handle(msgs.CopyDone())
    s.handle(msgs.CommandComplete('COPY 1'))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    op.result()
    assert out.getvalue() == 'caf\xe9\n'


def test_copy_out_requires_stream():
    s = new_session()
    op = s.execute_unnamed('copy t to stdout')
    op.start()
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.ReadyForQuery(TransactionStatus.IDLE))
    s.handle(msgs.CopyOutResponse(False, (0,)))
    assert op.done
    with pytest.raises(InterfaceError, match='output stream is required'):
        op.result()


##
# Unsolicited messages


def test_notices_and_notifications_outside_operations():
    s = new_session()
    assert s.handle(msgs.NoticeResponse({'S': 'WARNING'})) == Step()
    assert s.handle(msgs.NotificationResponse(1, 'chan', 'hi')) == Step()
    assert [n.fields for n in s.notices] == [{'S': 'WARNING'}]
    assert [n.payload for n in s.notifications] == ['hi']


def test_unsolicited_error_is_fatal():
    s = new_session()
    with pytest.raises(DatabaseError):
        s.handle(msgs.ErrorResponse({'S': 'FATAL', 'C': '57P01', 'M': 'terminating connection'}))
