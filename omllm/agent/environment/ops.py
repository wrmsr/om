# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
What an environment - the machine or container the tools work in - says of itself. `EnvironmentOps` is asked once, at
an agent's setup, for the facts which go into its system prompt and for its working directory; a remote environment
answers through the remote agent. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and standard
library only.
"""
import abc
import dataclasses as dc
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.dataclasses import install_dataclass_kw_only_init


##


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class EnvironmentInfo:
    # The working directory, absolute and symlink-resolved in the environment's own namespace.
    cwd: str

    # `platform.system()`, `platform.release()`, and `platform.machine()` there: 'Linux', '6.8.0-138-generic', 'x86_64'.
    system: str
    release: str
    machine: str

    hostname: str

    # The user the tools run as, and that user's home and shell, where they can be told.
    user: ta.Optional[str] = None
    home: ta.Optional[str] = None
    shell: ta.Optional[str] = None

    # The container runtime the environment finds itself running under - 'docker', 'podman' - or None where none is
    # detected. Detected from inside, so it says nothing of how the environment is reached.
    container: ta.Optional[str] = None

    # Whether the environment is somewhere other than where the harness runs, so that the tools' files and processes
    # are not the user's own machine's. Set by whatever reaches a remote environment, never by the environment itself.
    remote: bool = False


##


class EnvironmentOps(Abstract):
    @abc.abstractmethod
    def get_info(self, *, cwd: ta.Optional[str] = None) -> ta.Awaitable[EnvironmentInfo]:
        """
        Describes the environment, with its working directory resolved: the one given, in the environment's own
        namespace and relative to its own directory if not absolute, or that directory itself. A directory which does
        not exist there raises FileNotFoundError, and a path there which is not a directory NotADirectoryError.
        """

        raise NotImplementedError
