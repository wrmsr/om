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


class DisplayPathResolver(lang.Abstract):
    """How a path is shown: as given, or relative to something the frontend knows about where it is."""

    @abc.abstractmethod
    def resolve_display_path(self, path: str) -> str:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class CwdDisplayPathResolver(DisplayPathResolver):
    """Paths beneath the cwd are shown relative to it; any other path, or a relative one, as given."""

    cwd: str

    def resolve_display_path(self, path: str) -> str:
        if not os.path.isabs(path) or not os.path.isabs(cwd := self.cwd):
            return path

        cwd = os.path.normpath(cwd)
        if os.path.commonpath([os.path.normpath(path), cwd]) != cwd:
            return path

        return os.path.relpath(path, cwd)


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

    # How paths are shown. None shows every path as given.
    paths: DisplayPathResolver | None = None


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
    """A path as shown: as the options' resolver has it, or as given without one."""

    if (paths := options.paths) is None:
        return path

    return paths.resolve_display_path(path)


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
