"""
What keeps everything but the page's own scripts away from the api. This is the frontend to an agent which may run
commands, served on a port any local process can reach - and through which any web page open in a local browser can
try to reach it too.

  - The Host header must name this server - by an address, or by a name it knows to be its own - so that a page
    elsewhere cannot reach it by rebinding a name of its own to the server's address.
  - An Origin header, where a browser sends one, must be this server's.
  - An api request must carry the token which the page this server serves is given - which a page served from anywhere
    else cannot read, and which, being a custom header, a page cannot make a cross-origin request carry without the
    preflight the server never approves.

None of this defends against something which can already read the page: any local user, for one.
"""
import hmac
import ipaddress
import secrets
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import typedvalues as tv
from omcore.http import asgi


##


TOKEN_HEADER = b'x-omllm-web-token'


class WebToken(tv.UniqueScalarTypedValue[str], final=True):
    def __post_init__(self) -> None:
        check.non_empty_str(self.v)

    @classmethod
    def generate(cls) -> WebToken:
        return cls(secrets.token_urlsafe(24))


#


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def is_loopback_host(host: str) -> bool:
    if host == 'localhost':
        return True

    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def split_host_header(v: str) -> tuple[str, int | None] | None:
    """A Host header's host and port, the brackets of an ipv6 address dropped - or None, for a malformed one."""

    if v.startswith('['):
        host, sep, rest = v[1:].partition(']')
        if not sep:
            return None
    else:
        host, sep, port = v.partition(':')
        rest = sep + port

    if not host:
        return None

    if not rest:
        return host.lower(), None

    if not rest.startswith(':') or not rest[1:].isdigit():
        return None

    return host.lower(), int(rest[1:])


@ta.final
@dc.dataclass(frozen=True)
class AllowedHosts:
    """
    The Host headers a server answers to: any naming it by an ip address - which dns rebinding, needing a name of its
    own to rebind, cannot make a browser send - and those naming it by one of a few names it knows to be its own.
    """

    port: int
    names: ta.AbstractSet[str]

    def __contains__(self, header: str) -> bool:
        if (split := split_host_header(header)) is None:
            return False

        host, port = split
        if (port if port is not None else 80) != self.port:
            return False

        return host in self.names or _is_ip_address(host)


def build_allowed_hosts(host: str, port: int) -> AllowedHosts:
    names = {'localhost'}
    if not _is_ip_address(host):
        names.add(host.lower())

    return AllowedHosts(port, frozenset(names))


#


class WebRequestRejectedError(Exception):
    pass


class WebRequestGuard:
    def __init__(
            self,
            *,
            token: WebToken,
            allowed_hosts: AllowedHosts,
    ) -> None:
        super().__init__()

        self._token = token
        self._allowed_hosts = allowed_hosts

    @staticmethod
    def _header(scope: asgi.Scope, name: bytes) -> bytes | None:
        for k, v in scope['headers']:
            if k.lower() == name:
                return v
        return None

    def check(self, scope: asgi.Scope, *, api: bool) -> None:
        """Raises WebRequestRejectedError for a request not to be answered."""

        host = (self._header(scope, b'host') or b'').decode('latin-1')
        if host not in self._allowed_hosts:
            raise WebRequestRejectedError(f'host: {host!r}')

        if (origin := self._header(scope, b'origin')) is not None:
            if origin.decode('latin-1') != f'http://{host}':
                raise WebRequestRejectedError(f'origin: {origin!r}')

        if api:
            token = self._header(scope, TOKEN_HEADER) or b''
            if not hmac.compare_digest(token, self._token.v.encode('ascii')):
                raise WebRequestRejectedError('token')
