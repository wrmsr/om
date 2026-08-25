import re

from omcore import check


def mysql_server_is(conn, version_tuple):
    """
    Returns True if the given connection is on the version given or greater.

    This only checks the server version string provided when the connection is established, therefore any check for a
    version tuple greater than (5, 5, 5) will always fail on MariaDB, as it always starts with 5.5.5, e.g.
    5.5.5-10.7.1-MariaDB-1:10.7.1+maria~focal.
    """

    server_version = conn.get_server_info()
    server_version_tuple = tuple(
        (int(dig) if dig is not None else 0)
        for dig in check.not_none(re.match(r'(\d+)\.(\d+)\.(\d+)', server_version)).group(1, 2, 3)
    )
    return server_version_tuple >= version_tuple


def get_mysql_vendor(conn):
    server_version = conn.get_server_info()

    if 'MariaDB' in server_version:
        return 'mariadb'

    return 'mysql'
