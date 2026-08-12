import typing as ta

from ..console import Console
from ..console import ConsoleEvent
from ..readline import ReadlineAlikeReader
from ..readline import ReadlineConfig
from ..render import RenderedScreen
from ..types import Completer


##


class ScriptedConsole(Console):
    """A Console that plays back a scripted sequence of events and records what is rendered."""

    def __init__(
            self,
            events: ta.Iterable[ConsoleEvent],
            *,
            width: int = 80,
            height: int = 25,
            encoding: str = 'utf-8',
    ) -> None:
        super().__init__(0, 1, encoding=encoding)

        self._events = iter(events)
        self.set_height_width(height, width)

        self._beeps = 0
        self._refresh_count = 0

    @property
    def beeps(self) -> int:
        return self._beeps

    @property
    def refresh_count(self) -> int:
        return self._refresh_count

    def refresh(self, rendered_screen: RenderedScreen) -> None:
        self._refresh_count += 1
        self.sync_rendered_screen(rendered_screen)

    def prepare(self) -> None:
        pass

    def restore(self) -> None:
        pass

    def move_cursor(self, x: int, y: int) -> None:
        self._posxy = (x, y)

    def set_cursor_vis(self, visible: bool) -> None:
        pass

    def get_height_width(self) -> tuple[int, int]:
        return self._height, self._width

    def get_event(self, block: bool = True) -> ConsoleEvent | None:
        # Exhaustion raises StopIteration, ending the test's event loop.
        return next(self._events)

    def push_char(self, char: int | bytes) -> None:
        raise NotImplementedError

    def beep(self) -> None:
        self._beeps += 1

    def clear(self) -> None:
        pass

    def finish(self) -> None:
        pass

    def flush_output(self) -> None:
        pass

    def forgetinput(self) -> None:
        pass

    def get_pending(self) -> ConsoleEvent:
        return ConsoleEvent('key', '', b'')

    def wait(self, timeout: float | None = None) -> bool:
        return True

    @property
    def input_hook(self) -> ta.Callable[[], int] | None:
        return None

    def repaint(self) -> None:
        pass


##


def keys_to_events(*keys: str) -> ta.Iterator[ConsoleEvent]:
    """Yield key events. Multi-character strings are named keys ('up', 'backspace', ...)."""

    for key in keys:
        yield ConsoleEvent('key', key, key.encode())


def code_to_events(code: str) -> ta.Iterator[ConsoleEvent]:
    yield from keys_to_events(*code)


def make_reader(
        events: ta.Iterable[ConsoleEvent],
        *,
        width: int = 80,
        height: int = 25,
        completer: Completer | None = None,
) -> ReadlineAlikeReader:
    console = ScriptedConsole(list(events), width=width, height=height)
    config = ReadlineConfig(readline_completer=completer)
    reader = ReadlineAlikeReader(console=console, config=config)

    # Keep test output deterministic regardless of the environment's tty / color support.
    reader.can_colorize = False

    # Don't install the global threading excepthook during tests.
    reader.threading_hook = lambda: None

    reader.prompts.ps1 = '>>> '
    reader.prompts.ps2 = '>>> '
    reader.prompts.ps3 = '... '
    reader.prompts.ps4 = '... '

    return reader


def read_line(reader: ReadlineAlikeReader) -> str:
    """Run the reader's readline() loop until a command finishes it."""

    return reader.readline()


def drain_events(reader: ReadlineAlikeReader) -> None:
    """Prepare the reader and handle scripted events until they are exhausted."""

    reader.prepare()
    try:
        while True:
            reader.handle1()
    except StopIteration:
        pass
