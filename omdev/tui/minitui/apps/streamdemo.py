"""
The phase-1 proof: a fake llm stream rendered through the inline surface's commit model.

Paragraphs stream word-by-word into the live region (a bounded tail + spinner status line); each finished paragraph is
committed into the terminal's native scrollback and never touched again. Watch it in tmux: scrollback works, the history
survives exit, and only the live tail repaints.

Run: ./python -m x.minitui.apps.streamdemo [--visualize-redraws]

Ctrl-c exits (cleanly restoring the terminal).
"""
import sys
import time
import typing as ta

from omcore.term.spinners import SPINNERS

from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..surfaces.inlines import InlineSurface
from ..text.segments import Segment
from ..text.styles import Style
from ..text.themes import DEFAULT_THEME
from ..text.themes import SUCCESS


##


DEMO_THEME = DEFAULT_THEME.extend({
    'speaker': Style(fg=SUCCESS, bold=True),
})


PARAGRAPHS: ta.Sequence[str] = [
    (
        'This is minitui: the live region you are watching is the only thing being repainted - everything above this '
        'point has been committed to your terminal\'s own scrollback and will never be touched again.'
    ),

    (
        'Because committed lines are real terminal history, scrollback works natively (try it in tmux), copy and '
        'paste work, and the whole transcript remains visible after the program exits. No alternate screen, no '
        'dual-write hacks.'
    ),

    (
        'The streaming tail below is retained-frame diffed: each new word costs only the changed span of the changed '
        'line, wrapped in synchronized output so nothing tears. When a paragraph finishes, its lines commit - and if '
        'they commit exactly as displayed, that costs zero bytes.'
    ),

    (
        'Next up: the event layer, controls, and a vim engine with a scrolled-viewport input textarea. But first, '
        'this little loop needed to feel right in a real terminal.'
    ),
]


def wrap_words(words: ta.Sequence[str], width: int) -> list[str]:
    lines: list[str] = []
    current = ''
    for word in words:
        candidate = f'{current} {word}' if current else word
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


class StreamDemo:
    def __init__(
            self,
            surface: InlineSurface,
            *,
            tail_height: int = 6,
            word_delay_s: float = .04,
    ) -> None:
        super().__init__()

        self._surface = surface
        self._tail_height = tail_height
        self._word_delay_s = word_delay_s

        self._spin_frames = SPINNERS['dots3']
        self._spin_index = 0

    def _line(self, *parts: tuple[str, ta.Any]) -> Line:
        return line_from_segments([Segment(text, style) for text, style in parts], DEMO_THEME)

    def _status_line(self, message: str) -> Line:
        self._spin_index += 1
        spinner = self._spin_frames[self._spin_index % len(self._spin_frames)]
        return self._line(
            (spinner, 'status.spinner'),
            (' ', None),
            (message, 'status.text'),
        )

    def _tail_frame(self, streamed_words: ta.Sequence[str], status: str) -> Frame:
        width = max(self._surface.width, 8)
        tail = wrap_words(streamed_words, width)[-self._tail_height:]
        lines = [
            *(self._line((text, None)) for text in tail),
            self._line(),
            self._status_line(status),
        ]
        return Frame(tuple(lines), cursor=(0, len(lines) - 1), cursor_visible=False)

    def _commit_paragraph(self, words: ta.Sequence[str]) -> None:
        width = max(self._surface.width, 8)
        self._surface.commit([
            *(self._line((text, None)) for text in wrap_words(words, width)),
            self._line(),
        ])

    def run(self) -> None:
        surface = self._surface

        surface.commit([
            self._line(('assistant', 'speaker'), (' (streamed via minitui)', 'status.text')),
            self._line(),
        ])

        for n, paragraph in enumerate(PARAGRAPHS):
            words = paragraph.split()
            streamed: list[str] = []
            for word in words:
                surface.take_resized()
                streamed.append(word)
                surface.present(self._tail_frame(
                    streamed,
                    f'streaming paragraph {n + 1}/{len(PARAGRAPHS)}...',
                ))
                time.sleep(self._word_delay_s)

            # The tail was displaying exactly these wrapped lines, so most of this commit costs nothing.
            self._commit_paragraph(streamed)

        done_message = 'done - this line is all that remains live; everything above is plain scrollback.'
        done_lines = tuple(
            self._line((text, 'status.text'))
            for text in wrap_words(done_message.split(), max(surface.width, 8))
        )
        surface.present(Frame(
            done_lines,
            cursor=(0, len(done_lines) - 1),
        ))


def _main() -> None:
    surface = InlineSurface(
        visualize_redraws='--visualize-redraws' in sys.argv[1:],
    )

    surface.prepare()
    try:
        StreamDemo(surface).run()
    except KeyboardInterrupt:
        pass
    finally:
        surface.restore()


if __name__ == '__main__':
    _main()
