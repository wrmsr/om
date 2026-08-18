"""
The tree-sitter incremental highlighter - the 'big boy' the highlighting architecture was carved out for.

Strictly quarantined optional dependency (`tree-sitter` plus per-language `tree_sitter_<name>` grammar packages,
probed without importing). Document range edits translate directly onto `Tree.edit()` - `TextEdit` was shaped for
exactly this - so a keystroke costs an incremental reparse of the damaged region instead of a full pass. The
highlighter tracks its own copy of the source: if the fed edits ever mismatch reality (missed edit, external change),
`highlight()` detects it and silently falls back to a full parse - incrementality is an optimization, never a
correctness dependency.

Capture names from each grammar's bundled highlights query map onto the same `code.*` tags the zero-dep highlighters
emit, so themes are shared.
"""
import functools
import importlib
import importlib.util
import typing as ta

from omcore import lang

from ..text.highlights import SegmentRows
from ..text.segments import Segment
from .edits import TextEdit
from .highlighting import IncrementalHighlighter


with lang.auto_proxy_import(globals()):
    import tree_sitter


##


@functools.cache
def tree_sitter_available() -> bool:
    return importlib.util.find_spec('tree_sitter') is not None


# Full capture name (or its pre-dot base) -> tag. Applied in this order; later assignments win per character.
_CAPTURE_TAGS: ta.Sequence[tuple[str, str]] = (
    ('type', 'code.type'),
    ('constructor', 'code.def'),
    ('constant', 'code.number'),
    ('constant.builtin', 'code.builtin'),
    ('function', 'code.def'),
    ('function.builtin', 'code.builtin'),
    ('attribute', 'code.decorator'),
    ('decorator', 'code.decorator'),
    ('number', 'code.number'),
    ('keyword', 'code.keyword'),
    ('string', 'code.string'),
    ('escape', 'code.string'),
    ('comment', 'code.comment'),
)

_CAPTURE_ORDER: ta.Mapping[str, int] = {name: i for i, (name, _) in enumerate(_CAPTURE_TAGS)}
_CAPTURE_TAG_MAP: ta.Mapping[str, str] = dict(_CAPTURE_TAGS)


def _capture_tag(name: str) -> tuple[int, str] | None:
    """(application order, tag) for a capture name, trying the full name then its pre-dot base."""

    for key in (name, name.split('.', maxsplit=1)[0]):
        if (tag := _CAPTURE_TAG_MAP.get(key)) is not None:
            return (_CAPTURE_ORDER[key], tag)
    return None


def _byte_col(line: str, col: int) -> int:
    return len(line[:col].encode('utf-8'))


def _char_col(line_bytes: bytes, byte_col: int) -> int:
    return len(line_bytes[:byte_col].decode('utf-8', 'replace'))


class TreeSitterHighlighter(IncrementalHighlighter):
    def __init__(self, language: ta.Any, highlights_query: str) -> None:
        super().__init__()

        self._language = tree_sitter.Language(language)
        self._parser = tree_sitter.Parser(self._language)
        self._query = tree_sitter.Query(self._language, highlights_query)

        self._lines: list[str] | None = None  # the source the current tree corresponds to
        self._tree: ta.Any = None

        self._full_parses = 0
        self._incremental_parses = 0

    @property
    def parse_counts(self) -> tuple[int, int]:
        """(full, incremental) - observability for tests and tuning."""

        return (self._full_parses, self._incremental_parses)

    ##
    # Incremental feed

    def note_edit(self, edit: TextEdit) -> None:
        if self._tree is None or self._lines is None:
            return

        lines = self._lines
        if not (edit.start.row < len(lines) and edit.end.row < len(lines)):
            # The edit doesn't fit the source we think we have; drop incremental state.
            self._tree = None
            self._lines = None
            return

        def to_byte(row: int, byte_col_in_row: int) -> int:
            return sum(len(line.encode('utf-8')) + 1 for line in lines[:row]) + byte_col_in_row

        start_bcol = _byte_col(lines[edit.start.row], edit.start.col)
        old_end_bcol = _byte_col(lines[edit.end.row], edit.end.col)
        start_byte = to_byte(edit.start.row, start_bcol)
        old_end_byte = to_byte(edit.end.row, old_end_bcol)

        text_bytes = edit.text.encode('utf-8')
        new_end = edit.new_end
        text_lines = edit.text.split('\n')
        if len(text_lines) == 1:
            new_end_bcol = start_bcol + len(text_bytes)
        else:
            new_end_bcol = len(text_lines[-1].encode('utf-8'))

        self._tree.edit(
            start_byte=start_byte,
            old_end_byte=old_end_byte,
            new_end_byte=start_byte + len(text_bytes),
            start_point=(edit.start.row, start_bcol),
            old_end_point=(edit.end.row, old_end_bcol),
            new_end_point=(new_end.row, new_end_bcol),
        )

        # Mirror the edit onto our tracked source, exactly as Document.replace does.
        prefix = lines[edit.start.row][: edit.start.col]
        suffix = lines[edit.end.row][edit.end.col:]
        lines[edit.start.row: edit.end.row + 1] = (prefix + edit.text + suffix).split('\n')

    ##
    # Highlighting

    def highlight(self, lines: ta.Sequence[str]) -> SegmentRows:
        line_list = list(lines)
        source = '\n'.join(line_list).encode('utf-8') + b'\n'

        if self._tree is not None and self._lines == line_list:
            tree = self._parser.parse(source, self._tree)
            self._incremental_parses += 1
        else:
            tree = self._parser.parse(source)
            self._full_parses += 1

        self._tree = tree
        self._lines = line_list

        line_bytes = [line.encode('utf-8') for line in line_list]

        # Per-character tag arrays; later application order wins.
        tags: list[list[tuple[int, str] | None]] = [[None] * len(line) for line in line_list]

        captures = tree_sitter.QueryCursor(self._query).captures(tree.root_node)
        for name, nodes in captures.items():
            if (order_tag := _capture_tag(name)) is None:
                continue
            order, tag = order_tag
            for node in nodes:
                srow, sbcol = node.start_point
                erow, ebcol = node.end_point
                for row in range(srow, min(erow + 1, len(line_list))):
                    a = _char_col(line_bytes[row], sbcol) if row == srow else 0
                    b = _char_col(line_bytes[row], ebcol) if row == erow else len(line_list[row])
                    row_tags = tags[row]
                    for col in range(a, min(b, len(row_tags))):
                        prev = row_tags[col]
                        if prev is None or prev[0] <= order:
                            row_tags[col] = (order, tag)

        rows: list[list[Segment]] = []
        for line, row_tags in zip(line_list, tags):
            segments: list[Segment] = []
            text = ''
            current: str | None = None
            for c, entry in zip(line, row_tags):
                char_tag = entry[1] if entry is not None else None
                if text and char_tag != current:
                    segments.append(Segment(text, current))
                    text = ''
                current = char_tag
                text += c
            if text:
                segments.append(Segment(text, current))
            rows.append(segments)
        return rows


##


# Grammar-package aliases: file extensions / info strings -> tree_sitter_<name> module suffixes.
_LANGUAGE_ALIASES: ta.Mapping[str, str] = {
    'py': 'python',
    'python': 'python',
    'python3': 'python',
    'rs': 'rust',
    'rust': 'rust',
    'go': 'go',
    'js': 'javascript',
    'javascript': 'javascript',
    'ts': 'typescript',
    'typescript': 'typescript',
    'c': 'c',
    'cc': 'cpp',
    'cpp': 'cpp',
    'json': 'json',
    'sh': 'bash',
    'bash': 'bash',
}


def get_tree_sitter_highlighter(name: str) -> TreeSitterHighlighter | None:
    """
    A fresh TreeSitterHighlighter for the language/extension `name`, or None (tree-sitter or grammar pack missing).

    Instances carry incremental state, so each consuming document gets its own (module imports are cached by Python;
    per-instance query construction is cheap at editor-open frequency).
    """

    if not tree_sitter_available():
        return None
    if (suffix := _LANGUAGE_ALIASES.get(name.strip().lower())) is None:
        return None
    module_name = f'tree_sitter_{suffix}'
    if importlib.util.find_spec(module_name) is None:
        return None
    module = importlib.import_module(module_name)
    if not hasattr(module, 'HIGHLIGHTS_QUERY'):
        return None
    return TreeSitterHighlighter(module.language(), module.HIGHLIGHTS_QUERY)
