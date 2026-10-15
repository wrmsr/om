"""
Publish TCP ports of running Docker containers, or hand them host-side services, without restarting them and without
target-side tools.

Host: Python 3.10+, Docker CLI, macOS or Linux.

Daemon: rootful Linux Docker / Docker Desktop; amd64 or arm64.

Helper: a native Linux image with Python 3.10+ (default: python:3.14-slim).

python hotport.py expose TARGET [HOST_IP:]HOST_PORT[:TARGET_PORT]
python hotport.py unexpose TARGET [HOST_IP:]HOST_PORT
python hotport.py inject TARGET TARGET_PORT[:[UPSTREAM_HOST:]UPSTREAM_PORT]
python hotport.py uninject TARGET TARGET_PORT
python hotport.py list [TARGET]
python hotport.py cleanup [TARGET]

Each mapping is one long-lived privileged helper container (--pid=host) that setns()es into the target's network
namespace and relays TCP connections. Nothing is executed in the target and the target needs no tools; services bound
only to the target's loopback are reachable. State lives in helper labels, not in a local host registry.

expose: Docker publishes HOST_PORT to the helper (-p); the helper dials 127.0.0.1:TARGET_PORT inside the target.

inject: the helper plants a listener on the target's 127.0.0.1:TARGET_PORT and dials the upstream (default
host.docker.internal:TARGET_PORT) from its own network namespace. With --net bridge (default) that reaches the host on
Docker Desktop, and on Linux via host-gateway, i.e. host services not bound to loopback only. With --net host the
helper lives in the daemon host's network namespace, which on Linux reaches services on the host's own 127.0.0.1.

Mappings are not persistent Docker configuration. The helper exits when the target's network namespace goes away
(stop/restart) and is left in place as a record until `cleanup`; re-run expose/inject after restarting the target.
TCP only. Rootless Docker and nonstandard runtimes such as gVisor are deliberately out of scope. This is an
administrative tool, not a hostile-container security boundary.
"""
import argparse
import dataclasses as dc
import hashlib
import inspect
import ipaddress
import json
import subprocess
import sys
import textwrap
import time
import typing as ta


##


_LABEL = 'io.wrmsr.hotport.record'

_DEFAULT_IMAGE = 'python:3.14-slim'

_DEFAULT_UPSTREAM_HOST = 'host.docker.internal'

_READY_PREFIX = 'HOTPORT READY '


@dc.dataclass(frozen=True)
class MappingSpec:
    kind: str  # 'expose' | 'inject'
    target_id: str
    target_name: str
    target_started: str

    # expose: host side (published by Docker) -> target side (dialed inside the target)
    host_ip: str = ''  # '' = all host interfaces
    host_port: int = 0
    target_port: int = 0
    connect_host: str = '127.0.0.1'

    # inject: target side (bound inside the target) -> upstream (dialed from the helper's own namespace)
    listen_host: str = '127.0.0.1'
    upstream_host: str = ''
    upstream_port: int = 0
    net: str = 'bridge'

    def describe(self) -> str:
        if self.kind == 'expose':
            return f'{self.host_ip or "*"}:{self.host_port} -> target {self.connect_host}:{self.target_port}'
        return f'target {self.listen_host}:{self.target_port} -> {self.upstream_host}:{self.upstream_port} ({self.net})'

    def key(self) -> str:
        if self.kind == 'expose':
            return f'{self.host_ip}:{self.host_port}'
        return f'{self.listen_host}:{self.target_port}'


def split_host_ports(spec: str) -> list[str]:
    """Splits on ':' outside [...] and strips the brackets, so IPv6 literals survive."""

    parts: list[str] = []
    cur = ''
    depth = 0
    for ch in spec:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if ch == ':' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    if depth:
        raise ValueError(f'unbalanced brackets: {spec!r}')
    return [p[1:-1] if p.startswith('[') and p.endswith(']') else p for p in parts]


def parse_port(s: str) -> int:
    try:
        port = int(s)
    except ValueError:
        raise ValueError(f'invalid port: {s!r}') from None
    if not 1 <= port <= 65535:
        raise ValueError(f'port out of range: {port}')
    return port


def parse_ip(s: str, what: str) -> str:
    try:
        return str(ipaddress.ip_address(s))
    except ValueError:
        raise ValueError(f'{what} must be an IP literal, not {s!r}') from None


def parse_expose_spec(spec: str) -> tuple[str, int, int]:
    """[HOST_IP:]HOST_PORT[:TARGET_PORT] -> (host_ip, host_port, target_port)"""

    parts = split_host_ports(spec)
    if len(parts) == 1:
        host_ip, host_port, target_port = '', parts[0], parts[0]
    elif len(parts) == 2:
        if parts[0] and not parts[0].isdigit():
            host_ip, host_port, target_port = parts[0], parts[1], parts[1]
        else:
            host_ip, host_port, target_port = '', parts[0], parts[1]
    elif len(parts) == 3:
        host_ip, host_port, target_port = parts
    else:
        raise ValueError(f'expected [HOST_IP:]HOST_PORT[:TARGET_PORT], got {spec!r}')
    return (
        parse_ip(host_ip, 'host ip') if host_ip else '',
        parse_port(host_port),
        parse_port(target_port),
    )


def parse_unexpose_spec(spec: str) -> tuple[str, int]:
    """[HOST_IP:]HOST_PORT -> (host_ip, host_port)"""

    parts = split_host_ports(spec)
    if len(parts) == 1:
        return '', parse_port(parts[0])
    if len(parts) == 2:
        return (parse_ip(parts[0], 'host ip') if parts[0] else ''), parse_port(parts[1])
    raise ValueError(f'expected [HOST_IP:]HOST_PORT, got {spec!r}')


def parse_inject_spec(spec: str) -> tuple[int, str, int]:
    """TARGET_PORT[:[UPSTREAM_HOST:]UPSTREAM_PORT] -> (target_port, upstream_host, upstream_port)"""

    parts = split_host_ports(spec)
    if len(parts) == 1:
        target_port, upstream_host, upstream_port = parts[0], _DEFAULT_UPSTREAM_HOST, parts[0]
    elif len(parts) == 2:
        target_port, upstream_host, upstream_port = parts[0], _DEFAULT_UPSTREAM_HOST, parts[1]
    elif len(parts) == 3:
        target_port, upstream_host, upstream_port = parts
    else:
        raise ValueError(f'expected TARGET_PORT[:[UPSTREAM_HOST:]UPSTREAM_PORT], got {spec!r}')
    if not upstream_host:
        raise ValueError('empty upstream host')
    return parse_port(target_port), upstream_host, parse_port(upstream_port)


def build_helper_name(*, target_id: str, kind: str, key: str) -> str:
    digest = hashlib.sha256(f'{target_id}\0{kind}\0{key}'.encode()).hexdigest()[:24]
    return f'hotport-{digest}'


##  Remote payload: all dependencies intentionally live inside this function.


def _helper_main() -> None:
    import asyncio
    import ctypes as ct
    import errno
    import json
    import os
    import signal
    import socket
    import sys
    import threading
    import time
    import typing as ta

    request = json.loads(sys.argv[1])

    if sys.platform != 'linux':
        raise RuntimeError('helper must run on Linux')

    clone_newnet = 0x40000000

    libc = ct.CDLL(None, use_errno=True)
    libc.setns.restype = ct.c_int
    libc.setns.argtypes = [ct.c_int, ct.c_int]

    verbose = bool(request.get('verbose'))

    def log(msg: str) -> None:
        print(f'hotport: {msg}', file=sys.stderr, flush=True)

    def check(result: int, operation: str) -> int:
        if result == -1:
            err = ct.get_errno()
            hint = ''
            if err == errno.EPERM:
                hint = '; the helper needs --privileged --pid=host --userns=host on a rootful daemon'
            raise OSError(err, f'{operation}: {os.strerror(err)}{hint}')
        return result

    def read_text(path: str) -> str:
        with open(path) as f:
            return f.read()

    def identity(pid: int) -> dict[str, ta.Any]:
        ns = os.stat(f'/proc/{pid}/ns/net')
        fields = read_text(f'/proc/{pid}/stat').rsplit(')', 1)[1].split()
        return {
            'start_ticks': int(fields[19]),  # /proc/PID/stat field 22; comm may contain spaces or ')'.
            'net_ns': [ns.st_dev, ns.st_ino],
        }

    pid = int(request['target_pid'])
    if pid <= 0:
        raise ValueError('invalid target PID')

    ident = identity(pid)
    target_ns = os.open(f'/proc/{pid}/ns/net', os.O_RDONLY | os.O_CLOEXEC)
    self_ns = os.open('/proc/self/ns/net', os.O_RDONLY | os.O_CLOEXEC)
    # The PID could have been recycled between the stat and the open; the fd now pins the namespace we read.
    if identity(pid) != ident or os.stat(f'/proc/self/fd/{target_ns}').st_ino != ident['net_ns'][1]:
        raise RuntimeError('target changed during helper startup; refusing stale PID/namespace')

    ns_fds = {'self': self_ns, 'target': target_ns}

    def enter(ns: str) -> None:
        # setns(CLONE_NEWNET) moves only the calling thread; sockets belong to the namespace they are created in.
        check(libc.setns(ns_fds[ns], clone_newnet), f'setns({ns} net)')

    def family(host: str) -> int:
        return socket.AF_INET6 if ':' in host else socket.AF_INET

    # Listener: created in the listen namespace, served from the dial namespace.
    listen_ns, listen_host, listen_port = request['listen_ns'], request['listen_host'], int(request['listen_port'])
    enter(listen_ns)
    srv = socket.socket(family(listen_host), socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((listen_host, listen_port))
    except OSError as exc:
        raise RuntimeError(
            f'cannot listen on {listen_host}:{listen_port} in the {listen_ns} namespace: {exc.strerror}',
        ) from None
    srv.listen(128)
    srv.setblocking(False)

    # Dial side: resolve once, in the dial namespace, since resolver sockets must live there too.
    dial_ns, dial_host, dial_port = request['dial_ns'], request['dial_host'], int(request['dial_port'])
    enter(dial_ns)
    try:
        infos = socket.getaddrinfo(dial_host, dial_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError(f'cannot resolve {dial_host} in the {dial_ns} namespace: {exc}') from None
    infos.sort(key=lambda i: i[0] != socket.AF_INET)  # prefer IPv4
    dial_addr: tuple[str, int] = infos[0][4][:2]  # type: ignore[assignment]

    # Watchdog: the pinned namespace outlives the target, so detect the target going away ourselves.
    def watchdog() -> None:
        while True:
            time.sleep(2.)
            try:
                ok = identity(pid) == ident
            except OSError:
                ok = False
            if not ok:
                log('target process or network namespace is gone; exiting')
                os._exit(3)

    threading.Thread(target=watchdog, daemon=True).start()

    active = 0

    async def pump(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while data := await reader.read(65536):
                writer.write(data)
                await writer.drain()
            if writer.can_write_eof():
                writer.write_eof()  # propagate half-close
        except OSError:
            writer.close()

    async def handle(cr: asyncio.StreamReader, cw: asyncio.StreamWriter) -> None:
        nonlocal active
        peer = cw.get_extra_info('peername')
        try:
            ur, uw = await asyncio.wait_for(asyncio.open_connection(*dial_addr), timeout=10.)
        except (OSError, asyncio.TimeoutError) as exc:
            log(f'{peer}: dial {dial_addr[0]}:{dial_addr[1]} failed: {exc}')
            cw.close()
            return
        active += 1
        if verbose:
            log(f'{peer}: open ({active} active)')
        try:
            await asyncio.gather(pump(cr, uw), pump(ur, cw))
        finally:
            active -= 1
            for w in (cw, uw):
                w.close()
            if verbose:
                log(f'{peer}: closed ({active} active)')

    async def main() -> None:
        loop = asyncio.get_running_loop()
        stop = asyncio.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop.set)
        server = await asyncio.start_server(handle, sock=srv)
        print(_READY_PREFIX + json.dumps({
            'target_pid': pid,
            'identity': ident,
            'listen': [listen_ns, listen_host, listen_port],
            'dial': [dial_ns, dial_addr[0], dial_addr[1]],
        }), flush=True)
        async with server:
            await stop.wait()
        log('stopped')

    asyncio.run(main())


##  Host-side Docker orchestration.


class DockerCli:
    def __init__(
            self,
            *,
            executable: str = 'docker',
            context: str | None = None,
            timeout: float = 300.,
            verbose: bool = False,
    ) -> None:
        super().__init__()

        self._prefix = [executable]
        if context is not None:
            self._prefix.extend(['--context', context])
        self._timeout = timeout
        self._verbose = verbose

    def run(self, *args: str, merge_stderr: bool = False) -> str:
        if self._verbose:
            # Do not flood stderr with the several-hundred-line Python payload.
            shown = list(args)
            if '-c' in shown:
                index = shown.index('-c')
                shown[index + 1] = '<python payload>'
            print(f'docker {shown!r}', file=sys.stderr)

        try:
            result = subprocess.run(
                [
                    *self._prefix,
                    *args,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f'docker {args[0]} timed out after {self._timeout:g} seconds') from exc

        if result.returncode:
            detail = (result.stdout if merge_stderr else result.stderr).strip()
            raise RuntimeError(f'docker {args[0]} failed ({result.returncode}):\n{detail}')

        return result.stdout.strip()

    def inspect(self, container: str) -> dict[str, ta.Any]:
        return json.loads(self.run('container', 'inspect', container))[0]

    def try_inspect(self, container: str) -> dict[str, ta.Any] | None:
        try:
            return self.inspect(container)
        except RuntimeError as exc:
            if 'No such' in str(exc):
                return None
            raise

    def logs(self, container: str) -> str:
        return self.run('container', 'logs', container, merge_stderr=True)


def require_running(info: ta.Mapping[str, ta.Any]) -> None:
    if (
            not info['State']['Running'] or
            info['State']['Pid'] <= 0 or
            info['State'].get('Restarting')
    ):
        raise RuntimeError(f"container is not stably running: {info['Name']}")


def require_same_incarnation(before: ta.Mapping[str, ta.Any], after: ta.Mapping[str, ta.Any]) -> None:
    require_running(after)
    for key in ('Pid', 'StartedAt'):
        if before['State'][key] != after['State'][key]:
            raise RuntimeError(f"container restarted during operation: {after['Name']}")


class HotPorter:
    def __init__(
            self,
            docker: DockerCli,
            *,
            image: str = _DEFAULT_IMAGE,
            python: str = 'python3',
            ready_timeout: float = 30.,
            verbose: bool = False,
    ) -> None:
        super().__init__()

        self._docker = docker
        self._image = image
        self._python = python
        self._ready_timeout = ready_timeout
        self._verbose = verbose

    #

    def _get_platform(self) -> str:
        info = json.loads(self._docker.run('info', '--format', '{{json .}}'))
        if info.get('OSType') != 'linux':
            raise RuntimeError('the Docker daemon must run Linux containers')
        if any('rootless' in s for s in info.get('SecurityOptions', [])):
            raise RuntimeError('rootless Docker is not supported')
        arch = {
            'x86_64': 'amd64',
            'amd64': 'amd64',
            'aarch64': 'arm64',
            'arm64': 'arm64',
        }.get(info['Architecture'])
        if arch is None:
            raise RuntimeError(f"unsupported daemon architecture: {info['Architecture']}")
        return f'linux/{arch}'

    def _payload(self) -> str:
        return (
            f'_READY_PREFIX = {_READY_PREFIX!r}\n' +
            textwrap.dedent(inspect.getsource(_helper_main)) +
            '\n_helper_main()\n'
        )

    def _helper_request(self, spec: MappingSpec, target_pid: int) -> dict[str, ta.Any]:
        if spec.kind == 'expose':
            return {
                'target_pid': target_pid,
                'listen_ns': 'self',
                'listen_host': '0.0.0.0',
                'listen_port': spec.host_port,
                'dial_ns': 'target',
                'dial_host': spec.connect_host,
                'dial_port': spec.target_port,
                'verbose': self._verbose,
            }
        if spec.kind == 'inject':
            return {
                'target_pid': target_pid,
                'listen_ns': 'target',
                'listen_host': spec.listen_host,
                'listen_port': spec.target_port,
                'dial_ns': 'self',
                'dial_host': spec.upstream_host,
                'dial_port': spec.upstream_port,
                'verbose': self._verbose,
            }
        raise ValueError(spec.kind)

    def _helper_create_args(self, spec: MappingSpec, name: str, platform: str) -> list[str]:
        args = [
            'create',
            '--name', name,
            '--platform', platform,
            '--pid=host',
            '--privileged',
            '--userns=host',
            '--user=0:0',
            '--label', f'{_LABEL}={json.dumps(dc.asdict(spec))}',
        ]
        if spec.kind == 'expose':
            publish = f'{spec.host_port}:{spec.host_port}/tcp'
            if spec.host_ip:
                publish = f'{spec.host_ip}:{publish}'
            args.extend(['--network=bridge', '--publish', publish])
        else:
            args.append(f'--network={spec.net}')
            if spec.net == 'bridge':
                args.extend(['--add-host', 'host.docker.internal:host-gateway'])
        return args

    def _wait_ready(self, name: str) -> dict[str, ta.Any]:
        deadline = time.monotonic() + self._ready_timeout
        while True:
            info = self._docker.inspect(name)
            logs = self._docker.logs(name)
            for line in logs.splitlines():
                if line.startswith(_READY_PREFIX):
                    return json.loads(line[len(_READY_PREFIX):])
            if not info['State']['Running']:
                raise RuntimeError(f"helper exited ({info['State']['ExitCode']}):\n{logs.strip()}")
            if time.monotonic() > deadline:
                raise RuntimeError(f'helper did not become ready:\n{logs.strip()}')
            time.sleep(.2)

    def _start(self, spec: MappingSpec, target_info: ta.Mapping[str, ta.Any]) -> dict[str, ta.Any]:
        require_running(target_info)
        platform = self._get_platform()
        name = build_helper_name(target_id=spec.target_id, kind=spec.kind, key=spec.key())

        # The deterministic name is also a daemon-side reservation for this target/mapping.
        existing = self._docker.try_inspect(name)
        if existing is not None:
            if existing['State']['Running']:
                raise RuntimeError(f'mapping already exists ({name}); remove it first')
            self._docker.run('container', 'rm', '--force', name)  # a dead helper is only a record

        self._docker.run(
            *self._helper_create_args(spec, name, platform),
            '--entrypoint', self._python,
            self._image,
            '-I',
            '-S',
            '-c',
            self._payload(),
            json.dumps(self._helper_request(spec, target_info['State']['Pid'])),
        )

        try:
            self._docker.run('container', 'start', name)
            ready = self._wait_ready(name)
            # The helper pinned whatever /proc/PID was; this confirms PID was the target the whole time.
            require_same_incarnation(target_info, self._docker.inspect(spec.target_id))
        except BaseException:
            try:
                self._docker.run('container', 'rm', '--force', name)
            except RuntimeError as exc:
                print(f'Could not clean up helper {name}: {exc}', file=sys.stderr)
            raise

        return {
            'helper': name,
            'target': spec.target_name,
            'mapping': spec.describe(),
            **ready,
        }

    #

    def expose(
            self,
            target: str,
            spec: str,
            *,
            connect_host: str = '127.0.0.1',
    ) -> dict[str, ta.Any]:
        host_ip, host_port, target_port = parse_expose_spec(spec)
        target_info = self._docker.inspect(target)
        return self._start(
            MappingSpec(
                kind='expose',
                target_id=target_info['Id'],
                target_name=target_info['Name'].lstrip('/'),
                target_started=target_info['State']['StartedAt'],
                host_ip=host_ip,
                host_port=host_port,
                target_port=target_port,
                connect_host=parse_ip(connect_host, 'connect host'),
            ),
            target_info,
        )

    def inject(
            self,
            target: str,
            spec: str,
            *,
            listen_host: str = '127.0.0.1',
            net: str = 'bridge',
    ) -> dict[str, ta.Any]:
        target_port, upstream_host, upstream_port = parse_inject_spec(spec)
        if net not in ('bridge', 'host'):
            raise ValueError(f'net must be bridge or host, not {net!r}')
        target_info = self._docker.inspect(target)
        return self._start(
            MappingSpec(
                kind='inject',
                target_id=target_info['Id'],
                target_name=target_info['Name'].lstrip('/'),
                target_started=target_info['State']['StartedAt'],
                target_port=target_port,
                listen_host=parse_ip(listen_host, 'listen host'),
                upstream_host=upstream_host,
                upstream_port=upstream_port,
                net=net,
            ),
            target_info,
        )

    #

    def _records(self) -> list[tuple[dict[str, ta.Any], MappingSpec]]:
        ids = self._docker.run(
            'container', 'ls', '--all', '--quiet', '--no-trunc',
            '--filter', f'label={_LABEL}',
        ).split()
        result = []
        for container_id in ids:
            helper = self._docker.inspect(container_id)
            try:
                spec = MappingSpec(**json.loads(helper['Config']['Labels'][_LABEL]))
            except (KeyError, TypeError, ValueError):
                continue  # a label from a different version of this tool
            result.append((helper, spec))
        return result

    def _resolve_target(self, target: str) -> tuple[str | None, str]:
        """Returns (id, name). Records match either, so helpers of a removed or recreated target are still found."""

        info = self._docker.try_inspect(target)
        if info is not None:
            return info['Id'], info['Name'].lstrip('/')
        return None, target

    def _matching(
            self,
            target: str | None,
            *,
            kind: str | None = None,
            key: str | None = None,
    ) -> list[tuple[dict[str, ta.Any], MappingSpec]]:
        target_id, target_name = self._resolve_target(target) if target is not None else (None, None)
        return [
            (helper, spec)
            for helper, spec in self._records()
            if target is None or spec.target_id == target_id or spec.target_name == target_name
            if kind is None or spec.kind == kind
            if key is None or spec.key() == key
        ]

    def list_mappings(self, target: str | None = None) -> list[dict[str, ta.Any]]:
        result = []
        for helper, spec in self._matching(target):
            current = self._docker.try_inspect(spec.target_id)
            if current is None:
                target_state = 'removed'
            elif not current['State']['Running']:
                target_state = 'stopped'
            elif current['State']['StartedAt'] != spec.target_started:
                target_state = 'restarted'
            else:
                target_state = 'running'
            state = helper['State']['Status']
            if state == 'exited':
                state = f"exited({helper['State']['ExitCode']})"
            result.append({
                'helper': helper['Name'].lstrip('/'),
                'helper_state': state,
                'kind': spec.kind,
                'mapping': spec.describe(),
                'target': spec.target_name,
                'target_state': target_state,
            })
        return result

    def remove(self, target: str, *, kind: str, key: str) -> list[str]:
        matches = self._matching(target, kind=kind, key=key)
        if not matches:
            raise RuntimeError(f'no such {kind} mapping for {target}: {key}')
        removed = []
        for helper, _ in matches:
            self._docker.run('container', 'rm', '--force', helper['Id'])
            removed.append(helper['Name'].lstrip('/'))
        return removed

    def cleanup(self, target: str | None = None) -> list[str]:
        removed = []
        for helper, _ in self._matching(target):
            if helper['State']['Running']:
                continue
            self._docker.run('container', 'rm', '--force', helper['Id'])
            removed.append(helper['Name'].lstrip('/'))
        return removed


##


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--context')
    parser.add_argument('--image', default=_DEFAULT_IMAGE)
    parser.add_argument('--python', default='python3', dest='helper_python')
    parser.add_argument(
        '--timeout',
        type=float,
        default=300.,
        help='timeout per Docker CLI invocation, in seconds',
    )
    parser.add_argument(
        '--ready-timeout',
        type=float,
        default=30.,
        help='seconds to wait for a helper to report ready',
    )
    parser.add_argument('--verbose', action='store_true', help='echo docker commands; helpers log each connection')

    commands = parser.add_subparsers(dest='command', required=True)

    expose = commands.add_parser(
        'expose',
        help='publish a target port on the host; HOST_PORT alone means the same port on both sides',
    )
    expose.add_argument('target')
    expose.add_argument('spec', metavar='[HOST_IP:]HOST_PORT[:TARGET_PORT]')
    expose.add_argument(
        '--connect-host',
        default='127.0.0.1',
        help='IP dialed inside the target (default 127.0.0.1; reaches services bound to 0.0.0.0 or loopback)',
    )

    unexpose = commands.add_parser('unexpose', help='remove a published port')
    unexpose.add_argument('target')
    unexpose.add_argument('spec', metavar='[HOST_IP:]HOST_PORT')

    inject = commands.add_parser(
        'inject',
        help='make an upstream service appear on the target loopback; default upstream is host.docker.internal:TARGET_PORT',  # noqa
    )
    inject.add_argument('target')
    inject.add_argument('spec', metavar='TARGET_PORT[:[UPSTREAM_HOST:]UPSTREAM_PORT]')
    inject.add_argument(
        '--listen-host',
        default='127.0.0.1',
        help='IP bound inside the target (default 127.0.0.1; 0.0.0.0 also serves the target network)',
    )
    inject.add_argument(
        '--net',
        default='bridge',
        choices=('bridge', 'host'),
        help='helper network: bridge reaches the host via host.docker.internal / host-gateway; '
             'host runs in the daemon host network namespace (Linux: reaches 127.0.0.1 services)',
    )

    uninject = commands.add_parser('uninject', help='remove an injected listener')
    uninject.add_argument('target')
    uninject.add_argument('spec', metavar='TARGET_PORT')
    uninject.add_argument('--listen-host', default='127.0.0.1')

    listing = commands.add_parser('list', help='list helper records')
    listing.add_argument('target', nargs='?')
    listing.add_argument('--json', action='store_true')

    cleanup = commands.add_parser('cleanup', help='remove helpers that are no longer running')
    cleanup.add_argument('target', nargs='?')

    args = parser.parse_args()
    if args.timeout <= 0 or args.ready_timeout <= 0:
        parser.error('timeouts must be positive')

    docker = DockerCli(
        executable=args.docker,
        context=args.context,
        timeout=args.timeout,
        verbose=args.verbose,
    )
    hp = HotPorter(
        docker,
        image=args.image,
        python=args.helper_python,
        ready_timeout=args.ready_timeout,
        verbose=args.verbose,
    )

    try:
        if args.command == 'expose':
            print(json.dumps(hp.expose(args.target, args.spec, connect_host=args.connect_host), indent=2))

        elif args.command == 'unexpose':
            host_ip, host_port = parse_unexpose_spec(args.spec)
            for name in hp.remove(args.target, kind='expose', key=f'{host_ip}:{host_port}'):
                print(name)

        elif args.command == 'inject':
            print(json.dumps(hp.inject(args.target, args.spec, listen_host=args.listen_host, net=args.net), indent=2))

        elif args.command == 'uninject':
            key = f"{parse_ip(args.listen_host, 'listen host')}:{parse_port(args.spec)}"
            for name in hp.remove(args.target, kind='inject', key=key):
                print(name)

        elif args.command == 'list':
            rows = hp.list_mappings(args.target)
            if args.json:
                print(json.dumps(rows, indent=2))
            elif rows:
                cols = ['helper', 'helper_state', 'kind', 'mapping', 'target', 'target_state']
                widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
                print('  '.join(c.upper().ljust(widths[c]) for c in cols).rstrip())
                for r in rows:
                    print('  '.join(str(r[c]).ljust(widths[c]) for c in cols).rstrip())

        elif args.command == 'cleanup':
            for name in hp.cleanup(args.target):
                print(name)

        else:
            raise ValueError(args.command)

    except (RuntimeError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _main()
