"""Headless terminal rendering for styled diff documents."""
import pathlib

from ...diffs.types import PatchSet
from .. import minitui as mt
from .rendering import render_diff_document
from .themes import DIFF_STYLE_THEME


##


DIFF_TERMINAL_THEME = mt.Theme(DIFF_STYLE_THEME.as_dict())


def render_diff_ansi(
        patch_set: PatchSet,
        project_root: pathlib.Path | None = None,
        *,
        width: int = 80,
        tab_size: int = 4,
        syntax_highlighting: bool = True,
        color_depth: mt.ColorDepth = mt.ColorDepth.TRUE,
) -> str:
    """Render a patch set to ANSI without constructing a minitui runtime or driver."""

    document = render_diff_document(
        patch_set,
        project_root,
        width=width,
        tab_size=tab_size,
        syntax_highlighting=syntax_highlighting,
    )
    return mt.render_ansi_styled_document(
        document,
        theme=DIFF_TERMINAL_THEME,
        depth=color_depth,
    )
