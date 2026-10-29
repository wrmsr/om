# ruff: noqa: N802 S105 SLF001
import collections
import hashlib
import ssl

import pytest

from ..scramp2 import MECHS
from ..scramp2 import CBindData
from ..scramp2 import CbName
from ..scramp2 import ChannelBinding
from ..scramp2 import Gs2Header
from ..scramp2 import IterationCount
from ..scramp2 import Message
from ..scramp2 import Nonce
from ..scramp2 import Password
from ..scramp2 import Salt
from ..scramp2 import ScramClient
from ..scramp2 import ScramError
from ..scramp2 import ScramMechanism
from ..scramp2 import ServerError
from ..scramp2 import ServerFinal
from ..scramp2 import ServerFirst
from ..scramp2 import Username
from ..scramp2 import _get_client_final
from ..scramp2 import _get_client_first
from ..scramp2 import _make_auth_message
from ..scramp2 import _set_server_final
from ..scramp2 import _set_server_first
from ..scramp2 import _username_unescape
from ..scramp2 import b64dec
from ..scramp2 import hi
from ..scramp2 import pbkdf2_hmac_hashlib
from ..scramp2 import pbkdf2_hmac_pure_python
from ..scramp2 import saslprep
from ..scramp2 import xor


SCRAMP = __package__.rpartition('.')[0] + '.scramp2'


@pytest.mark.parametrize(
    ('msg_in', 'error_in', 'error_msg', 'server_error'),
    [
        (
            'error',
            'invalid-encoding',
            'Server error must be None or of type ServerError: other-error',
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_ScramError_init_error(msg_in, error_in, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        ScramError(msg_in, error_in)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('string', 'error_msg', 'server_error'),
    [
        (
            '!!!!',
            'Invalid base 64 encoding: invalid-encoding',
            ServerError.INVALID_ENCODING,
        ),
    ],
)
def test_b64dec_fails(string, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        b64dec(string)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('a', 'b', 'msg'),
    [
        (b'', b'a', 'zip() argument 2 is longer than argument 1'),
    ],
)
def test_xor_fails(a, b, msg):
    with pytest.raises(ValueError) as exc_info:  # noqa
        xor(a, b)

    assert str(exc_info.value) == msg


def test_hashlib_pbkdf2_hmac_present(mocker):
    hi_pbkdf2_hmac_mock = mocker.patch(SCRAMP + '.hi_pbkdf2_hmac', autospec=True)
    hf = 1
    password = 2
    salt = 3
    iterations = 3
    hi(hf, password, salt, iterations)  # type: ignore
    hi_pbkdf2_hmac_mock.assert_called_once_with(
        pbkdf2_hmac_hashlib, hf, password, salt, iterations,
    )


def test_hashlib_pbkdf2_hmac_missing(monkeypatch, mocker):
    monkeypatch.delattr('hashlib.pbkdf2_hmac')
    hi_pbkdf2_hmac_mock = mocker.patch(SCRAMP + '.hi_pbkdf2_hmac', autospec=True)
    hf = 1
    password = 2
    salt = 3
    iterations = 3
    hi(hf, password, salt, iterations)  # type: ignore
    hi_pbkdf2_hmac_mock.assert_called_once_with(
        pbkdf2_hmac_pure_python, hf, password, salt, iterations,
    )


@pytest.mark.parametrize(
    ('hf', 'password', 'salt', 'iterations'),
    [
        (
            hashlib.sha256,
            b'a',
            b64dec('W22ZaJ0SNY7soEsUEjb6gQ=='),
            4,
        ),
    ],
)
def test_pbkdf2_hmac_pure_python(hf, password, salt, iterations):
    hashlib_result = pbkdf2_hmac_hashlib(hf, password, salt, iterations)
    pure_result = pbkdf2_hmac_pure_python(hf, password, salt, iterations)
    assert pure_result == hashlib_result


@pytest.mark.parametrize(
    ('source', 'error_msg', 'server_error'),
    [  # Should use unicode 3.2
        (
            '\U0001f130',
            'unassigned code points forbidden: invalid-encoding',
            ServerError.INVALID_ENCODING,
        ),
    ],
)
def test_saslprep_error(source, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        saslprep(source)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('msg', 'att_strs', 'result'),
    [
        ('c=jk,i=5000', ['ci'], collections.OrderedDict(c='jk', i=IterationCount(5000))),
        ('c=jk,i=4096', ['abc', 'ci'], collections.OrderedDict(c='jk', i=IterationCount(4096))),
        ('c=b', ['c'], collections.OrderedDict(c='b')),
        ('k=k,c=b', ['*c'], collections.OrderedDict(k='k', c='b')),
    ],
)
def test_Message_init(msg, att_strs, result):
    msg = Message(msg, 'trial', *att_strs)
    assert msg._msg == result


@pytest.mark.parametrize(
    ('msg', 'att_seqs', 'error_msg'),
    [
        (
            'junk',
            ['abc'],
            (
                "Malformed trial message. Attributes must be separated by a ',' "
                "and each attribute must start with a letter followed by a '=': "
                "other-error"
            ),
        ),
        (
            '',
            ['abc'],
            (
                "Malformed trial message. Attributes must be separated by a ',' and "
                "each attribute must start with a letter followed by a '=': other-error"
            ),
        ),
        (
            'c=jk,d=kln',
            ['abc'],
            (
                "Malformed trial message. Expected the attribute str to be one of "
                "['abc'] but found 'c*' (where '*' is unrecognised attributes): "
                "other-error"
            ),
        ),
        (
            'c=jk,c=kln',
            ['c'],
            'Duplicate attributes not allowed in message: other-error',
        ),
        (
            'e=error',
            ['c'],
            (
                "Malformed trial message. Expected the attribute str to be one of "
                "['c'] but found 'e': other-error"
            ),
        ),
        (
            'e=\x00',
            ['e'],
            (
                "Malformed trial message. Attribute values can't contain the NUL "
                "character: other-error"
            ),
        ),
        (
            'r=a,x=b,p=c,y=d',
            ['r*p'],
            (
                "Malformed trial message. Expected the attribute str to be one of "
                "['r*p'] but found 'r*p*' (where '*' is unrecognised attributes): "
                "other-error"
            ),
        ),
        (
            b'c=jk,i=kln',
            ['r*p'],
            'A message must be of type str: other-error',
        ),
        # Malformed iteration count in server first
        (
            (
                'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
                's=W22ZaJ0SNY7soEsUEjb6gQ==,i=not_an_integer'
            ),
            ['rsi'],
            'The iteration count can only contain ASCII digits: other-error',
        ),
        # Server signature contains invalid base 64 encoding
        (
            ('v=é'),
            ['v'],
            'Invalid base 64 encoding: invalid-encoding',
        ),
    ],
)
def test_Message_init_error(msg, att_seqs, error_msg):
    with pytest.raises(ScramError) as exc_info:
        Message(msg, 'trial', *att_seqs)

    assert str(exc_info.value) == error_msg


@pytest.mark.parametrize(
    ('i', 'error_msg', 'server_error'),
    [
        (
            True,
            'The value must be an int: other-error',
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_IterationCount_init_error(i, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        IterationCount(i)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('i', 'error_msg', 'server_error'),
    [
        (
            '',
            'The iteration count must not be empty: other-error',
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_IterationCount_from_str_error(i, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        IterationCount.from_str(i)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


def test_IterationCount_lt_error():
    IterationCount(4096).__lt__(5000)
    with pytest.raises(TypeError) as exc_info:
        _ = IterationCount(4096) < 5000

    assert (
        str(exc_info.value)
        == "'<' not supported between instances of 'IterationCount' and 'int'"
    )


@pytest.mark.parametrize(
    ('username', 'expected_username'),
    [
        # RFC 5802, section 5.1
        ('u=3Dse=2Cr', 'u=se,r'),
    ],
)
def test_username_unescape(username, expected_username):
    actual_username = _username_unescape(username)
    assert actual_username == expected_username


@pytest.mark.parametrize(
    ('username', 'error_msg', 'server_error'),
    [
        # RFC 5802, section 5.1
        (
            '=',
            (
                "An '=' in a username must be followed by '3D', or  '2C': "
                "invalid-username-encoding"
            ),
            ServerError.INVALID_USERNAME_ENCODING,
        ),
    ],
)
def test_username_unescape_error(username, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        _username_unescape(username)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('data', 'error_msg', 'server_error'),
    [
        (
            b'',
            'Problem loading certificate from DER: other-error',
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_CBindData_from_der_error(data, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        CBindData.from_der(data)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('cb', 'use_binding'),
    [
        (
            ChannelBinding(CbName('tls-unique'), CBindData(b'bee')),
            True,
        ),
    ],
)
def test_Gs2Header_from_binding(cb, use_binding):
    Gs2Header.from_binding(cb, True)


@pytest.mark.parametrize(
    ('header_str', 'error_msg', 'server_error'),
    [
        (
            'p=an=ame,,',
            (
                "The channel binding name must contain only ASCII characters that are "
                "alphabetic or a digit or '.' or '-': other-error"
            ),
            ServerError.OTHER_ERROR,
        ),
        (
            'p=tls-unique,,trailing',  # No traling characters after the last comma
            "The gs2-header can't have characters after the last comma: other-error",
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_Gs2Header_from_str_error(header_str, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        Gs2Header.from_str(header_str)
    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('gs2_char', 'cb_name', 'expected'),
    [
        ('p', CbName('tls-unique'), 'p=tls-unique,,'),
    ],
)
def test_Gs2Header_str(gs2_char, cb_name, expected):
    gs2_header = Gs2Header(gs2_char, cb_name)
    assert str(gs2_header) == expected


@pytest.mark.parametrize(
    ('gs2_char', 'cb_name'),
    [
        ('p', CbName('tls-unique')),
    ],
)
def test_Gs2Header_eq(gs2_char, cb_name):
    gs2_header_a = Gs2Header(gs2_char, cb_name)
    gs2_header_b = Gs2Header(gs2_char, cb_name)
    assert gs2_header_a == gs2_header_b


@pytest.mark.parametrize(
    ('username', 'error_msg', 'server_error'),
    [
        (
            '',
            'The username cannot be empty: other-error',
            ServerError.OTHER_ERROR,
        ),
        (
            '\u00ad',
            'The username cannot be empty: other-error',
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_Username_init_error(username, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        Username(username)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('salt', 'error_msg', 'server_error'),
    [
        (
            '',  # Must be bytes
            (
                "The 'salt' must be of type bytes, but found type <class 'str'>: "
                "other-error"
            ),
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_Salt_init_error(salt, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        Salt(salt)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('salt_str', 'error_msg', 'server_error'),
    [
        (
            '!!!',
            'Invalid base 64 encoding: invalid-encoding',
            ServerError.INVALID_ENCODING,
        ),
    ],
)
def test_Salt_from_str_error(salt_str, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        Salt.from_str(salt_str)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('nonce', 'error_msg', 'server_error'),
    [
        (
            b'',  # Must be str
            (
                "The 'nonce' must be of type str, but found type <class 'bytes'>: "
                "other-error"
            ),
            ServerError.OTHER_ERROR,
        ),
        (
            '',  # Can't be empty
            "An empty string isn't allowed: other-error",
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_Nonce_init_error(nonce, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        Nonce(nonce)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    ('name', 'error_msg', 'server_error'),
    [
        (
            'bogus',
            (
                "The channel binding type is not recognised by Scramp. The recognised "
                "types are ['tls-exporter', 'tls-server-end-point', 'tls-unique', "
                "'tls-unique-for-telnet']: unsupported-channel-binding-type"
            ),
            ServerError.UNSUPPORTED_CHANNEL_BINDING_TYPE,
        ),
        (
            'tls-exporter',
            (
                "The channel binding types ['tls-exporter'] are not supported by "
                "Scramp. Please see the README for details: "
                "unsupported-channel-binding-type"
            ),
            ServerError.UNSUPPORTED_CHANNEL_BINDING_TYPE,
        ),
    ],
)
def test_CbName_init_error(name, error_msg, server_error):
    with pytest.raises(ScramError) as exc_info:
        CbName(name)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


@pytest.mark.parametrize(
    'mechanism_name',
    ['SCRAM-SHA-256', 'SCRAM-SHA-512-PLUS', 'SCRAM-SHA3-512-PLUS'],
)
def test_ScramMechanism_init(mechanism_name):
    mechanism = ScramMechanism(mechanism_name)
    mech_data = MECHS[mechanism_name]

    assert mechanism.strength == mech_data.strength
    assert mechanism.iteration_count == mech_data.iteration_count


@pytest.mark.parametrize(
    ('mechanism_name', 'password', 'iteration_count', 'salt'),
    [
        (
            'SCRAM-SHA3-512',
            'pencil',
            50000,
            b'aaaaaaaaaaaaaaaa',
        ),
        (
            'SCRAM-SHA3-512',
            'pencil',
            20000,
            b'xxxxxxxxxxxxxxxx',
        ),
        (
            'SCRAM-SHA-512-PLUS',
            'pencil',
            50000,
            b'aaaaaaaaaaaaaaaa',
        ),
        (
            'SCRAM-SHA3-512-PLUS',
            'pencil',
            20000,
            b'xxxxxxxxxxxxxxxx',
        ),
    ],
)
def test_ScramMechanism_make_auth_info(mechanism_name, password, iteration_count, salt):
    m = ScramMechanism(mechanism=mechanism_name)
    m.make_auth_info(password, iteration_count, salt)


@pytest.mark.parametrize(
    ('mechanism_name', 'password', 'iteration_count', 'salt', 'error_msg', 'server_error'),
    [
        (
            'SCRAM-SHA3-512',
            'pencil',
            1,
            b'aaaaaaaaaaaaaaaa',
            'The value must not be < 4096: other-error',
            ServerError.OTHER_ERROR,
        ),
        (
            'SCRAM-SHA3-512',
            'pencil',
            20000,
            '',
            (
                "The 'salt' must be of type bytes, but found type "
                "<class 'str'>: other-error"
            ),
            ServerError.OTHER_ERROR,
        ),
    ],
)
def test_ScramMechanism_make_auth_info_error(
    mechanism_name, password, iteration_count, salt, error_msg, server_error,
):
    m = ScramMechanism(mechanism=mechanism_name)
    with pytest.raises(ScramError) as exc_info:
        m.make_auth_info(password, iteration_count, salt)

    assert str(exc_info.value) == error_msg
    assert exc_info.value.server_error == server_error


EXCHANGE_SCRAM_SHA_256 = {
    'username': 'user',
    'password': 'pencil',
    'c_mechanisms': ['SCRAM-SHA-256'],
    's_mechanism': 'SCRAM-SHA-256',
    'cfirst': 'n,,n=user,r=rOprNGfwEbeRWgbNEkqO',
    'sfirst': 'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
    'cfinal': 'c=biws,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    'p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=',
    'cfinal_without_proof': 'c=biws,'
    'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'sfinal': 'v=6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4=',
    'cfirst_bare': 'n=user,r=rOprNGfwEbeRWgbNEkqO',
    'c_nonce': 'rOprNGfwEbeRWgbNEkqO',
    's_nonce': '%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'nonce': 'rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'auth_message': (
        b'n=user,r=rOprNGfwEbeRWgbNEkqO,'
        b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
        b's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096,c=biws,'
        b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'
    ),
    'salt': 'W22ZaJ0SNY7soEsUEjb6gQ==',
    'iterations': 4096,
    'server_signature': '6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4=',
    'hf': hashlib.sha256,
    'stored_key': 'WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY=',
    'server_key': 'wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU=',
    'c_use_binding': False,
    's_init_use_binding': False,
    's_use_binding': False,
    'c_channel_binding': None,
    's_channel_binding': None,
}

EXCHANGE_SCRAM_SHA_256_PLUS = {
    'username': 'user',
    'password': 'pencil',
    'c_mechanisms': ['SCRAM-SHA-256-PLUS'],
    's_mechanism': 'SCRAM-SHA-256-PLUS',
    'cfirst': 'p=tls-unique,,n=user,r=rOprNGfwEbeRWgbNEkqO',
    'sfirst': 'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
    'cfinal': 'c=cD10bHMtdW5pcXVlLCx4eHg=,'
    'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    'p=v0J7PaQUPWowoTrwRLCKLzIZBpNUhWFlTrUKI1j9DpM=',
    'cfinal_without_proof': 'c=cD10bHMtdW5pcXVlLCx4eHg=,'
    'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'sfinal': 'v=XjAev9iHBOvTxT+eNzBaFmP1IrqWah2PpZAa0wQrfY4=',
    'cfirst_bare': 'n=user,r=rOprNGfwEbeRWgbNEkqO',
    'c_nonce': 'rOprNGfwEbeRWgbNEkqO',
    's_nonce': '%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'nonce': 'rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
    'auth_message': (
        b'n=user,r=rOprNGfwEbeRWgbNEkqO,'
        b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
        b's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096,c=cD10bHMtdW5pcXVlLCx4eHg=,'
        b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'
    ),
    'salt': 'W22ZaJ0SNY7soEsUEjb6gQ==',
    'iterations': 4096,
    'server_signature': 'XjAev9iHBOvTxT+eNzBaFmP1IrqWah2PpZAa0wQrfY4=',
    'hf': hashlib.sha256,
    'stored_key': 'WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY=',
    'server_key': 'wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU=',
    'c_use_binding': True,
    's_init_use_binding': True,
    's_use_binding': True,
    'c_channel_binding': ('tls-unique', b'xxx'),
    's_channel_binding': ('tls-unique', b'xxx'),
}


params = [
    # Standard SCRAM_SHA_1
    {
        'username': 'user',
        'password': 'pencil',
        'c_mechanisms': ['SCRAM-SHA-1'],
        's_mechanism': 'SCRAM-SHA-1',
        'cfirst': 'n,,n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'cfirst_bare': 'n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'sfirst': 'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        's=QSXCR+Q6sek8bf92,i=4096',
        'cfinal': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        'p=v0X8v3Bz2T0CJGbJQyF0X+HI4Ts=',
        'cfinal_without_proof': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'sfinal': 'v=rmF9pqV8S7suAoZWja4dJRkFsKQ=',
        'c_nonce': 'fyko+d2lbbFgONRv9qkxdawL',
        's_nonce': '3rfcNHYJY1ZVvWVs7j',
        'nonce': 'fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'auth_message': (
            b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
            b's=QSXCR+Q6sek8bf92,i=4096,c=biws,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j'
        ),
        'salt': 'QSXCR+Q6sek8bf92',
        'iterations': 4096,
        'server_signature': 'rmF9pqV8S7suAoZWja4dJRkFsKQ=',
        'hf': hashlib.sha1,
        'stored_key': '6dlGYMOdZcOPutkcNY8U2g7vK9Y=',
        'server_key': 'D+CSWLOshSulAsxiupA+qs2/fTE=',
        'c_use_binding': False,
        's_init_use_binding': False,
        's_use_binding': False,
        'c_channel_binding': None,
        's_channel_binding': None,
    },
    # SCRAM_SHA_1 where the client supports channel binding but the server does not
    {
        'username': 'user',
        'password': 'pencil',
        'c_mechanisms': ['SCRAM-SHA-1'],
        's_mechanism': 'SCRAM-SHA-1',
        'cfirst': 'y,,n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'sfirst': 'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        's=QSXCR+Q6sek8bf92,i=4096',
        'cfinal': 'c=eSws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        'p=BjZF5dV+EkD3YCb3pH3IP8riMGw=',
        'cfinal_without_proof': 'c=eSws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'sfinal': 'v=dsprQ5R2AGYt1kn4bQRwTAE0PTU=',
        'cfirst_bare': 'n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'c_nonce': 'fyko+d2lbbFgONRv9qkxdawL',
        's_nonce': '3rfcNHYJY1ZVvWVs7j',
        'nonce': 'fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'auth_message': (
            b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
            b's=QSXCR+Q6sek8bf92,i=4096,c=eSws,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j'
        ),
        'salt': 'QSXCR+Q6sek8bf92',
        'iterations': 4096,
        'server_signature': 'dsprQ5R2AGYt1kn4bQRwTAE0PTU=',
        'hf': hashlib.sha1,
        'stored_key': '6dlGYMOdZcOPutkcNY8U2g7vK9Y=',
        'server_key': 'D+CSWLOshSulAsxiupA+qs2/fTE=',
        'c_use_binding': False,
        's_init_use_binding': False,
        's_use_binding': False,
        'c_channel_binding': ('tls-unique', b'xxx'),
        's_channel_binding': None,
    },
    # Standard SCRAM_SHA_1_PLUS
    {
        'username': 'user',
        'password': 'pencil',
        'c_mechanisms': ['SCRAM-SHA-1-PLUS'],
        's_mechanism': 'SCRAM-SHA-1-PLUS',
        'cfirst': 'p=tls-unique,,n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'sfirst': 'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        's=QSXCR+Q6sek8bf92,i=4096',
        'cfinal': 'c=cD10bHMtdW5pcXVlLCx4eHg=,'
        'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        'p=/63TtbB5lIS6610+k4/luJMJqAI=',
        'cfinal_without_proof': 'c=cD10bHMtdW5pcXVlLCx4eHg=,'
        'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'sfinal': 'v=GCPHy5gy1sRwXTCbwNhiiWIzLtU=',
        'cfirst_bare': 'n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'c_nonce': 'fyko+d2lbbFgONRv9qkxdawL',
        's_nonce': '3rfcNHYJY1ZVvWVs7j',
        'nonce': 'fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'auth_message': (
            b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
            b's=QSXCR+Q6sek8bf92,i=4096,c=cD10bHMtdW5pcXVlLCx4eHg=,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j'
        ),
        'salt': 'QSXCR+Q6sek8bf92',
        'iterations': 4096,
        'server_signature': 'GCPHy5gy1sRwXTCbwNhiiWIzLtU=',
        'hf': hashlib.sha1,
        'stored_key': '6dlGYMOdZcOPutkcNY8U2g7vK9Y=',
        'server_key': 'D+CSWLOshSulAsxiupA+qs2/fTE=',
        'c_use_binding': True,
        's_init_use_binding': True,
        's_use_binding': True,
        'c_channel_binding': ('tls-unique', b'xxx'),
        's_channel_binding': ('tls-unique', b'xxx'),
    },
    EXCHANGE_SCRAM_SHA_256,
    EXCHANGE_SCRAM_SHA_256_PLUS,
    # Standard SCRAM_SHA_1 with username that needs escaping
    {
        'username': 'u=se,r',
        'password': 'pencil',
        'c_mechanisms': ['SCRAM-SHA-1'],
        's_mechanism': 'SCRAM-SHA-1',
        'cfirst': 'n,,n=u=3Dse=2Cr,r=fyko+d2lbbFgONRv9qkxdawL',
        'cfirst_bare': 'n=u=3Dse=2Cr,r=fyko+d2lbbFgONRv9qkxdawL',
        'sfirst': 'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        's=QSXCR+Q6sek8bf92,i=4096',
        'cfinal': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        'p=vqBTKFd8G1j1sueD4sUotSjIYfs=',
        'cfinal_without_proof': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'sfinal': 'v=ySs7A8qkVwzSKc4pAqR/R4+/50g=',
        'c_nonce': 'fyko+d2lbbFgONRv9qkxdawL',
        's_nonce': '3rfcNHYJY1ZVvWVs7j',
        'nonce': 'fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'auth_message': (
            b'n=u=3Dse=2Cr,r=fyko+d2lbbFgONRv9qkxdawL,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
            b's=QSXCR+Q6sek8bf92,i=4096,c=biws,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j'
        ),
        'salt': 'QSXCR+Q6sek8bf92',
        'iterations': 4096,
        'server_signature': 'ySs7A8qkVwzSKc4pAqR/R4+/50g=',
        'hf': hashlib.sha1,
        'stored_key': '6dlGYMOdZcOPutkcNY8U2g7vK9Y=',
        'server_key': 'D+CSWLOshSulAsxiupA+qs2/fTE=',
        'c_use_binding': False,
        's_init_use_binding': False,
        's_use_binding': False,
        'c_channel_binding': None,
        's_channel_binding': None,
    },
    # SCRAM_SHA3_512
    {
        'username': 'user',
        'password': 'pencil',
        'c_mechanisms': ['SCRAM-SHA3-512'],
        's_mechanism': 'SCRAM-SHA3-512',
        'cfirst': 'n,,n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'cfirst_bare': 'n=user,r=fyko+d2lbbFgONRv9qkxdawL',
        'sfirst': 'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        's=QSXCR+Q6sek8bf92,i=10000',
        'cfinal': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        'p=KOkd92LduC09A+RDxbTvgxH9Nn6efom/uAy6U5/fqpwLH1J+wQnZcKx5W1zd'
        '7YMPU8PrusBUK5RgRk4yHx+3Mg==',
        'cfinal_without_proof': 'c=biws,r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'sfinal': 'v=L8sKlyFigUkpTO8I3eaJSyuQhsDynb2eD1MWl+2ELjw7fJkbzr'
        '8N6Z41pkOAfjzuW/sT6+UElBTt5WbaxZ8oag==',
        'c_nonce': 'fyko+d2lbbFgONRv9qkxdawL',
        's_nonce': '3rfcNHYJY1ZVvWVs7j',
        'nonce': 'fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
        'auth_message': (
            b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
            b's=QSXCR+Q6sek8bf92,i=10000,c=biws,'
            b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j'
        ),
        'salt': 'QSXCR+Q6sek8bf92',
        'iterations': 10000,
        'server_signature': 'L8sKlyFigUkpTO8I3eaJSyuQhsDynb2eD1MWl+'
        '2ELjw7fJkbzr8N6Z41pkOAfjzuW/sT6+UElBTt5WbaxZ8oag==',
        'hf': hashlib.sha3_512,
        'stored_key': '7tmSwbz0qdlCWaMqA8gm8gNQ3VHbW1zEKpX+ST1QX5RzBefTHhYe3'
        'EtogaGggZioWX1pp471+gbmGOn31w5iTg==',
        'server_key': 'lLR0hmplzlAmeKBf3SO/jzdaPse5fUr+phiGcjHEq84uBSsC'
        'yaP21OIWheSKAGSIRiXVztaC3hBde0ZM/Ae/Ug==',
        'c_use_binding': False,
        's_init_use_binding': False,
        's_use_binding': False,
        'c_channel_binding': None,
        's_channel_binding': None,
    },
]


@pytest.mark.parametrize('x', params)
def test_get_client_first(x):
    channel_binding = x['c_channel_binding']
    if channel_binding is None:
        cb = None
    else:
        cb_name, cb_data = channel_binding
        cb = ChannelBinding(CbName(cb_name), CBindData(cb_data))
    gs2_header = Gs2Header.from_binding(cb, x['c_use_binding'])
    cfirst_bare, cfirst = _get_client_first(
        Username(x['username']), x['c_nonce'], gs2_header,
    )

    assert cfirst_bare == x['cfirst_bare']
    assert cfirst == x['cfirst']


@pytest.mark.parametrize('x', params)
def test_make_auth_message(x):
    auth_msg = _make_auth_message(
        x['cfirst_bare'],
        x['sfirst'],
        x['cfinal_without_proof'],
    )
    assert auth_msg == x['auth_message']


@pytest.mark.parametrize('x', params)
def test_get_client_final(x):
    channel_binding = x['c_channel_binding']
    if channel_binding is None:
        cb = None
    else:
        cb_name, cb_data = channel_binding
        cb = ChannelBinding(CbName(cb_name), CBindData(cb_data))
    gs2_header = Gs2Header.from_binding(cb, x['c_use_binding'])
    salt = Salt.from_str(x['salt'])
    password = Password(x['password'])
    server_signature, cfinal = _get_client_final(
        x['hf'],
        password,
        salt,
        x['iterations'],
        x['nonce'],
        x['cfirst_bare'],
        x['sfirst'],
        cb,
        gs2_header,
    )

    assert server_signature == b64dec(x['server_signature'])
    assert cfinal == x['cfinal']


@pytest.mark.parametrize('x', params)
def test_client_order(x):
    c = ScramClient(
        x['c_mechanisms'],
        x['username'],
        x['password'],
        channel_binding=x['c_channel_binding'],
    )

    with pytest.raises(ScramError):
        c.set_server_first(x['sfirst'])


@pytest.mark.parametrize('x', params)
def test_client(x):
    c = ScramClient(
        x['c_mechanisms'],
        x['username'],
        x['password'],
        channel_binding=x['c_channel_binding'],
        c_nonce=x['c_nonce'],
    )

    assert c.get_client_first() == x['cfirst']

    c.set_server_first(x['sfirst'])

    assert c.get_client_final() == x['cfinal']


@pytest.mark.parametrize(
    ('server_first', 'c_nonce'),
    [
        (
            ServerFirst(
                'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
                's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
            ),
            Nonce('rOprNGfwEbeRWgbNEkqO'),
        ),
    ],
)
def test_set_server_first(server_first, c_nonce):
    _set_server_first(server_first, c_nonce)


@pytest.mark.parametrize(
    ('server_first', 'c_nonce', 'error_msg'),
    [
        # Error from server
        (
            ServerFirst('e=other-error'),
            Nonce('fyko+d2lbbFgONRv9qkxdawL'),
            'The server returned an error: other-error',
        ),
        # The nonce must be longer than the c_nonce
        (
            ServerFirst('r=fyko+d2lbbFgONRv9qkxdawL,s=W22ZaJ0SNY7soEsUEjb6gQ==,i=5000'),
            Nonce('fyko+d2lbbFgONRv9qkxdawL'),
            'The nonce must be longer than the client nonce: other-error',
        ),
        (
            ServerFirst('e=other-error,x=a'),
            Nonce('fyko+d2lbbFgONRv9qkxdawL'),
            'The server returned an error: other-error',
        ),
    ],
)
def test_set_server_first_error(server_first, c_nonce, error_msg):
    with pytest.raises(ScramError) as exc_info:
        _set_server_first(server_first, c_nonce)

    assert str(exc_info.value) == error_msg


@pytest.mark.parametrize(
    ('msg', 'server_signature'),
    [
        (
            ServerFinal('v=6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4='),
            b64dec('6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4='),
        ),
    ],
)
def test_set_server_final(msg, server_signature):
    _set_server_final(msg, server_signature)


def test_ScramClient_init_error_no_cert(mocker):
    mechanisms = ['SCRAM-SHA-256-PLUS']
    username = 'max'
    password = 'pencil'
    sock = mocker.MagicMock(spec=ssl.SSLSocket)
    sock.getpeercert.return_value = None
    channel_binding = 'tls-server-end-point', sock
    c_nonce = 'rOprNGfwEbeRWgbNEkqO'
    with pytest.raises(ScramError) as exc_info:
        ScramClient(
            mechanisms,
            username,
            password,
            channel_binding=channel_binding,
            c_nonce=c_nonce,
        )
    expected_error_msg = 'There is no peer certificate for the SSL socket: other-error'
    assert str(exc_info.value) == expected_error_msg


@pytest.mark.parametrize(
    ('mechanisms', 'username', 'password', 'channel_binding', 'c_nonce'),
    [
        (
            ['SCRAM-SHA-256-PLUS'],
            'max',
            'pencil',
            ('tls-unique', b'xxx'),
            'rOprNGfwEbeRWgbNEkqO',
        ),
    ],
)
def test_ScramClient_init(
    mocker, mechanisms, username, password, channel_binding, c_nonce,
):
    ScramClient(
        mechanisms,
        username,
        password,
        channel_binding=channel_binding,
        c_nonce=c_nonce,
    )


# @pytest.mark.parametrize(
#     'ssl_socket_class',
#     [
#         ssl.SSLSocket,
#         ssl.SSLObject,
#     ],
# )
# def test_ScramClient_init_tls_server_end_point(mocker, ssl_socket_class):
#     mechanisms = ['SCRAM-SHA-512-PLUS']
#     username = 'max'
#     password = 'pencil'
#
#     ssl_socket = mocker.create_autospec(ssl_socket_class, instance=True)
#     ssl_socket.getpeercert = mocker.Mock(return_value=b'cafe')
#     mock_cert = mocker.Mock()
#     mock_cert.hash_algo = 'sha512'
#     mocker.patch('scramp.core.Certificate.load', return_value=mock_cert)
#     channel_binding = 'tls-server-end-point', ssl_socket
#     c_nonce = None
#
#     client = ScramClient(
#         mechanisms, username, password, channel_binding=channel_binding, c_nonce=c_nonce,
#     )
#     assert client.cb == ChannelBinding(
#         CbName('tls-server-end-point'),
#         CBindData(
#             b'5\x9dQ\xe2\xc4a\x17g\x1bK\xeci\x98\x9e\x16R\x96}\xe4~D\x15\xfb\xb3\x1fn]='
#             b'\re?s\x10\xf2\xf8\xa6+\x91i\x9d\x84,iO\x8emDu\xb4\x19\x06i\xa7\x1a\xf1i\xc6'
#             b'K\x81\xcbp\xd1\xaf\xd7',
#         ),
#     )


@pytest.mark.parametrize(
    'ssl_socket_class',
    [
        ssl.SSLSocket,
        ssl.SSLObject,
    ],
)
def test_ScramClient_init_tls_unique_ssl_socket(mocker, ssl_socket_class):
    mechanisms = ['SCRAM-SHA-512-PLUS']
    username = 'max'
    password = 'pencil'
    cb_name = 'tls-unique'
    cb_data = b'x'
    ssl_socket = mocker.create_autospec(ssl_socket_class, instance=True)
    ssl_socket.get_channel_binding.return_value = cb_data

    channel_binding = 'tls-unique', ssl_socket
    client = ScramClient(
        mechanisms,
        username=username,
        password=password,
        channel_binding=channel_binding,
    )

    ssl_socket.get_channel_binding.assert_called_once_with(cb_name)
    assert client.cb == ChannelBinding(CbName(cb_name), CBindData(cb_data))


@pytest.mark.parametrize(
    ('mechanisms', 'username', 'password', 'channel_binding', 'msg'),
    [
        (
            ['SCRAM-SHA-512-PLUS'],
            'max',
            'pencil',
            ('c', 'd'),
            (
                "The channel binding type is not recognised by Scramp. The recognised "
                "types are ['tls-exporter', 'tls-server-end-point', 'tls-unique', "
                "'tls-unique-for-telnet']: unsupported-channel-binding-type"
            ),
        ),
    ],
)
def test_ScramClient_init_error(mechanisms, username, password, channel_binding, msg):
    with pytest.raises(ScramError) as exc_info:
        ScramClient(mechanisms, username, password, channel_binding=channel_binding)

    assert str(exc_info.value) == msg


def test_ScramClient_set_server_final_missing_param():
    x = EXCHANGE_SCRAM_SHA_256
    c = ScramClient(
        x['c_mechanisms'],  # type: ignore
        x['username'],  # type: ignore
        x['password'],  # type: ignore
        c_nonce=x['c_nonce'],  # type: ignore
    )
    c.get_client_first()
    c.set_server_first(x['sfirst'])
    c.get_client_final()
    with pytest.raises(
        ScramError,
        match=(
            r"Malformed server final message. Attributes must be separated by a ',' "
            r"and each attribute must start with a letter followed by a '=': other-error"
        ),
    ):
        c.set_server_final('junk')
