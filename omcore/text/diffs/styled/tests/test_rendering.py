import pytest

from .....html import styled as hst
from .....term import styled as tst
from .... import diffs
from ...parsing import parse_patch
from ...term import render_diff_ansi
from ...themes import DIFF_STYLE_THEME
from ..options import DiffStyledDocOptions
from ..rendering import DiffStyledDocRenderer
from ..rendering import render_diff_styled_doc
from ..split import SplitDiffHunkLayout
from ..unified import UnifiedDiffHunkLayout
from .utils import MODIFIED_DIFF


##


@pytest.mark.parametrize(('width', 'layout'), [(80, 'unified'), (159, 'unified'), (160, 'split'), (200, 'split')])
def test_auto_splits_only_from_its_width_up(width, layout):
    assert DiffStyledDocOptions(width=width).resolved_layout == layout


def test_auto_split_width_and_explicit_layouts():
    assert DiffStyledDocOptions(width=100, auto_split_width=100).resolved_layout == 'split'
    assert DiffStyledDocOptions(width=200, layout='unified').resolved_layout == 'unified'
    assert DiffStyledDocOptions(width=80, layout='split').resolved_layout == 'split'

    with pytest.raises(Exception):  # noqa
        DiffStyledDocOptions(layout='sideways')  # type: ignore[arg-type]


def test_a_given_hunk_layout_is_used_whatever_the_options_say():
    patch = parse_patch(MODIFIED_DIFF)
    options = DiffStyledDocOptions(width=60, layout='split')

    given = DiffStyledDocRenderer(options, hunk_layout=UnifiedDiffHunkLayout(options)).render(patch)

    assert given == render_diff_styled_doc(patch, width=60, layout='unified')
    assert given != DiffStyledDocRenderer(options, hunk_layout=SplitDiffHunkLayout(options)).render(patch)


##
# The frame around the hunks is the same whichever layout fills it.


LAYOUTS = pytest.mark.parametrize('layout', ['split', 'unified'])


@LAYOUTS
def test_markup_shaped_source_text_is_literal(layout):
    document = render_diff_styled_doc(parse_patch("""\
--- a/types.py
+++ b/types.py
@@ -1 +1 @@ list[str]
-value: list[int]
+value: list[str]
"""), width=80, layout=layout)

    assert 'list[str]' in document.plain
    assert 'value: list[int]' in document.plain
    assert '<span style=' in hst.render_html(document, theme=DIFF_STYLE_THEME)


@LAYOUTS
def test_special_file_bodies(layout):
    deleted = render_diff_styled_doc(parse_patch("""\
diff --git a/old.txt b/old.txt
deleted file mode 100644
--- a/old.txt
+++ /dev/null
"""), width=60, layout=layout)
    binary = render_diff_styled_doc(parse_patch("""\
diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""), width=60, layout=layout)
    renamed = render_diff_styled_doc(parse_patch("""\
diff --git a/old.txt b/new.txt
similarity index 100%
rename from old.txt
rename to new.txt
--- a/old.txt
+++ b/new.txt
"""), width=60, layout=layout)

    assert 'File was removed' in deleted.plain
    assert 'File is binary' in binary.plain
    assert 'old.txt → new.txt' in renamed.plain
    assert 'File was only renamed' in renamed.plain


@LAYOUTS
def test_headless_ansi_has_same_visible_text(layout):
    patch = parse_patch(MODIFIED_DIFF)
    document = render_diff_styled_doc(patch, width=60, layout=layout)

    ansi = render_diff_ansi(patch, width=60, layout=layout)

    assert tst.strip_ansi_escapes(ansi) == document.plain
    assert '\x1b[' in ansi


def test_layouts_share_the_frame():
    patch = parse_patch(MODIFIED_DIFF)
    split = render_diff_styled_doc(patch, width=60, layout='split').lines
    unified = render_diff_styled_doc(patch, width=60, layout='unified').lines

    # Summary, file header, hunk header - and after the body, the closing rule and trailer.
    assert split[:5] == unified[:5]
    assert split[-2:] == unified[-2:]


def test_diffs_package_exports_the_layouts():
    assert diffs.render_diff_styled_doc is render_diff_styled_doc
    assert diffs.SplitDiffHunkLayout is SplitDiffHunkLayout
    assert diffs.UnifiedDiffHunkLayout is UnifiedDiffHunkLayout
    assert tuple(diffs.DIFF_LAYOUTS) == ('auto', 'split', 'unified')
