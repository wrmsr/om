"""
The host side of the remote environment: `RemoteEnvironmentOps` implements the ordinary `EnvironmentOps` interface over
an rpc connection to a remote agent's `RemoteEnvironmentService`, marking what comes back as remote - which the agent,
knowing only its own surroundings, cannot say of itself.
"""
import typing as ta

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj
from omcore.rpc.connection import RpcConnection
from omcore.rpc.errors import RpcRemoteError
from omcore.rpc.translate import translate_rpc_remote_builtin_error

from ..ops import EnvironmentInfo
from ..ops import EnvironmentOps
from .protocol import REMOTE_ENVIRONMENT_INFO_METHOD
from .protocol import RemoteEnvironmentInfo
from .protocol import RemoteEnvironmentInfoParams


##


class RemoteEnvironmentOps(EnvironmentOps):
    def __init__(
            self,
            connection: RpcConnection,
    ) -> None:
        super().__init__()

        self._connection = connection

    async def _call(self, method: str, params: ta.Any) -> ta.Any:
        try:
            return await self._connection.request(method, params)
        except RpcRemoteError as e:
            raise translate_rpc_remote_builtin_error(e) from e

    async def inspect_environment(self, *, cwd: str | None = None) -> EnvironmentInfo:
        r: RemoteEnvironmentInfo = unmarshal_obj(
            await self._call(
                REMOTE_ENVIRONMENT_INFO_METHOD,
                marshal_obj(RemoteEnvironmentInfoParams(
                    cwd=cwd,
                )),
            ),
            RemoteEnvironmentInfo,
        )

        return EnvironmentInfo(
            cwd=r.cwd,

            system=r.system,
            release=r.release,
            machine=r.machine,

            hostname=r.hostname,

            user=EnvironmentInfo.User(
                name=r.user.name,
                home=r.user.home,
                shell=r.user.shell,
            ) if r.user is not None else None,

            container=r.container,

            remote=True,
        )
