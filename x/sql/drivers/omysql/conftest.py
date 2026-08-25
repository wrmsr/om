# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import types
import typing as ta
import urllib.parse

import pytest

from omcore import check
from omcore.sql.tests.harness import HarnessDbs
from omcore import sql

from . import dbapi


# The server's CA certificate, for the SSL tests.
# TODO: extract / generate dynamically
@pytest.fixture(scope='session')
def ca_pem() -> str:
    return 'test_omysql_ca.pem'


class Database(ta.TypedDict):
    host: str
    port: int
    user: str
    passwd: str
    database: str

    use_unicode: ta.NotRequired[bool]
    local_infile: ta.NotRequired[bool]


@pytest.fixture(scope='session')
def _databases(harness) -> ta.Sequence[Database]:
    spec = harness[HarnessDbs].specs()['mysql']
    url = check.isinstance(spec.loc, sql.UrlDbLoc)
    pu = urllib.parse.urlparse(check.isinstance(url.url, str))

    dbs = [
        {
            **(base := {
                'host': pu.hostname,
                'port': pu.port,
                'user': pu.username,
                'passwd': pu.password,
            }),
            'database': 'test_omysql_1',
            'use_unicode': True,
            'local_infile': True,
        },
        {
            **base,
            'database': 'test_omysql_2',
        },
    ]

    return list(map(types.MappingProxyType, dbs))  # type: ignore


@pytest.fixture(scope='session')
def mysql_server_params(_databases):
    """
    Connection parameters for the MySQL server itself, with no database selected. Root credentials, per the config.
    """

    return {k: v for k, v in _databases[0].items() if k != 'database'}


@pytest.fixture(scope='session')
def mysql_bootstrap(_databases, mysql_server_params):
    """
    Creates the configured test _databases and enables local_infile, undoing both afterwards. Everything it does is
    idempotent, so leftovers from a previous run killed at any point are absorbed.
    """

    con = dbapi.connect(**mysql_server_params)
    try:
        cur = con.cursor()

        cur.execute('select @@global.local_infile')
        prior_local_infile = bool(cur.fetchone()[0])
        cur.execute('set global local_infile = 1')

        for params in _databases:
            cur.execute(f'create database if not exists `{params["database"]}`')

        yield

        for params in _databases:
            cur.execute(f'drop database if exists `{params["database"]}`')

        cur.execute(f'set global local_infile = {1 if prior_local_infile else 0}')
    finally:
        con.close()


@pytest.fixture
def databases(_databases, mysql_bootstrap):
    """
    Fresh copies of the connection parameter sets for the configured test databases. The canonical way for tests to
    obtain them: the first entry is the primary test database, the second a secondary one.
    """

    return [dict(params) for params in _databases]
