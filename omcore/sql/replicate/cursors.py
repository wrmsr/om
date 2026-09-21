import typing as ta
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

    A position has the one writer - the link whose it is - so what was last read or written here is what is there, and
    is not read again: looking at a log which has nothing new in it then costs nothing at the node the positions are
    kept on, which is usually the far one. A connection is taken as something to call for one, and is called only if it
    comes to that. Should a step fail `forget` is to be called, as what did and did not get written is then unknown.
    """

    def __init__(self, node: Node) -> None:
        super().__init__()

        self._node = node

        self._rows: dict[tuple[str, str], CursorRow | None] = {}

    def forget(self) -> None:
        self._rows.clear()

    def _read(self, link: str, table: str, conn: ta.Callable[[], Conn] | None) -> CursorRow | None:
        try:
            return self._rows[(link, table)]
        except KeyError:
            pass

        with self._node.connected(conn() if conn is not None else None) as node_conn:
            row = self._node.backend.read_cursor(node_conn, self._node.cursor_table, link, table)

        self._rows[(link, table)] = row
        return row

    def _write(self, link: str, table: str, row: CursorRow, conn: ta.Callable[[], Conn] | None) -> None:
        if self._rows.get((link, table)) == row:
            return

        self._rows.pop((link, table), None)
        with self._node.connected(conn() if conn is not None else None) as node_conn:
            self._node.backend.write_cursor(node_conn, self._node.cursor_table, link, table, row)
        self._rows[(link, table)] = row

    #

    def read(self, link: str, table: str, *, conn: ta.Callable[[], Conn] | None = None) -> CursorState:
        if (row := self._read(link, table, conn)) is None:
            return CursorState()
        return CursorState(
            position=uuid.UUID(row.position) if row.position is not None else None,
            sweeps=row.sweeps,
        )

    def write(
            self,
            link: str,
            table: str,
            state: CursorState,
            *,
            conn: ta.Callable[[], Conn] | None = None,
    ) -> None:
        self._write(
            link,
            table,
            CursorRow(str(state.position) if state.position is not None else None, state.sweeps),
            conn,
        )

    #

    def read_log(self, link: str, *, conn: ta.Callable[[], Conn] | None = None) -> int:
        """The last log sequence number the link has examined; zero before any."""

        if (row := self._read(link, LOG_TABLE_NAME, conn)) is None or row.position is None:
            return 0
        return int(row.position)

    def write_log(self, link: str, seq: int, *, conn: ta.Callable[[], Conn] | None = None) -> None:
        self._write(link, LOG_TABLE_NAME, CursorRow(str(seq), 0), conn)
