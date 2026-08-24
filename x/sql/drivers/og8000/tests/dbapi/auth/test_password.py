import pytest

from ....dbapi import DatabaseError
from ....dbapi import connect


# This requires a line in pg_hba.conf that requires 'password' for the
# database test_og8000_password


def test_password(db_kwargs):
    db_kwargs['database'] = 'test_og8000_password'

    # Should only raise an exception saying db doesn't exist
    with pytest.raises(DatabaseError, match='3D000'):
        with connect(**db_kwargs):
            pass
