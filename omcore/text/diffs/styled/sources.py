"""
Where a document gets the full texts of the files a patch changes. A patch carries only its hunks, and a hunk on its own
can be highlighted wrongly - one starting inside a docstring, say - so a document draws on the whole files when a
source can supply them.

Nothing a source supplies is taken on trust: the full texts may be of some other version than the patch was made from -
a file on disk edited since, a different revision - and are only used where every hunk's lines are where the patch says.
"""
import abc
import os.path
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ... import diffs
from ..newlines import split_newlines


##


@dc.dataclass(frozen=True, kw_only=True)
class DiffFileTexts(lang.Final):
    """
    A file's full text on each side of a patch, as lines without their line endings - None where it is not known. Split
    them with `split_newlines`, at newlines only, or they will not line up with the patch's lines.
    """

    source: ta.Sequence[str] | None = None
    target: ta.Sequence[str] | None = None


class DiffFileSource(lang.Abstract):
    """Supplies facts about the files a patch changes that the patch itself does not carry."""

    @abc.abstractmethod
    def get_texts(self, patch: diffs.FilePatch) -> DiffFileTexts | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_target_size(self, patch: diffs.FilePatch) -> int | None:
        """The size in bytes of the file as the patch leaves it, as shown for a binary file."""

        raise NotImplementedError


##


def texts_match_hunks(
        patch: diffs.FilePatch,
        lines: ta.Sequence[str],
        *,
        side: ta.Literal['source', 'target'],
) -> bool:
    """Whether a full text has every hunk's lines for its side exactly where the patch puts them."""

    excluded = diffs.HunkLineKind.ADD if side == 'source' else diffs.HunkLineKind.REMOVE

    for hunk in patch.hunks:
        start, count = (hunk.old_start, hunk.old_count) if side == 'source' else (hunk.new_start, hunk.new_count)
        begin = max(start - 1, 0)

        expected = [line.text for line in hunk.lines if line.kind is not excluded]
        if list(lines[begin:begin + count]) != expected:
            return False

    return True


##


class DictDiffFileSource(DiffFileSource):
    """Texts already in hand - kept by the path a patch gives its file, its new path or else its old one."""

    def __init__(self, texts: ta.Mapping[str, DiffFileTexts]) -> None:
        super().__init__()

        self._texts = texts

    def get_texts(self, patch: diffs.FilePatch) -> DiffFileTexts | None:
        if (path := patch.new_path or patch.old_path) is None:
            return None
        return self._texts.get(path)

    def get_target_size(self, patch: diffs.FilePatch) -> int | None:
        return None


class FilesystemDiffFileSource(DiffFileSource):
    """
    Files under a root directory, taken as the patch's target - so only right for a patch of what is there now, like the
    working tree's own diff. Its source text is left for the document to rebuild from the target and the hunks.
    """

    def __init__(self, root: str) -> None:
        super().__init__()

        self._root = root

    def _target_path(self, patch: diffs.FilePatch) -> str | None:
        if (path := patch.new_path) is None:
            return None
        return os.path.join(self._root, path)

    def get_texts(self, patch: diffs.FilePatch) -> DiffFileTexts | None:
        if (path := self._target_path(patch)) is None:
            return None

        # Read without newline translation, which would break lines at lone carriage returns a patch keeps within them.
        try:
            with open(path, encoding='utf-8', newline='') as f:
                text = f.read()
        except (OSError, UnicodeError):
            return None

        return DiffFileTexts(target=split_newlines(text))

    def get_target_size(self, patch: diffs.FilePatch) -> int | None:
        if (path := self._target_path(patch)) is None:
            return None

        try:
            return os.stat(path).st_size
        except OSError:
            return None
