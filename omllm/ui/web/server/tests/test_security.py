from ..security import build_allowed_hosts
from ..security import split_host_header


def test_split_host_header():
    assert split_host_header('localhost:8077') == ('localhost', 8077)
    assert split_host_header('LocalHost') == ('localhost', None)
    assert split_host_header('[::1]:8077') == ('::1', 8077)
    assert split_host_header('[::1]') == ('::1', None)

    for bad in ['', ':80', '[::1', 'a:b', 'fe80::1:8077', '[::1]x']:
        assert split_host_header(bad) is None, bad


def test_allowed_hosts():
    loopback = build_allowed_hosts('127.0.0.1', 8077)
    for ok in ['127.0.0.1:8077', 'localhost:8077', '[::1]:8077', '127.0.0.2:8077', '10.1.2.3:8077']:
        assert ok in loopback, ok
    for bad in ['evil.example:8077', 'localhost:8078', 'localhost', '127.0.0.1']:
        assert bad not in loopback, bad

    # A server bound to all interfaces answers to its addresses, but still not to names it does not know.
    wildcard = build_allowed_hosts('0.0.0.0', 8077)  # noqa: S104
    assert '192.168.1.5:8077' in wildcard
    assert 'evil.example:8077' not in wildcard

    named = build_allowed_hosts('box.lan', 80)
    assert 'box.lan' in named
    assert 'BOX.LAN:80' in named
    assert 'other.lan' not in named
