"""
Builds the `python -I -S -c <bootstrap> <control_fd>` launch. The child receives exactly one fd from the parent: the
control socket, dup2'd to `control_fd` at spawn. Queued on it beforehand is the handshake (`managers/spawn.py::
send_control_fds`): a `{"n": N}` header line and N fds via SCM_RIGHTS - the payload blob first (one line of json
`ShimPayload` followed by the shim source, in an unlinked temp file so it can be any size), then the caller's pass-fds.
The bootstrap drains that, reads the blob, execs the source as module `__procs_shim__`, and calls
`main(ShimPayload(**payload), passed_fds)`. Nothing is ever made inheritable in the parent.
"""
import json
import os
import sys
import tempfile
import typing as ta

from omcore import check
from omcore import lang

from ..types.options import Credentials
from ..types.options import Deathsig
from ..types.options import PassFd
from ..types.options import ProcessOptions
from ..types.options import Rlimit
from ..types.options import Umask
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio
from ._shim import MAX_FDS_PER_MESSAGE
from ._shim import ShimPayload
from ._shim import encode_os
from .launcher import Launcher
from .launcher import LaunchPlan
from .launcher import SpecTransform
from .launcher import apply_transforms


##


SHIM_MODULE_NAME: ta.Final[str] = '__procs_shim__'

# Mirrors `_shim.receive_control` - the one piece of shim logic that has to exist before the shim source has arrived.
BOOTSTRAP: ta.Final[str] = f"""
import array,json,os,socket,sys,types
s=socket.socket(fileno=int(sys.argv[1]))
b=b'';n=None;fds=array.array('i')
while n is None or len(fds)<n:
    m,a,_f,_a=s.recvmsg(4096,socket.CMSG_SPACE({MAX_FDS_PER_MESSAGE}*fds.itemsize))
    if not m and not a:raise EOFError('control socket closed during handshake')
    for l,t,d in a:
        if l==socket.SOL_SOCKET and t==socket.SCM_RIGHTS:fds.frombytes(d[:len(d)-len(d)%fds.itemsize])
    if n is None:
        b+=m
        if b'\\n' in b:n=int(json.loads(b.split(b'\\n',1)[0])['n'])
s.detach()
f=os.fdopen(fds[0],'r',encoding='utf-8');p=json.loads(f.readline());src=f.read();f.close()
mod=types.ModuleType('{SHIM_MODULE_NAME}');sys.modules[mod.__name__]=mod
exec(compile(src,'<processes-shim>','exec'),mod.__dict__)
mod.main(mod.ShimPayload(**p),list(fds[1:]))
""".strip()


@lang.cached_function
def shim_source() -> str:
    return lang.get_relative_resources('.', globals=globals())['_shim.py'].read_text()


def decode_shim_status(status: bytes) -> tuple[str, int | None, str]:
    """
    Decodes a non-empty exec-status record written by the shim: a json `[stage, errno, message]`. Anything undecodable
    is reported as a 'status' stage failure carrying the raw bytes.
    """

    try:
        stage, err_no, msg = json.loads(status)
    except Exception:  # noqa
        return 'status', None, repr(status)
    return str(stage), err_no if isinstance(err_no, int) else None, str(msg)


##


def build_payload(
        spec: ProcessSpec,
        options: ProcessOptions,
        *,
        status_fd: int,
        keep_fds: ta.Sequence[int] = (),
        set_ctty: bool = False,
) -> ShimPayload:
    kw: dict[str, ta.Any] = {}

    if (um := options.get(Umask)) is not None:
        kw.update(umask=um.v)

    if (rls := options.get(Rlimit)):
        kw.update(rlimits=[[r.resource, r.soft, r.hard] for r in rls])

    if (cr := options.get(Credentials)) is not None:
        kw.update(
            user=cr.user,
            group=cr.group,
            extra_groups=list(cr.extra_groups) if cr.extra_groups is not None else None,
        )

    if (ds := options.get(Deathsig)) is not None:
        kw.update(deathsig=int(ds.signal))

    # argv / env / cwd go as base64 of their OS bytes - `encode_os` also means an unencodable str fails loudly here, in
    # the parent, rather than in the child.
    return ShimPayload(
        argv=[encode_os(a) for a in spec.argv],
        env={encode_os(k): encode_os(v) for k, v in spec.resolve_env().items()},
        status_fd=status_fd,
        cwd=encode_os(spec.cwd) if spec.cwd is not None else None,
        keep_fds=list(keep_fds),
        set_ctty=set_ctty,
        **kw,
    )


##


class ShimLauncher(Launcher):
    def __init__(
            self,
            *,
            python: ta.Sequence[str] | None = None,
            transforms: ta.Sequence[SpecTransform] = (),
    ) -> None:
        super().__init__()

        self._python = tuple(python) if python is not None else (sys.executable,)
        check.arg(all(self._python))
        self._transforms = tuple(transforms)

    @property
    def python(self) -> ta.Sequence[str]:
        return self._python

    def validate(self) -> None:
        exe = self._python[0]
        if not (os.path.isabs(exe) and os.access(exe, os.X_OK)):
            raise ValueError(f'Shim python is not an absolute executable path: {exe!r}')

    #

    def _write_payload_file(self, payload: ShimPayload) -> int:
        # SECURITY: this blob carries the target's *entire environment* - which routinely holds secrets (tokens, keys) -
        # and its argv. It goes into a `tempfile.TemporaryFile`: mode 0600, and on Linux an `O_TMPFILE` file that never
        # has a name (nlink 0 from birth, nothing to race); elsewhere mkstemp + immediate unlink. Only a same-uid
        # process going through /proc/<pid>/fd could read it, which could already read the child's /proc/<pid>/environ.
        # It does however live on the temp filesystem (page cache, potentially disk) for the few milliseconds until the
        # child has read it and both ends are closed. `os.memfd_create` (Linux, memory-only, sealable) is the next step
        # if that window ever matters.
        f = tempfile.TemporaryFile(prefix='om-processes-payload-')  # noqa: SIM115
        try:
            # `json.dumps` escapes everything non-ascii, so the payload is exactly one line.
            f.write(payload.to_json().encode('ascii'))
            f.write(b'\n')
            f.write(shim_source().encode('utf-8'))
            f.flush()
            fd = os.dup(f.fileno())
        finally:
            f.close()
        os.lseek(fd, 0, os.SEEK_SET)
        return fd

    def plan(
            self,
            spec: ProcessSpec,
            options: ProcessOptions,
    ) -> LaunchPlan:
        spec = apply_transforms(self._transforms, spec, options)

        keep_fds = [pf.v for pf in options.get(PassFd, ())]

        # The control socket sits above every pass-fd target so relocating them in the shim can never land on it.
        control_fd = max([3, *(k + 1 for k in keep_fds)])

        payload = build_payload(
            spec,
            options,
            status_fd=control_fd,
            keep_fds=keep_fds,
            set_ctty=isinstance(spec.stdio, PtyStdio),
        )

        payload_fd = self._write_payload_file(payload)

        argv = [
            *self._python,
            '-I',
            '-S',
            '-c',
            BOOTSTRAP,
            str(control_fd),
        ]

        return LaunchPlan(
            spec=spec,
            argv=argv,
            # The shim's own environment. `-I` makes the interpreter ignore PYTHON* vars in it; the target gets the
            # exact env from the payload regardless.
            env=spec.resolve_env(),
            control_fd=control_fd,
            send_fds=[payload_fd, *keep_fds],
            owned_fds=[payload_fd],
        )
