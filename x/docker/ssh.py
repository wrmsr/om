"""
ssh into dockerdev containers over `docker exec`, with nothing listening anywhere.

Host: Python 3.10+, Docker CLI, OpenSSH client; macOS or Linux.

Image: openssh-server installed (host keys generated at install time, as Debian/Ubuntu do) and a user that can be
exec'd as root. No sshd_config edits, no authorized_keys, no EXPOSE, no password, no sshd process.

Each ssh connection is one `docker exec -i -u root TARGET sh -c '... exec sshd -i ...'`. The proxy writes the caller's
public key into /run/om-ssh/ inside the container and starts sshd in inetd mode with `-f /dev/null`, so every policy
decision is on the command line below rather than in the image. Authorization is Docker socket access: anyone who can
`docker exec` already owns the container, so the ssh key adds no reachability and is a single unencrypted ed25519
pair generated once into ~/.om/ssh/. The ssh ControlMaster/ControlPersist machinery provides the long-lived channel
on top, and `ssh -O forward` / `-O cancel` add and remove port forwards on it at any time.

python dockerdev_ssh.py config [--install | --uninstall]      # `Host om-*` stanza; install Include into ~/.ssh/config
python dockerdev_ssh.py ssh NAME                                # interactive login
python dockerdev_ssh.py run NAME CMD [ARG...]                   # non-interactive, multiplexed
python dockerdev_ssh.py master NAME {start,stop,check}          # explicit control master lifecycle
python dockerdev_ssh.py forward NAME [-L SPEC]... [-R SPEC]... [-D PORT]...
python dockerdev_ssh.py cancel NAME [-L SPEC]... [-R SPEC]... [-D PORT]...
python dockerdev_ssh.py key [--rotate]
python dockerdev_ssh.py argv NAME                               # the ssh command line, for other tools
python dockerdev_ssh.py proxy ALIAS                             # the ProxyCommand; not for direct use

Once `config --install` has run, plain `ssh om-NAME`, scp, sftp, rsync, and IDE remote-ssh hosts work by name.

Container resolution is a Resolver; the default inspects Docker by name, dockerdev substitutes its db.
"""
import argparse
import dataclasses as dc
import os
import shlex
import shutil
import subprocess
import sys
import typing as ta


##  Container resolution


@dc.dataclass(frozen=True)
class Container:
    id: str
    name: str
    running: bool


class Resolver(ta.Protocol):
    def resolve(self, name: str) -> Container: ...


class DockerResolver:
    """Resolves a container by Docker name or id. dockerdev replaces this with a db lookup."""

    def __init__(self, docker: str = 'docker') -> None:
        super().__init__()

        self._docker = docker

    def resolve(self, name: str) -> Container:
        result = subprocess.run(
            [self._docker, 'container', 'inspect', '--format', '{{.Id}} {{.Name}} {{.State.Running}}', name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode:
            raise LookupError(f'no such container: {name}: {result.stderr.strip()}')
        cid, cname, running = result.stdout.split()
        return Container(id=cid, name=cname.lstrip('/'), running=running == 'true')


##  Config


_DOCKER_CANDIDATES = (
    '/usr/local/bin/docker',
    '/opt/homebrew/bin/docker',
    '/Applications/Docker.app/Contents/Resources/bin/docker',
    '/usr/bin/docker',
)


def find_docker(docker: str = 'docker') -> str:
    """ProxyCommands spawned by GUI-launched IDEs get a skeletal PATH; look harder than `which`."""

    if os.sep in docker:
        return docker
    if (found := shutil.which(docker)) is not None:
        return found
    for candidate in _DOCKER_CANDIDATES:
        if os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError(f'cannot find {docker!r} on PATH or in the usual places')


@dc.dataclass(frozen=True)
class SshConfig:
    state_dir: str = '~/.om/ssh'    # key pair, control sockets, generated ssh config
    host_prefix: str = 'om-'        # `ssh om-NAME`
    user: str = 'om'                # the only user sshd will admit; must exist in the image
    docker: str = 'docker'
    control_persist: str = '10m'    # how long an idle master lingers after its last client
    x11: bool = False               # X11Forwarding (needs xauth in the image)
    use_pam: bool = True            # see the UsePAM note below; must be True for a `!`-locked passwordless account
    proxy_command: tuple[str, ...] | None = None  # argv that runs `proxy ALIAS`; default: this file via sys.executable

    @property
    def state_path(self) -> str:
        return os.path.abspath(os.path.expanduser(self.state_dir))

    @property
    def key_path(self) -> str:
        return os.path.join(self.state_path, 'id_ed25519')

    @property
    def control_dir(self) -> str:
        return os.path.join(self.state_path, 'ctl')

    @property
    def config_path(self) -> str:
        return os.path.join(self.state_path, 'config')

    @property
    def proxy_argv(self) -> list[str]:
        """argv that, with the host alias appended, runs the proxy with this same configuration."""

        if self.proxy_command is not None:
            return list(self.proxy_command)
        argv = [sys.executable, os.path.abspath(__file__)]
        for flag, value, default in (
                ('--state-dir', self.state_dir, SshConfig.state_dir),
                ('--host-prefix', self.host_prefix, SshConfig.host_prefix),
                ('--user', self.user, SshConfig.user),
                ('--docker', self.docker, SshConfig.docker),
        ):
            if value != default:
                argv.extend([flag, value])
        if self.x11:
            argv.append('--x11')
        if not self.use_pam:
            argv.append('--no-pam')
        argv.append('proxy')
        return argv


##  In-container side: what the proxy runs via docker exec, as root, with the connection on stdin/stdout.
#
#   UsePAM note: with UsePAM=no, sshd's allowed_user() refuses any account whose shadow password is the '!' locked
#   marker, even for pubkey auth ("User <x> not allowed because account is locked"). `useradd` with no -p produces
#   exactly that, so a passwordless dev user is unreachable under UsePAM=no. Two ways out:
#     * UsePAM=yes (the default here): the locked passwordless account logs in fine, and sshd consults the image's
#       /etc/pam.d/sshd for account/session management only (not as an auth method), so pubkey-only still holds given
#       PasswordAuthentication=no + KbdInteractiveAuthentication=no + AuthenticationMethods=publickey below.
#     * UsePAM=no + give the user password field '*' (disabled, not locked) instead of '!': no PAM at all, every policy
#       on this command line. See the Dockerfile fragment. '*' is what root usually has; sshd accepts it.

_SSHD_SCRIPT = r'''
set -eu
d=/run/om-ssh
umask 022
install -d -m 0755 /run/sshd "$d"
printf '%s\n' "$OM_SSH_AUTHORIZED_KEYS" > "$d/authorized_keys.tmp"
mv -f "$d/authorized_keys.tmp" "$d/authorized_keys"
sshd=$(command -v sshd || echo /usr/sbin/sshd)
set --
if ! ls /etc/ssh/ssh_host_*_key >/dev/null 2>&1; then
  [ -f "$d/host_ed25519" ] || ssh-keygen -q -t ed25519 -N '' -f "$d/host_ed25519" >/dev/null
  set -- "$@" -h "$d/host_ed25519"
fi
[ -z "${OM_SSH_DEBUG:-}" ] || set -- "$@" -e -o LogLevel=DEBUG1
exec "$sshd" -i -f /dev/null "$@" \
  -o "AuthorizedKeysFile=$d/authorized_keys" \
  -o "AllowUsers=$OM_SSH_USER" \
  -o PermitRootLogin=no \
  -o AuthenticationMethods=publickey \
  -o PasswordAuthentication=no \
  -o KbdInteractiveAuthentication=no \
  -o PermitEmptyPasswords=no \
  -o "UsePAM=$OM_SSH_USEPAM" \
  -o UseDNS=no \
  -o PrintMotd=no \
  -o PrintLastLog=no \
  -o AllowTcpForwarding=yes \
  -o GatewayPorts=clientspecified \
  -o AllowStreamLocalForwarding=yes \
  -o StreamLocalBindUnlink=yes \
  -o AllowAgentForwarding=yes \
  -o "X11Forwarding=$OM_SSH_X11" \
  -o X11UseLocalhost=no \
  -o "AcceptEnv=LANG LC_*" \
  -o "Subsystem=sftp internal-sftp"
'''.strip()


##  Host side


class DockerDevSsh:
    def __init__(
            self,
            cfg: SshConfig = SshConfig(),
            resolver: Resolver | None = None,
            *,
            ssh: str = 'ssh',
    ) -> None:
        super().__init__()

        self._cfg = cfg
        self._resolver = resolver if resolver is not None else DockerResolver(cfg.docker)
        self._ssh = ssh

    @property
    def cfg(self) -> SshConfig:
        return self._cfg

    #  naming

    def alias(self, name: str) -> str:
        """Container name -> ssh host alias. Already-prefixed names pass through."""

        return name if name.startswith(self._cfg.host_prefix) else self._cfg.host_prefix + name

    def unalias(self, alias: str) -> str:
        return alias.removeprefix(self._cfg.host_prefix)

    #  state

    def ensure_state(self) -> None:
        os.makedirs(self._cfg.state_path, mode=0o700, exist_ok=True)
        os.makedirs(self._cfg.control_dir, mode=0o700, exist_ok=True)

    def ensure_key(self, *, rotate: bool = False) -> str:
        """The single, unencrypted ed25519 identity. Possession grants nothing without Docker socket access."""

        self.ensure_state()
        key = self._cfg.key_path
        if rotate:
            for p in (key, key + '.pub'):
                try:
                    os.unlink(p)
                except FileNotFoundError:
                    pass
        if not (os.path.exists(key) and os.path.exists(key + '.pub')):
            subprocess.run(
                ['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', 'dockerdev', '-f', key],
                check=True,
                stdin=subprocess.DEVNULL,
            )
        return key

    def public_key(self) -> str:
        with open(self.ensure_key() + '.pub') as f:
            return f.read().strip()

    #  ssh client configuration: one source of truth, rendered as a Host stanza or as -o arguments

    def options(self, *, debug: bool = False) -> dict[str, str]:
        cfg = self._cfg
        proxy = [*cfg.proxy_argv, *(['--debug'] if debug else []), '%h']
        opts = {
            'User': cfg.user,
            'ProxyCommand': shlex.join(proxy),
            'IdentityFile': cfg.key_path,
            'IdentitiesOnly': 'yes',
            # Not a network: tampering requires owning the Docker socket, and every container from one image build
            # shares the package-generated host keys anyway.
            'StrictHostKeyChecking': 'no',
            'UserKnownHostsFile': '/dev/null',
            # ERROR keeps interactive/IDE logins quiet (it suppresses the per-connect "Permanently added ... known
            # hosts" warning). Our own verbs preflight in the parent for clear errors; a bare `ssh om-NAME` that
            # fails will be terse. `--debug` raises this and forces a fresh, unmultiplexed connection.
            'LogLevel': 'ERROR',
            'ControlMaster': 'auto',
            'ControlPath': os.path.join(cfg.control_dir, '%h'),
            'ControlPersist': cfg.control_persist,
            'ForwardAgent': 'no',
        }
        if debug:
            opts.update(LogLevel='DEBUG', ControlMaster='no', ControlPath='none')
        return opts

    def config_text(self) -> str:
        def value(v: str) -> str:
            return f'"{v}"' if any(c.isspace() for c in v) and not v.startswith('"') else v

        lines = [
            '# Generated by dockerdev; edits will be overwritten. Hosts resolve through `docker exec`, nothing listens.',
            f'Host {self._cfg.host_prefix}*',
        ]
        for k, v in self.options().items():
            if k == 'ProxyCommand':
                lines.append(f'  {k} {v}')  # already shell-quoted; ssh hands it to $SHELL -c as is
            else:
                lines.append(f'  {k} {value(v)}')
        return '\n'.join(lines) + '\n'

    _INCLUDE_MARK = '# dockerdev-ssh'

    def _user_ssh_config_path(self) -> str:
        return os.path.join(os.path.expanduser('~'), '.ssh', 'config')

    def install_config(self) -> str:
        """Writes the stanza and includes it first in ~/.ssh/config, ahead of any `Host *` that could shadow it."""

        self.ensure_key()
        with open(self._cfg.config_path, 'w') as f:
            f.write(self.config_text())

        path = self._user_ssh_config_path()
        os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
        include = f'Include {self._cfg.config_path}  {self._INCLUDE_MARK}\n'
        try:
            with open(path) as f:
                existing = f.read()
        except FileNotFoundError:
            existing = ''
        kept = [l for l in existing.splitlines(keepends=True) if self._INCLUDE_MARK not in l]
        with open(path, 'w') as f:
            f.write(include)
            f.write(''.join(kept))
        os.chmod(path, 0o600)
        return self._cfg.config_path

    def uninstall_config(self) -> None:
        path = self._user_ssh_config_path()
        try:
            with open(path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
        with open(path, 'w') as f:
            f.writelines(l for l in lines if self._INCLUDE_MARK not in l)
        try:
            os.unlink(self._cfg.config_path)
        except FileNotFoundError:
            pass

    def ssh_argv(
            self,
            name: str,
            *,
            ssh_args: ta.Sequence[str] = (),
            command: ta.Sequence[str] | str = (),
            batch: bool = False,
            debug: bool = False,
    ) -> list[str]:
        """Self-contained: ignores the user's ssh config, so it works whether or not `config --install` ran."""

        self.ensure_key()
        argv = [self._ssh, '-F', '/dev/null']
        for k, v in self.options(debug=debug).items():
            argv.append(f'-o{k}={v}')
        if batch:
            argv.append('-oBatchMode=yes')
        if debug:
            argv.append('-vv')  # LogLevel=DEBUG and no-mux come from options(debug=True)
        argv.extend(ssh_args)
        argv.append(self.alias(name))
        if command:
            argv.append('--')
            argv.append(command if isinstance(command, str) else shlex.join(command))
        return argv

    #  preflight: resolve in the parent so our verbs fail fast and clearly, rather than relying on ssh to relay the
    #  ProxyCommand's stderr (which LogLevel=ERROR suppresses). The proxy still resolves independently for plain
    #  `ssh om-NAME`, which has no parent to preflight.

    def preflight(self, name: str) -> Container:
        c = self._resolver.resolve(self.unalias(name))
        if not c.running:
            raise RuntimeError(f'container is not running: {c.name}')
        return c

    #  proxy side

    def proxy_argv(self, alias: str, *, debug: bool = False) -> list[str]:
        c = self._resolver.resolve(self.unalias(alias))
        if not c.running:
            raise RuntimeError(f'container is not running: {c.name}')
        return [
            find_docker(self._cfg.docker),
            'exec',
            '-i',
            '-u', 'root',
            '-e', f'OM_SSH_AUTHORIZED_KEYS={self.public_key()}',
            '-e', f'OM_SSH_USER={self._cfg.user}',
            '-e', f'OM_SSH_X11={"yes" if self._cfg.x11 else "no"}',
            '-e', f'OM_SSH_USEPAM={"yes" if self._cfg.use_pam else "no"}',
            '-e', f'OM_SSH_DEBUG={"1" if debug else ""}',
            c.id,
            'sh', '-c', _SSHD_SCRIPT,
        ]

    def exec_proxy(self, alias: str, *, debug: bool = False) -> ta.NoReturn:
        """Replaces this process: nothing of ours stays in the data path."""

        argv = self.proxy_argv(alias, debug=debug)
        os.execv(argv[0], argv)

    #  sessions: an ssh control master per container is the long-lived channel a headless caller owns

    def _control(self, name: str, op: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            self.ssh_argv(name, ssh_args=['-O', op, *args]),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _control_path(self, name: str) -> str:
        return os.path.join(self._cfg.control_dir, self.alias(name))

    def master_check(self, name: str) -> bool:
        return self._control(name, 'check').returncode == 0

    def master_start(self, name: str) -> bool:
        """Returns True if a master was started, False if one was already running."""

        if self.master_check(name):
            return False
        try:
            os.unlink(self._control_path(name))  # stale socket from a killed ssh would disable multiplexing
        except FileNotFoundError:
            pass
        subprocess.run(
            self.ssh_argv(name, ssh_args=['-M', '-N', '-f'], batch=True),
            check=True,
            stdin=subprocess.DEVNULL,
        )
        return True

    def master_stop(self, name: str) -> bool:
        return self._control(name, 'exit').returncode == 0

    @staticmethod
    def _forward_args(local: ta.Iterable[str], remote: ta.Iterable[str], dynamic: ta.Iterable[str]) -> list[str]:
        args: list[str] = []
        for flag, specs in (('-L', local), ('-R', remote), ('-D', dynamic)):
            for spec in specs:
                args.extend([flag, str(spec)])
        if not args:
            raise ValueError('no forwards given')
        return args

    def forward(
            self,
            name: str,
            *,
            local: ta.Iterable[str] = (),    # [bind:]port:host:hostport   host side -> container side
            remote: ta.Iterable[str] = (),   # [bind:]port:host:hostport   container side -> host side
            dynamic: ta.Iterable[str] = (),  # [bind:]port                 SOCKS on the host, egress in the container
    ) -> None:
        """Adds forwards to the running master; starts one if needed. Raises if any forward is refused."""

        self.preflight(name)
        self.master_start(name)
        r = self._control(name, 'forward', *self._forward_args(local, remote, dynamic))
        if r.returncode:
            raise RuntimeError(f'forward failed: {r.stderr.strip()}')

    def cancel(
            self,
            name: str,
            *,
            local: ta.Iterable[str] = (),
            remote: ta.Iterable[str] = (),
            dynamic: ta.Iterable[str] = (),
    ) -> None:
        r = self._control(name, 'cancel', *self._forward_args(local, remote, dynamic))
        if r.returncode:
            raise RuntimeError(f'cancel failed: {r.stderr.strip()}')

    def run(
            self,
            name: str,
            command: ta.Sequence[str] | str,
            *,
            ssh_args: ta.Sequence[str] = (),
            **kwargs: ta.Any,
    ) -> subprocess.CompletedProcess:
        """subprocess.run of a command in the container over the (auto-started) master. kwargs go to subprocess.run."""

        self.preflight(name)
        kwargs.setdefault('stdin', subprocess.DEVNULL)
        return subprocess.run(
            self.ssh_argv(name, ssh_args=ssh_args, command=command, batch=True),
            **kwargs,
        )


##


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--state-dir', default=SshConfig.state_dir)
    parser.add_argument('--host-prefix', default=SshConfig.host_prefix)
    parser.add_argument('--user', default=SshConfig.user)
    parser.add_argument('--docker', default=SshConfig.docker)
    parser.add_argument('--control-persist', default=SshConfig.control_persist)
    parser.add_argument('--x11', action='store_true')
    parser.add_argument(
        '--no-pam',
        dest='use_pam',
        action='store_false',
        help="run sshd with UsePAM=no; requires the image's user to have password '*' not '!' (see --help notes)",
    )

    commands = parser.add_subparsers(dest='command', required=True)

    config = commands.add_parser('config', help='print the generated ssh config stanza')
    g = config.add_mutually_exclusive_group()
    g.add_argument('--install', action='store_true', help='write it and Include it first in ~/.ssh/config')
    g.add_argument('--uninstall', action='store_true')

    key = commands.add_parser('key', help='print the public key, generating the pair if needed')
    key.add_argument('--rotate', action='store_true')

    ssh = commands.add_parser('ssh', help='interactive login')
    ssh.add_argument('name')
    ssh.add_argument('--debug', action='store_true', help='sshd logs to stderr; ssh -vv')

    run = commands.add_parser('run', help='run a command, non-interactively, over the control master')
    run.add_argument('name')
    run.add_argument('cmd', nargs=argparse.REMAINDER)

    master = commands.add_parser('master', help='control master lifecycle')
    master.add_argument('name')
    master.add_argument('op', choices=('start', 'stop', 'check'))

    for verb, help_ in (('forward', 'add port forwards to the master'), ('cancel', 'remove port forwards')):
        p = commands.add_parser(verb, help=help_)
        p.add_argument('name')
        p.add_argument('-L', dest='local', action='append', default=[], metavar='[BIND:]PORT:HOST:HOSTPORT')
        p.add_argument('-R', dest='remote', action='append', default=[], metavar='[BIND:]PORT:HOST:HOSTPORT')
        p.add_argument('-D', dest='dynamic', action='append', default=[], metavar='[BIND:]PORT')

    argv = commands.add_parser('argv', help='print the self-contained ssh command line for a container')
    argv.add_argument('name')

    proxy = commands.add_parser('proxy', help='ProxyCommand entry point (internal)')
    proxy.add_argument('alias')
    proxy.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    dds = DockerDevSsh(SshConfig(
        state_dir=args.state_dir,
        host_prefix=args.host_prefix,
        user=args.user,
        docker=args.docker,
        control_persist=args.control_persist,
        x11=args.x11,
        use_pam=args.use_pam,
    ))

    try:
        if args.command == 'config':
            if args.install:
                print(f'installed {dds.install_config()}, included from ~/.ssh/config')
            elif args.uninstall:
                dds.uninstall_config()
            else:
                sys.stdout.write(dds.config_text())

        elif args.command == 'key':
            dds.ensure_key(rotate=args.rotate)
            print(dds.public_key())

        elif args.command == 'ssh':
            dds.preflight(args.name)
            argv = dds.ssh_argv(args.name, debug=args.debug)
            os.execvp(argv[0], argv)

        elif args.command == 'run':
            if not args.cmd:
                parser.error('run: no command given')
            sys.exit(dds.run(args.name, args.cmd, stdin=None).returncode)

        elif args.command == 'master':
            if args.op == 'start':
                print('started' if dds.master_start(args.name) else 'already running')
            elif args.op == 'stop':
                print('stopped' if dds.master_stop(args.name) else 'not running')
            else:
                running = dds.master_check(args.name)
                print('running' if running else 'not running')
                sys.exit(0 if running else 1)

        elif args.command in ('forward', 'cancel'):
            getattr(dds, args.command)(args.name, local=args.local, remote=args.remote, dynamic=args.dynamic)

        elif args.command == 'argv':
            print(shlex.join(dds.ssh_argv(args.name)))

        elif args.command == 'proxy':
            dds.exec_proxy(args.alias, debug=args.debug)

        else:
            raise ValueError(args.command)

    except (RuntimeError, LookupError, FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _main()
