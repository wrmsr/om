import socket
import ssl
import typing as ta

from ..err import OperationalError


SslContextArg: ta.TypeAlias = ssl.SSLContext | ta.Mapping[str, ta.Any] | None


##


def make_ssl_context(arg: SslContextArg) -> ssl.SSLContext:
    if isinstance(arg, ssl.SSLContext):
        return arg
    sslp = dict(arg or {})
    ca = sslp.get('ca')
    capath = sslp.get('capath')
    hasnoca = ca is None and capath is None
    ctx = ssl.create_default_context(cafile=ca, capath=capath)
    # MySQL's automatically generated self signed certificates don't pass 3.13+ strict verification.
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    ctx.check_hostname = not hasnoca and sslp.get('check_hostname', True)
    verify = sslp.get('verify_mode')
    if verify is None:
        ctx.verify_mode = ssl.CERT_NONE if hasnoca else ssl.CERT_REQUIRED
    elif isinstance(verify, bool):
        ctx.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
    else:
        ctx.verify_mode = {
            'none': ssl.CERT_NONE,
            'optional': ssl.CERT_OPTIONAL,
            'required': ssl.CERT_REQUIRED,
        }.get(str(verify).lower(), ssl.CERT_NONE if hasnoca else ssl.CERT_REQUIRED)
    if 'cert' in sslp:
        ctx.load_cert_chain(sslp['cert'], keyfile=sslp.get('key'), password=sslp.get('password'))
    if 'cipher' in sslp:
        ctx.set_ciphers(sslp['cipher'])
    return ctx


def connect_socket(
        *,
        unix_socket: str | None = None,
        host: str | None = None,
        port: int = 3306,
        connect_timeout: float | None = None,
        bind_address: str | None = None,
) -> socket.socket:
    try:
        if unix_socket is not None:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(connect_timeout)
            sock.connect(unix_socket)
        else:
            source = (bind_address, 0) if bind_address is not None else None
            sock = socket.create_connection((host, port), connect_timeout, source_address=source)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except OSError as e:
        raise OperationalError(2003, f"Can't connect to MySQL server on {host!r} ({e})") from e
    sock.settimeout(None)
    return sock
