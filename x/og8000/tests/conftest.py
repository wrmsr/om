import pytest

from .. import native
from .dbs import DB_KWARGS


@pytest.fixture(scope='session')
def db_setup():
    with native.Connection(**DB_KWARGS) as con:
        con.run('CREATE EXTENSION IF NOT EXISTS hstore')


@pytest.fixture(scope='class')
def db_kwargs(db_setup):
    return dict(DB_KWARGS)
