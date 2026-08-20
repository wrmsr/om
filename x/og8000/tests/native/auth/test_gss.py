import pytest

from ....exceptions import DatabaseError
from ....native import Connection
from ....native import InterfaceError


def test_gss(db_kwargs):
    """
    This requires a line in pg_hba.conf that requires gss for the database
    pg8000_gss
    """

    db_kwargs['database'] = 'pg8000_gss'

    # Should raise an exception saying gss isn't supported
    with pytest.raises((InterfaceError, DatabaseError)) as exc_info:
        Connection(**db_kwargs)

    if isinstance(exc_info.value, DatabaseError):
        if exc_info.value.args[0].get('C') != '3D000':  # invalid_catalog_name
            raise exc_info.value
        pytest.skip("pg_hba.conf does not force gss auth for the database 'pg8000_gss'")

    assert str(exc_info.value) == 'Authentication method 7 not supported by pg8000.'
