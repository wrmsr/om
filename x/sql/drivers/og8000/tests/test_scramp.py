import hashlib
import typing as ta

import pytest

from .. import scramp
from ..certs import tls_server_end_point
from ..scramp import Gs2Header
from ..scramp import Nonce
from ..scramp import Salt
from ..scramp import ScramClient
from ..scramp import ScramException
from ..scramp import Username
from ..scramp import _get_client_final
from ..scramp import _parse_message
from ..scramp import _set_server_first
from ..scramp import _validate_channel_binding
from ..scramp import b64dec
from ..scramp import make_channel_binding
from ..scramp import xor


@pytest.mark.parametrize(
    'string,error_msg,server_error',
    [
        [
            '!!!!',
            "Invalid base 64 encoding '!!!!': invalid-encoding",
            'invalid-encoding',
        ],
    ],
)
def test_b64dec_fails(string, error_msg, server_error):
    with pytest.raises(ScramException) as exc_info:
        b64dec(string)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


@pytest.mark.parametrize(
    'a,b,msg',
    [
        [b'', b'a', 'zip() argument 2 is longer than argument 1'],
    ],
)
def test_xor_fails(a, b, msg):
    with pytest.raises(ValueError) as exc_info:
        xor(a, b)

    assert str(exc_info.value) == msg


@pytest.mark.parametrize(
    'msg,att_sets,error_msg',
    [
        [
            '',
            [{'a', 'b', 'c'}],
            "Malformed trial message. Attributes must be separated by a ',' and each "
            "attribute must start with a letter followed by a '=': other-error",
        ],
        [
            'c=jk,d=kln',
            [{'a', 'b', 'c'}],
            'Malformed trial message. Expected the attribute set to be one of '
            '[{a, b, c}] but found {c}: other-error',
        ],
        [
            'c=jk,c=kln',
            [{'c'}],
            'Duplicate attributes not allowed in message. The duplicated attribute '
            'is c. : other-error',
        ],
        [
            'e=error',
            [{'c'}],
            'Malformed trial message. Expected the attribute set to be one of [{c}] '
            'but found {e}: other-error',
        ],
        [
            'e=\x00',
            [{'e'}],
            "Malformed trial message. Attribute values can't contain the NUL "
            "character: other-error",
        ],
    ],
)
def test_parse_message_fail(msg, att_sets, error_msg):
    with pytest.raises(ScramException) as exc_info:
        _parse_message(msg, 'trial', *att_sets)

    assert str(exc_info.value) == error_msg


@pytest.mark.parametrize(
    'msg,att_sets,result',
    [
        ['c=jk,i=kln', [{'c', 'i'}], {'c': 'jk', 'i': 'kln'}],
        ['c=jk,i=kln', [{'a', 'b', 'c'}, {'c', 'i'}], {'c': 'jk', 'i': 'kln'}],
        ['c=b', [{'c'}], {'c': 'b'}],
        ['k=k,c=b', [{'c'}], {'c': 'b'}],
    ],
)
def test_parse_message_succeed(msg, att_sets, result):
    assert _parse_message(msg, 'trial', *att_sets) == result


@pytest.mark.parametrize(
    'cb,msg',
    [
        [
            ('c', 'd'),
            "The channel_binding parameter must either be None or a "
            "tuple with the first element a str specifying one of the channel types "
            "('tls-server-end-point', 'tls-unique', 'tls-unique-for-telnet').",
        ],
    ],
)
def test_validate_channel_binding_fail(cb, msg):
    with pytest.raises(ScramException) as exc_info:
        _validate_channel_binding(cb)

    assert str(exc_info.value) == msg


@pytest.mark.parametrize(
    'gs2_char,cb_name,expected',
    [
        ['p', 'aname', 'p=aname,,'],
    ],
)
def test_Gs2Header_str(gs2_char, cb_name, expected):
    gs2_header = Gs2Header(gs2_char, cb_name)
    assert str(gs2_header) == expected


@pytest.mark.parametrize(
    'gs2_char,cb_name',
    [
        ['p', 'aname'],
    ],
)
def test_Gs2Header_eq(gs2_char, cb_name):
    gs2_header_a = Gs2Header(gs2_char, cb_name)
    gs2_header_b = Gs2Header(gs2_char, cb_name)
    assert gs2_header_a == gs2_header_b


@pytest.mark.parametrize(
    'salt,error_msg,server_error',
    [
        [
            '',  # Must be bytes
            "The 'salt' must be of type bytes, but found type <class 'str'>: "
            "other-error",
            'other-error',
        ],
    ],
)
def test_Salt_init_error(salt, error_msg, server_error):
    with pytest.raises(ScramException) as exc_info:
        Salt(salt)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


@pytest.mark.parametrize(
    'salt_str,error_msg,server_error',
    [
        [
            '!!!',
            "Invalid salt encoding: Invalid base 64 encoding '!!!': "
            "invalid-encoding: invalid-encoding",
            'invalid-encoding',
        ],
    ],
)
def test_Salt_from_str_error(salt_str, error_msg, server_error):
    with pytest.raises(ScramException) as exc_info:
        Salt.from_str(salt_str)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


@pytest.mark.parametrize(
    'nonce,error_msg,server_error',
    [
        [
            b'',  # Must be str
            "The 'nonce' must be of type str, but found type <class 'bytes'>: "
            "other-error",
            'other-error',
        ],
    ],
)
def test_Nonce_init_error(nonce, error_msg, server_error):
    with pytest.raises(ScramException) as exc_info:
        Nonce(nonce)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


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
    'auth_message': b'n=user,r=rOprNGfwEbeRWgbNEkqO,'
    b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    b's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096,c=biws,'
    b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
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
    'auth_message': b'n=user,r=rOprNGfwEbeRWgbNEkqO,'
    b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
    b's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096,c=cD10bHMtdW5pcXVlLCx4eHg=,'
    b'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
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
        'auth_message': b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        b's=QSXCR+Q6sek8bf92,i=4096,c=biws,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
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
        'auth_message': b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        b's=QSXCR+Q6sek8bf92,i=4096,c=eSws,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
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
        'auth_message': b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        b's=QSXCR+Q6sek8bf92,i=4096,c=cD10bHMtdW5pcXVlLCx4eHg=,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
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
        'auth_message': b'n=u=3Dse=2Cr,r=fyko+d2lbbFgONRv9qkxdawL,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        b's=QSXCR+Q6sek8bf92,i=4096,c=biws,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
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
        'auth_message': b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j,'
        b's=QSXCR+Q6sek8bf92,i=10000,c=biws,'
        b'r=fyko+d2lbbFgONRv9qkxdawL3rfcNHYJY1ZVvWVs7j',
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
    gs2_header = Gs2Header.from_binding(x['c_channel_binding'], x['c_use_binding'])
    cfirst_bare, cfirst = scramp._get_client_first(
        Username(x['username']), x['c_nonce'], gs2_header,
    )

    assert cfirst_bare == x['cfirst_bare']
    assert cfirst == x['cfirst']


@pytest.mark.parametrize('x', params)
def test_make_auth_message(x):
    auth_msg = scramp._make_auth_message(
        x['cfirst_bare'],
        x['sfirst'],
        x['cfinal_without_proof'],
    )
    assert auth_msg == x['auth_message']


@pytest.mark.parametrize('x', params)
def test_get_client_final(x):
    gs2_header = Gs2Header.from_binding(x['c_channel_binding'], x['c_use_binding'])
    salt = Salt.from_str(x['salt'])
    server_signature, cfinal = _get_client_final(
        x['hf'],
        x['password'],
        salt,
        x['iterations'],
        x['nonce'],
        x['cfirst_bare'],
        x['sfirst'],
        x['c_channel_binding'],
        gs2_header,
    )

    assert server_signature == x['server_signature']
    assert cfinal == x['cfinal']


@pytest.mark.parametrize('x', params)
def test_client_order(x):
    c = ScramClient(
        x['c_mechanisms'],
        x['username'],
        x['password'],
        channel_binding=x['c_channel_binding'],
    )

    with pytest.raises(ScramException):
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


def test_check_stage():
    with pytest.raises(
        ScramException,
        match='The next method to be called is set_server_first, not this method.',
    ):
        scramp._check_stage(
            scramp.ClientStage,
            scramp.ClientStage.get_client_first,
            scramp.ClientStage.set_server_final,
        )


@pytest.mark.parametrize(
    'server_first,c_nonce,min_iteration_count,error_msg',
    [
        # Error from server
        [
            'e=other-error',
            'fyko+d2lbbFgONRv9qkxdawL',
            1000,
            'The server returned the error: other-error',
        ],
        # Malformed server first
        [
            'junk',
            'fyko+d2lbbFgONRv9qkxdawL',
            1000,
            "Malformed server first message. Attributes must be separated by a ',' "
            "and each attribute must start with a letter followed by a '=': "
            "other-error",
        ],
        # Malformed iteration count in server first
        [
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            's=W22ZaJ0SNY7soEsUEjb6gQ==,i=not_an_integer',
            'fyko+d2lbbFgONRv9qkxdawL',
            1000,
            'Server iteration count not_an_integer is not valid',
        ],
    ],
)
def test_set_server_first_error(server_first, c_nonce, min_iteration_count, error_msg):
    with pytest.raises(ScramException) as exc_info:
        _set_server_first(server_first, c_nonce, min_iteration_count)
    assert str(exc_info.value) == error_msg


def test_set_server_final_missing_param():
    x: ta.Any = EXCHANGE_SCRAM_SHA_256
    c = ScramClient(
        x['c_mechanisms'],
        x['username'],
        x['password'],
        c_nonce=x['c_nonce'],
    )
    c.get_client_first()
    c.set_server_first(x['sfirst'])
    c.get_client_final()
    with pytest.raises(
        ScramException,
        match="Malformed server final message. Attributes must be separated by a ',' "
        "and each attribute must start with a letter followed by a '=': other-error",
    ):
        c.set_server_final('junk')


# def test_make_channel_binding_tls_server_end_point(mocker):
#     ssl_socket = mocker.Mock()
#     ssl_socket.getpeercert = mocker.Mock(return_value=b'cafe')
#     mock_cert = mocker.Mock()
#     mock_cert.hash_algo = 'sha512'
#     mocker.patch('scramp.core.Certificate.load', return_value=mock_cert)
#     result = make_channel_binding('tls-server-end-point', ssl_socket)
#     assert result == (
#         'tls-server-end-point',
#         b'5\x9dQ\xe2\xc4a\x17g\x1bK\xeci\x98\x9e\x16R\x96}\xe4~D\x15\xfb\xb3\x1fn]='
#         b'\re?s\x10\xf2\xf8\xa6+\x91i\x9d\x84,iO\x8emDu\xb4\x19\x06i\xa7\x1a\xf1i\xc6'
#         b'K\x81\xcbp\xd1\xaf\xd7',
#     )


# A self-signed ECDSA P-256 certificate with a SHA-256 signature, so tls-server-end-point is its plain SHA-256 digest.
_TEST_CERT_DER = bytes.fromhex(
    '3082018430820129a0030201020214066c82b1b73a7b99001aee02051b863a02ae596c300a06082a8648ce3d040302301631'
    '14301206035504030c0b6f67383030302d746573743020170d3236303832303232303535305a180f32313236303732373232'
    '303535305a30163114301206035504030c0b6f67383030302d746573743059301306072a8648ce3d020106082a8648ce3d03'
    '010703420004a480dc4432f6d17bb6893a742b3f9000bfd62f6d65c5dce68329ab8cfce3e9d98a03521e6df7ca926e34630d'
    'f291c43d2f6fa0da0c70e4325677c431289a4943a3533051301d0603551d0e041604142a8d1375cb275f04854a57257328cc'
    '8b730303c6301f0603551d230418301680142a8d1375cb275f04854a57257328cc8b730303c6300f0603551d130101ff0405'
    '30030101ff300a06082a8648ce3d0403020349003046022100a70d306145bc05e3404c4294fa1c34c37965d4def196f40684'
    'ac2ce104f4132a0221008a288761b7c7a965f1f4a550b2d91bc642488075aeffd2e82d748ef47ea8f9e5',
)


class _StaticSslSocket:
    def __init__(self, *, cert_der=None, channel_binding=None):
        self._cert_der = cert_der
        self._channel_binding = channel_binding

    def getpeercert(self, binary_form=False):
        return self._cert_der

    def get_channel_binding(self, cb_type='tls-unique'):
        return self._channel_binding


def test_make_channel_binding_tls_unique():
    ssl_socket = _StaticSslSocket(channel_binding=b'cafe')
    assert make_channel_binding('tls-unique', ssl_socket) == ('tls-unique', b'cafe')  # type: ignore


def test_make_channel_binding_tls_unique_unavailable():
    with pytest.raises(ValueError, match='tls-unique'):
        make_channel_binding('tls-unique', _StaticSslSocket())  # type: ignore


def test_make_channel_binding_tls_server_end_point():
    ssl_socket = _StaticSslSocket(cert_der=_TEST_CERT_DER)
    expected = hashlib.sha256(_TEST_CERT_DER).digest()
    assert tls_server_end_point(_TEST_CERT_DER) == expected
    assert make_channel_binding('tls-server-end-point', ssl_socket) == ('tls-server-end-point', expected)  # type: ignore  # noqa


def test_make_channel_binding_tls_server_end_point_no_certificate():
    with pytest.raises(ValueError, match='certificate'):
        make_channel_binding('tls-server-end-point', _StaticSslSocket())  # type: ignore


def test_make_channel_binding_certificate_backend_passthrough():
    ssl_socket = _StaticSslSocket(cert_der=_TEST_CERT_DER)
    with pytest.raises(ValueError, match='unknown certificate backend'):
        make_channel_binding('tls-server-end-point', ssl_socket, certificate_backend='bogus')  # type: ignore


def test_make_channel_binding_unknown_name():
    with pytest.raises(ScramException, match='not recognized'):
        make_channel_binding('tls-bogus', _StaticSslSocket())  # type: ignore
