# ruff: noqa: UP006 UP007 UP045
# @om-lite
import errno
import os
import platform
import socket
import typing as ta

from .ops import EnvironmentInfo
from .ops import EnvironmentOps


##


def environment_resolve_cwd(path: ta.Optional[str]) -> str:
    """The absolute, symlink-resolved form of a working directory, which must exist and be one."""

    cwd = os.path.abspath(os.path.realpath(path if path is not None else os.getcwd()))

    if not os.path.exists(cwd):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), cwd)
    if not os.path.isdir(cwd):
        raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), cwd)

    return cwd


def environment_detect_container() -> ta.Optional[str]:
    """The container runtime this process is running under, as far as the usual marker files say. Best effort."""

    if os.path.exists('/.dockerenv'):
        return 'docker'
    if os.path.exists('/run/.containerenv'):
        return 'podman'
    return None


class LocalEnvironmentOps(EnvironmentOps):
    """The environment this process is in. On the host that is the user's own machine; in the remote agent, its own."""

    @staticmethod
    def _user() -> ta.Tuple[ta.Optional[str], ta.Optional[str], ta.Optional[str]]:
        pw_name: ta.Optional[str] = None
        pw_dir: ta.Optional[str] = None
        pw_shell: ta.Optional[str] = None
        try:
            import pwd  # noqa: PLC0415
        except ImportError:  # pragma: no cover
            pass
        else:
            try:
                pw = pwd.getpwuid(os.getuid())
            except KeyError:
                pass
            else:
                pw_name, pw_dir, pw_shell = pw.pw_name, pw.pw_dir, pw.pw_shell

        # The account is authoritative for who; the session's own variables for where it lives and what it runs, as
        # they are what a shell started here would see.
        user = pw_name or os.environ.get('USER') or os.environ.get('LOGNAME') or None
        home = os.environ.get('HOME') or pw_dir or None
        shell = os.environ.get('SHELL') or pw_shell or None

        return user, home, shell

    async def get_info(self, *, cwd: ta.Optional[str] = None) -> EnvironmentInfo:
        user, home, shell = self._user()

        return EnvironmentInfo(
            cwd=environment_resolve_cwd(cwd),

            system=platform.system(),
            release=platform.release(),
            machine=platform.machine(),

            hostname=socket.gethostname(),

            user=user,
            home=home,
            shell=shell,

            container=environment_detect_container(),
        )
