import os.path
import platform
import sys
import tempfile
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore.secrets import all as sec

from ..build.config import Config
from .args import RunArgs
from .consts import CONTAINER_STAGING_DIR


##


@dc.dataclass(frozen=True, kw_only=True)
class RunHost:
    """
    What a run reads from the machine it is launched from, gathered in one place so that a run can be planned - and
    tested - without that machine. `RunHost.current()` reads the real one.
    """

    # `platform.system()`.
    platform_system: str

    # `sys.platform`.
    sys_platform: str

    # The user's home directory, if known. Only an x11 run on linux needs it.
    home: str | None = None

    # The working directory, in which a git mount looks for `.git`.
    cwd: str

    # Where secrets to inject come from. Unset, a run which asks to inject any fails rather than reading them from
    # somewhere implicit.
    load_secrets: ta.Callable[[], sec.Secrets] | None = None

    # Makes the host directory staged files are written to. Unset, `tempfile.mkdtemp`.
    mkdtemp: ta.Callable[[], str] | None = None

    @classmethod
    def current(
            cls,
            *,
            load_secrets: ta.Callable[[], sec.Secrets] | None = None,
            mkdtemp: ta.Callable[[], str] | None = None,
    ) -> RunHost:
        return cls(
            platform_system=platform.system(),
            sys_platform=sys.platform,
            home=os.environ.get('HOME'),
            cwd=os.getcwd(),
            load_secrets=load_secrets,
            mkdtemp=mkdtemp,
        )


##


@dc.dataclass(kw_only=True)
class RunPlan:
    """
    What one `docker run` will be, accumulated by the run steps in order: the options before the image, the shell lines
    the autoexec entrypoint runs ahead of the command (and the environment it execs the command with), the entrypoint,
    the files staged for the container, and the environment of the docker client process itself.
    """

    cfg: Config
    args: RunArgs
    run_id: uuid.UUID
    host: RunHost

    options: list[str] = dc.field(default_factory=list)

    autoexec_lines: list[str] = dc.field(default_factory=list)
    autoexec_env: dict[str, str] = dc.field(default_factory=dict)

    entrypoint: str | None = None

    client_env: dict[str, str | sec.Secret] = dc.field(default_factory=dict)

    staging_dir: str | None = None

    #

    def add_options(self, *options: str) -> None:
        self.options.extend(options)

    def add_autoexec_lines(self, *lines: str) -> None:
        self.autoexec_lines.extend(lines)

    def set_autoexec_env(self, key: str, value: str) -> None:
        self.autoexec_env[key] = value

    def set_entrypoint(self, entrypoint: str) -> None:
        self.entrypoint = entrypoint

    def set_client_env(self, key: str, value: str | sec.Secret) -> None:
        self.client_env[key] = value

    #

    def stage_file(self, name: str, content: str, *, mode: int = 0o755) -> str:
        """Writes a file for the container to see in its staging dir, returning its path there."""

        check.non_empty_str(name)
        check.arg(os.sep not in name and name not in ('.', '..'), name)

        if (staging_dir := self.staging_dir) is None:
            if (mkdtemp := self.host.mkdtemp) is None:
                mkdtemp = tempfile.mkdtemp
            staging_dir = self.staging_dir = mkdtemp()

        path = os.path.join(staging_dir, name)
        with open(path, 'x') as f:
            f.write(content)
        os.chmod(path, mode)  # noqa

        return f'{CONTAINER_STAGING_DIR}/{name}'
