# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
The wire shape of the remote environment: the one request the host's `RemoteEnvironmentOps` makes of the agent's
`RemoteEnvironmentService`, and its result. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and
marshaled with the lite marshaler.
"""
import dataclasses as dc
import typing as ta


##


REMOTE_ENVIRONMENT_INFO_METHOD = 'environment.info'


@dc.dataclass(frozen=True)
class RemoteEnvironmentInfoParams:
    cwd: ta.Optional[str]


@dc.dataclass(frozen=True)
class RemoteEnvironmentInfo:
    """The agent's `EnvironmentInfo`, less what only the host can say of it: that it is remote."""

    cwd: str

    system: str
    release: str
    machine: str

    hostname: str

    @dc.dataclass(frozen=True)
    class User:
        name: ta.Optional[str]
        home: ta.Optional[str]
        shell: ta.Optional[str]

    user: ta.Optional[User]

    container: ta.Optional[str]
