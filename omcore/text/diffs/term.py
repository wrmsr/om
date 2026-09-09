"""Headless terminal rendering for styled diff documents."""
import pathlib

from ...term import styled as tst
from .. import diffs
from .styled import render_diff_styled_doc
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
    doc = render_diff_styled_doc(
        patch_set,
        project_root,
        width=width,
        tab_size=tab_size,
        syntax_highlighting=syntax_highlighting,
    )

    return tst.render_ansi(
        doc,
        theme=DIFF_STYLE_THEME,
        depth=color_depth,
    )
