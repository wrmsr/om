import hashlib

import pytest

from .. import scramp
from ..scramp import AuthFn
from ..scramp import Gs2Header
from ..scramp import Nonce
from ..scramp import Salt
from ..scramp import ScramClient
from ..scramp import ScramException
from ..scramp import ScramMechanism
from ..scramp import ServerErrors
from ..scramp import Username
from ..scramp import _check_client_key
from ..scramp import _get_client_final
from ..scramp import _parse_message
from ..scramp import _set_client_final
from ..scramp import _set_client_first
from ..scramp import _set_server_first
from ..scramp import _username_unescape
from ..scramp import _validate_channel_binding
from ..scramp import b64dec
from ..scramp import b64enc
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
    'username, expected_username',
    [
        # RFC 5802, section 5.1
        ['u=3Dse=2Cr', 'u=se,r'],
    ],
)
def test_username_unescape(username, expected_username):
    actual_username = _username_unescape(username)
    assert actual_username == expected_username


@pytest.mark.parametrize(
    'username,error_msg,server_error',
    [
        # RFC 5802, section 5.1
        [
            '=',
            "An '=' in a username must be followed by '3D', or  '2C': "
            "invalid-username-encoding",
            'invalid-username-encoding',
        ],
    ],
)
def test_username_unescape_error(username, error_msg, server_error):
    with pytest.raises(ScramException) as exc_info:
        _username_unescape(username)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


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


def test_AuthFn_init_callable():
    class Auth:
        def __call__(self, _):
            pass

    AuthFn(Auth())


@pytest.mark.parametrize(
    'password,iteration_count,salt,msg',
    [
        [
            'pencil',
            1,
            b'a',
            'The iteration count is not valid: The value must not be < 10000',
        ],
        [
            'pencil',
            20000,
            '',
            "The 'salt' must be of type bytes, but found type "
            "<class 'str'>: other-error",
        ],
    ],
)
def test_make_auth_info_fail(password, iteration_count, salt, msg):
    m = ScramMechanism(mechanism='SCRAM-SHA3-512')
    with pytest.raises(ScramException) as exc_info:
        m.make_auth_info(password, iteration_count, salt)

    assert str(exc_info.value) == msg


@pytest.mark.parametrize(
    'hf,stored_key, auth_msg, proof, msg',
    [
        # Client signature and proof of different lengths, so xor() should fail
        [
            hashlib.sha256,
            b64dec(
                '7tmSwbz0qdlCWaMqA8gm8gNQ3VHbW1zEKpX+ST1QX5RzBefTHhYe3'
                'EtogaGggZioWX1pp471+gbmGOn31w5iTg==',
            ),
            b'n=user,r=fyko+d2lbbFgONRv9qkxdawL,',
            'W22ZaJ0SNY7soEsUEjb6gQ==',
            "Can't create client key.: invalid-proof",
        ],
    ],
)
def test_check_client_key_fail(hf, stored_key, auth_msg, proof, msg):
    with pytest.raises(ScramException) as exc_info:
        _check_client_key(hf, stored_key, auth_msg, proof)

    assert str(exc_info.value) == msg
    assert str(exc_info.value.server_error) == ServerErrors.INVALID_PROOF


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


@pytest.mark.parametrize('x', params)
def test_set_client_first(x):
    m = ScramMechanism(mechanism=x['s_mechanism'])
    salt_in = Salt.from_str(x['salt'])

    def auth_fn(username):
        lookup = {
            x['username']: m.make_auth_info(
                x['password'],
                salt=bytes(salt_in),
                iteration_count=x['iterations'],
            ),
        }
        return lookup[username]

    (
        nonce,
        cfirst_bare,
        upgrade_mechanism,
        gs2_header,
        salt,
        stored_key,
        server_key,
        i,
    ) = _set_client_first(
        x['cfirst'],
        Nonce(x['s_nonce']),
        x['s_channel_binding'],
        x['s_init_use_binding'],
        AuthFn(auth_fn),
    )

    assert nonce == Nonce(x['nonce'])
    assert cfirst_bare == x['cfirst_bare']
    assert upgrade_mechanism == (x['s_init_use_binding'] != x['s_use_binding'])
    expected_gs2_header = Gs2Header.from_binding(
        x['c_channel_binding'], x['c_use_binding'],
    )
    assert gs2_header == expected_gs2_header
    assert salt == salt_in
    assert b64enc(stored_key) == x['stored_key']
    assert b64enc(server_key) == x['server_key']
    assert i == x['iterations']


@pytest.mark.parametrize('x', params)
def test_get_server_first(x):
    sfirst = scramp._get_server_first(x['nonce'], x['salt'], x['iterations'])

    assert sfirst == x['sfirst']


@pytest.mark.parametrize('x', params)
def test_set_client_final(x):
    gs2_header = Gs2Header.from_binding(x['c_channel_binding'], x['c_use_binding'])
    server_signature = scramp._set_client_final(
        x['hf'],
        x['cfinal'],
        Nonce(x['nonce']),
        b64dec(x['stored_key']),
        b64dec(x['server_key']),
        x['cfirst_bare'],
        x['sfirst'],
        x['s_channel_binding'],
        gs2_header,
    )

    assert server_signature == x['server_signature']


@pytest.mark.parametrize('x', params)
def test_get_server_final(x):
    server_final = scramp._get_server_final(x['server_signature'], None)
    assert server_final == x['sfinal']


@pytest.mark.parametrize('x', params)
def test_server_order(x):
    m = ScramMechanism(mechanism=x['s_mechanism'])

    def auth_fn(username):
        lookup = {
            x['username']: m.make_auth_info(
                x['password'], salt=x['salt'], iteration_count=x['iterations'],
            ),
        }
        return lookup[username]

    s = m.make_server(auth_fn, channel_binding=x['s_channel_binding'])

    with pytest.raises(ScramException):
        s.set_client_final(x['cfinal'])


@pytest.mark.parametrize('x', params)
def test_server(x):
    m = ScramMechanism(mechanism=x['s_mechanism'])

    def auth_fn(username):
        lookup = {
            x['username']: m.make_auth_info(
                x['password'], salt=b64dec(x['salt']), iteration_count=x['iterations'],
            ),
        }
        return lookup[username]

    s = m.make_server(
        auth_fn, channel_binding=x['s_channel_binding'], s_nonce=x['s_nonce'],
    )

    s.set_client_first(x['cfirst'])

    assert s.get_server_first() == x['sfirst']

    s.set_client_final(x['cfinal'])

    assert s.get_server_final() == x['sfinal']


def test_check_stage():
    with pytest.raises(
        ScramException,
        match='The next method to be called is get_server_first, not this method.',
    ):
        scramp._check_stage(
            scramp.ServerStage,
            scramp.ServerStage.set_client_first,
            scramp.ServerStage.get_server_final,
        )


@pytest.mark.parametrize(
    'client_first,s_nonce,channel_binding,use_binding,error_msg,server_error',
    [
        # Client requires channel binding but the server doesn't
        [
            'p=tls-unique,,n=user,r=rOprNGfwEbeRWgbNEkqO',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            "Received GS2 flag 'p' which indicates that the client "
            "requires channel binding, but the server does not: "
            "channel-binding-not-supported",
            'channel-binding-not-supported',
        ],
        # Client first is invalid
        [
            'junk',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            'The client sent a malformed first message: other-error',
            'other-error',
        ],
        # Client first bare message malformed
        [
            'n,,junk',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            "Malformed client first bare message. Attributes must be separated by a "
            "',' and each attribute must start with a letter followed by a '=': "
            "other-error",
            'other-error',
        ],
        # authzid must be empty
        [
            'n,anid,n=user,r=rOprNGfwEbeRWgbNEkqO',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            'The GS2 authzid anid must be empty: other-error',
            'other-error',
        ],
        # gs2-cbind-flag must be valid
        [
            'n=invalid,,n=user,r=rOprNGfwEbeRWgbNEkqO',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            "Received GS2 flag n=invalid which isn't recognized: other-error",
            'other-error',
        ],
    ],
)
def test_set_client_first_error(
    client_first, s_nonce, channel_binding, use_binding, error_msg, server_error,
):

    salt, stored_key, server_key = b'a', b'b', b'c'

    def auth_fn(username):
        lookup = {'user': (salt, stored_key, server_key)}
        return lookup[username]

    with pytest.raises(ScramException) as exc_info:
        _set_client_first(client_first, s_nonce, channel_binding, use_binding, auth_fn)

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


def test_set_client_first_error_auth_fn():

    def auth_fn(_):
        raise Exception()

    with pytest.raises(ScramException) as exc_info:
        _set_client_first(
            'n,,n=user,r=rOprNGfwEbeRWgbNEkqO',
            Nonce('%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0'),
            None,
            False,
            AuthFn(auth_fn),
        )

    assert str(exc_info.value) == 'Unknown user: unknown-user'
    assert str(exc_info.value.server_error) == 'unknown-user'


@pytest.mark.parametrize(
    'hf,client_final,nonce,stored_key,server_key,client_first_bare,server_first,'
    'channel_binding,use_binding,error_msg,server_error',
    # Malformed client final message
    [
        [
            hashlib.sha256,
            'junk',
            '%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
            b64dec('WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY='),
            b64dec('wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU='),
            'n=user,r=rOprNGfwEbeRWgbNEkqO',
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
            None,
            Gs2Header('n', None),
            "Malformed client final message. Attributes must be separated by a ',' "
            "and each attribute must start with a letter followed by a '=': "
            "other-error",
            'other-error',
        ],
        # Invalid client final
        [
            hashlib.sha256,
            'c=biws,r=invalid,p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=',
            '%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
            b64dec('WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY='),
            b64dec('wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU='),
            'n=user,r=rOprNGfwEbeRWgbNEkqO',
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
            None,
            Gs2Header('n', None),
            "Server nonce doesn't match.: other-error",
            'other-error',
        ],
        # Channel has invalid base 64 encoding, so b64dec() should fail
        [
            hashlib.sha256,
            'c=!!!,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            'p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=',
            '%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
            b64dec('WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY='),
            b64dec('wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU='),
            'n=user,r=rOprNGfwEbeRWgbNEkqO',
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
            None,
            Gs2Header('n', None),
            "The channel binding isn't correctly encoded: Invalid base 64 "
            "encoding '!!!': invalid-encoding: invalid-encoding",
            'invalid-encoding',
        ],
        # Even if channel binding isn't used, check it's valid
        [
            hashlib.sha256,
            'c=rOprNGfwEbeRWgbNEkqO,'
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            'p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=',
            'rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0',
            b64dec('WG5d8oPm3OtcPnkdi4Uo7BkeZkBFzpcXkuLmtbsT4qY='),
            b64dec('wfPLwcE6nTWhTAmQ7tl2KeoiWGPlZqQxSrmfPwDl2dU='),
            'n=user,r=rOprNGfwEbeRWgbNEkqO',
            'r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,'
            's=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096',
            None,
            Gs2Header('n', None),
            "The channel bindings don't match.: channel-bindings-dont-match",
            'channel-bindings-dont-match',
        ],
    ],
)
def test_set_client_final_error(
    hf,
    client_final,
    nonce,
    stored_key,
    server_key,
    client_first_bare,
    server_first,
    channel_binding,
    use_binding,
    error_msg,
    server_error,
):
    with pytest.raises(ScramException) as exc_info:
        _set_client_final(
            hf,
            client_final,
            nonce,
            stored_key,
            server_key,
            client_first_bare,
            server_first,
            channel_binding,
            use_binding,
        )

    assert str(exc_info.value) == error_msg
    assert str(exc_info.value.server_error) == server_error


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
    x = EXCHANGE_SCRAM_SHA_256
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
