import ssl

import pytest

from ....native import Connection


def test_ssl(db_kwargs, pg_server_ssl):
    if not pg_server_ssl:
        pytest.skip('server does not accept SSL')

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    db_kwargs['ssl_context'] = context

    with Connection(**db_kwargs):
        pass
