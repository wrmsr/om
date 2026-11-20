"""
An IRC-shaped curses demo; Python 3.11+, Unix, no third-party packages.

Run: python3 curses_irc_native.py
Type /quit to exit. PgUp/PgDn scroll; arrows/Home/End edit; Ctrl-U clears.

Replace DemoClient with your existing client's adapter to Client. This demo does not connect to a server. send()
completion produces the sole local echo; an adapter for a server with echo-message should suppress duplicate echoes.

Deliberate limits: one channel, approximate Unicode cell widths, code-point editing, no bracketed-paste protection
(pasted newlines can submit messages), no grapheme/complex-emoji handling, no reconnect or pending-send persistence.
History is capped at 1,000 messages and rewrapped on each changed frame.
"""
import asyncio
import curses
import dataclasses
import locale
import typing as ta
import unicodedata
from collections import deque


@dataclasses.dataclass(frozen=True)
class Message:
    nick: str
    text: str


class Client(ta.Protocol):
    def messages(self) -> ta.AsyncIterator[Message]: ...

    async def send(self, text: str) -> None: ...


class DemoClient:
    async def messages(self) -> ta.AsyncIterator[Message]:
        messages = [
            Message('alice', 'This is a simulated feed; no network is used.'),
            Message('bob', 'Type a message. Incoming messages keep arriving while you edit.'),
            Message('alice', 'Resize the terminal or use PgUp and PgDn.'),
            Message('bob', 'Common Unicode: café, naïve, 日本語. Complex emoji are out of scope.'),
        ]
        index = 0
        while True:
            await asyncio.sleep(2)
            yield messages[index % len(messages)]
            index += 1

    async def send(self, text: str) -> None:
        await asyncio.sleep(0.15)  # Simulate an asynchronous write/rate limiter.


@dataclasses.dataclass
class State:
    history: deque[str] = dataclasses.field(default_factory=lambda: deque(maxlen=1000))
    text: str = ''
    cursor: int = 0
    scroll: int = 0
    dirty: bool = True
    connected: bool = True


def clean(text: str) -> str:
    # Display controls as visible placeholders; preserve the underlying input.
    return ''.join(ch if ch.isprintable() else '?' for ch in text)


def cell_width(ch: str) -> int:
    if unicodedata.category(ch) in ('Mn', 'Me'):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def text_width(text: str) -> int:
    return sum(cell_width(ch) for ch in clean(text))


def clip(text: str, width: int) -> str:
    result = ''
    used = 0
    for ch in clean(text):
        size = cell_width(ch)
        if used + size > width:
            break
        if size or result:  # Do not attach a leading mark to a neighboring cell.
            result += ch
            used += size
    return result


def wrap(text: str, width: int) -> list[str]:
    result = []
    line = ''
    used = 0
    for ch in clean(text):
        size = cell_width(ch)
        if size > width:
            ch, size = '?', 1
        if used + size > width:
            result.append(line)
            line, used = '', 0
        if size or line:
            line += ch
            used += size
    result.append(line)
    return result


def draw(screen: curses.window, state: State) -> None:
    height, columns = screen.getmaxyx()
    width = max(0, columns - 1)  # Never write the bottom-right cell.
    screen.erase()
    if height < 3 or width < 4:
        if width:
            screen.addstr(0, 0, clip('Terminal too small', width))
    else:
        body_height = height - 2
        lines = [line for message in state.history for line in wrap(message, width)]
        state.scroll = min(state.scroll, max(0, len(lines) - body_height))
        end = len(lines) - state.scroll
        for y, line in enumerate(lines[max(0, end - body_height):end]):
            screen.addstr(y, 0, line)
        status = 'connected' if state.connected else 'disconnected'
        status = f'#demo | {status} | PgUp/PgDn | /quit | back: {state.scroll}'
        screen.addstr(height - 2, 0, clip(status, width), curses.A_REVERSE)

        capacity = width - 2
        start = 0
        while start < state.cursor and text_width(state.text[start:state.cursor]) > capacity:
            start += 1
        screen.addstr(height - 1, 0, '> ' + clip(state.text[start:], capacity))
        screen.move(height - 1, 2 + text_width(state.text[start:state.cursor]))
    screen.noutrefresh()
    curses.doupdate()
    state.dirty = False


async def run(screen: curses.window, client: Client) -> None:
    screen.keypad(True)
    screen.nodelay(True)
    curses.set_escdelay(25)
    state = State()
    outbox: asyncio.Queue[str] = asyncio.Queue(maxsize=32)

    def append(text: str) -> None:
        state.history.append(text)
        if state.scroll:
            state.scroll += len(wrap(text, max(1, screen.getmaxyx()[1] - 1)))
        state.dirty = True

    async def receive() -> None:
        async for message in client.messages():
            append(f'<{message.nick}> {message.text}')
        state.connected = False
        append('* incoming message stream ended')

    async def send() -> None:
        while True:
            text = await outbox.get()
            await client.send(text)
            append(f'<you> {text}')

    append('* Offline demo. Type /quit to exit. Pasted newlines submit messages.')
    workers = [asyncio.create_task(receive()), asyncio.create_task(send())]
    running = True
    try:
        while running:
            for worker in workers:
                if worker.done():
                    worker.result()  # Propagate failures through curses.wrapper.
            for _ in range(128):  # Bound work so network tasks get a turn.
                try:
                    key = screen.get_wch()
                except curses.error:
                    break  # Expected when the nonblocking input queue is empty.
                state.dirty = True
                if key == curses.KEY_RESIZE:
                    continue
                if key in ('\n', '\r', curses.KEY_ENTER):
                    if state.text == '/quit':
                        running = False
                        break
                    if state.text:
                        try:
                            outbox.put_nowait(state.text)
                        except asyncio.QueueFull:
                            append('* send queue full; your input was kept')
                        else:
                            state.text, state.cursor, state.scroll = '', 0, 0
                elif key in ('\b', '\x7f', curses.KEY_BACKSPACE):
                    if state.cursor:
                        state.text = state.text[:state.cursor - 1] + state.text[state.cursor:]
                        state.cursor -= 1
                elif key == curses.KEY_DC:
                    state.text = state.text[:state.cursor] + state.text[state.cursor + 1:]
                elif key == curses.KEY_LEFT:
                    state.cursor = max(0, state.cursor - 1)
                elif key == curses.KEY_RIGHT:
                    state.cursor = min(len(state.text), state.cursor + 1)
                elif key == curses.KEY_HOME:
                    state.cursor = 0
                elif key == curses.KEY_END:
                    state.cursor = len(state.text)
                elif key == '\x15':
                    state.text, state.cursor = '', 0
                elif key == curses.KEY_PPAGE:
                    state.scroll += max(1, screen.getmaxyx()[0] - 3)
                elif key == curses.KEY_NPAGE:
                    state.scroll = max(0, state.scroll - max(1, screen.getmaxyx()[0] - 3))
                elif isinstance(key, str) and key.isprintable():
                    state.text = state.text[:state.cursor] + key + state.text[state.cursor:]
                    state.cursor += 1
            if state.dirty:
                draw(screen, state)
            await asyncio.sleep(0.02)
    finally:
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    curses.wrapper(lambda screen: asyncio.run(run(screen, DemoClient())))
