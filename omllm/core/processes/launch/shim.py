"""
Builds the `python -I -S -c <bootstrap> <payload_fd>` launch. The payload fd carries one text file: a first line holding
the json `ShimPayload`, followed by the shim source. The bootstrap reads both, execs the source as a module named
`__procs_shim__`, and calls its `main(ShimPayload(**payload))`. The payload rides an unlinked temp file rather than a
pipe so it can be arbitrarily large without stalling the parent.
"""
import json
import os
import sys
import tempfile
import typing as ta

from omcore import check
from omcore import lang

from ..spawn.shim import ShimPayload
from ..types.options import Credentials
from ..types.options import Deathsig
from ..types.options import PassFd
from ..types.options import ProcessOptions
from ..types.options import Rlimit
from ..types.options import Umask
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio
from .launcher import Launcher
from .launcher import LaunchPlan
from .launcher import SpecTransform
from .launcher import apply_transforms


##


SHIM_MODULE_NAME: ta.Final[str] = '__procs_shim__'

BOOTSTRAP: ta.Final[str] = (
    'import json,os,sys,types;'
    "f=os.fdopen(int(sys.argv[1]),'r',encoding='utf-8');"
    'p=json.loads(f.readline());s=f.read();f.close();'
    f"m=types.ModuleType('{SHIM_MODULE_NAME}');"
    'sys.modules[m.__name__]=m;'
    "exec(compile(s,'<processes-shim>','exec'),m.__dict__);"
    'm.main(m.ShimPayload(**p))'
)


@lang.cached_function
def shim_source() -> str:
    return lang.get_relative_resources('..spawn', globals=globals())['shim.py'].read_text()


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

    return ShimPayload(
        argv=list(spec.argv),
        env=dict(spec.resolve_env()),
        status_fd=status_fd,
        cwd=spec.cwd,
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
        f = tempfile.TemporaryFile(prefix='om-processes-payload-')  # noqa: SIM115
        try:
            # `json.dumps` escapes everything non-ascii (incl. surrogate escapes), so the payload is exactly one line.
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
            status_fd: int,
    ) -> LaunchPlan:
        spec = apply_transforms(self._transforms, spec, options)

        keep_fds = [pf.v for pf in options.get(PassFd, ())]

        payload = build_payload(
            spec,
            options,
            status_fd=status_fd,
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
            str(payload_fd),
        ]

        return LaunchPlan(
            spec=spec,
            argv=argv,
            # The shim's own environment. `-I` makes the interpreter ignore PYTHON* vars in it; the target gets the
            # exact env from the payload regardless.
            env=spec.resolve_env(),
            pass_fds=[payload_fd, status_fd, *keep_fds],
            owned_fds=[payload_fd],
        )
