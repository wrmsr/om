import datetime

import pytest

from ...formats.json import all as json
from ...lite import marshal as msh
from ..pidfiles import DAEMON_PIDFILE_FORMAT
from ..pidfiles import DAEMON_PIDFILE_FORMAT_VERSION
from ..pidfiles import DaemonPidfileInfo
from ..pidfiles import DaemonPidfileInfoError
from ..pidfiles import dumps_daemon_pidfile_info
from ..pidfiles import loads_daemon_pidfile_info
from ..pidfiles import parse_daemon_pidfile_info


##


def _info() -> DaemonPidfileInfo:
    return DaemonPidfileInfo(
        pid=12345,
        instance_id='0123456789abcdef',
        started_at=datetime.datetime(2026, 8, 10, 12, 34, 56, 789, tzinfo=datetime.UTC),
    )


def test_daemon_pidfile_info_is_lite_marshal_compatible_compact_json():
    info = _info()

    marshaled = msh.marshal_obj(info)
    unmarshaled: DaemonPidfileInfo = msh.unmarshal_obj(marshaled, DaemonPidfileInfo)
    assert unmarshaled == info

    suffix = dumps_daemon_pidfile_info(info)
    assert '\n' not in suffix
    assert '\r' not in suffix
    assert json.loads(suffix) == {
        'pid': 12345,
        'instance_id': '0123456789abcdef',
        'started_at': '2026-08-10T12:34:56.000789+00:00',
        'format': DAEMON_PIDFILE_FORMAT,
        'format_version': DAEMON_PIDFILE_FORMAT_VERSION,
    }
    assert loads_daemon_pidfile_info(suffix) == info


def test_daemon_pidfile_info_parser_supports_legacy_and_future_optional_fields():
    info = _info()
    suffix_obj = json.loads(dumps_daemon_pidfile_info(info))
    suffix_obj['future_optional_field'] = {'ignored': True}

    assert parse_daemon_pidfile_info('12345\n') is None
    assert parse_daemon_pidfile_info(f'12345\n{json.dumps_compact(suffix_obj)}\n') == info


@pytest.mark.parametrize(('raw', 'match'), [
    ('not-a-pid\n', 'Invalid daemon pid line'),
    ('12346\n' + dumps_daemon_pidfile_info(_info()) + '\n', 'does not match'),
    ('12345\n{}\n', 'Invalid daemon pidfile format'),
    ('12345\n{}\nextra\n', 'Expected two daemon pidfile lines'),
])
def test_daemon_pidfile_info_parser_rejects_invalid_records(raw, match):
    with pytest.raises(DaemonPidfileInfoError, match=match):
        parse_daemon_pidfile_info(raw)


def test_daemon_pidfile_info_requires_aware_utc_start_time():
    with pytest.raises(DaemonPidfileInfoError, match='aware UTC'):
        dumps_daemon_pidfile_info(DaemonPidfileInfo(
            pid=12345,
            instance_id='0123456789abcdef',
            started_at=datetime.datetime(2026, 8, 10),  # noqa: DTZ001
        ))
