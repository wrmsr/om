# ruff: noqa: A001 A002
import asyncio
import collections
import typing as ta

from omcore import check

from .... import agent as agn
from .... import harness as har
from .app import MinituiChatApp


Input: ta.TypeAlias = str | har.ParsedCommand


##


class PromptPump:
    """Serializes prompts, with a separate owned path for commands allowed during a prompt."""

    def __init__(
            self,
            *,
            agent: agn.Agent,
            app: MinituiChatApp,
            commands: har.CommandsManager | None = None,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._app = app
        self._commands = commands

        self._queue: collections.deque[Input] = collections.deque()
        self._task: asyncio.Task | None = None
        self._closing = False
        self._command_tasks: set[asyncio.Task] = set()

    def submit(self, text: str) -> None:
        if self._closing or not text.strip():
            return

        input: Input

        if text.startswith('/'):
            # Echoed as it is submitted rather than as it runs, so that pressing enter is seen to have registered even
            # when the command then has to wait its turn.
            # TODO: show a command (or a prompt) which is queued but not yet run as such - slightly grayed, say - until
            # it does. What is committed to scrollback cannot be restyled, so it would likely have to sit in the live
            # region until then, and only move down into scrollback as it runs.
            self._app.show_command_echo(text)

            try:
                input = check.not_none(self._commands).parse(text[1:])
            except har.ParseCommandError as e:
                if e.message is not None:
                    self._app.display_ui_text(e.message)
                return

            if self._task is not None and input.command.can_run_while_busy:
                task = asyncio.get_running_loop().create_task(self._run_one(input))
                self._command_tasks.add(task)
                task.add_done_callback(self._command_tasks.discard)
                return

        else:
            self._app.show_user_message(text)

            input = text

        self._queue.append(input)
        self._maybe_start()

    def _maybe_start(self) -> None:
        if self._closing or self._task is not None or not self._queue:
            return

        input = self._queue.popleft()
        task = asyncio.get_running_loop().create_task(self._run_one(input))
        self._task = task

        # Slot bookkeeping lives in a done callback rather than in _run_one's finally: a task cancelled before its first
        # step never runs its body at all, and the pump must not wedge on it.
        task.add_done_callback(self._on_task_done)

    async def _run_one(self, input: Input) -> None:
        try:
            if isinstance(input, str):
                await self._agent.prompt(input)

            elif isinstance(input, har.ParsedCommand):
                await input.run()

            else:
                raise TypeError(input)

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

        tasks = list(self._command_tasks)
        if (task := self._task) is not None:
            tasks.append(task)

        # Cancel every owned task before joining any of them: a command's cleanup may need the prompt to unwind.
        for task in tasks:
            if not task.cancelling():
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
