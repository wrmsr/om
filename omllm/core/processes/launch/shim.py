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
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec
from omcore.subprocesses.wrap import subprocess_shell_wrap_exec

from ..types.options import Credentials
from ..types.options import Deathsig
from ..types.options import PassFd
from ..types.options import ProcessOptions
from ..types.options import Rlimit
from ..types.options import Umask
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio
from ._bootstrap import _BootstrapConsts
from ._shim import ShimPayload
from ._shim import encode_os
from .launcher import Launcher
from .launcher import LaunchPlan
from .launcher import SpecTransform
from .launcher import apply_transforms


##


@lang.cached_function
def bootstrap_source() -> str:
    import textwrap

    # We can't technically `inspect.getsource` without a `__file__` - we'll probably never need to run like that, but
    # let's accomodate it anyway :)
    bs_mod_src = lang.get_relative_resources('.', globals=globals())['_bootstrap.py'].read_text()
    bs_mod_lines = bs_mod_src.splitlines(keepends=True)
    bs_fn_line = check.single(i for i, l in enumerate(bs_mod_lines) if l.startswith('def _bootstrap_body('))
    bs_src = textwrap.dedent(''.join(bs_mod_lines[bs_fn_line + 1:]))

    for an, av in sorted(_BootstrapConsts.__dict__.items(), key=lambda kv: -len(kv[0])):
        bs_src = bs_src.replace(f'_BootstrapConsts.{an}', repr(av))

    bs_src = '\n'.join(
        cl
        for l in bs_src.splitlines()
        if (cl := (l.split('#')[0]).rstrip())
        if cl.strip()
    )

    return bs_src


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
        setsid: bool = False,
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
        setsid=setsid,
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
            shell_wrap_shim: bool | ta.Literal['maybe'] = False,
    ) -> None:
        super().__init__()

        self._python = tuple(python) if python is not None else (sys.executable,)
        check.arg(all(self._python))
        self._transforms = tuple(transforms)
        self._shell_wrap_shim = shell_wrap_shim

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
            *,
            child_setsid: bool = False,
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
            setsid=child_setsid,
            set_ctty=isinstance(spec.stdio, PtyStdio),
        )

        payload_fd = self._write_payload_file(payload)

        argv: ta.Sequence[str] = [
            *self._python,
            '-I',
            '-S',
            '-c',
            bootstrap_source(),
            str(control_fd),
        ]

        if self._shell_wrap_shim == 'maybe':
            argv = subprocess_maybe_shell_wrap_exec(*argv)
        elif self._shell_wrap_shim:
            argv = subprocess_shell_wrap_exec(*argv)

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
