import abc
import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.text import diffs

from .types import CanText
from .types import DiffText
from .types import JsonTextStyle
from .types import MarkdownText


O = ta.TypeVar('O')


##


@dc.dataclass(frozen=True, kw_only=True)
class TextRenderingOptions:
    density: ta.Literal['pretty', 'compact', None] = None

    json_style: JsonTextStyle = JsonTextStyle.DEFAULT

    # How a frontend drawing diffs lays out their hunks - side by side, or one beneath the other. None leaves it to the
    # diff renderer, which chooses by the width it is given.
    diff_layout: diffs.DiffLayout | None = None

    # How big a diffed file may be for its hunks to be highlighted with the whole file around them. None leaves it to
    # the diff renderer's defaults.
    diff_context_limits: diffs.DiffContextLimits | None = None

    # The working directory, paths beneath which are shown relative to it. None shows every path as given.
    cwd: str | None = None

    # Shows every path as given, even those beneath the cwd.
    absolute_paths: bool = False


class TextRenderer(lang.Abstract, ta.Generic[O]):
    @abc.abstractmethod
    def render(self, *ts: CanText) -> O:
        raise NotImplementedError


##


def resolve_json_text_style(
        options: TextRenderingOptions,
        style: JsonTextStyle = JsonTextStyle.DEFAULT,
) -> JsonTextStyle:
    """Layers, least to most specific: the options density, the options json_style, the given (node) style."""

    return (
        JsonTextStyle(mode=options.density)
        .merge(options.json_style)
        .merge(style)
    )


##


def resolve_display_path(options: TextRenderingOptions, path: str) -> str:
    """A path as shown: relative to the options' cwd if beneath it, unless they ask for absolute paths."""

    if (
            options.absolute_paths or
            (cwd := options.cwd) is None or
            not os.path.isabs(path) or
            not os.path.isabs(cwd)
    ):
        return path

    cwd = os.path.normpath(cwd)
    if os.path.commonpath([os.path.normpath(path), cwd]) != cwd:
        return path

    return os.path.relpath(path, cwd)


def resolve_display_diff_text(options: TextRenderingOptions, t: DiffText) -> DiffText:
    """A diff block as shown: its path resolved for display, its texts untouched."""

    if t.path is None or (path := resolve_display_path(options, t.path)) == t.path:
        return t

    return dc.replace(t, path=path)


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
