import typing as ta


type KeySpec = str  # like r"\C-c"
type Keymap = tuple[tuple[KeySpec, CommandName], ...]

type CommandName = str  # like "interrupt"

type Completer = ta.Callable[[str, int], str | None]
type CompletionAction = tuple[str, ta.Callable[[], str | None]]

type CharBuffer = list[str]
type CharWidths = list[int]

type EventData = list[str]
type EventTuple = tuple[CommandName, EventData]

type CursorXY = tuple[int, int]
type Dimensions = tuple[int, int]
type ScreenInfoRow = tuple[int, list[int]]
