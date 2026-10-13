"""
Outputs to rows: what the frontend commits for an echoed source and for each output an execution writes. Rows are
width-safe (committed lines must never exceed the terminal width) and carry the repl's theme tags.
"""
import typing as ta

from omcore import check
from omcore.term import styled as tst
from omcore.text import styled as st

from ...minitui.text.segments import Segment
from ...minitui.text.wrap import wrap_segments
from ..languages import Language
from ..outputs import ErrorOutput
from ..outputs import NoteOutput
from ..outputs import Output
from ..outputs import ResultOutput
from ..outputs import StdoutOutput
from ..outputs import TerminalOutput


SegmentRows: ta.TypeAlias = list[list[Segment]]


##


_OUTPUT_TAGS: ta.Mapping[type[Output], str] = {
    StdoutOutput: 'repl.stdout',
    ResultOutput: 'repl.result',
    ErrorOutput: 'repl.error',
    TerminalOutput: 'repl.stdout',
    NoteOutput: 'repl.note',
}


def _clean(line: str) -> str:
    """Segments carry plain text only: no escapes, no carriage returns; tabs expand to a fixed width."""

    return line.replace('\r', '').replace('\x1b', '^[').expandtabs(4)


def _wrap_line(line: str, tag: str, width: int) -> SegmentRows:
    if not line:
        return [[]]
    return [list(row) for row in wrap_segments([Segment(line, tag)], width)]


def _wrap_plain_line(line: str, tag: str, width: int) -> SegmentRows:
    return _wrap_line(_clean(line), tag, width)


def render_echo(language: Language, source: str, width: int) -> SegmentRows:
    """The submitted source as the classic transcript shows it: prompted first line, continuation-prompted rest."""

    rows: SegmentRows = []
    for i, raw in enumerate(source.split('\n')):
        prompt = language.prompt if i == 0 else language.continuation_prompt
        segments = [Segment(prompt, 'repl.prompt')]
        if (line := _clean(raw)):
            segments.append(Segment(line, 'repl.echo'))
        rows.extend(list(row) for row in wrap_segments(segments, width))
    return rows


def _wrap_terminal_line(line: str, tag: str, width: int) -> SegmentRows:
    """
    A line of terminal output: the styles its SGR escapes select are concrete and shown as they are, and what they
    leave plain takes the output's own tag.
    """

    segments: list[Segment] = []
    for run in tst.parse_ansi_text(line).runs():
        # Cleaned as any output is, and before it is a segment: what is left of a sequence the parse did not take
        # for one is still an escape.
        if not (text := _clean(run.text)):
            continue
        if run.styles:
            patch = check.isinstance(check.single(run.styles), st.StylePatch)
            segments.append(Segment(text, patch.resolve()))
        else:
            segments.append(Segment(text, tag))

    if not segments:
        return [[]]
    return [list(row) for row in wrap_segments(segments, width)]


def render_output(output: Output, width: int) -> SegmentRows:
    tag = next((t for c, t in _OUTPUT_TAGS.items() if isinstance(output, c)), None)
    if tag is None:
        raise TypeError(output)

    text = output.text
    if isinstance(output, (StdoutOutput, TerminalOutput)) and text.endswith('\n'):
        text = text[:-1]  # the row break is the newline

    wrap_line = _wrap_terminal_line if isinstance(output, TerminalOutput) else _wrap_plain_line

    rows: SegmentRows = []
    for raw in text.split('\n'):
        rows.extend(wrap_line(raw, tag, width))
    return rows


def render_note(text: str, width: int) -> SegmentRows:
    """A remark from the frontend itself - not the code's output."""

    return _wrap_line(_clean(text), 'repl.note', width)
