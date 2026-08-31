"""
The incremental extension of the text-layer Highlighter protocol.

Lives in docs/ (not text/) because it speaks `TextEdit` - the document layer's range-edit currency. Consumers that hold
an `IncrementalHighlighter` feed it every applied edit; implementations use that to avoid full reparses. A plain
`Highlighter` remains the universal fallback - anything accepting an IncrementalHighlighter must work identically (just
slower) with a non-incremental one.
"""
import abc

from omcore import lang

from ..text.highlights.base import Highlighter
from .edits import TextEdit


##


class IncrementalHighlighter(Highlighter, lang.Abstract):
    @abc.abstractmethod
    def note_edit(self, edit: TextEdit) -> None:
        """
        Inform the highlighter of a document edit (in document order, every edit - undo inverses included).

        The next `highlight()` call may then reuse incremental state. Implementations must stay correct when edits are
        missed (they detect source mismatch and fall back to a full pass).
        """

        raise NotImplementedError
