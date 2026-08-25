import contextlib
import os
import re
import time

from omcore import check


def parse_server_version(version):
    major = check.not_none(re.match(r'\d+', version)).group()  # leading digits in 17.0, 17rc1
    return int(major)


@contextlib.contextmanager
def set_tz(tz):
    """Sets the process timezone for the duration, restoring the previous one however the body exits."""

    orig_tz = os.environ.get('TZ')
    os.environ['TZ'] = tz
    time.tzset()
    try:
        yield
    finally:
        if orig_tz is None:
            del os.environ['TZ']
        else:
            os.environ['TZ'] = orig_tz
        time.tzset()
