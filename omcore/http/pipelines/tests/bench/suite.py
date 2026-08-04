# ruff: noqa: PYI034 UP006 UP007 UP037 UP045
# @om-lite
"""
Self-contained HTTP pipeline benchmarks.

IMPORTANT FDIO CLIENT COMPARABILITY NOTE:
    The ``fdio`` *client* case is intentionally a lean driver-plus-codec benchmark, not an implementation of the full
    ``omcore.http.clients.pipelines`` client stack used by the ``sync`` and ``asyncio`` cases. It uses the real HTTP
    request encoder and request-aware response decoder, but omits the higher-level client handler, output buffering and
    flow service, dechunking, decompression, aggregation, compression, request timeout policy, and TLS. It also counts
    decoded response body bytes without assembling them into one final ``bytes`` object. Its results are useful as an
    indicator of fdio driver/codec performance and of the surrounding machinery's cost, but they are not an
    apples-to-apples high-level HTTP-client comparison. There is currently no general fdio ``HttpClient`` adapter or
    settled ownership model for threading an ``FdioManager`` through that interface.

    The ``fdio`` *server* case does use the same request decoder, request aggregator, response encoder, and benchmark
    application pipeline as the ``sync`` and ``asyncio`` server cases, so this warning does not apply to that server
    comparison.

Examples::

    ./python -m omcore.http.pipelines.tests.bench.bench --suite all
    ./python -m omcore.http.pipelines.tests.bench.bench --suite clients --nginx /usr/sbin/nginx
    ./python -m omcore.http.pipelines.tests.bench.bench --suite servers --json

The benchmark intentionally uses only the standard library and programs commonly present on a development machine.
Each client case runs against a fresh temporary nginx instance unless ``--client-base-url`` is supplied, preventing
closed connections from earlier cases from contaminating later ones. Server cases are driven by concurrent curl
processes. Each client case and each server implementation runs in a separate process so peak RSS is meaningful and
failures do not contaminate later cases. Peak RSS includes the interpreter and common benchmark harness; RSS growth is
measured from a post-warmup baseline.
"""
import argparse
import asyncio
import concurrent.futures as cf
import contextlib
import dataclasses as dc
import gc
import importlib
import importlib.util
import json
import math
import os
import platform
import resource
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import typing as ta
import urllib.parse
import urllib.request

from .....io.fdio.handlers import ServerSocketFdioHandler
from .....io.fdio.manager import FdioManager
from .....io.fdio.pollers import SelectFdioPoller
from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from .....io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from .....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.dataclasses import install_dataclass_kw_only_init
from ....clients.base import HttpClientRequest
from ....clients.pipelines.asyncio import AsyncioIoPipelineAsyncHttpClient
from ....clients.pipelines.sync import IoPipelineHttpClient
from ...aggregators import IoPipelineHttpAggregationConfig
from ...clients.requests import IoPipelineHttpRequestEncoder
from ...clients.responses import IoPipelineHttpClientResponseDecoder
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ...servers.requests import IoPipelineHttpRequestAggregatorDecoder
from ...servers.requests import IoPipelineHttpRequestDecoder
from ...servers.responses import IoPipelineHttpResponseEncoder


##


MODULE_NAME = __package__ + '.bench'

CLIENT_IMPLEMENTATIONS = (
    'sync',
    'asyncio',
    'fdio',
    'httpx',
    'urllib',
)

SERVER_IMPLEMENTATIONS = (
    'sync',
    'asyncio',
    'fdio',
    'uvicorn',
)

SCENARIOS = (
    'requests',
    'download',
    'upload',
)


##
# Results and statistics


def _percentile(values: ta.Sequence[float], quantile: float) -> float:
    if not values:
        raise ValueError('no values')
    if not 0. <= quantile <= 1.:
        raise ValueError(quantile)

    ordered = sorted(values)
    pos = (len(ordered) - 1) * quantile
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def _latency_stats_ms(latencies_ns: ta.Sequence[int]) -> ta.Dict[str, float]:
    values = [ns / 1_000_000. for ns in latencies_ns]
    if not values:
        raise ValueError('no latencies')

    return {
        'min': min(values),
        'mean': statistics.fmean(values),
        'p50': _percentile(values, .50),
        'p90': _percentile(values, .90),
        'p99': _percentile(values, .99),
        'max': max(values),
    }


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class BenchmarkResult:
    suite: str
    scenario: str
    implementation: str

    available: bool = True
    reason: ta.Optional[str] = None

    requests: int = 0
    concurrency: int = 0
    elapsed_s: float = 0.
    requests_per_s: float = 0.
    transferred_bytes: int = 0
    bytes_per_s: float = 0.
    latency_ms: ta.Optional[ta.Mapping[str, float]] = None

    rss_before_bytes: ta.Optional[int] = None
    peak_rss_bytes: ta.Optional[int] = None
    rss_growth_bytes: ta.Optional[int] = None

    notes: ta.Sequence[str] = ()

    def as_dict(self) -> ta.Dict[str, ta.Any]:
        return dc.asdict(self)


def _make_result(
        *,
        suite: str,
        implementation: str,
        scenario: str,
        requests: int,
        concurrency: int,
        elapsed_s: float,
        transferred_bytes: int,
        latencies_ns: ta.Sequence[int],
        rss_before_bytes: ta.Optional[int] = None,
        peak_rss_bytes: ta.Optional[int] = None,
        notes: ta.Sequence[str] = (),
) -> BenchmarkResult:
    if requests < 1 or elapsed_s <= 0. or len(latencies_ns) != requests:
        raise ValueError((requests, elapsed_s, len(latencies_ns)))

    rss_growth_bytes: ta.Optional[int] = None
    if rss_before_bytes is not None and peak_rss_bytes is not None:
        rss_growth_bytes = max(0, peak_rss_bytes - rss_before_bytes)

    return BenchmarkResult(
        suite=suite,
        implementation=implementation,
        scenario=scenario,
        requests=requests,
        concurrency=concurrency,
        elapsed_s=elapsed_s,
        requests_per_s=requests / elapsed_s,
        transferred_bytes=transferred_bytes,
        bytes_per_s=transferred_bytes / elapsed_s,
        latency_ms=_latency_stats_ms(latencies_ns),
        rss_before_bytes=rss_before_bytes,
        peak_rss_bytes=peak_rss_bytes,
        rss_growth_bytes=rss_growth_bytes,
        notes=notes,
    )


##
# Generic helpers


def _parse_size(value: str) -> int:
    original = value
    value = value.strip().lower()
    suffixes = {
        'k': 1024,
        'kb': 1024,
        'kib': 1024,
        'm': 1024 ** 2,
        'mb': 1024 ** 2,
        'mib': 1024 ** 2,
        'g': 1024 ** 3,
        'gb': 1024 ** 3,
        'gib': 1024 ** 3,
    }

    multiplier = 1
    for suffix in sorted(suffixes, key=len, reverse=True):
        if value.endswith(suffix):
            value = value[:-len(suffix)]
            multiplier = suffixes[suffix]
            break

    try:
        size = int(float(value) * multiplier)
    except ValueError:
        raise argparse.ArgumentTypeError(f'invalid size: {original!r}') from None
    if size < 1:
        raise argparse.ArgumentTypeError(f'size must be positive: {original!r}')
    return size


def _parse_names(value: str, allowed: ta.Sequence[str]) -> ta.Tuple[str, ...]:
    names = tuple(part.strip() for part in value.split(',') if part.strip())
    unknown = sorted(set(names) - set(allowed))
    if unknown:
        raise ValueError(f'unknown values {unknown!r}; expected from {list(allowed)!r}')
    if not names:
        raise ValueError('empty selection')
    return names


def _partition(total: int, concurrency: int) -> ta.List[int]:
    if total < 1 or concurrency < 1:
        raise ValueError((total, concurrency))
    workers = min(total, concurrency)
    base, extra = divmod(total, workers)
    return [base + (1 if i < extra else 0) for i in range(workers)]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return ta.cast(ta.Tuple[str, int], sock.getsockname())[1]


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command_version(executable: str, *args: str) -> ta.Optional[str]:
    resolved = shutil.which(executable) if os.path.sep not in executable else executable
    if not resolved:
        return None
    try:
        completed = subprocess.run(
            [resolved, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = completed.stdout.strip() or completed.stderr.strip()
    return output.splitlines()[0] if output else None


def _make_metadata(args: argparse.Namespace) -> ta.Dict[str, ta.Any]:
    return {
        'python': sys.version.split()[0],
        'python_implementation': platform.python_implementation(),
        'platform': platform.platform(),
        'cpu_count': os.cpu_count(),
        'suite': args.suite,
        'clients': args.clients,
        'servers': args.servers,
        'scenarios': args.scenarios,
        'requests': args.requests,
        'transfer_requests': args.transfer_requests,
        'warmup': args.warmup,
        'concurrency': args.concurrency,
        'payload_size': args.payload_size,
        'memory_note': 'peak RSS includes the interpreter and common harness; growth starts after warmup',
        'nginx': _command_version(args.nginx, '-v') if not args.client_base_url else None,
        'curl': _command_version(args.curl, '--version'),
    }


def _ru_maxrss_bytes() -> int:
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == 'Darwin':
        return rss
    return rss * 1024


def _read_process_rss_bytes(pid: int) -> ta.Optional[int]:
    status_path = f'/proc/{pid}/status'
    try:
        with open(status_path, encoding='ascii') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) * 1024
    except (FileNotFoundError, OSError, ValueError):
        pass

    if platform.system() == 'Darwin':
        try:
            cp = subprocess.run(
                ['ps', '-o', 'rss=', '-p', str(pid)],
                check=True,
                capture_output=True,
                text=True,
            )
            return int(cp.stdout.strip()) * 1024
        except (OSError, subprocess.SubprocessError, ValueError):
            pass

    return None


class _ProcessRssSampler:
    def __init__(self, pid: int, interval_s: float = .005) -> None:
        super().__init__()

        self._pid = pid
        self._interval_s = interval_s
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._peak = 0
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self) -> None:
        if (rss := _read_process_rss_bytes(self._pid)) is not None:
            with self._lock:
                self._peak = max(self._peak, rss)

    def _run(self) -> None:
        while not self._stop.wait(self._interval_s):
            self._sample()

    def start(self) -> None:
        self._sample()
        self._thread.start()

    def reset(self) -> ta.Optional[int]:
        current = _read_process_rss_bytes(self._pid)
        with self._lock:
            self._peak = current or 0
        return current

    @property
    def peak(self) -> ta.Optional[int]:
        self._sample()
        with self._lock:
            return self._peak or None

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.)
        self._sample()

    def __enter__(self) -> '_ProcessRssSampler':
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _wait_http_ready(
        process: subprocess.Popen,
        port: int,
        *,
        timeout_s: float,
) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: ta.Optional[BaseException] = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f'process exited before becoming ready ({process.returncode})\n'
                f'stdout:\n{stdout}\nstderr:\n{stderr}',
            )

        try:
            with socket.create_connection(('127.0.0.1', port), timeout=.2) as sock:
                sock.sendall(b'GET /empty HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
                data = sock.recv(256)
                if data.startswith(b'HTTP/1.'):
                    return
        except OSError as exc:
            last_error = exc

        time.sleep(.02)

    raise TimeoutError(f'HTTP server did not become ready on port {port}: {last_error!r}')


def _stop_process(process: subprocess.Popen) -> ta.Tuple[str, str]:
    if process.poll() is not None:
        return process.communicate()

    process.terminate()
    try:
        return process.communicate(timeout=3.)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.communicate()


##
# nginx client fixture


def _write_payload(path: str, size: int) -> None:
    chunk = bytes(range(256)) * 256
    remaining = size
    with open(path, 'wb') as f:
        while remaining:
            part = chunk[:min(remaining, len(chunk))]
            f.write(part)
            remaining -= len(part)


class _NginxFixture:
    def __init__(
            self,
            executable: str,
            payload_size: int,
            timeout_s: float,
    ) -> None:
        super().__init__()

        self._executable = executable
        self._payload_size = payload_size
        self._timeout_s = timeout_s

        self._temp_dir: ta.Optional[tempfile.TemporaryDirectory] = None
        self._process: ta.Optional[subprocess.Popen] = None

    port: int
    base_url: str
    payload_path: str

    def __enter__(self) -> '_NginxFixture':
        executable = shutil.which(self._executable) if os.path.sep not in self._executable else self._executable
        if not executable or not os.path.isfile(executable):
            raise FileNotFoundError(f'nginx executable not found: {self._executable!r}')

        temp_dir = self._temp_dir = tempfile.TemporaryDirectory(prefix='omcore-http-bench-nginx-')
        root = temp_dir.name
        for name in ('logs', 'client_body', 'proxy', 'fastcgi', 'uwsgi', 'scgi'):
            os.makedirs(os.path.join(root, name))

        self.port = _find_free_port()
        self.base_url = f'http://127.0.0.1:{self.port}'
        self.payload_path = os.path.join(root, 'payload.bin')
        _write_payload(self.payload_path, self._payload_size)

        conf_path = os.path.join(root, 'nginx.conf')
        max_body = max(64 * 1024, self._payload_size * 2)
        conf = f"""
worker_processes 1;
master_process off;
daemon off;
pid {os.path.join(root, 'nginx.pid')};
error_log {os.path.join(root, 'logs', 'error.log')} warn;

events {{
    worker_connections 4096;
}}

http {{
    access_log off;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 0;
    client_max_body_size {max_body};
    client_body_temp_path {os.path.join(root, 'client_body')};
    proxy_temp_path {os.path.join(root, 'proxy')};
    fastcgi_temp_path {os.path.join(root, 'fastcgi')};
    uwsgi_temp_path {os.path.join(root, 'uwsgi')};
    scgi_temp_path {os.path.join(root, 'scgi')};

    server {{
        listen 127.0.0.1:{self.port};
        server_name localhost;

        location = /empty {{
            return 204;
        }}

        location = /download {{
            alias {self.payload_path};
            default_type application/octet-stream;
        }}

        location = /upload {{
            proxy_request_buffering on;
            proxy_http_version 1.1;
            proxy_set_header Connection close;
            proxy_pass http://127.0.0.1:{self.port}/_sink;
        }}

        location = /_sink {{
            return 204;
        }}
    }}
}}
"""
        with open(conf_path, 'w', encoding='utf-8') as f:
            f.write(conf)

        check = subprocess.run(
            [executable, '-p', root + os.path.sep, '-c', conf_path, '-t'],
            check=False,
            capture_output=True,
            text=True,
        )
        if check.returncode:
            raise RuntimeError(f'nginx configuration failed:\n{check.stdout}\n{check.stderr}')

        self._process = subprocess.Popen(
            [executable, '-p', root + os.path.sep, '-c', conf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_http_ready(self._process, self.port, timeout_s=self._timeout_s)
        except BaseException:
            _stop_process(self._process)
            raise

        return self

    def __exit__(self, *args: object) -> None:
        try:
            if self._process is not None:
                _stop_process(self._process)
        finally:
            if self._temp_dir is not None:
                self._temp_dir.cleanup()


##
# Client benchmark workers


class _SyncRequester:
    def request(self, request: HttpClientRequest) -> ta.Tuple[int, int]:
        raise NotImplementedError

    def close(self) -> None:
        pass


class _PipelineSyncRequester(_SyncRequester):
    def __init__(self) -> None:
        super().__init__()

        self._client = IoPipelineHttpClient()

    def request(self, request: HttpClientRequest) -> ta.Tuple[int, int]:
        response = self._client.request(request)
        return response.status, len(response.data or b'')


class _UrllibRequester(_SyncRequester):
    def __init__(self) -> None:
        super().__init__()

        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(self, request: HttpClientRequest) -> ta.Tuple[int, int]:
        headers: ta.Dict[str, str] = {}
        if request.headers_ is not None:
            for key, values in request.headers_.items():
                headers[key] = ', '.join(values)

        urllib_request = urllib.request.Request(  # noqa: S310 - benchmark URLs are constructed as loopback HTTP URLs.
            request.url,
            data=request.data.encode('utf-8') if isinstance(request.data, str) else request.data,
            headers=headers,
            method=request.method_or_default,
        )
        with self._opener.open(urllib_request, timeout=request.timeout_s) as response:
            return response.status, len(response.read())


class _HttpxRequester(_SyncRequester):
    def __init__(self, timeout_s: float) -> None:
        super().__init__()

        httpx = importlib.import_module('httpx')
        self._client = httpx.Client(
            timeout=timeout_s,
            trust_env=False,
            headers={'Connection': 'close'},
        )

    def request(self, request: HttpClientRequest) -> ta.Tuple[int, int]:
        response = self._client.request(
            request.method_or_default,
            request.url,
            headers=request.headers_.all if request.headers_ is not None else None,
            content=request.data,
        )
        return response.status_code, len(response.content)

    def close(self) -> None:
        self._client.close()


def _make_client_request(
        base_url: str,
        scenario: str,
        payload: bytes,
        timeout_s: float,
) -> HttpClientRequest:
    if scenario == 'requests':
        return HttpClientRequest(
            f'{base_url}/empty',
            headers={'Connection': 'close'},
            timeout_s=timeout_s,
        )
    elif scenario == 'download':
        return HttpClientRequest(
            f'{base_url}/download',
            headers={'Connection': 'close'},
            timeout_s=timeout_s,
        )
    elif scenario == 'upload':
        return HttpClientRequest(
            f'{base_url}/upload',
            method='POST',
            headers={'Connection': 'close', 'Content-Type': 'application/octet-stream'},
            data=payload,
            timeout_s=timeout_s,
        )
    else:
        raise ValueError(scenario)


def _validate_client_response(scenario: str, payload_size: int, status: int, body_size: int) -> int:
    if not 200 <= status < 300:
        raise RuntimeError(f'unexpected HTTP status: {status}')
    if scenario == 'download':
        if body_size != payload_size:
            raise RuntimeError(f'unexpected download size: {body_size} != {payload_size}')
        return body_size
    if body_size:
        raise RuntimeError(f'unexpected response body for {scenario}: {body_size}')
    return payload_size if scenario == 'upload' else 0


def _run_sync_requester_batch(
        implementation: str,
        request: HttpClientRequest,
        scenario: str,
        payload_size: int,
        requests: int,
        concurrency: int,
        warmup: int,
        timeout_s: float,
) -> ta.Tuple[float, ta.List[int], int, int]:
    counts = _partition(requests, concurrency)
    requesters: ta.List[_SyncRequester] = []
    for _ in counts:
        if implementation == 'sync':
            requesters.append(_PipelineSyncRequester())
        elif implementation == 'urllib':
            requesters.append(_UrllibRequester())
        elif implementation == 'httpx':
            requesters.append(_HttpxRequester(timeout_s))
        else:
            raise ValueError(implementation)

    def run_one(requester: _SyncRequester, count: int) -> ta.Tuple[ta.List[int], int]:
        latencies: ta.List[int] = []
        transferred = 0
        for _ in range(count):
            started_ns = time.perf_counter_ns()
            status, body_size = requester.request(request)
            latencies.append(time.perf_counter_ns() - started_ns)
            transferred += _validate_client_response(scenario, payload_size, status, body_size)
        return latencies, transferred

    try:
        with cf.ThreadPoolExecutor(max_workers=len(counts), thread_name_prefix='http-bench-client') as executor:
            if warmup:
                warm_counts = _partition(warmup, min(warmup, len(counts)))
                futures = [
                    executor.submit(run_one, requesters[i], count)
                    for i, count in enumerate(warm_counts)
                ]
                for future in futures:
                    future.result()

            gc.collect()
            rss_before = _read_process_rss_bytes(os.getpid()) or _ru_maxrss_bytes()

            started = time.perf_counter()
            futures = [
                executor.submit(run_one, requester, count)
                for requester, count in zip(requesters, counts)
            ]
            latencies: ta.List[int] = []
            transferred = 0
            for future in futures:
                worker_latencies, worker_transferred = future.result()
                latencies.extend(worker_latencies)
                transferred += worker_transferred
            elapsed = time.perf_counter() - started

        return elapsed, latencies, transferred, rss_before

    finally:
        for requester in requesters:
            requester.close()


async def _run_asyncio_requester_batch_async(
        request: HttpClientRequest,
        scenario: str,
        payload_size: int,
        requests: int,
        concurrency: int,
        warmup: int,
) -> ta.Tuple[float, ta.List[int], int, int]:
    client = AsyncioIoPipelineAsyncHttpClient()

    async def run_one(count: int) -> ta.Tuple[ta.List[int], int]:
        latencies: ta.List[int] = []
        transferred = 0
        for _ in range(count):
            started_ns = time.perf_counter_ns()
            response = await client.request(request)
            latencies.append(time.perf_counter_ns() - started_ns)
            transferred += _validate_client_response(
                scenario,
                payload_size,
                response.status,
                len(response.data or b''),
            )
        return latencies, transferred

    async with client:
        if warmup:
            await asyncio.gather(*(run_one(count) for count in _partition(warmup, concurrency)))

        gc.collect()
        rss_before = _read_process_rss_bytes(os.getpid()) or _ru_maxrss_bytes()

        started = time.perf_counter()
        results = await asyncio.gather(*(run_one(count) for count in _partition(requests, concurrency)))
        elapsed = time.perf_counter() - started

    latencies: ta.List[int] = []
    transferred = 0
    for worker_latencies, worker_transferred in results:
        latencies.extend(worker_latencies)
        transferred += worker_transferred
    return elapsed, latencies, transferred, rss_before


class _FdioClientHandler(IoPipelineHandler):
    def __init__(
            self,
            request: FullIoPipelineHttpRequest,
            started_ns: int,
            on_complete: ta.Callable[[int, int, int], None],
    ) -> None:
        super().__init__()

        self._request = request
        self._started_ns = started_ns
        self._on_complete = on_complete

        self._status: ta.Optional[int] = None
        self._body_size = 0

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._request)
            return

        if isinstance(msg, IoPipelineHttpResponseHead):
            self._status = msg.status
            return

        if isinstance(msg, IoPipelineHttpResponseBodyData):
            self._body_size += ByteStreamBuffers.bytes_len(msg.data)
            return

        if isinstance(msg, IoPipelineHttpResponseEnd):
            if self._status is None:
                raise RuntimeError('response ended without a head')
            self._on_complete(self._status, self._body_size, time.perf_counter_ns() - self._started_ns)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineHttpResponseAborted):
            raise ConnectionError(f'HTTP response aborted: {msg!r}')

        if isinstance(msg, IoPipelineMessages.FinalInput):
            raise ConnectionError('connection closed before HTTP response completed')

        ctx.feed_in(msg)


def _make_fdio_request(base_url: str, scenario: str, payload: bytes) -> ta.Tuple[str, int, FullIoPipelineHttpRequest]:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != 'http' or parsed.hostname is None:
        raise ValueError(f'fdio benchmark only supports plain HTTP URLs: {base_url!r}')
    host = parsed.hostname
    port = parsed.port or 80

    if scenario == 'requests':
        target, method, body = '/empty', 'GET', b''
    elif scenario == 'download':
        target, method, body = '/download', 'GET', b''
    elif scenario == 'upload':
        target, method, body = '/upload', 'POST', payload
    else:
        raise ValueError(scenario)

    return host, port, FullIoPipelineHttpRequest.simple(
        f'{host}:{port}',
        target,
        method=method,
        content_type='application/octet-stream' if body else None,
        body=body,
        connection='close',
    )


def _run_fdio_client_once(
        base_url: str,
        scenario: str,
        payload: bytes,
        requests: int,
        concurrency: int,
        timeout_s: float,
) -> ta.Tuple[float, ta.List[int], int]:
    host, port, request = _make_fdio_request(base_url, scenario, payload)
    poller = SelectFdioPoller()
    manager = FdioManager(poller)

    active: ta.Set[IoPipelineDriverSocketFdioHandler] = set()
    latencies: ta.List[int] = []
    transferred = 0
    launched = 0
    completed = 0

    def on_complete(status: int, body_size: int, latency_ns: int) -> None:
        nonlocal completed, transferred
        transferred += _validate_client_response(scenario, len(payload), status, body_size)
        latencies.append(latency_ns)
        completed += 1

    def launch() -> None:
        nonlocal launched
        started_ns = time.perf_counter_ns()
        sock = socket.create_connection((host, port), timeout=timeout_s)
        sock.settimeout(None)
        driver = IoPipelineDriverSocketFdioHandler(
            sock,
            sock.getpeername(),
            IoPipeline.Spec([
                IoPipelineHttpRequestEncoder(),
                IoPipelineHttpClientResponseDecoder(),
                _FdioClientHandler(request, started_ns, on_complete),
            ]),
        )
        try:
            if driver.next(read=False) is not None:
                raise RuntimeError('unexpected fdio pipeline output')
            manager.register(driver)
            active.add(driver)
            launched += 1
        except BaseException:
            driver.close()
            raise

    started = time.perf_counter()
    deadline = started + max(timeout_s, timeout_s * requests)
    try:
        while completed < requests:
            while launched < requests and len(active) < min(concurrency, requests):
                launch()

            manager.poll(timeout=min(.1, max(0., deadline - time.monotonic())))
            active = {driver for driver in active if not driver.closed}

            if time.monotonic() >= deadline:
                raise TimeoutError(f'fdio client benchmark timed out after {completed}/{requests} requests')

        return time.perf_counter() - started, latencies, transferred

    finally:
        for driver in active:
            driver.close()
        manager.poll(timeout=0.)
        poller.close()


def _run_fdio_client_batch(
        base_url: str,
        scenario: str,
        payload: bytes,
        requests: int,
        concurrency: int,
        warmup: int,
        timeout_s: float,
) -> ta.Tuple[float, ta.List[int], int, int]:
    if warmup:
        _run_fdio_client_once(base_url, scenario, payload, warmup, concurrency, timeout_s)

    gc.collect()
    rss_before = _read_process_rss_bytes(os.getpid()) or _ru_maxrss_bytes()
    elapsed, latencies, transferred = _run_fdio_client_once(
        base_url,
        scenario,
        payload,
        requests,
        concurrency,
        timeout_s,
    )
    return elapsed, latencies, transferred, rss_before


def _run_client_worker(args: argparse.Namespace) -> BenchmarkResult:
    payload = bytes(range(256)) * (args.payload_size // 256) + bytes(range(args.payload_size % 256))
    request = _make_client_request(args.base_url, args.scenario, payload, args.timeout)

    if args.implementation in ('sync', 'httpx', 'urllib'):
        elapsed, latencies, transferred, rss_before = _run_sync_requester_batch(
            args.implementation,
            request,
            args.scenario,
            args.payload_size,
            args.case_requests,
            args.concurrency,
            args.warmup,
            args.timeout,
        )

    elif args.implementation == 'asyncio':
        elapsed, latencies, transferred, rss_before = asyncio.run(_run_asyncio_requester_batch_async(
            request,
            args.scenario,
            args.payload_size,
            args.case_requests,
            args.concurrency,
            args.warmup,
        ))

    elif args.implementation == 'fdio':
        elapsed, latencies, transferred, rss_before = _run_fdio_client_batch(
            args.base_url,
            args.scenario,
            payload,
            args.case_requests,
            args.concurrency,
            args.warmup,
            args.timeout,
        )

    else:
        raise ValueError(args.implementation)

    return _make_result(
        suite='client',
        implementation=args.implementation,
        scenario=args.scenario,
        requests=args.case_requests,
        concurrency=min(args.concurrency, args.case_requests),
        elapsed_s=elapsed,
        transferred_bytes=transferred,
        latencies_ns=latencies,
        rss_before_bytes=rss_before,
        peak_rss_bytes=_ru_maxrss_bytes(),
        notes=(
            'one HTTP/1.1 connection per request',
            *(
                ('fdio connection establishment is synchronous',)
                if args.implementation == 'fdio'
                else ()
            ),
        ),
    )


def _run_client_case(
        *,
        implementation: str,
        scenario: str,
        base_url: str,
        requests: int,
        concurrency: int,
        warmup: int,
        payload_size: int,
        timeout_s: float,
) -> BenchmarkResult:
    command = [
        sys.executable,
        '-m', MODULE_NAME,
        '--_worker', 'client',
        '--implementation', implementation,
        '--scenario', scenario,
        '--base-url', base_url,
        '--case-requests', str(requests),
        '--concurrency', str(concurrency),
        '--warmup', str(warmup),
        '--payload-size', str(payload_size),
        '--timeout', str(timeout_s),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    peak_rss = 0
    deadline = time.monotonic() + max(30., timeout_s * (requests + warmup))
    while process.poll() is None:
        if (rss := _read_process_rss_bytes(process.pid)) is not None:
            peak_rss = max(peak_rss, rss)
        if time.monotonic() >= deadline:
            process.kill()
            stdout, stderr = process.communicate()
            raise TimeoutError(f'client worker timed out\nstdout:\n{stdout}\nstderr:\n{stderr}')
        time.sleep(.005)

    stdout, stderr = process.communicate()
    if process.returncode:
        raise RuntimeError(
            f'client worker failed ({process.returncode})\nstdout:\n{stdout}\nstderr:\n{stderr}',
        )

    try:
        data = json.loads([line for line in stdout.splitlines() if line.strip()][-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f'invalid client worker output:\n{stdout}\nstderr:\n{stderr}') from exc

    result = BenchmarkResult(**data)
    peak_rss = max(peak_rss, result.peak_rss_bytes or 0)
    growth = None
    if result.rss_before_bytes is not None and peak_rss:
        growth = max(0, peak_rss - result.rss_before_bytes)
    return dc.replace(
        result,
        peak_rss_bytes=peak_rss or result.peak_rss_bytes,
        rss_growth_bytes=growth,
    )


##
# Pipeline server workers


class _BenchmarkServerHandler(IoPipelineHandler):
    def __init__(self, payload: bytes, max_upload_size: int) -> None:
        super().__init__()

        self._payload = payload
        self._max_upload_size = max_upload_size

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not isinstance(msg, FullIoPipelineHttpRequest):
            ctx.feed_in(msg)
            return

        method = msg.head.method.upper()
        target = msg.head.target.partition('?')[0]
        if method == 'GET' and target == '/empty':
            status, body = 204, b''
        elif method == 'GET' and target == '/download':
            status, body = 200, self._payload
        elif method == 'POST' and target == '/upload':
            if ByteStreamBuffers.bytes_len(msg.body) > self._max_upload_size:
                status, body = 413, b''
            else:
                status, body = 204, b''
        else:
            status, body = 404, b'not found'

        ctx.feed_out(FullIoPipelineHttpResponse.simple(status=status, body=body))
        ctx.feed_final_output()


def _make_benchmark_server_spec(payload: bytes, max_upload_size: int) -> IoPipeline.Spec:
    aggregation_config = IoPipelineHttpAggregationConfig(
        body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(
            max_size=max_upload_size,
            chunk_size=min(64 * 1024, max_upload_size),
        ),
    )
    return IoPipeline.Spec([
        IoPipelineHttpRequestDecoder(),
        IoPipelineHttpRequestAggregatorDecoder(config=aggregation_config),
        IoPipelineHttpResponseEncoder(),
        _BenchmarkServerHandler(payload, max_upload_size),
    ])


def _serve_sync(port: int, payload: bytes, max_upload_size: int, threads: int) -> ta.NoReturn:
    def handle(conn: socket.socket) -> None:
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            SyncSocketIoPipelineDriver(
                _make_benchmark_server_spec(payload, max_upload_size),
                conn,
            ).loop_until_done()
        finally:
            conn.close()

    with socket.create_server(('127.0.0.1', port), reuse_port=False) as server:
        with cf.ThreadPoolExecutor(max_workers=threads, thread_name_prefix='http-bench-server') as executor:
            while True:
                conn, _ = server.accept()
                executor.submit(handle, conn)


async def _serve_asyncio_async(port: int, payload: bytes, max_upload_size: int) -> ta.NoReturn:
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        driver = PollAsyncioStreamIoPipelineDriver(
            _make_benchmark_server_spec(payload, max_upload_size),
            reader,
            writer,
        )
        await driver.loop_until_done()

    server = await asyncio.start_server(handle, '127.0.0.1', port)
    async with server:
        await server.serve_forever()
    raise RuntimeError('server stopped')


def _serve_fdio(port: int, payload: bytes, max_upload_size: int) -> ta.NoReturn:
    poller = SelectFdioPoller()
    manager = FdioManager(poller)
    connections: ta.Set[IoPipelineDriverSocketFdioHandler] = set()

    def on_connect(sock: socket.socket, addr: ta.Any) -> None:
        driver = IoPipelineDriverSocketFdioHandler(
            sock,
            addr,
            _make_benchmark_server_spec(payload, max_upload_size),
        )
        try:
            if driver.next(read=False) is not None:
                raise RuntimeError('unexpected fdio pipeline output')
            manager.register(driver)
            connections.add(driver)
        except BaseException:
            driver.close()
            raise

    server_sock = socket.create_server(('127.0.0.1', port))
    server = ServerSocketFdioHandler(server_sock, on_connect)
    # ServerSocketFdioHandler deliberately uses the smallest useful default backlog. A load fixture must admit its
    # whole connection burst, so expand the same listening socket after the handler has initialized it.
    server_sock.listen(socket.SOMAXCONN)
    manager.register(server)
    try:
        while True:
            manager.poll()
            connections = {connection for connection in connections if not connection.closed}
    finally:
        server.close()
        for connection in connections:
            connection.close()
        poller.close()
    raise RuntimeError('server stopped')


def _serve_uvicorn(port: int, payload: bytes, max_upload_size: int) -> ta.NoReturn:
    uvicorn = importlib.import_module('uvicorn')

    async def app(scope: ta.Mapping[str, ta.Any], receive: ta.Callable, send: ta.Callable) -> None:
        if scope['type'] != 'http':
            return

        body_size = 0
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            if event['type'] != 'http.request':
                continue
            body_size += len(event.get('body', b''))
            if not event.get('more_body', False):
                break

        method = scope['method'].upper()
        target = scope['path']
        if method == 'GET' and target == '/empty':
            status, body = 204, b''
        elif method == 'GET' and target == '/download':
            status, body = 200, payload
        elif method == 'POST' and target == '/upload':
            status, body = (204, b'') if body_size <= max_upload_size else (413, b'')
        else:
            status, body = 404, b'not found'

        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [
                (b'content-length', str(len(body)).encode('ascii')),
                (b'content-type', b'application/octet-stream'),
                (b'connection', b'close'),
            ],
        })
        await send({'type': 'http.response.body', 'body': body})

    uvicorn.run(
        app,
        host='127.0.0.1',
        port=port,
        access_log=False,
        log_level='critical',
        timeout_keep_alive=0,
    )
    raise RuntimeError('server stopped')


def _run_server_worker(args: argparse.Namespace) -> ta.NoReturn:
    payload = bytes(range(256)) * (args.payload_size // 256) + bytes(range(args.payload_size % 256))
    max_upload_size = max(64 * 1024, args.payload_size * 2)

    if args.implementation == 'sync':
        _serve_sync(args.port, payload, max_upload_size, args.server_threads)
    elif args.implementation == 'asyncio':
        asyncio.run(_serve_asyncio_async(args.port, payload, max_upload_size))
    elif args.implementation == 'fdio':
        _serve_fdio(args.port, payload, max_upload_size)
    elif args.implementation == 'uvicorn':
        _serve_uvicorn(args.port, payload, max_upload_size)
    else:
        raise ValueError(args.implementation)
    raise RuntimeError('server stopped')


##
# curl server load


def _make_curl_command(
        executable: str,
        url: str,
        scenario: str,
        count: int,
        payload_path: str,
        timeout_s: float,
) -> ta.List[str]:
    command = [
        executable,
        '--silent',
        '--show-error',
        '--http1.1',
        '--max-time',
        str(timeout_s),
        '--header',
        'Connection: close',
        '--header',
        'Expect:',
        '--write-out',
        'OMCORE_BENCH %{http_code} %{time_total} %{size_download} %{size_upload}\\n',
    ]
    if scenario == 'upload':
        command.extend(['--request', 'POST', '--data-binary', f'@{payload_path}'])
    for _ in range(count):
        command.extend(['--output', os.devnull, url])
    return command


def _run_curl_load(
        executable: str,
        base_url: str,
        scenario: str,
        requests: int,
        concurrency: int,
        payload_path: str,
        timeout_s: float,
) -> ta.Tuple[float, ta.List[int], int]:
    if scenario == 'requests':
        url = f'{base_url}/empty'
    elif scenario == 'download':
        url = f'{base_url}/download'
    elif scenario == 'upload':
        url = f'{base_url}/upload'
    else:
        raise ValueError(scenario)

    processes: ta.List[subprocess.Popen] = []
    started = time.perf_counter()
    try:
        for count in _partition(requests, concurrency):
            processes.append(subprocess.Popen(
                _make_curl_command(executable, url, scenario, count, payload_path, timeout_s),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ))

        latencies: ta.List[int] = []
        transferred = 0
        for process in processes:
            try:
                stdout, stderr = process.communicate(timeout=timeout_s * requests + 10.)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                stdout, stderr = process.communicate()
                raise TimeoutError(
                    f'curl load worker timed out\nstdout:\n{stdout}\nstderr:\n{stderr}',
                ) from exc
            if process.returncode:
                raise RuntimeError(
                    f'curl load worker failed ({process.returncode})\nstdout:\n{stdout}\nstderr:\n{stderr}',
                )

            for line in stdout.splitlines():
                if not line.startswith('OMCORE_BENCH '):
                    continue
                _, status, latency_s, downloaded, uploaded = line.split()
                if not 200 <= int(status) < 300:
                    raise RuntimeError(f'unexpected curl HTTP status: {line!r}')
                latencies.append(int(float(latency_s) * 1_000_000_000))
                if scenario == 'download':
                    transferred += int(downloaded)
                elif scenario == 'upload':
                    transferred += int(uploaded)

        elapsed = time.perf_counter() - started
        if len(latencies) != requests:
            raise RuntimeError(f'curl reported {len(latencies)} of {requests} request latencies')
        return elapsed, latencies, transferred

    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()


def _run_server_implementation(
        *,
        implementation: str,
        scenarios: ta.Sequence[str],
        executable: str,
        requests: int,
        transfer_requests: int,
        concurrency: int,
        warmup: int,
        payload_size: int,
        timeout_s: float,
        server_threads: int,
) -> ta.List[BenchmarkResult]:
    port = _find_free_port()
    command = [
        sys.executable,
        '-m',
        MODULE_NAME,
        '--_worker',
        'server',
        '--implementation',
        implementation,
        '--port',
        str(port),
        '--payload-size',
        str(payload_size),
        '--server-threads',
        str(server_threads),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stopped = False
    try:
        _wait_http_ready(process, port, timeout_s=timeout_s)
        base_url = f'http://127.0.0.1:{port}'

        with tempfile.TemporaryDirectory(prefix='omcore-http-bench-curl-') as temp_dir:
            payload_path = os.path.join(temp_dir, 'payload.bin')
            _write_payload(payload_path, payload_size)

            results: ta.List[BenchmarkResult] = []
            with _ProcessRssSampler(process.pid) as sampler:
                for scenario in scenarios:
                    case_requests = requests if scenario == 'requests' else transfer_requests
                    if warmup:
                        _run_curl_load(
                            executable,
                            base_url,
                            scenario,
                            min(warmup, case_requests),
                            concurrency,
                            payload_path,
                            timeout_s,
                        )

                    rss_before = sampler.reset()
                    elapsed, latencies, transferred = _run_curl_load(
                        executable,
                        base_url,
                        scenario,
                        case_requests,
                        concurrency,
                        payload_path,
                        timeout_s,
                    )
                    peak_rss = sampler.peak
                    results.append(_make_result(
                        suite='server',
                        implementation=implementation,
                        scenario=scenario,
                        requests=case_requests,
                        concurrency=min(concurrency, case_requests),
                        elapsed_s=elapsed,
                        transferred_bytes=transferred,
                        latencies_ns=latencies,
                        rss_before_bytes=rss_before,
                        peak_rss_bytes=peak_rss,
                        notes=(
                            'curl-reported latency; wall throughput includes load-generator orchestration',
                            'one HTTP/1.1 connection per request',
                        ),
                    ))

            return results

    except BaseException as exc:
        stdout, stderr = _stop_process(process)
        stopped = True
        raise RuntimeError(
            f'{implementation} server benchmark failed: {exc}\n'
            f'server stdout:\n{stdout}\nserver stderr:\n{stderr}',
        ) from exc

    finally:
        if not stopped:
            _stop_process(process)


##
# Suite orchestration and output


def _unavailable_result(suite: str, implementation: str, scenario: str, reason: str) -> BenchmarkResult:
    return BenchmarkResult(
        suite=suite,
        implementation=implementation,
        scenario=scenario,
        available=False,
        reason=reason,
    )


def _run_client_suite(
        args: argparse.Namespace,
        scenarios: ta.Sequence[str],
        *,
        target_factory: ta.Optional[ta.Callable[[], ta.ContextManager[str]]] = None,
        case_runner: ta.Callable[..., BenchmarkResult] = _run_client_case,
) -> ta.List[BenchmarkResult]:
    implementations = _parse_names(args.clients, CLIENT_IMPLEMENTATIONS)
    results: ta.List[BenchmarkResult] = []

    if target_factory is None:
        @contextlib.contextmanager
        def default_target() -> ta.Iterator[str]:
            if args.client_base_url:
                yield args.client_base_url.rstrip('/')
            else:
                # A fresh listening port prevents one-connection-per-request cases from inheriting closed-connection
                # state from cases that ran earlier in the suite. This is deliberately portable rather than relying on
                # platform-specific socket options or TCP sysctls.
                with _NginxFixture(args.nginx, args.payload_size, args.timeout) as nginx:
                    yield nginx.base_url

        target_factory = default_target

    for implementation in implementations:
        if implementation == 'httpx' and not _module_available('httpx'):
            results.extend(
                _unavailable_result('client', implementation, scenario, 'httpx is not installed')
                for scenario in scenarios
            )
            continue

        for scenario in scenarios:
            with target_factory() as base_url:
                case_requests = args.requests if scenario == 'requests' else args.transfer_requests
                results.append(case_runner(
                    implementation=implementation,
                    scenario=scenario,
                    base_url=base_url,
                    requests=case_requests,
                    concurrency=args.concurrency,
                    warmup=min(args.warmup, case_requests),
                    payload_size=args.payload_size,
                    timeout_s=args.timeout,
                ))

    return results


def _run_server_suite(args: argparse.Namespace, scenarios: ta.Sequence[str]) -> ta.List[BenchmarkResult]:
    implementations = _parse_names(args.servers, SERVER_IMPLEMENTATIONS)
    executable = shutil.which(args.curl) if os.path.sep not in args.curl else args.curl
    if not executable or not os.path.isfile(executable):
        raise FileNotFoundError(f'curl executable not found: {args.curl!r}')

    results: ta.List[BenchmarkResult] = []
    for implementation in implementations:
        if implementation == 'uvicorn' and not _module_available('uvicorn'):
            results.extend(
                _unavailable_result('server', implementation, scenario, 'uvicorn is not installed')
                for scenario in scenarios
            )
            continue

        results.extend(_run_server_implementation(
            implementation=implementation,
            scenarios=scenarios,
            executable=executable,
            requests=args.requests,
            transfer_requests=args.transfer_requests,
            concurrency=args.concurrency,
            warmup=args.warmup,
            payload_size=args.payload_size,
            timeout_s=args.timeout,
            server_threads=max(args.server_threads, args.concurrency),
        ))
    return results


def _format_rate(value: float) -> str:
    if value >= 1000.:
        return f'{value:,.0f}'
    if value >= 100.:
        return f'{value:,.1f}'
    return f'{value:,.2f}'


def _format_mib(value: ta.Optional[int]) -> str:
    if value is None:
        return '-'
    return f'{value / (1024 ** 2):.1f}'


def _print_results(metadata: ta.Mapping[str, ta.Any], results: ta.Sequence[BenchmarkResult]) -> None:
    print(
        f'Python {metadata["python"]} '
        f'({metadata["python_implementation"]}); '
        f'{metadata["platform"]}; '
        f'CPUs={metadata["cpu_count"]}; '
        f'payload={metadata["payload_size"]} bytes',
    )
    if metadata.get('nginx'):
        print(f'nginx: {metadata["nginx"]}')
    if metadata.get('curl'):
        print(f'curl: {metadata["curl"]}')
    print()

    headings = (
        'suite',
        'scenario',
        'implementation',
        'n/c',
        'req/s',
        'MiB/s',
        'p50 ms',
        'p99 ms',
        'RSS MiB',
        '+RSS MiB',
    )
    rows: ta.List[ta.Tuple[str, ...]] = []
    for result in sorted(results, key=lambda r: (r.suite, r.scenario)):
        if not result.available:
            rows.append((
                result.suite,
                result.scenario,
                result.implementation,
                '-',
                'unavailable',
                '-',
                '-',
                '-',
                '-',
                result.reason or '-',
            ))
            continue

        latency = result.latency_ms or {}
        rows.append((
            result.suite,
            result.implementation,
            result.scenario,
            f'{result.requests}/{result.concurrency}',
            _format_rate(result.requests_per_s),
            _format_rate(result.bytes_per_s / (1024 ** 2)) if result.transferred_bytes else '-',
            f'{latency.get("p50", 0.):.3f}',
            f'{latency.get("p99", 0.):.3f}',
            _format_mib(result.peak_rss_bytes),
            _format_mib(result.rss_growth_bytes),
        ))

    widths = [len(heading) for heading in headings]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def line(row: ta.Sequence[str]) -> str:
        return '  '.join(value.ljust(widths[i]) for i, value in enumerate(row)).rstrip()

    print(line(headings))
    print(line(tuple('-' * width for width in widths)))
    for row in rows:
        print(line(row))


##
# CLI


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Dependency-light HTTP pipeline client/server benchmarks.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--suite', choices=('all', 'clients', 'servers'), default='all')
    parser.add_argument('--clients', default=','.join(CLIENT_IMPLEMENTATIONS))
    parser.add_argument('--servers', default=','.join(SERVER_IMPLEMENTATIONS))
    parser.add_argument('--scenarios', default=','.join(SCENARIOS))
    parser.add_argument('--requests', type=_positive_int, default=1000, help='request-count workload operations')
    parser.add_argument(
        '--transfer-requests',
        type=_positive_int,
        default=64,
        help='operations per upload/download case',
    )
    parser.add_argument('--warmup', type=int, default=25, help='warmup operations per case; zero disables warmup')
    parser.add_argument('--concurrency', type=_positive_int, default=16)
    parser.add_argument('--payload-size', type=_parse_size, default=1024 ** 2)
    parser.add_argument('--timeout', type=float, default=30.)
    parser.add_argument('--server-threads', type=_positive_int, default=64)
    parser.add_argument('--nginx', default=os.environ.get('OMCORE_HTTP_BENCH_NGINX', 'nginx'))
    parser.add_argument('--curl', default=os.environ.get('OMCORE_HTTP_BENCH_CURL', 'curl'))
    parser.add_argument('--client-base-url', help='use an existing client target instead of starting nginx')
    parser.add_argument('--json', action='store_true', help='emit a JSON report instead of a table')

    parser.add_argument('--_worker', dest='worker_mode', choices=('client', 'server'), help=argparse.SUPPRESS)
    parser.add_argument('--implementation', help=argparse.SUPPRESS)
    parser.add_argument('--scenario', help=argparse.SUPPRESS)
    parser.add_argument('--base-url', help=argparse.SUPPRESS)
    parser.add_argument('--case-requests', type=_positive_int, help=argparse.SUPPRESS)
    parser.add_argument('--port', type=int, help=argparse.SUPPRESS)
    return parser


def _main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.warmup < 0:
        parser.error('--warmup must be non-negative')
    if args.timeout <= 0.:
        parser.error('--timeout must be positive')

    if args.worker_mode == 'client':
        if not all((args.implementation, args.scenario, args.base_url, args.case_requests)):
            parser.error('incomplete internal client worker arguments')
        print(json.dumps(_run_client_worker(args).as_dict(), sort_keys=True))
        return

    if args.worker_mode == 'server':
        if not args.implementation or not args.port:
            parser.error('incomplete internal server worker arguments')
        _run_server_worker(args)

    try:
        scenarios = _parse_names(args.scenarios, SCENARIOS)
        results: ta.List[BenchmarkResult] = []
        if args.suite in ('all', 'clients'):
            results.extend(_run_client_suite(args, scenarios))
        if args.suite in ('all', 'servers'):
            results.extend(_run_server_suite(args, scenarios))
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    metadata = _make_metadata(args)
    if args.json:
        print(json.dumps({
            'metadata': metadata,
            'results': [result.as_dict() for result in results],
        }, indent=2, sort_keys=True))
    else:
        _print_results(metadata, results)


if __name__ == '__main__':
    _main()
