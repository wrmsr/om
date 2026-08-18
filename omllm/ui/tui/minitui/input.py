"""
Input side of the minitui backend: the permission asker.

`PermissionAsker.ask` is awaited from deep inside the tool executor, mid-turn. Here it surfaces as a warm-window
confirmation card (allow f10 / deny f2) whose response resolves an asyncio future - the driver keeps rendering (and the
user keeps typing) while the turn is parked on the decision.
"""
import asyncio

from omcore import inject as inj
from omxtra.tui import minitui as mt

from .... import agent as agn
from ..config import Config
from .app import MinituiChatApp


##


class CardPermissionAsker(agn.PermissionAsker):
    def __init__(self, *, app: MinituiChatApp) -> None:
        super().__init__()

        self._app = app

    async def ask(
            self,
            requestor: agn.PermissionRequestor,
            target: agn.PermissionTarget,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()

        def respond(allowed: bool) -> None:
            if not fut.done():
                fut.set_result(allowed)

        self._app.begin_permission_card(
            f'{requestor!r}',
            [
                [mt.Segment(f'target: {target!r}', 'card.detail')],
                [mt.Segment(f'rule: {rule!r}', 'card.detail')],
            ],
            respond,
        )

        return agn.PermissionState.ALLOW if await fut else agn.PermissionState.DENY


##


def bind_input(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(CardPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=CardPermissionAsker),
    )
