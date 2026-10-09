"""Headless terminal rendering for styled diff documents."""
from ...term import styled as tst
from .. import diffs
from .styled.options import DiffLayout
from .styled.rendering import render_diff_styled_doc
from .styled.sources import DiffFileSource
from .themes import DIFF_STYLE_THEME


##


def render_diff_ansi(
        patch_set: diffs.PatchSet,
        file_source: DiffFileSource | None = None,
        *,
        width: int = 80,
        tab_size: int = 4,
        syntax_highlighting: bool = True,
        layout: DiffLayout = 'auto',
        color_depth: tst.ColorDepth = tst.ColorDepth.TRUE,
) -> str:
    doc = render_diff_styled_doc(
        patch_set,
        file_source,
        width=width,
        tab_size=tab_size,
        syntax_highlighting=syntax_highlighting,
        layout=layout,
    )

    return tst.render_ansi(
        doc,
        theme=DIFF_STYLE_THEME,
        depth=color_depth,
    )
