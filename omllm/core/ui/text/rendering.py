import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .types import CanText
from .types import DiffText
from .types import MarkdownText


O = ta.TypeVar('O')


##


@dc.dataclass(frozen=True, kw_only=True)
class TextRenderingOptions:
    density: ta.Literal['pretty', 'compact', None] = None


class TextRenderer(lang.Abstract, ta.Generic[O]):
    @abc.abstractmethod
    def render(self, t: CanText) -> O:
        raise NotImplementedError


##


def squash_markdown_text(t: MarkdownText) -> str:
    """The compact-density degradation of a markdown block - raw source, whitespace-squashed. Not a rendering."""

    return ' '.join(t.s.split())


def summarize_diff_text(t: DiffText) -> str:
    """The compact-density degradation of a diff block - a one-line change summary."""

    adds = sum(1 for l in t.diff_lines if l.startswith('+') and not l.startswith('+++'))
    dels = sum(1 for l in t.diff_lines if l.startswith('-') and not l.startswith('---'))

    s = f'+{adds} -{dels}'
    if t.path is not None:
        s = f'{t.path}: {s}'
    return s
