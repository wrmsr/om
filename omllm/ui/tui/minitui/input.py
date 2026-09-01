"""
Input side of the minitui backend: the permission asker.

`PermissionAsker.ask` is awaited from deep inside a tool executor, mid-turn. Here it surfaces as a warm-window
confirmation card (allow f10 / deny f2) whose response resolves an asyncio future - the driver keeps rendering (and the
user keeps typing) while that execution is parked on the decision. Concurrent requests queue behind the active card. An
ask withdrawn by the app (its turn ended while the tool was still live) surfaces as `PermissionAskAbortedError`, never
as a cancellation the requesting task did not ask for.
"""
import asyncio

from omcore import check
from omcore import inject as inj
from omdev.tui import minitui as mt

from .... import agent as agn
from ..config import Config
from .app import MinituiChatApp
from .toolcards import tool_card_key


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
        context = check.not_none(requestor.tool_context)
        fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()

        def respond(allowed: bool) -> None:
            if not fut.done():
                fut.set_result(allowed)

        def cancel() -> None:
            fut.cancel()

        self._app.begin_permission_card(
            tool_card_key(context),
            context.tool.name if context.tool is not None else f'{requestor!r}',
            [
                [mt.Segment(f'target: {target!r}', 'card.detail')],
                [mt.Segment(f'rule: {rule!r}', 'card.detail')],
            ],
            respond,
            on_cancel=cancel,
        )

        try:
            allowed = await fut
        except asyncio.CancelledError:
            # The future was cancelled but this task was not: the app withdrew the ask (its turn ended) while the tool
            # was still live. Per the PermissionAsker contract that is an execution error for the tool, not a
            # cancellation of the turn - the turn loop could not tell the two apart.
            if not check.not_none(asyncio.current_task()).cancelling():
                raise agn.PermissionAskAbortedError(target) from None
            raise

        return agn.PermissionState.ALLOW if allowed else agn.PermissionState.DENY


##


def bind_input(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(CardPermissionAsker, singleton=True),
        inj.bind(agn.PermissionAsker, to_key=CardPermissionAsker),
    )
