"""
Builds the `python -I -S -c <bootstrap> <payload_fd>` launch. The bootstrap loads two marshal'd values from the payload
fd - the shim source (as text) and the payload dict - `exec`s the source and calls its `main(payload)`. The payload
rides an unlinked temp file rather than a pipe so it can be arbitrarily large without stalling the parent.
"""
import marshal
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
from .launcher import Launcher
from .launcher import LaunchPlan
from .launcher import SpecTransform
from .launcher import apply_transforms


##


BOOTSTRAP: ta.Final[str] = (
    'import marshal,os,sys;'
    "f=os.fdopen(int(sys.argv[1]),'rb');"
    's=marshal.load(f);p=marshal.load(f);f.close();'
    "n={'__name__':'__procs_shim__'};"
    "exec(compile(s,'<processes-shim>','exec'),n);"
    "n['main'](p)"
)


@lang.cached_function
def shim_source() -> str:
    return lang.get_relative_resources('..spawn', globals=globals())['shim.py'].read_text()


def decode_shim_status(status: bytes) -> tuple[str, int | None, str]:
    """
    Decodes a non-empty exec-status record written by the shim: a marshal'd `(stage, errno, message)`. Anything
    undecodable is reported as a 'status' stage failure carrying the raw bytes.
    """

    try:
        stage, err_no, msg = marshal.loads(status)  # noqa: S302
    except Exception:  # noqa
        return 'status', None, repr(status)
    return str(stage), err_no if isinstance(err_no, int) else None, str(msg)


##


def _fsencode(s: int | str | bytes) -> int | bytes:
    if isinstance(s, int):
        return s
    return os.fsencode(s)


def build_payload(
        spec: ProcessSpec,
        options: ProcessOptions,
        *,
        status_fd: int,
        keep_fds: ta.Sequence[int] = (),
        close_fds: ta.Sequence[int] = (),
        set_ctty: bool = False,
) -> dict[str, ta.Any]:
    payload: dict[str, ta.Any] = {
        'argv': [os.fsencode(a) for a in spec.argv],
        'env': {os.fsencode(k): os.fsencode(v) for k, v in spec.resolve_env().items()},
        'cwd': os.fsencode(spec.cwd) if spec.cwd is not None else None,
        'status_fd': status_fd,
        'keep_fds': list(keep_fds),
        'close_fds': list(close_fds),
    }

    if set_ctty:
        payload['set_ctty'] = True

    if (um := options.get(Umask)) is not None:
        payload['umask'] = um.v

    if (rls := options.get(Rlimit)):
        payload['rlimits'] = [(r.resource, r.soft, r.hard) for r in rls]

    if (cr := options.get(Credentials)) is not None:
        payload['user'] = _fsencode(cr.user) if cr.user is not None else None
        payload['group'] = _fsencode(cr.group) if cr.group is not None else None
        payload['extra_groups'] = [_fsencode(g) for g in cr.extra_groups] if cr.extra_groups is not None else None

    if (ds := options.get(Deathsig)) is not None:
        payload['deathsig'] = int(ds.signal)

    return payload


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

    def _write_payload_file(self, payload: dict[str, ta.Any]) -> int:
        f = tempfile.TemporaryFile(prefix='om-processes-payload-')  # noqa: SIM115
        try:
            f.write(marshal.dumps(shim_source()))
            f.write(marshal.dumps(payload))
            f.flush()
            fd = os.dup(f.fileno())
        finally:
            f.close()
        os.lseek(fd, 0, os.SEEK_SET)
        os.set_inheritable(fd, True)
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
            cwd=None,
            pass_fds=[payload_fd, status_fd, *keep_fds],
            owned_fds=[payload_fd],
        )
