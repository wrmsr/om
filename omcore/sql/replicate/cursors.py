import uuid

from ... import dataclasses as dc
from ... import lang
from ..api.core import Conn
from .backends.base import CursorRow
from .names import LOG_TABLE_NAME
from .nodes import Node


##


@dc.dataclass(frozen=True, kw_only=True)
class CursorState(lang.Final):
    position: uuid.UUID | None = None  # the last key applied, or nothing between sweeps
    sweeps: int = 0  # completed sweeps of the table


class CursorStore(lang.Final):
    """
    A link's positions, kept on whichever node the link says holds them: a sweep position per table, and the log tail's
    sequence number under the log table's own reserved name.
    """

    def __init__(self, node: Node) -> None:
        super().__init__()

        self._node = node

    def read(self, link: str, table: str, *, conn: Conn | None = None) -> CursorState:
        with self._node.connected(conn) as node_conn:
            row = self._node.backend.read_cursor(node_conn, self._node.cursor_table, link, table)
        if row is None:
            return CursorState()
        return CursorState(
            position=uuid.UUID(row.position) if row.position is not None else None,
            sweeps=row.sweeps,
        )

    def write(self, link: str, table: str, state: CursorState, *, conn: Conn | None = None) -> None:
        with self._node.connected(conn) as node_conn:
            self._node.backend.write_cursor(
                node_conn,
                self._node.cursor_table,
                link,
                table,
                CursorRow(str(state.position) if state.position is not None else None, state.sweeps),
            )

    #

    def read_log(self, link: str, *, conn: Conn | None = None) -> int:
        """The last log sequence number the link has examined; zero before any."""

        with self._node.connected(conn) as node_conn:
            row = self._node.backend.read_cursor(node_conn, self._node.cursor_table, link, LOG_TABLE_NAME)
        if row is None or row.position is None:
            return 0
        return int(row.position)

    def write_log(self, link: str, seq: int, *, conn: Conn | None = None) -> None:
        with self._node.connected(conn) as node_conn:
            self._node.backend.write_cursor(
                node_conn,
                self._node.cursor_table,
                link,
                LOG_TABLE_NAME,
                CursorRow(str(seq), 0),
            )
