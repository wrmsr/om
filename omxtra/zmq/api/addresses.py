"""
Pure endpoint address values and parsing. No filesystem or network operations happen here.

Supported forms:
 - `tcp://host:port`, with `host` a name, an IPv4 literal, or a bracketed IPv6 literal. For binding only, `host` may be
   `*` (all interfaces) and `port` may be `*` or `0` (an ephemeral port, resolved by the bind).
 - `ipc:///absolute/path` - a filesystem Unix-domain stream socket. Relative, abstract, and wildcard paths are rejected.
"""
import ipaddress
import os

from omcore import dataclasses as dc
from omcore import lang

from .errors import InvalidAddressError


type AnyAddress = str | Address


##


# The smallest Unix-domain socket path limit among supported platforms: 104 bytes including the terminating NUL on
# macOS, against 108 on Linux.
MAX_IPC_PATH_BYTES = 103


class Address(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class TcpAddress(Address):
    host: str
    port: int

    def __post_init__(self) -> None:
        if not self.host or any(c.isspace() or c in '/[]' for c in self.host):
            raise InvalidAddressError(f'invalid tcp host: {self.host!r}')
        if ':' in self.host:
            try:
                ipaddress.IPv6Address(self.host)
            except ValueError as e:
                raise InvalidAddressError(f'invalid tcp IPv6 host: {self.host!r}') from e
        if not (0 <= self.port <= 0xffff):
            raise InvalidAddressError(f'invalid tcp port: {self.port!r}')

    @property
    def is_ipv6(self) -> bool:
        return ':' in self.host

    @property
    def is_wildcard_host(self) -> bool:
        return self.host == '*'

    @property
    def is_ephemeral(self) -> bool:
        return self.port == 0

    @property
    def is_connectable(self) -> bool:
        return not (self.is_wildcard_host or self.is_ephemeral)

    def __str__(self) -> str:
        host = f'[{self.host}]' if self.is_ipv6 else self.host
        return f'tcp://{host}:{self.port}'


@dc.dataclass(frozen=True)
class IpcAddress(Address):
    path: str

    def __post_init__(self) -> None:
        if not self.path.startswith('/'):
            raise InvalidAddressError(f'ipc path must be absolute: {self.path!r}')
        if '\0' in self.path:
            raise InvalidAddressError('ipc path must not contain NUL')
        if len(os.fsencode(self.path)) > MAX_IPC_PATH_BYTES:
            raise InvalidAddressError(f'ipc path exceeds {MAX_IPC_PATH_BYTES} bytes: {self.path!r}')

    def __str__(self) -> str:
        return f'ipc://{self.path}'


##


def _parse_tcp(rest: str) -> TcpAddress:
    if rest.startswith('['):
        host, sep, tail = rest[1:].partition(']')
        if not sep or not tail.startswith(':'):
            raise InvalidAddressError(f'invalid tcp address: tcp://{rest}')
        port_str = tail[1:]
    else:
        host, sep, port_str = rest.rpartition(':')
        if not sep:
            raise InvalidAddressError(f'tcp address requires a port: tcp://{rest}')
        if ':' in host:
            raise InvalidAddressError(f'IPv6 tcp hosts must be bracketed: tcp://{rest}')

    if port_str == '*':
        port = 0
    elif port_str.isdigit() and port_str.isascii():
        port = int(port_str)
    else:
        raise InvalidAddressError(f'invalid tcp port: {port_str!r}')

    return TcpAddress(host, port)


def parse_address(address: AnyAddress) -> Address:
    if isinstance(address, Address):
        return address
    if not isinstance(address, str):
        raise InvalidAddressError(f'address must be a str, not {type(address).__name__}')

    scheme, sep, rest = address.partition('://')
    if not sep:
        raise InvalidAddressError(f'address requires a scheme: {address!r}')

    if scheme == 'tcp':
        return _parse_tcp(rest)
    elif scheme == 'ipc':
        return IpcAddress(rest)
    else:
        raise InvalidAddressError(f'unsupported address scheme: {scheme!r}')


def check_connectable(address: AnyAddress) -> Address:
    addr = parse_address(address)
    if isinstance(addr, TcpAddress) and not addr.is_connectable:
        raise InvalidAddressError(f'cannot connect to a wildcard or ephemeral address: {addr}')
    return addr


def check_bindable(address: AnyAddress) -> Address:
    return parse_address(address)
