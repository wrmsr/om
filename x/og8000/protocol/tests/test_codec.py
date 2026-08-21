import pytest

from ...exceptions import ProtocolError
from .. import messages as msgs
from ..codes import DescribeKind
from ..codes import TransactionStatus
from ..decoding import BackendMessageDecoder
from ..encoding import FrontendMessageEncoder
from ..encoding import frame_message


##
# Encoding


@pytest.mark.parametrize(
    ('msg', 'expected'),
    [
        (msgs.SslRequest(), b'\x00\x00\x00\x08\x04\xd2\x16/'),
        (
            msgs.StartupMessage({'user': b'postgres', 'database': b'om'}),
            b'\x00\x00\x00\x23\x00\x03\x00\x00user\x00postgres\x00database\x00om\x00\x00',
        ),
        (msgs.PasswordMessage(b'barbour'), b'p\x00\x00\x00\x0cbarbour\x00'),
        (
            msgs.SaslInitialResponse('SCRAM-SHA-256', b'n,,n=u'),
            b'p\x00\x00\x00\x1cSCRAM-SHA-256\x00\x00\x00\x00\x06n,,n=u',
        ),
        (msgs.SaslResponse(b'c=biws'), b'p\x00\x00\x00\x0ac=biws'),
        (msgs.Query('select 1'), b'Q\x00\x00\x00\x0dselect 1\x00'),
        (
            msgs.Parse('', 'select $1', [23, -1]),
            b'P\x00\x00\x00\x19\x00select $1\x00\x00\x02\x00\x00\x00\x17\x00\x00\x00\x00',
        ),
        (
            msgs.Bind('', 'stmt', ['x', None]),
            b'B\x00\x00\x00\x19\x00stmt\x00\x00\x00\x00\x02\x00\x00\x00\x01x\xff\xff\xff\xff\x00\x00',
        ),
        (msgs.Describe(DescribeKind.STATEMENT, 'stmt'), b'D\x00\x00\x00\x0aSstmt\x00'),
        (msgs.Describe(DescribeKind.PORTAL, ''), b'D\x00\x00\x00\x06P\x00'),
        (msgs.Execute('', 0), b'E\x00\x00\x00\x09\x00\x00\x00\x00\x00'),
        (msgs.Close(DescribeKind.STATEMENT, 'stmt'), b'C\x00\x00\x00\x0aSstmt\x00'),
        (msgs.Flush(), b'H\x00\x00\x00\x04'),
        (msgs.Sync(), b'S\x00\x00\x00\x04'),
        (msgs.Terminate(), b'X\x00\x00\x00\x04'),
        (msgs.CopyData(b'1\t2\n'), b'd\x00\x00\x00\x081\t2\n'),
        (msgs.CopyDone(), b'c\x00\x00\x00\x04'),
        (msgs.CopyFail('nope'), b'f\x00\x00\x00\x09nope\x00'),
    ],
)
def test_encode(msg, expected):
    assert FrontendMessageEncoder().encode(msg) == expected


def test_encode_uses_client_encoding():
    enc = FrontendMessageEncoder(encoding='latin1')
    assert enc.encode(msgs.Query('caf\xe9')) == b'Q\x00\x00\x00\x09caf\xe9\x00'
    enc.set_encoding('utf8')
    assert enc.encode(msgs.Query('caf\xe9')) == b'Q\x00\x00\x00\x0acaf\xc3\xa9\x00'


def test_encode_unknown_message():
    with pytest.raises(TypeError):
        FrontendMessageEncoder().encode(msgs.ReadyForQuery(TransactionStatus.IDLE))  # type: ignore[arg-type]


def test_frame_message():
    assert frame_message(b'p', b'barbour\x00') == b'p\x00\x00\x00\x0cbarbour\x00'


##
# Decoding


@pytest.mark.parametrize(
    ('code', 'payload', 'expected'),
    [
        (b'R', b'\x00\x00\x00\x00', msgs.AuthenticationOk()),
        (b'R', b'\x00\x00\x00\x03', msgs.AuthenticationCleartextPassword()),
        (b'R', b'\x00\x00\x00\x05abcd', msgs.AuthenticationMd5Password(b'abcd')),
        (
            b'R',
            b'\x00\x00\x00\x0aSCRAM-SHA-256-PLUS\x00SCRAM-SHA-256\x00\x00',
            msgs.AuthenticationSasl(['SCRAM-SHA-256-PLUS', 'SCRAM-SHA-256']),
        ),
        (b'R', b'\x00\x00\x00\x0br=abc', msgs.AuthenticationSaslContinue(b'r=abc')),
        (b'R', b'\x00\x00\x00\x0cv=abc', msgs.AuthenticationSaslFinal(b'v=abc')),
        (b'R', b'\x00\x00\x00\x07xyz', msgs.AuthenticationOther(7, b'xyz')),
        (b'K', b'\x00\x00\x04\xd2\x00\x00\x16\x2e', msgs.BackendKeyData(1234, 5678)),
        (b'S', b'client_encoding\x00UTF8\x00', msgs.ParameterStatus('client_encoding', 'UTF8')),
        (b'Z', b'I', msgs.ReadyForQuery(TransactionStatus.IDLE)),
        (b'Z', b'E', msgs.ReadyForQuery(TransactionStatus.IN_FAILED_TRANSACTION)),
        (
            b'T',
            b'\x00\x01id\x00\x00\x00\x40\x01\x00\x02\x00\x00\x00\x17\x00\x04\xff\xff\xff\xff\x00\x00',
            msgs.RowDescription([msgs.FieldDescription('id', 16385, 2, 23, 4, -1, 0)]),
        ),
        (b'D', b'\x00\x03\x00\x00\x00\x01x\xff\xff\xff\xff\x00\x00\x00\x00', msgs.DataRow([b'x', None, b''])),
        (b'C', b'INSERT 0 3\x00', msgs.CommandComplete('INSERT 0 3')),
        (
            b'E',
            b'SERROR\x00C42601\x00Msyntax error\x00\x00',
            msgs.ErrorResponse({'S': 'ERROR', 'C': '42601', 'M': 'syntax error'}),
        ),
        (b'N', b'SWARNING\x00C01000\x00\x00', msgs.NoticeResponse({'S': 'WARNING', 'C': '01000'})),
        (b'A', b'\x00\x00\x00\x2achan\x00payload\x00', msgs.NotificationResponse(42, 'chan', 'payload')),
        (b't', b'\x00\x02\x00\x00\x00\x17\x00\x00\x00\x19', msgs.ParameterDescription((23, 25))),
        (b'G', b'\x00\x00\x02\x00\x00\x00\x00', msgs.CopyInResponse(False, (0, 0))),
        (b'H', b'\x01\x00\x01\x00\x01', msgs.CopyOutResponse(True, (1,))),
        (b'd', b'1\t2\n', msgs.CopyData(b'1\t2\n')),
        (b'c', b'', msgs.CopyDone()),
        (b'1', b'', msgs.ParseComplete()),
        (b'2', b'', msgs.BindComplete()),
        (b'3', b'', msgs.CloseComplete()),
        (b's', b'', msgs.PortalSuspended()),
        (b'n', b'', msgs.NoData()),
        (b'I', b'', msgs.EmptyQueryResponse()),
    ],
)
def test_decode(code, payload, expected):
    assert BackendMessageDecoder().decode(code, payload) == expected


def test_decode_error_response_with_invalid_encoding():
    """Error text is decoded leniently, as the client encoding may not be known or honored yet."""

    msg = BackendMessageDecoder().decode(b'E', b'S\xc2err\x00\x00')
    assert msg == msgs.ErrorResponse({'S': '�err'})


def test_decode_uses_client_encoding():
    dec = BackendMessageDecoder(encoding='latin1')
    assert dec.decode(b'C', b'caf\xe9\x00') == msgs.CommandComplete('caf\xe9')
    dec.set_encoding('utf8')
    assert dec.decode(b'C', b'caf\xc3\xa9\x00') == msgs.CommandComplete('caf\xe9')


def test_decode_unknown_message_type():
    with pytest.raises(ProtocolError):
        BackendMessageDecoder().decode(b'?', b'')


def test_decode_unknown_transaction_status():
    with pytest.raises(ProtocolError):
        BackendMessageDecoder().decode(b'Z', b'X')
