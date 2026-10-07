"""
The minitui frontend's reusable core: binds a `Session` to a `TextArea` and a commit callback. Submissions are echoed,
queued, and run one at a time through the runner; each output an execution writes commits as it arrives; the input's
highlighter and prompt follow the active language while the console is active. Not a control - it owns no layout and
reads no keys. A host app composes it: the standalone `ReplApp` here, or a chat app lending its input box.
"""
import collections
import typing as ta

from ...minitui.controls.textarea import TextArea
from ...minitui.text.parts import TextParts
from ...minitui.text.segments import Segment
from ..interpreters import InterpreterBusyError
from ..interpreters import ResultStatus
from ..languages import Language
from ..outputs import CallbackOutputSink
from ..outputs import Output
from ..runners import Runner
from ..runners import Running
from ..sessions import Session
from .highlighting import get_language_highlighter
from .rendering import render_echo
from .rendering import render_note
from .rendering import render_output


CommitFn: ta.TypeAlias = ta.Callable[[ta.Sequence[ta.Sequence[Segment]]], None]


##


class Console:
    def __init__(
            self,
            session: Session,
            textarea: TextArea,
            *,
            runner: Runner,
            commit: CommitFn,
            width: ta.Callable[[], int],
            on_exit: ta.Callable[[], None] | None = None,
            on_change: ta.Callable[[], None] | None = None,
    ) -> None:
        """
        `commit` receives width-safe rows to append to scrollback; `width` is asked at render time. `on_exit` fires
        when executed code asks to leave (`exit()`); `on_change` whenever something displayed may have changed - the
        host's invalidate.
        """

        super().__init__()

        self._session = session
        self._textarea = textarea
        self._runner = runner
        self._commit = commit
        self._width = width
        self._on_exit = on_exit
        self._on_change = on_change

        self._queue: collections.deque[str] = collections.deque()
        self._running: Running | None = None
        self._active = False

        session.add_listener(self._on_session_change)

    @property
    def session(self) -> Session:
        return self._session

    @property
    def textarea(self) -> TextArea:
        return self._textarea

    @property
    def language(self) -> Language:
        return self._session.active.language

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def is_running(self) -> bool:
        return self._running is not None and not self._running.done

    @property
    def queued(self) -> int:
        return len(self._queue)

    def _changed(self) -> None:
        if (fn := self._on_change) is not None:
            fn()

    ##
    # The input box

    def activate(self) -> None:
        """Take the textarea: its highlighter and prompt follow the active language from here on."""

        if self._active:
            return
        self._active = True
        self._apply_language()
        self._changed()

    def deactivate(self) -> None:
        """Give the textarea back as it was: no highlighter, no prompt."""

        if not self._active:
            return
        self._active = False
        self._textarea.set_highlighter(None)
        self._textarea.set_prompt('')
        self._changed()

    def _apply_language(self) -> None:
        if not self._active:
            return
        language = self.language
        self._textarea.set_highlighter(get_language_highlighter(language))
        self._textarea.set_prompt(language.prompt, 'repl.prompt')

    def _on_session_change(self, session: Session) -> None:
        self._apply_language()
        self._changed()

    def switch(self, name: str) -> None:
        self._session.switch(name)

    ##
    # Execution

    def submit(self, text: str) -> None:
        """Echo and queue a source; it runs when whatever is ahead of it has finished."""

        if not text.strip():
            return
        self._commit(render_echo(self.language, text, self._width()))
        self._queue.append(text)
        self._pump()
        self._changed()

    def _pump(self) -> None:
        if self.is_running or not self._queue:
            return
        text = self._queue.popleft()
        self._running = self._runner.start(lambda: self._run(text))

    async def _run(self, text: str) -> None:
        sink = CallbackOutputSink(self._on_output)
        exited = False
        try:
            result = await self._session.execute(text, sink)
        except InterpreterBusyError:
            self._note('the interpreter is busy')
        except Exception as e:  # noqa: BLE001
            self._note(f'error: {e!r}')
        except BaseException:
            self._note('interrupted')
            raise
        else:
            exited = result.status is ResultStatus.EXIT
        finally:
            self._commit([[]])
            # Cleared before pumping: the next execution starts from here, inside this one's wind-down.
            self._running = None
            self._changed()
            self._pump()

        if exited and (fn := self._on_exit) is not None:
            fn()

    def _on_output(self, output: Output) -> None:
        self._commit(render_output(output, self._width()))
        self._changed()

    def _note(self, text: str) -> None:
        self._commit(render_note(text, self._width()))

    def cancel(self) -> bool:
        """Cancel the running execution, if any. Queued ones stay queued."""

        if (running := self._running) is not None and not running.done:
            running.cancel()
            return True
        return False

    def clear_queue(self) -> None:
        self._queue.clear()

    ##
    # Status

    def status_parts(self) -> TextParts:
        return [
            (self.language.display_name, 'repl.language'),
            ('  running' if self.is_running else '', 'status.dim'),
            (f'  +{n} queued' if (n := len(self._queue)) else '', 'status.dim'),
        ]
