import typing as ta

from ... import dataclasses as dc
from ... import lang
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


def apply_rows(target: Node, td: TableDef, rows: ta.Sequence[SourceRow]) -> ApplyReport:
    """
    Brings the target up to the source for a batch, by comparison rather than by trust: a row ships only when the target
    lacks it or holds a lower version, so applying a batch twice is a no-op. A target ahead of the source, or a
    different origin on the same key, is a broken invariant and halts the link. One transaction per batch.
    """

    if not rows:
        return ApplyReport()

    backend = target.backend
    table = target.table_name(td)
    shadow = target.shadow_name(td)

    applied = deleted = skipped = 0

    with target.db.connect() as conn:
        with conn.begin() as txn:
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

                if row.deleted:
                    backend.delete_row(txn, td, table, row.key)
                    deleted += 1
                else:
                    backend.upsert_row(txn, td, table, row.values or {})
                    applied += 1

                # The target's own trigger just stamped the row as locally authored; this puts the truth back.
                backend.upsert_shadow(txn, shadow, row.key, row.state)

    return ApplyReport(
        applied=applied,
        deleted=deleted,
        skipped=skipped,
    )
