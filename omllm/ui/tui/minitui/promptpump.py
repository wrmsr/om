import asyncio

from .... import harness as har
from .app import MinituiChatApp


##


class PromptPump:
    """Runs prompts one at a time as loop tasks; mid-turn submissions queue in order."""

    def __init__(
            self,
            *,
            session: har.Session,
            app: MinituiChatApp,
    ) -> None:
        super().__init__()

        self._session = session
        self._app = app

        self._queue: list[str] = []
        self._task: asyncio.Task | None = None
        self._closing = False

    def submit(self, text: str) -> None:
        # A submission made mid-turn queues as the next prompt - it does not steer the running one. Steering exists
        # (`Session.steer`, delivered at the running turn's next opportunity) and is to be reached through a `/steer`
        # command; for that to work, commands will have to be dispatched here immediately while a turn runs, rather than
        # queued behind it like a prompt.
        if self._closing or not text.strip():
            return
        if text.startswith('/'):
            self._app.show_command_echo(text)
        else:
            self._app.show_user_message(text)
        self._queue.append(text)
        self._maybe_start()

    def _maybe_start(self) -> None:
        if self._closing or self._task is not None or not self._queue:
            return
        text = self._queue.pop(0)
        task = asyncio.get_running_loop().create_task(self._run_one(text))
        self._task = task
        # Slot bookkeeping lives in a done callback rather than in _run_one's finally: a task cancelled before its first
        # step never runs its body at all, and the pump must not wedge on it.
        task.add_done_callback(self._on_task_done)

    async def _run_one(self, text: str) -> None:
        try:
            await self._session.prompt(text)
        except Exception as e:  # noqa: BLE001
            self._app.display_text(f'error: {e!r}', 'error')

    def _on_task_done(self, task: asyncio.Task) -> None:
        if self._task is task:
            self._task = None
        if self._app.is_busy:
            # Backstop for a lost terminal event. The loop shields its AgentEndEvent publish from cancellation, so this
            # is for a subscriber ahead of the renderer raising out of it. The prompt task is over either way, so close
            # the turn here.
            self._app.abort_ai_turn(cancelled=task.cancelled())
        self._maybe_start()

    def cancel_current(self) -> bool:
        if (task := self._task) is None or task.done():
            return False
        if not task.cancelling():
            task.cancel()
        # The turn closes on its terminal event, which comes only once the run has unwound - a tool's process stopped, a
        # parked ask released. That can take a moment, and a repeat of the key does nothing more.
        self._app.set_cancelling()
        return True

    async def aclose(self) -> None:
        self._closing = True
        self._queue.clear()
        if (task := self._task) is not None:
            if not task.cancelling():
                task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001, S110
                pass  # unwound at shutdown; errors already surfaced by _run_one
