"""Headless terminal rendering for styled diff documents."""
import pathlib

from omcore.term import styled as tst
from omcore.text import diffs

from .rendering import render_diff_document
from .themes import DIFF_STYLE_THEME


##


def render_diff_ansi(
        patch_set: diffs.PatchSet,
        project_root: pathlib.Path | None = None,
        *,
        width: int = 80,
        tab_size: int = 4,
        syntax_highlighting: bool = True,
        color_depth: tst.ColorDepth = tst.ColorDepth.TRUE,
) -> str:
    """Render a patch set to ANSI without constructing a terminal runtime or driver."""

    document = render_diff_document(
        patch_set,
        project_root,
        width=width,
        tab_size=tab_size,
        syntax_highlighting=syntax_highlighting,
    )
    return tst.render_ansi(document, theme=DIFF_STYLE_THEME, depth=color_depth)
