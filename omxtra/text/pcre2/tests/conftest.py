import pytest

from . import capiclients


##


@pytest.fixture(scope='session')
def capiclient_file(tmp_path_factory):
    """The capi capsule's test client, compiled into a temporary directory the first time a test asks for it."""

    return capiclients.build_capiclient(str(tmp_path_factory.mktemp('pcre2-capiclient')))


@pytest.fixture(scope='session')
def capiclient(capiclient_file):
    """The capi capsule's test client, loaded into this process."""

    return capiclients.load_capiclient(capiclient_file)
