import pytest

from ....dbapi import DatabaseError
from ....dbapi import InterfaceError
from ....dbapi import connect


# This requires a line in pg_hba.conf that requires gss for the database test_og8000_gss


def test_gss(db_kwargs):
    db_kwargs['database'] = 'test_og8000_gss'

    # Should raise an exception saying gss isn't supported
    with pytest.raises((InterfaceError, DatabaseError)) as exc_info:
        connect(**db_kwargs)

    if isinstance(exc_info.value, DatabaseError):
        if exc_info.value.args[0].get('C') != '3D000':  # invalid_catalog_name
            raise exc_info.value
        pytest.skip("pg_hba.conf does not force gss auth for the database 'test_og8000_gss'")

    assert str(exc_info.value) == 'Authentication method 7 not supported by pg8000.'
