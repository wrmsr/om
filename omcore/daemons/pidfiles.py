import contextlib
import contextvars
import dataclasses as dc
import datetime
import os
import typing as ta
import uuid

from ..formats.json import all as json
from ..lite import marshal as msh
from ..os.pidfiles.pidfile import Pidfile


##


DAEMON_PIDFILE_FORMAT: ta.Final = 'omcore.daemon.pidfile'
DAEMON_PIDFILE_FORMAT_VERSION: ta.Final = 1


@dc.dataclass(frozen=True)
class DaemonPidfileInfo:
    pid: int
    instance_id: str
    started_at: datetime.datetime

    format: ta.Literal['omcore.daemon.pidfile'] = DAEMON_PIDFILE_FORMAT
    format_version: ta.Literal[1] = DAEMON_PIDFILE_FORMAT_VERSION


class DaemonPidfileInfoError(ValueError):
    pass


def _validate_daemon_pidfile_info(info: DaemonPidfileInfo) -> DaemonPidfileInfo:
    if not isinstance(info.pid, int) or isinstance(info.pid, bool) or info.pid <= 0:
        raise DaemonPidfileInfoError(f'Invalid daemon pid: {info.pid!r}')
    if not isinstance(info.instance_id, str) or not info.instance_id:
        raise DaemonPidfileInfoError(f'Invalid daemon instance id: {info.instance_id!r}')
    if not isinstance(info.started_at, datetime.datetime) or info.started_at.utcoffset() != datetime.timedelta():
        raise DaemonPidfileInfoError(f'Daemon start time is not an aware UTC datetime: {info.started_at!r}')
    if info.format != DAEMON_PIDFILE_FORMAT:
        raise DaemonPidfileInfoError(f'Invalid daemon pidfile format: {info.format!r}')
    if type(info.format_version) is not int or info.format_version != DAEMON_PIDFILE_FORMAT_VERSION:
        raise DaemonPidfileInfoError(f'Invalid daemon pidfile format version: {info.format_version!r}')
    return info


def make_daemon_pidfile_info() -> DaemonPidfileInfo:
    return DaemonPidfileInfo(
        pid=os.getpid(),
        instance_id=uuid.uuid4().hex,
        started_at=datetime.datetime.now(datetime.UTC),
    )


def dumps_daemon_pidfile_info(info: DaemonPidfileInfo) -> str:
    suffix = json.dumps_compact(msh.marshal_obj(_validate_daemon_pidfile_info(info)))
    if '\n' in suffix or '\r' in suffix:
        raise DaemonPidfileInfoError('Daemon pidfile info did not encode to a single line')
    return suffix


def loads_daemon_pidfile_info(s: str) -> DaemonPidfileInfo:
    try:
        obj = json.loads(s)
        if not isinstance(obj, dict):
            raise TypeError(obj)

        if obj.get('format') != DAEMON_PIDFILE_FORMAT:
            raise DaemonPidfileInfoError(f'Invalid daemon pidfile format: {obj.get("format")!r}')
        format_version = obj.get('format_version')
        if type(format_version) is not int or format_version != DAEMON_PIDFILE_FORMAT_VERSION:
            raise DaemonPidfileInfoError(
                f'Invalid daemon pidfile format version: {format_version!r}',
            )
        if not isinstance(obj.get('pid'), int) or isinstance(obj.get('pid'), bool):
            raise DaemonPidfileInfoError(f'Invalid daemon pid: {obj.get("pid")!r}')
        if not isinstance(obj.get('instance_id'), str):
            raise DaemonPidfileInfoError(f'Invalid daemon instance id: {obj.get("instance_id")!r}')
        if not isinstance(obj.get('started_at'), str):
            raise DaemonPidfileInfoError(f'Invalid daemon start time: {obj.get("started_at")!r}')

        return _validate_daemon_pidfile_info(msh.unmarshal_obj(
            obj,
            DaemonPidfileInfo,
            msh.ObjMarshalOptions(non_strict_fields=True),
        ))

    except DaemonPidfileInfoError:
        raise
    except Exception as exc:
        raise DaemonPidfileInfoError(f'Invalid daemon pidfile info: {exc}') from exc


def parse_daemon_pidfile_info(raw: str) -> DaemonPidfileInfo | None:
    lines = raw.splitlines()
    if not lines:
        return None

    try:
        pid = int(lines[0].strip())
    except ValueError as exc:
        raise DaemonPidfileInfoError(f'Invalid daemon pid line: {lines[0]!r}') from exc

    if len(lines) == 1:
        return None
    if len(lines) != 2:
        raise DaemonPidfileInfoError(f'Expected two daemon pidfile lines, got {len(lines)}')

    info = loads_daemon_pidfile_info(lines[1])
    if info.pid != pid:
        raise DaemonPidfileInfoError(
            f'Daemon pid line {pid} does not match info pid {info.pid}',
        )
    return info


def read_daemon_pidfile_info(pidfile: Pidfile) -> DaemonPidfileInfo | None:
    if (raw := pidfile.read_raw()) is None:
        return None
    return parse_daemon_pidfile_info(raw)


##


_CURRENT_DAEMON_PIDFILE_INFO: contextvars.ContextVar[DaemonPidfileInfo | None] = contextvars.ContextVar(
    f'{__name__}._CURRENT_DAEMON_PIDFILE_INFO',
    default=None,
)


def current_daemon_pidfile_info() -> DaemonPidfileInfo | None:
    return _CURRENT_DAEMON_PIDFILE_INFO.get()


@contextlib.contextmanager
def daemon_pidfile_info_context(info: DaemonPidfileInfo) -> ta.Iterator[None]:
    token = _CURRENT_DAEMON_PIDFILE_INFO.set(info)
    try:
        yield
    finally:
        _CURRENT_DAEMON_PIDFILE_INFO.reset(token)
