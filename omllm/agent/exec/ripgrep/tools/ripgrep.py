import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .....core import processes
from ....fs.permissions import FsPermissionTarget
from ....permissions.types import PermissionDecider
from ....permissions.types import PermissionRequestor
from ....tools.classes import ToolClass
from ....types.tools import ToolContext
from ....types.tools import ToolDescription
from ...ops import ExecOps
from ...ops import ExecParams
from ...ops import format_exec_output
from ...permissions import ExecPermissionTarget


##


# Appended *after* the model-supplied args - rg is last-flag-wins, so these override rather than trust them. Defense in
# depth against rg features that read surprising places or spawn helper programs; the sandbox (exec scoped to rg itself,
# reads scoped to the cwd, env scrubbed) is the actual boundary - these just fail earlier and clearer:
#
#  --no-config:            don't read $RIPGREP_CONFIG_PATH (scrubbed from the env anyway)
#  --no-pre:               don't spawn a preprocessor per file
#  --no-search-zip:        don't spawn decompressors
#  --hyperlink-format=none: --hostname-bin is only ever spawned for hyperlink output
#  --no-follow:            don't follow symlinks out of the tree (seatbelt resolves paths, so they'd only error)
#  --no-ignore-parent:     don't walk *above* the cwd for ignore files
#  --no-ignore-global:     don't read ~/.gitignore_global &c (there is no HOME anyway)
SAFETY_RG_ARGS: ta.Final[ta.Sequence[str]] = (
    '--no-config',
    '--no-pre',
    '--no-search-zip',
    '--hyperlink-format=none',
    '--no-follow',
    '--no-ignore-parent',
    '--no-ignore-global',
    '--color=never',
)


def _rg_prefix_read_roots(rg: str) -> list[str]:
    """Package-manager lib trees for a keg-installed rg (homebrew's rg links pcre2 from its prefix for `-P`)."""

    if rg.startswith('/opt/homebrew/'):
        return ['/opt/homebrew/Cellar', '/opt/homebrew/lib', '/opt/homebrew/opt']
    if rg.startswith('/usr/local/'):
        return ['/usr/local/Cellar', '/usr/local/lib', '/usr/local/opt']
    if rg.startswith('/opt/local/'):
        return ['/opt/local/lib', '/opt/local/libexec']
    return []


##


@dc.dataclass(frozen=True)
class RipgrepToolParams:
    args: ta.Sequence[str]

    _: dc.KW_ONLY

    timeout_s: float | None = None


class RipgrepTool(ToolClass[RipgrepToolParams]):
    name: ta.Final = 'ripgrep'

    params_cls: ta.Final = RipgrepToolParams

    description: ta.Final = ToolDescription(
        """\
        Executes ripgrep with the given arguments in current working directory. Returns stdout and stderr.

        If you are familiar with ripgrep, prefer to use this over invoking regular 'grep' or similar tools via shell
        execution.
        """,
        dict(
            args='The arguments to pass to ripgrep.',
            timeout_s='An optional timeout in seconds.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            exec: ExecOps,  # noqa
            sandbox: bool = True,  # Escape hatch for debugging only - this tool is meant to run confined.
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._exec = exec
        self._sandbox = sandbox

    async def execute(self, ctx: ToolContext, params: RipgrepToolParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if (scope := ctx.env.processes) is None:
            raise ValueError('No process scope configured')

        # Seatbelt matches resolved vnode paths, so grant - and search from - the resolved cwd.
        cwd = os.path.realpath(cwd)
        if not os.path.isdir(cwd):
            raise NotADirectoryError(cwd)

        #

        # Currently just a smoketest: parse for early, legible failure on malformed args. Intended to grow into
        # pre-spawn arg policy - but the sandbox below is the boundary, not this.
        from ..args.parsing import RgArgvParser

        parser = RgArgvParser()
        parsed = parser.parse(params.args)  # noqa

        #

        await self._permissions.check_allowed(
            permission_requestor := PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(cwd, 'r'),
        )

        rg = os.path.realpath(check.not_none(shutil.which('rg')))

        cmd = [
            rg,
            *params.args,
            *SAFETY_RG_ARGS,
        ]

        await self._permissions.check_allowed(
            permission_requestor,
            ExecPermissionTarget(cmd),
        )

        options: list[processes.ProcessOption] = []
        if self._sandbox:
            # rg is a read-only, non-forking tool: reads scoped to the search tree plus the libs it loads, exec of only
            # itself, no children, no mach, no writes anywhere, no tmp, no network - all the policy defaults, plus a
            # minimal library set instead of the wider system roots.
            options.append(processes.platform_sandbox(processes.SandboxPolicy(
                read_roots=[cwd],
                system_read_roots=[
                    *processes.SandboxDefaults.MINIMAL_SYSTEM_READ_ROOTS,
                    os.path.dirname(rg),
                    *_rg_prefix_read_roots(rg),
                ],
                private_tmp=False,
            )))

        # A minimal environment: rg must not find a real HOME (~/.gitignore_global &c), and the harness's own environ
        # (api keys...) has no business inside the sandbox. Locale vars pass through for correct unicode handling.
        env: dict[str, str] = {
            'PATH': '/usr/bin:/bin',
            'HOME': '/var/empty',
        }
        for k in ('LANG', 'LC_ALL', 'LC_CTYPE'):
            if (v := os.environ.get(k)) is not None:
                env[k] = v

        result = await self._exec.exec(scope, ExecParams(
            cmd,
            cwd=cwd,
            env=env,
            timeout_s=params.timeout_s,
            options=options,
        ))

        return format_exec_output(result, timeout_s=params.timeout_s)
