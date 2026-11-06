from ..config import WebConfig


##


def test_no_auth_arguments():
    assert WebConfig().no_auth is False
    assert WebConfig.parse_from_arguments([]).no_auth is False
    assert WebConfig.parse_from_arguments(['--no-auth']).no_auth is True
