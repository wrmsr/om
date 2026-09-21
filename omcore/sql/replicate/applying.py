import typing as ta

from ... import dataclasses as dc
from ... import lang
from ..api.core import Conn
from ..tabledefs.tabledefs import TableDef
from .errors import ReplicationConflictError
from .nodes import Node
from .rows import SourceRow


##


@dc.dataclass(frozen=True, kw_only=True)
class ApplyReport(lang.Final):
    applied: int = 0
    deleted: int = 0
    skipped: int = 0


def apply_rows(
        target: Node,
        td: TableDef,
        rows: ta.Sequence[SourceRow],
        *,
        conn: Conn | None = None,
) -> ApplyReport:
    """
    Brings the target up to the source for a batch, by comparison rather than by trust: a row ships only when the target
    lacks it or holds a lower version, so applying a batch twice is a no-op. A target ahead of the source, or a
    different origin on the same key, is a broken invariant and halts the link. One transaction per batch, and a
    statement per kind of write in it rather than per row. No two of the rows may share a key.
    """

    if not rows:
        return ApplyReport()

    backend = target.backend
    table = target.table_name(td)
    shadow = target.shadow_name(td)

    ship: list[SourceRow] = []
    skipped = 0

    with target.connected(conn) as target_conn:
        with target_conn.begin() as txn:
            states = backend.fetch_shadow_states(txn, shadow, [r.key for r in rows])

            for row in rows:
                if (st := states.get(row.key)) is not None:
                    if st.origin != row.origin:
                        raise ReplicationConflictError(
                            f'{td.name.last}[{row.key}] '
                            f'on {target!r} '
                            f'has origin {st.origin} '
                            f'but the source says {row.origin}',
                        )
                    if st.version > row.version:
                        raise ReplicationConflictError(
                            f'{td.name.last}[{row.key}] '
                            f'on {target!r} '
                            f'is at version {st.version}, '
                            f'ahead of the source at {row.version}',
                        )
                    if st.version == row.version:
                        skipped += 1
                        continue

                ship.append(row)

            # The deletes go first, so that whatever a deleted row held uniquely is free for a row which now has it.
            deletes = [r for r in ship if r.deleted]
            upserts = [r for r in ship if not r.deleted]
            backend.delete_rows(txn, td, table, [r.key for r in deletes])
            backend.upsert_rows(txn, td, table, [r.values or {} for r in upserts])

            # And the shadows last: the target's own triggers have by now stamped every row written as locally
            # authored, and this puts the truth back.
            backend.upsert_shadows(txn, shadow, {r.key: r.state for r in ship})

    return ApplyReport(
        applied=len(upserts),
        deleted=len(deletes),
        skipped=skipped,
    )
