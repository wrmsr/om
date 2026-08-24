"""
Backwards compatible connection surface. The Connection class and connect() are thin aliases over the synchronous core
connection; the real implementation lives in og8000-style `core` and `protocol` packages.
"""
import os.path
import typing as ta
import warnings

from . import err
from .core.sync import SyncConnection
from .cursors import Cursor


# If set (a plugin name), used as the initial client auth plugin instead of the server's default. For testing the
# auth-switch path.
_DEFAULT_AUTH_PLUGIN: str | None = None


##


class Connection(SyncConnection):
    """A synchronous MySQL connection. See `core.sync.SyncConnection` for the implementation."""

    Warning = err.Warning
    Error = err.Error
    InterfaceError = err.InterfaceError
    DatabaseError = err.DatabaseError
    DataError = err.DataError
    OperationalError = err.OperationalError
    IntegrityError = err.IntegrityError
    InternalError = err.InternalError
    ProgrammingError = err.ProgrammingError
    NotSupportedError = err.NotSupportedError

    def __init__(
            self,
            *,
            cursorclass: type = Cursor,
            autocommit: bool | None = False,
            init_command: str | None = None,
            sql_mode: str | None = None,
            read_default_file: str | None = None,
            read_default_group: str | None = None,
            read_timeout: float | None = None,
            write_timeout: float | None = None,
            auth_plugin_map: ta.Mapping[ta.Any, ta.Any] | None = None,
            ssl_ca: str | None = None,
            ssl_cert: str | None = None,
            ssl_key: str | None = None,
            ssl_key_password: str | None = None,
            ssl_verify_cert: ta.Any = None,
            ssl_verify_identity: ta.Any = None,
            defer_connect: bool = False,
            passwd: str | bytes | None = None,  # deprecated alias for password
            db: str | bytes | None = None,  # deprecated alias for database
            **kwargs: ta.Any,
    ) -> None:
        if passwd is not None and not kwargs.get('password'):
            kwargs['password'] = passwd
        if db is not None and kwargs.get('database') is None:
            kwargs['database'] = db

        if read_default_file or read_default_group:
            _apply_option_file(kwargs, read_default_file, read_default_group)

        # read_timeout / write_timeout / auth_plugin_map are accepted for compatibility but not yet wired through.
        _ = (read_timeout, write_timeout, auth_plugin_map)

        if ssl_ca or ssl_cert or ssl_key or ssl_verify_cert or ssl_verify_identity:
            ssl_arg: ta.Any = {
                'ca': ssl_ca,
                'check_hostname': bool(ssl_verify_identity),
                'verify_mode': ssl_verify_cert if ssl_verify_cert is not None else False,
            }
            if ssl_cert is not None:
                ssl_arg['cert'] = ssl_cert
            if ssl_key is not None:
                ssl_arg['key'] = ssl_key
            if ssl_key_password is not None:
                ssl_arg['password'] = ssl_key_password
            kwargs['ssl'] = ssl_arg

        if _DEFAULT_AUTH_PLUGIN is not None:
            kwargs['force_auth_plugin'] = _DEFAULT_AUTH_PLUGIN

        # Set before super().__init__, as it may connect immediately and run _after_connect.
        self.cursorclass = cursorclass
        self._autocommit_mode = autocommit
        self._init_command = init_command
        self._sql_mode = sql_mode

        super().__init__(defer_connect=defer_connect, **kwargs)

    def _after_connect(self) -> None:
        self.set_character_set(self._charset, self._collation)

        if self._sql_mode is not None:
            with self.cursor() as c:
                c.execute('SET sql_mode=%s', (self._sql_mode,))

        if self._init_command is not None:
            with self.cursor() as c:
                c.execute(self._init_command)

        if self._autocommit_mode is not None:
            self.autocommit(self._autocommit_mode)

    def autocommit(self, value: bool) -> None:  # noqa: FBT001
        self._autocommit_mode = bool(value)
        if bool(value) != self.get_autocommit():
            self.query(f'SET AUTOCOMMIT = {1 if value else 0}')

    def cursor(self, cursor: type | None = None) -> ta.Any:
        return (cursor or self.cursorclass)(self)

    def set_character_set(self, charset: str, collation: str | None = None) -> None:
        query = f'SET NAMES {charset}' + (f' COLLATE {collation}' if collation else '')
        self.query(query)
        self._session.set_charset(charset)
        self._charset = charset
        self._collation = collation
        self._encoding = self._session.encoding

    def show_warnings(self) -> ta.Sequence[ta.Any]:
        self.query('SHOW WARNINGS')
        rows = self._result.rows if self._result is not None else None
        return rows if rows is not None else ()

    def set_charset(self, charset: str) -> None:
        warnings.warn("'set_charset' is deprecated, use 'set_character_set' instead", DeprecationWarning, stacklevel=2)
        self.set_character_set(charset)

    def kill(self, thread_id: int) -> None:
        if not isinstance(thread_id, int):
            raise TypeError('thread_id must be an integer')
        self.query(f'KILL {thread_id:d}')

    @property
    def encoders(self) -> ta.Mapping[ta.Any, ta.Any]:
        return self._encoders

    @property
    def decoders(self) -> ta.Mapping[int, ta.Any]:
        return self._decoders

    def insert_id(self) -> int:
        return self._result.insert_id if self._result is not None else 0

    def affected_rows(self) -> int:
        return self._result.affected_rows if self._result is not None else 0


def _apply_option_file(
        kwargs: ta.MutableMapping[str, ta.Any],
        read_default_file: str | None,
        read_default_group: str | None,
) -> None:
    from .optionfile import Parser  # noqa

    path = read_default_file or ('/etc/my.cnf')
    group = read_default_group or 'client'
    cfg = Parser()
    cfg.read(os.path.expanduser(path))

    for key, arg in [
        ('user', 'user'),
        ('password', 'password'),
        ('host', 'host'),
        ('database', 'database'),
        ('socket', 'unix_socket'),
        ('port', 'port'),
        ('bind-address', 'bind_address'),
        ('default-character-set', 'charset'),
    ]:
        if not kwargs.get(arg):
            try:
                value = cfg.get(group, key)
            except Exception:  # noqa: BLE001,S112
                continue
            kwargs[arg] = int(value) if arg == 'port' else value


def connect(**kwargs: ta.Any) -> Connection:
    return Connection(**kwargs)
