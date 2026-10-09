import typing as ta

from omcore.text import diffs
from omcore.text import styled as st

from .rendering import TextRenderingOptions
from .types import DiffText


##


def build_diff_doc_options(options: TextRenderingOptions, *, width: int) -> diffs.DiffStyledDocOptions:
    """
    The diff renderer's options for a frontend's: what the frontend leaves unset keeps the diff renderer's default.
    """

    overrides: dict[str, ta.Any] = {}
    if (layout := options.diff_layout) is not None:
        overrides['layout'] = layout
    if (context_limits := options.diff_context_limits) is not None:
        overrides['context_limits'] = context_limits

    return diffs.DiffStyledDocOptions(width=width, **overrides)


def render_diff_text_doc(
        t: DiffText,
        *,
        width: int,
        options: TextRenderingOptions | None = None,
) -> st.StyledDocument:
    """
    Lays out a diff block as a target-neutral styled document. The block carries both texts whole, so they are the
    source of its file's full context: every hunk is highlighted with the code around it, not just its own lines, as
    far as the options' context limits allow.
    """

    patch_set = diffs.parse_patch(''.join(t.diff_lines))

    # Keyed by the path the patch was parsed with - the parser's reading of the block's own path, not a guess at it.
    file_source = diffs.DictDiffFileSource({
        path: diffs.DiffFileTexts(
            source=diffs.split_newlines(t.old),
            target=diffs.split_newlines(t.new),
        )
        for file_patch in patch_set.files
        if (path := file_patch.new_path or file_patch.old_path) is not None
    })

    return diffs.DiffStyledDocRenderer(
        build_diff_doc_options(options if options is not None else TextRenderingOptions(), width=width),
        file_source=file_source,
    ).render(patch_set)
