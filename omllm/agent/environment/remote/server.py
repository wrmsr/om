# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
The target side of the remote environment: `RemoteEnvironmentService` answers for the environment the remote agent runs
in, through a `LocalEnvironmentOps` there. Lite: this runs inside the remote agent amalgam under Python 3.8+.
"""
import typing as ta

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj
from omcore.rpc.dispatch import RpcMethodFn

from ..local import LocalEnvironmentOps
from .protocol import REMOTE_ENVIRONMENT_INFO_METHOD
from .protocol import RemoteEnvironmentInfo
from .protocol import RemoteEnvironmentInfoParams


##


class RemoteEnvironmentService:
    def __init__(
            self,
            *,
            local_ops: ta.Optional[LocalEnvironmentOps] = None,
    ) -> None:
        super().__init__()

        if local_ops is None:
            local_ops = LocalEnvironmentOps()

        self._local_ops = local_ops

    async def info(self, params: ta.Any) -> ta.Any:
        p: RemoteEnvironmentInfoParams = unmarshal_obj(params, RemoteEnvironmentInfoParams)
        i = await self._local_ops.get_info(cwd=p.cwd)
        return marshal_obj(RemoteEnvironmentInfo(
            cwd=i.cwd,

            system=i.system,
            release=i.release,
            machine=i.machine,

            hostname=i.hostname,

            user=i.user,
            home=i.home,
            shell=i.shell,

            container=i.container,
        ))

    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return {
            REMOTE_ENVIRONMENT_INFO_METHOD: self.info,
        }
