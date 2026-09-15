import uuid

from ... import dataclasses as dc
from ... import lang
from .backends.base import CursorRow
from .nodes import Node


##


@dc.dataclass(frozen=True, kw_only=True)
class CursorState(lang.Final):
    position: uuid.UUID | None = None  # the last key applied, or nothing between sweeps
    sweeps: int = 0  # completed sweeps of the table


class CursorStore(lang.Final):
    """A link's sweep positions, kept on whichever node the link says holds them."""

    def __init__(self, node: Node) -> None:
        super().__init__()

        self._node = node

    def read(self, link: str, table: str) -> CursorState:
        with self._node.db.connect() as conn:
            row = self._node.backend.read_cursor(conn, self._node.cursor_table, link, table)
        if row is None:
            return CursorState()
        return CursorState(position=row.position, sweeps=row.sweeps)

    def write(self, link: str, table: str, state: CursorState) -> None:
        with self._node.db.connect() as conn:
            self._node.backend.write_cursor(
                conn,
                self._node.cursor_table,
                link,
                table,
                CursorRow(state.position, state.sweeps),
            )
