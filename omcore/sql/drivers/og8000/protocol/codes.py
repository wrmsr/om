"""Wire-level constants of the PostgreSQL frontend/backend protocol, version 3.0."""
import enum


##


PROTOCOL_VERSION = 196608  # 3.0
SSL_REQUEST_CODE = 80877103

NULL_BYTE = b'\x00'


##
# Backend message type codes


AUTHENTICATION = b'R'
BACKEND_KEY_DATA = b'K'
BIND_COMPLETE = b'2'
CLOSE_COMPLETE = b'3'
COMMAND_COMPLETE = b'C'
COPY_DATA = b'd'
COPY_DONE = b'c'
COPY_IN_RESPONSE = b'G'
COPY_OUT_RESPONSE = b'H'
DATA_ROW = b'D'
EMPTY_QUERY_RESPONSE = b'I'
ERROR_RESPONSE = b'E'
NO_DATA = b'n'
NOTICE_RESPONSE = b'N'
NOTIFICATION_RESPONSE = b'A'
PARAMETER_DESCRIPTION = b't'
PARAMETER_STATUS = b'S'
PARSE_COMPLETE = b'1'
PORTAL_SUSPENDED = b's'
READY_FOR_QUERY = b'Z'
ROW_DESCRIPTION = b'T'


##
# Frontend message type codes


BIND = b'B'
CLOSE = b'C'
COPY_FAIL = b'f'
DESCRIBE = b'D'
EXECUTE = b'E'
FLUSH = b'H'
PARSE = b'P'
PASSWORD = b'p'
QUERY = b'Q'
SYNC = b'S'
TERMINATE = b'X'


##


class AuthenticationCode(enum.IntEnum):
    OK = 0
    KERBEROS_V5 = 2
    CLEARTEXT_PASSWORD = 3
    MD5_PASSWORD = 5
    SCM_CREDENTIAL = 6
    GSS = 7
    GSS_CONTINUE = 8
    SSPI = 9
    SASL = 10
    SASL_CONTINUE = 11
    SASL_FINAL = 12


class DescribeKind(enum.Enum):
    STATEMENT = b'S'
    PORTAL = b'P'


class TransactionStatus(enum.Enum):
    IDLE = b'I'
    IN_TRANSACTION = b'T'
    IN_FAILED_TRANSACTION = b'E'


class ErrorField(enum.StrEnum):
    """Keys of ErrorResponse / NoticeResponse field mappings."""

    SEVERITY = 'S'
    SEVERITY_NONLOCALIZED = 'V'
    CODE = 'C'
    MESSAGE = 'M'
    DETAIL = 'D'
    HINT = 'H'
    POSITION = 'P'
    INTERNAL_POSITION = 'p'
    INTERNAL_QUERY = 'q'
    WHERE = 'W'
    SCHEMA_NAME = 's'
    TABLE_NAME = 't'
    COLUMN_NAME = 'c'
    DATA_TYPE_NAME = 'd'
    CONSTRAINT_NAME = 'n'
    FILE = 'F'
    LINE = 'L'
    ROUTINE = 'R'
