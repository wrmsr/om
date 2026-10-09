import difflib
import os.path

import pytest

from .... import styled as st
from ....styled import grid
from ...newlines import split_newlines
from ...parsing import parse_patch
from ..options import DiffContextLimits
from ..options import DiffStyledDocOptions
from ..rendering import DiffStyledDocRenderer
from ..rendering import render_diff_styled_doc
from ..sources import DictDiffFileSource
from ..sources import DiffFileSource
from ..sources import DiffFileTexts
from ..sources import FilesystemDiffFileSource
from ..sources import texts_match_hunks


##


def _patch(old, new, path='f.py'):
    return parse_patch(''.join(difflib.unified_diff(
        split_newlines(old, keepends=True),
        split_newlines(new, keepends=True),
        fromfile=f'a/{path}',
        tofile=f'b/{path}',
    )))


def _write(path, data):
    with open(path, 'wb') as f:
        f.write(data)


# A change deep inside a docstring: three lines of context either side keep the hunk clear of its opening quotes.
_DOC_OLD = '\n'.join([
    'def f():',
    '    """',
    *[f'    line {i}' for i in range(10)],
    '    """',
    '    return 1',
    '',
])
_DOC_NEW = _DOC_OLD.replace('line 6', 'LINE 6')


def _changed_row_is_string(document):
    row = next(line for line in document.lines if 'LINE 6' in line.text)
    return st.StyleName('code.string') in row.style_at(row.text.index('LINE 6'))


def _render(patch, file_source=None):
    return render_diff_styled_doc(patch, file_source, width=80, layout='unified')


##


def test_texts_match_hunks_only_where_the_patch_puts_them():
    [patch] = _patch('a\nb\nc\n', 'a\nB\nc\n').files

    assert texts_match_hunks(patch, ['a', 'B', 'c'], side='target')
    assert texts_match_hunks(patch, ['a', 'b', 'c'], side='source')

    assert not texts_match_hunks(patch, ['a', 'b', 'c'], side='target')
    assert not texts_match_hunks(patch, ['inserted', 'a', 'B', 'c'], side='target')
    assert not texts_match_hunks(patch, ['a', 'B'], side='target')


def test_full_texts_highlight_a_hunk_with_the_code_around_it():
    patch = _patch(_DOC_OLD, _DOC_NEW)
    file_source = DictDiffFileSource({
        'f.py': DiffFileTexts(source=split_newlines(_DOC_OLD), target=split_newlines(_DOC_NEW)),
    })

    assert _changed_row_is_string(_render(patch, file_source))

    # Alone, the hunk has no way to know it is inside a string.
    assert not _changed_row_is_string(_render(patch))


def test_a_file_on_disk_is_used_when_it_is_the_patch_target(tmp_path):
    root = str(tmp_path)
    _write(os.path.join(root, 'f.py'), _DOC_NEW.encode())

    # Its source is rebuilt from it and the hunks.
    assert _changed_row_is_string(_render(_patch(_DOC_OLD, _DOC_NEW), FilesystemDiffFileSource(root)))


def test_a_file_on_disk_changed_since_the_patch_is_not_trusted(tmp_path):
    root = str(tmp_path)
    patch = _patch(_DOC_OLD, _DOC_NEW)

    # As with the cli's default root and an old commit: the file has moved on, here by a line inserted above the hunk.
    _write(os.path.join(root, 'f.py'), ('# new first line\n' + _DOC_NEW).encode())

    drifted = _render(patch, FilesystemDiffFileSource(root))
    assert drifted == _render(patch)


def test_a_given_source_text_must_match_too():
    patch = _patch(_DOC_OLD, _DOC_NEW)
    file_source = DictDiffFileSource({
        'f.py': DiffFileTexts(source=split_newlines(_DOC_NEW), target=split_newlines(_DOC_NEW)),
    })

    assert _render(patch, file_source) == _render(patch)


def test_dict_source_finds_a_file_by_new_path_then_old():
    texts = DiffFileTexts(target=['x'])
    file_source = DictDiffFileSource({'kept.py': texts, 'gone.py': texts})

    [modified] = _patch('a\n', 'b\n', 'kept.py').files
    [deleted] = parse_patch("""\
diff --git a/gone.py b/gone.py
deleted file mode 100644
--- a/gone.py
+++ /dev/null
@@ -1 +0,0 @@
-x
""").files
    [other] = _patch('a\n', 'b\n', 'other.py').files

    assert file_source.get_texts(modified) is texts
    assert file_source.get_texts(deleted) is texts
    assert file_source.get_texts(other) is None
    assert file_source.get_target_size(modified) is None


def test_filesystem_source_reads_lines_as_the_patch_has_them(tmp_path):
    root = str(tmp_path)
    _write(os.path.join(root, 'f.py'), b'a\r\nb\x0cc\rd\n')
    _write(os.path.join(root, 'bin.py'), b'\xff\xfe\n')
    file_source = FilesystemDiffFileSource(root)

    # Only newlines end lines, and a line's carriage return ending goes with it.
    [patch] = _patch('x\n', 'y\n').files
    assert file_source.get_texts(patch) == DiffFileTexts(target=['a', 'b\x0cc\rd'])
    assert file_source.get_target_size(patch) == 9

    [undecodable] = _patch('x\n', 'y\n', 'bin.py').files
    [missing] = _patch('x\n', 'y\n', 'missing.py').files
    assert file_source.get_texts(undecodable) is None
    assert file_source.get_texts(missing) is None
    assert file_source.get_target_size(missing) is None


def test_a_binary_file_size_comes_from_the_source(tmp_path):
    root = str(tmp_path)
    _write(os.path.join(root, 'image.png'), b'12345')
    patch = parse_patch("""\
diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
""")

    assert 'File is binary · 5 bytes' in render_diff_styled_doc(patch, FilesystemDiffFileSource(root), width=60).plain


def test_control_characters_in_code_are_shown_not_passed_through():
    patch = _patch('say \x1b[31mred\n', 'say \x1b[32mgreen\n', 'esc.txt')

    for layout in ('split', 'unified'):
        document = render_diff_styled_doc(patch, width=60, layout=layout)
        assert '\x1b' not in document.plain
        assert '␛[31mred' in document.plain
        assert all(grid.cell_width(line) == 60 for line in document.lines if line)


##


def test_context_limits_count_lines_and_utf8_bytes():
    limits = DiffContextLimits(max_lines=2, max_bytes=8)

    assert limits.admits(['ab', 'cd'])
    assert not limits.admits(['a', 'b', 'c'])
    assert not limits.admits(['abcd', 'efgh'])

    # Counted as the file's bytes, not its characters: four two-byte characters and a newline.
    assert not limits.admits(['\u00e9' * 4])

    assert limits.admits_size(8)
    assert not limits.admits_size(9)

    assert DiffContextLimits(max_lines=None, max_bytes=None).admits(['x'] * 100_000)

    with pytest.raises(Exception):  # noqa
        DiffContextLimits(max_lines=-1)


class _SizedDiffFileSource(DiffFileSource):
    """Knows a file's size without reading it - and notes whether it was read all the same."""

    def __init__(self, size, texts):
        super().__init__()

        self._size = size
        self._texts = texts

        self.read = False

    def get_texts(self, patch):
        self.read = True
        return self._texts

    def get_target_size(self, patch):
        return self._size


def test_a_file_over_the_context_limits_is_highlighted_by_its_hunks_alone():
    patch = _patch(_DOC_OLD, _DOC_NEW)
    texts = DiffFileTexts(source=split_newlines(_DOC_OLD), target=split_newlines(_DOC_NEW))

    def render(file_source, **limits):
        options = DiffStyledDocOptions(width=80, layout='unified', context_limits=DiffContextLimits(**limits))
        return DiffStyledDocRenderer(options, file_source=file_source).render(patch)

    in_hand = DictDiffFileSource({'f.py': texts})
    assert _changed_row_is_string(render(in_hand))
    assert not _changed_row_is_string(render(in_hand, max_lines=10))
    assert not _changed_row_is_string(render(in_hand, max_bytes=100))

    # Where the source knows the size up front, a file over the limit is never read at all.
    sized = _SizedDiffFileSource(10_000, texts)
    assert not _changed_row_is_string(render(sized, max_bytes=1_000))
    assert not sized.read

    assert _changed_row_is_string(render(sized, max_bytes=None))
    assert sized.read
