"""Immutable documents composed of styled text lines."""
import collections.abc
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .text import StyledText
from .text import StyledTextLike


##


@dc.dataclass(frozen=True)
class StyledDocument(lang.Final):
    """
    Immutable, target-neutral styled text split into logical lines.

    Newline characters are structural rather than part of any line. `trailing_newline` distinguishes ``'a'`` from
    ``'a\n'`` without manufacturing an extra terminal row.
    """

    lines: tuple[StyledText, ...] = ()
    trailing_newline: bool = False

    def __post_init__(self) -> None:
        lines = tuple(self.lines)
        if not all(isinstance(line, StyledText) for line in lines):
            raise TypeError(lines)
        if any('\n' in line.text or '\r' in line.text for line in lines):
            raise ValueError(lines)
        if not isinstance(self.trailing_newline, bool):
            raise TypeError(self.trailing_newline)
        if not lines and self.trailing_newline:
            raise ValueError(self.trailing_newline)
        object.__setattr__(self, 'lines', lines)

    def __bool__(self) -> bool:
        return bool(self.lines)

    def __len__(self) -> int:
        return len(self.lines)

    def __iter__(self) -> collections.abc.Iterator[StyledText]:
        return iter(self.lines)

    def __getitem__(self, index: int | slice) -> StyledText | tuple[StyledText, ...]:
        return self.lines[index]

    @property
    def plain(self) -> str:
        text = '\n'.join(line.plain for line in self.lines)
        if self.trailing_newline:
            text += '\n'
        return text

    @property
    def text(self) -> StyledText:
        if not self.lines:
            return StyledText()
        text = StyledText('\n').join(self.lines)
        if self.trailing_newline:
            text += '\n'
        return text

    @classmethod
    def of_lines(
            cls,
            lines: ta.Iterable[StyledTextLike],
            *,
            trailing_newline: bool = False,
    ) -> ta.Self:
        """Build a document from newline-free lines."""

        return cls(
            tuple(StyledText.of(line) for line in lines),
            trailing_newline=trailing_newline,
        )

    @classmethod
    def of_text(cls, text: StyledTextLike) -> ta.Self:
        """Split styled text on newlines while retaining all visible character spans."""

        value = StyledText.of(text)
        if not value:
            return cls()

        trailing_newline = value.text.endswith('\n')
        lines: list[StyledText] = []
        start = 0
        while (end := value.text.find('\n', start)) >= 0:
            lines.append(value.slice(start, end))
            start = end + 1
        if start < len(value):
            lines.append(value.slice(start))

        return cls(tuple(lines), trailing_newline=trailing_newline)


type StyledContent = StyledTextLike | StyledDocument
