from omcore.text import diffs
from omcore.text import styled as st

from .types import DiffText


##


def render_diff_text_doc(
        t: DiffText,
        *,
        width: int,
        layout: diffs.DiffLayout = 'auto',
) -> st.StyledDocument:
    """
    Lays out a diff block as a target-neutral styled document. The block carries both texts whole, so they are the
    source of its file's full context: every hunk is highlighted with the code around it, not just its own lines.
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

    return diffs.render_diff_styled_doc(
        patch_set,
        file_source,
        width=width,
        layout=layout,
    )
