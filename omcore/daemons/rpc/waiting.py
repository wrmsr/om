from ... import dataclasses as dc
from ..waiting import Wait
from ..waiting import Waiter
from ..waiting import waiter_for
from .client import RpcClient
from .protocol import RpcUnavailableError


##


class RpcWait(Wait):
    """A daemon readiness probe that completes a full RPC handshake."""

    client: RpcClient.Config


class RpcWaiter(Waiter, dc.Frozen):
    wait: RpcWait

    def do_wait(self) -> bool:
        try:
            RpcClient(self.wait.client).ping()
        except RpcUnavailableError:
            return False
        else:
            return True


@waiter_for.register
def _(wait: RpcWait) -> RpcWaiter:
    return RpcWaiter(wait)
