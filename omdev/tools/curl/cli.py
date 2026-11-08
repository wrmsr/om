"""A small pipeline-backed HTTP command line client."""
import argparse
import asyncio
import base64
import contextlib
import http
import json
import math
import os
import re
import ssl
import sys
import typing as ta
import urllib.parse

from omcore.http.clients.base import HttpClientError
from omcore.http.clients.base import HttpClientRequest
from omcore.http.clients.pipelines.asyncio import AsyncioIoPipelineAsyncHttpClient
from omcore.http.clients.pipelines.sync import IoPipelineHttpClient
from omcore.http.headers import HttpHeaders
from omcore.io.pipelines.ssl.handlers import SslIoPipelineHandler

from .streaming import stream_async_request
from .streaming import stream_sync_request


##


_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Send an HTTP request with the omcore I/O pipeline clients.',
        epilog='Examples: curl URL; curl -X POST --json \'{"a":1}\' URL; '
        'curl --data-file - -o reply.bin URL',
    )
    parser.add_argument('url')
    parser.add_argument('--asyncio', action='store_true', help='use the asyncio pipeline client')
    parser.add_argument('-X', '--method', help='HTTP method (defaults to GET or POST with input)')
    parser.add_argument('-I', '--head', action='store_true', help='send HEAD and print response headers')
    parser.add_argument('-H', '--header', action='append', default=[], metavar='NAME: VALUE')
    parser.add_argument('-q', '--query', action='append', default=[], metavar='NAME=VALUE')
    parser.add_argument('-A', '--user-agent')
    parser.add_argument('--accept')
    parser.add_argument('--content-type')
    parser.add_argument('--compressed', action='store_true', help='request gzip compression')
    parser.add_argument('--raw', action='store_true', help='disable response decompression')

    auth = parser.add_mutually_exclusive_group()
    auth.add_argument('-u', '--basic', metavar='USER:PASS')
    auth.add_argument('--bearer', metavar='TOKEN')

    data = parser.add_mutually_exclusive_group()
    data.add_argument('-d', '--data', help='send the given UTF-8 text')
    data.add_argument('--data-file', metavar='PATH', help='stream a file, or - for stdin')
    data.add_argument('--json', help='send JSON text')
    data.add_argument('-F', '--form', action='append', metavar='NAME=VALUE', help='form field; repeatable')
    parser.add_argument('--trailer', action='append', default=[], metavar='NAME: VALUE')

    parser.add_argument('-i', '--include', action='store_true', help='include status and headers in output')
    parser.add_argument('-o', '--output', metavar='PATH', help='write output to file, or - for stdout')
    parser.add_argument('--no-body', action='store_true', help='discard the response body')
    parser.add_argument('--pretty', action='store_true', help='buffer and pretty-print a JSON response')
    parser.add_argument('--show-status', action='store_true', help='print the status to stderr')
    parser.add_argument('--fail', action='store_true', help='exit with code 22 on HTTP status >= 400')
    parser.add_argument('--timeout', type=float, default=60., help='request deadline in seconds')
    parser.add_argument('--connect-timeout', type=float, default=3., help='connection deadline in seconds')
    parser.add_argument('--chunk-size', type=int, default=64 * 1024, help='stream I/O chunk size')
    tls = parser.add_mutually_exclusive_group()
    tls.add_argument('--ca-file', metavar='PATH', help='CA certificate bundle for HTTPS')
    tls.add_argument('-k', '--insecure', action='store_true', help='disable HTTPS certificate checks')
    return parser


def _pair(value: str, separator: str, kind: str) -> tuple[str, str]:
    name, found, content = value.partition(separator)
    if not found or not name:
        raise ValueError(f'{kind} must be NAME{separator}VALUE: {value!r}')
    return name, content


def _header(value: str) -> tuple[str, str]:
    name, content = _pair(value, ':', 'header')
    content = content.lstrip(' \t')
    if not _HEADER_NAME.fullmatch(name):
        raise ValueError(f'invalid HTTP header name: {name!r}')
    if any(c in content for c in '\r\n\0'):
        raise ValueError(f'invalid HTTP header value for {name!r}')
    content.encode('latin-1')
    return name, content


def _make_url(url: str, query: ta.Sequence[str]) -> str:
    split = urllib.parse.urlsplit(url)
    if split.scheme not in ('http', 'https') or not split.netloc:
        raise ValueError('URL must be an absolute http:// or https:// URL')
    if split.fragment:
        raise ValueError('URL fragments are not sent in HTTP requests')
    if query:
        pairs = [_pair(item, '=', 'query parameter') for item in query]
        extra = urllib.parse.urlencode(pairs)
        split = split._replace(query='&'.join(part for part in (split.query, extra) if part))
    return urllib.parse.urlunsplit(split)


def _make_request(args: argparse.Namespace) -> tuple[HttpClientRequest, HttpHeaders]:
    if args.head and args.method and args.method.upper() != 'HEAD':
        raise ValueError('--head cannot be combined with a different --method')
    if args.head and any(value is not None for value in (args.data, args.data_file, args.json, args.form)):
        raise ValueError('HEAD cannot have an input body')
    if args.trailer and args.data_file is None:
        raise ValueError('--trailer requires --data-file')
    if args.pretty and args.no_body:
        raise ValueError('--pretty cannot be combined with --no-body')
    if not math.isfinite(args.timeout) or not math.isfinite(args.connect_timeout) or (
        args.timeout <= 0 or args.connect_timeout <= 0 or args.chunk_size <= 0
    ):
        raise ValueError('timeouts and chunk size must be positive')

    headers = [_header(value) for value in args.header]
    if args.user_agent:
        headers.append(_header(f'User-Agent: {args.user_agent}'))
    if args.accept:
        headers.append(_header(f'Accept: {args.accept}'))
    if args.content_type:
        headers.append(_header(f'Content-Type: {args.content_type}'))
    if args.basic is not None:
        if ':' not in args.basic:
            raise ValueError('--basic requires USER:PASS')
        token = base64.b64encode(args.basic.encode('utf-8')).decode('ascii')
        headers.append(('Authorization', f'Basic {token}'))
    if args.bearer is not None:
        headers.append(_header(f'Authorization: Bearer {args.bearer}'))

    body: bytes | None = None
    body_content_type: str | None = None
    if args.data is not None:
        body = args.data.encode('utf-8')
    elif args.json is not None:
        json.loads(args.json)
        body = args.json.encode('utf-8')
        body_content_type = 'application/json'
    elif args.form is not None:
        body = urllib.parse.urlencode([_pair(value, '=', 'form field') for value in args.form]).encode('ascii')
        body_content_type = 'application/x-www-form-urlencoded'

    hdrs = HttpHeaders(headers)
    hdrs = hdrs.update(
        ('Content-Type', body_content_type),
        ('Accept-Encoding', 'gzip' if args.compressed else None),
        if_present='skip',
    )
    if body is not None or args.data_file is not None:
        if 'content-length' in hdrs or 'transfer-encoding' in hdrs:
            raise ValueError('Content-Length and Transfer-Encoding are managed by the client')
    if args.data_file is not None and 'trailer' in hdrs:
        raise ValueError('Trailer is managed by the client')
    if args.basic is not None or args.bearer is not None:
        if len(hdrs['authorization']) != 1:
            raise ValueError('multiple Authorization headers')

    trailers = HttpHeaders([_header(value) for value in args.trailer])
    if args.method:
        method = args.method.upper()
    elif args.head:
        method = 'HEAD'
    elif body is not None or args.data_file is not None:
        method = 'POST'
    else:
        method = 'GET'
    if not _HEADER_NAME.fullmatch(method):
        raise ValueError(f'invalid HTTP method: {method!r}')

    return HttpClientRequest(
        url=_make_url(args.url, args.query),
        method=method,
        headers=hdrs,
        data=body,
        timeout_s=args.timeout,
        no_decompress=args.raw,
    ), trailers


def _ssl_context(args: argparse.Namespace) -> ssl.SSLContext | None:
    if args.insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return SslIoPipelineHandler.configure_ssl_context(ctx, SslIoPipelineHandler.Config.DEFAULT)
    if args.ca_file:
        ctx = ssl.create_default_context(cafile=args.ca_file)
        return SslIoPipelineHandler.configure_ssl_context(ctx, SslIoPipelineHandler.Config.DEFAULT)
    return None


def _write_head(out: ta.BinaryIO, status: int, headers: HttpHeaders | None) -> None:
    try:
        phrase = http.HTTPStatus(status).phrase
    except ValueError:
        phrase = ''
    out.write(f'HTTP {status} {phrase}\r\n'.encode('ascii'))
    for name, value in HttpHeaders.of(headers).raw:
        out.write(f'{name}: {value}\r\n'.encode('latin-1'))
    out.write(b'\r\n')


def _render_pretty(chunks: ta.Iterable[bytes | bytearray]) -> bytes:
    value = json.loads(b''.join(chunks))
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def _run_sync(
    args: argparse.Namespace,
    req: HttpClientRequest,
    trailers: HttpHeaders,
    source: ta.BinaryIO | None,
    out: ta.BinaryIO,
    err: ta.TextIO,
) -> int:
    config = IoPipelineHttpClient.Config(connect_timeout_s=args.connect_timeout)
    with IoPipelineHttpClient(config, ssl_ctx=_ssl_context(args)) as client:
        resp = (
            stream_sync_request(client, req, source, chunk_size=args.chunk_size, trailers=trailers)
            if source is not None else client.stream_request(req)
        )
        with resp:
            if args.include or args.head:
                _write_head(out, resp.status, resp.headers)
            if not args.no_body and not args.head:
                if args.pretty:
                    chunks = iter(lambda: resp.stream.read(args.chunk_size), b'')
                    out.write(_render_pretty(chunks))
                else:
                    while chunk := resp.stream.read(args.chunk_size):
                        out.write(chunk)
            out.flush()
            if args.show_status:
                print(resp.status, file=err)
            return 22 if args.fail and resp.status >= 400 else 0


async def _run_async(
    args: argparse.Namespace,
    req: HttpClientRequest,
    trailers: HttpHeaders,
    source: ta.BinaryIO | None,
    out: ta.BinaryIO,
    err: ta.TextIO,
) -> int:
    config = AsyncioIoPipelineAsyncHttpClient.Config(connect_timeout_s=args.connect_timeout)
    async with AsyncioIoPipelineAsyncHttpClient(config, ssl_ctx=_ssl_context(args)) as client:
        resp = (
            await stream_async_request(client, req, source, chunk_size=args.chunk_size, trailers=trailers)
            if source is not None else await client.stream_request(req)
        )
        async with resp:
            if args.include or args.head:
                _write_head(out, resp.status, resp.headers)
            if not args.no_body and not args.head:
                if args.pretty:
                    chunks = []
                    while chunk := await resp.stream.read(args.chunk_size):
                        chunks.append(chunk)
                    out.write(_render_pretty(chunks))
                else:
                    while chunk := await resp.stream.read(args.chunk_size):
                        out.write(chunk)
            out.flush()
            if args.show_status:
                print(resp.status, file=err)
            return 22 if args.fail and resp.status >= 400 else 0


def main(
    argv: ta.Sequence[str] | None = None,
    *,
    stdin: ta.BinaryIO | None = None,
    stdout: ta.BinaryIO | None = None,
    stderr: ta.TextIO | None = None,
) -> int:
    args = _parser().parse_args(argv)
    out = stdout if stdout is not None else sys.stdout.buffer
    err = stderr if stderr is not None else sys.stderr
    try:
        req, trailers = _make_request(args)
        if args.data_file is not None and args.output not in (None, '-') and args.data_file != '-':
            if os.path.exists(args.output) and os.path.samefile(args.data_file, args.output):
                raise ValueError('input and output files must differ')

        with contextlib.ExitStack() as stack:
            source: ta.BinaryIO | None = None
            if args.data_file == '-':
                source = stdin if stdin is not None else sys.stdin.buffer
            elif args.data_file is not None:
                source = stack.enter_context(open(args.data_file, 'rb'))

            if args.output not in (None, '-'):
                out = stack.enter_context(open(args.output, 'wb'))

            if args.asyncio:
                return asyncio.run(_run_async(args, req, trailers, source, out, err))
            return _run_sync(args, req, trailers, source, out, err)
    except (HttpClientError, OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'curl: {exc}', file=err)
        return 2
