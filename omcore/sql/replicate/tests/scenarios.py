"""The behaviors every dialect and every dialect pair must exhibit, written once against nodes. Not a test module."""
import datetime
import itertools
import typing as ta
import uuid

import pytest

from .... import check
from .... import dataclasses as dc
from ...api import querierfuncs as qf
from ...tabledefs.diffing import AddTrigger
from ...tabledefs.diffing import DropTrigger
from ...tabledefs.elements import Column
from ..config import CursorSide
from ..config import LinkSpec
from ..config import OriginFilter
from ..config import ReplicationSchema
from ..errors import ReplicationConflictError
from ..install import install_node
from ..links import Link
from ..links import LinkSyncReport
from ..links import sync_link_once
from ..links import sync_link_sweep
from ..links import sync_link_tail
from ..maintenance import prune_log
from ..nodes import Node
from ..rows import ShadowState
from ..triggers import CAPTURE_TRIGGER_VERSION
from ..workers import TailPacing
from ..workers import Worker
from .nodes import FailingDb
from .nodes import InjectedFaultError
from .nodes import delete_row
from .nodes import insert_row
from .nodes import read_rows
from .nodes import read_shadow
from .nodes import update_row


##


def _business(name: str) -> dict[str, ta.Any]:
    return {
        'id': uuid.uuid7(),
        'name': name,
    }


def _sink(**kw: ta.Any) -> dict[str, ta.Any]:
    return {
        'id': uuid.uuid7(),
        'i': None,
        's': None,
        'd': None,
        'u': None,
        'b': None,
        'f': None,
        'y': None,
        **kw,
    }


##


def check_install(node: Node, schema: ReplicationSchema) -> None:
    r1 = install_node(node, schema)
    assert r1.created_node
    assert node.node_id == r1.node_id

    # idempotent: nothing is created or migrated the second time, and the identity holds
    r2 = install_node(node, schema)
    assert not r2.created_node
    assert r2.node_id == r1.node_id
    assert all(not m.created and not m.ops for m in r2.migrations)

    # a trigger body version bump is a drop and an add of every capture trigger, and capture keeps working after
    r3 = install_node(node, schema, capture_trigger_version=CAPTURE_TRIGGER_VERSION + 1)
    ops = [o for m in r3.migrations for o in m.ops]
    assert len([o for o in ops if isinstance(o, AddTrigger)]) == 3 * len(schema.tables)
    assert len([o for o in ops if isinstance(o, DropTrigger)]) == 3 * len(schema.tables)
    td = schema.table('businesses')
    row = _business('after bump')
    insert_row(node, td, row)
    assert read_shadow(node, td)[row['id']].version == 1

    # and back down, since the other scenarios assume the default version
    install_node(node, schema)

    # triggers only, on a table that exists: nothing but trigger ops, and none once they are current
    r4 = install_node(node, schema, no_manage_base_tables=True)
    assert all(not m.ops for m in r4.migrations)


def check_install_triggers_only(node: Node, schema: ReplicationSchema) -> None:
    """
    Tables which are already there, and not ours to manage, get their triggers and nothing else - and then capture.
    """

    r = node.backend.tabledef_renderer
    with node.db.connect() as conn:
        for td in schema.tables:
            for stmt in r.render_create_statements(dc.replace(td, name=node.table_name(td))):
                qf.exec(conn, stmt)

    td = schema.table('businesses')
    before = _business('before')
    insert_row(node, td, before)

    install_node(node, schema, no_manage_base_tables=True)

    # the row which predates the triggers is backfilled, and one which follows them is captured
    after = _business('after')
    insert_row(node, td, after)
    sh = read_shadow(node, td)
    assert sh[before['id']].state == ShadowState(version=1, origin=node.node_id, deleted=False)
    assert sh[after['id']].state == ShadowState(version=1, origin=node.node_id, deleted=False)

    update_row(node, td, after['id'], {'name': 'after again'})
    assert read_shadow(node, td)[after['id']].version == 2


def check_capture_with_kept_columns(node: Node, schema: ReplicationSchema) -> None:
    """
    A change to a row whose table keeps an updated-at of its own is one change: a version, and an entry in the log.
    """

    install_node(node, schema)
    td = schema.table('notes')
    long_ago = datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC)
    k = uuid.uuid7()
    note: dict[str, ta.Any] = {'id': k, 'text': 'a', 'created_at': long_ago, 'updated_at': long_ago}

    def num_log_entries() -> int:
        with node.db.connect() as conn:
            return len([e for e in node.backend.read_log(conn, node.log_table, after=0, limit=100) if e.key == k])

    insert_row(node, td, note)
    assert read_shadow(node, td)[k].version == 1 and num_log_entries() == 1

    # the table's own trigger has its say - on sqlite, by an update of its own after the one made - and that is no
    # second change
    update_row(node, td, k, {'text': 'b'})
    assert read_rows(node, td)[k]['updated_at'] > long_ago
    assert read_shadow(node, td)[k].version == 2 and num_log_entries() == 2

    # nor is it one fewer when every column is written, the kept one with them, as applying a replicated row does
    with node.db.connect() as conn:
        node.backend.upsert_rows(conn, td, node.table_name(td), [{**note, 'text': 'c', 'updated_at': long_ago}])
    assert read_rows(node, td)[k]['text'] == 'c'
    assert read_shadow(node, td)[k].version == 3 and num_log_entries() == 3


def check_capture(node: Node, schema: ReplicationSchema) -> None:
    install_node(node, schema)
    td = schema.table('businesses')
    nid = node.node_id

    row = _business('a')
    k = row['id']

    insert_row(node, td, row)
    assert read_shadow(node, td)[k].state == ShadowState(version=1, origin=nid, deleted=False)

    update_row(node, td, k, {'name': 'b'})
    assert read_shadow(node, td)[k].state == ShadowState(version=2, origin=nid, deleted=False)
    assert read_shadow(node, td)[k].values == {'id': k, 'name': 'b'}

    delete_row(node, td, k)
    s = read_shadow(node, td)[k]
    assert s.state == ShadowState(version=3, origin=nid, deleted=True)
    assert s.values is None

    # a key that comes back continues its version, so the resurrection can never look older than the tombstone
    insert_row(node, td, {**row, 'name': 'c'})
    assert read_shadow(node, td)[k].state == ShadowState(version=4, origin=nid, deleted=False)

    # every dtype survives its own dialect's round trip through the base table
    sink = schema.table('kitchen_sink')
    full = _sink(
        i=2 ** 40,
        s='héllo',
        d=datetime.datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=datetime.UTC),
        u=uuid.uuid7(),
        b=False,
        f=1.5,
        y=b'\x00\xff',
    )
    empty = _sink()
    insert_row(node, sink, full)
    insert_row(node, sink, empty)
    got = read_rows(node, sink)
    assert got[full['id']] == full
    assert got[empty['id']] == empty


##


def _link(name: str, schema: ReplicationSchema, source: Node, target: Node, **kw: ta.Any) -> Link:
    return Link(LinkSpec(name=name, source=source.name, target=target.name, **kw), schema, source, target)


def check_roundtrip(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    for n in (edge, hub):
        install_node(n, schema)

    biz = schema.table('businesses')
    sink = schema.table('kitchen_sink')

    rows = [_business(f'b{i}') for i in range(7)]
    for r in rows:
        insert_row(edge, biz, r)
    full = _sink(
        i=-5,
        s='ünïcode',
        d=datetime.datetime(2021, 6, 7, 8, 9, 10, 500000, tzinfo=datetime.UTC),
        u=uuid.uuid7(),
        b=True,
        f=2.25,
        y=b'\x01\x02',
    )
    empty = _sink()
    insert_row(edge, sink, full)
    insert_row(edge, sink, empty)

    # a small batch so a sweep takes several steps
    link = _link('up', schema, edge, hub, batch_size=3, cursor_side=CursorSide.TARGET)

    rep = sync_link_sweep(link)
    assert rep.completed
    assert read_rows(hub, biz) == {r['id']: r for r in rows}
    assert read_rows(hub, sink) == {full['id']: full, empty['id']: empty}

    # the hub's shadow carries the edge's identity and versions, not its own
    hs = read_shadow(hub, biz)
    assert all(s.origin == edge.node_id and s.version == 1 and not s.deleted for s in hs.values())

    # another sweep ships nothing: everything compares equal
    rep = sync_link_sweep(link)
    assert all(t.applied == 0 and t.deleted == 0 for t in rep.tables)
    [tb] = [t for t in rep.tables if t.table == 'businesses']
    assert tb.scanned == tb.skipped == len(rows)
    assert [t.sweeps for t in rep.tables] == [2] * len(rep.tables)

    # an update and a delete propagate, as an update and as a delete with a tombstone
    update_row(edge, biz, rows[0]['id'], {'name': 'renamed'})
    delete_row(edge, biz, rows[1]['id'])
    sync_link_sweep(link)
    got = read_rows(hub, biz)
    assert got[rows[0]['id']]['name'] == 'renamed'
    assert rows[1]['id'] not in got
    hs = read_shadow(hub, biz)
    assert hs[rows[0]['id']].state == ShadowState(version=2, origin=edge.node_id, deleted=False)
    assert hs[rows[1]['id']].state == ShadowState(version=2, origin=edge.node_id, deleted=True)

    # a clustered table goes like any other, whatever physical form either end has for it: inserted, updated in place
    # (where its key may be no more than a unique index to upsert against), and deleted
    cat = schema.table('business_categories')
    cats = [{'id': uuid.uuid7(), 'business_id': rows[2]['id'], 'tag': f't{i}'} for i in range(4)]
    for c in cats:
        insert_row(edge, cat, c)
    sync_link_sweep(link)
    assert read_rows(hub, cat) == {c['id']: c for c in cats}
    update_row(edge, cat, cats[0]['id'], {'tag': 'retagged'})
    delete_row(edge, cat, cats[1]['id'])
    sync_link_sweep(link)
    assert read_rows(hub, cat) == read_rows(edge, cat) == {
        cats[0]['id']: {**cats[0], 'tag': 'retagged'},
        **{c['id']: c for c in cats[2:]},
    }
    assert read_shadow(hub, cat)[cats[1]['id']].state == ShadowState(version=2, origin=edge.node_id, deleted=True)

    # the hub never bounces the edge's own rows back at it
    down = _link('down', schema, hub, edge, origins=OriginFilter.ALL_EXCEPT_TARGET, cursor_side=CursorSide.TARGET)
    rep = sync_link_sweep(down)
    assert rep.scanned == 0


def check_fault_between_apply_and_cursor(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """A crash after the batch is applied but before the cursor moves: the next pass finds nothing left to do."""

    hub_db = check.isinstance(hub.db, FailingDb)
    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    rows = [_business(f'f{i}') for i in range(4)]
    for r in rows:
        insert_row(edge, biz, r)

    link = _link('up', schema, edge, hub, batch_size=10, cursor_side=CursorSide.TARGET)

    hub_db.fail_when = lambda text: 'cursor' in text and text.lstrip().startswith(('insert', 'update'))
    with pytest.raises(InjectedFaultError):
        sync_link_once(link)

    # the rows landed, the cursor did not
    assert read_rows(hub, biz) == {r['id']: r for r in rows}
    assert link.cursors.read('up', 'businesses').sweeps == 0

    hub_db.fail_when = lambda _: False
    rep = sync_link_once(link)
    [t] = [t for t in rep.tables if t.table == 'businesses']
    assert t.scanned == len(rows) and t.applied == 0 and t.skipped == len(rows) and t.completed
    assert link.cursors.read('up', 'businesses').sweeps == 1


def check_step_costs(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """What a step costs is a connection to each node and a few statements to a batch - neither of them to a row."""

    edge_db = check.isinstance(edge.db, FailingDb)
    hub_db = check.isinstance(hub.db, FailingDb)
    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    link = _link('up', schema, edge, hub)

    def step() -> LinkSyncReport:
        for db in (edge_db, hub_db):
            db.reset_counts()
        rep = sync_link_once(link)
        assert edge_db.num_connects == hub_db.num_connects == 1
        assert not edge_db.writes
        return rep

    # with nothing to ship, all that is written is where each table's sweep stands
    step()
    assert len(hub_db.writes) == len(schema.tables)

    # however many rows ship, they are one upsert, their shadows another, and the tail's position a third
    for num_rows in (3, 40):
        rows = [_business(f'c{num_rows}.{i}') for i in range(num_rows)]
        for r in rows:
            insert_row(edge, biz, r)
        assert check.not_none(step().tail).applied == num_rows
        assert len(hub_db.writes) == len(schema.tables) + 3

    # as do deletes, which are one more
    for r in rows[:5]:
        delete_row(edge, biz, r['id'])
    update_row(edge, biz, rows[5]['id'], {'name': 'renamed'})
    rep = step()
    assert (check.not_none(rep.tail).applied, check.not_none(rep.tail).deleted) == (1, 5)
    assert len(hub_db.writes) == len(schema.tables) + 4

    assert read_rows(hub, biz) == read_rows(edge, biz)


def check_chunked_apply(edge: Node, hub: Node, schema: ReplicationSchema, *, max_statement_params: int) -> None:
    """A batch too big for one statement goes as several, and arrives the same. The hub's backend has the low limit."""

    hub_db = check.isinstance(hub.db, FailingDb)
    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    num_cols = len(biz.elements[Column])
    link = _link('up', schema, edge, hub)

    rows = [_business(f'k{i}') for i in range(23)]
    for r in rows:
        insert_row(edge, biz, r)

    hub_db.reset_counts()
    assert check.not_none(sync_link_once(link).tail).applied == len(rows)
    assert read_rows(hub, biz) == read_rows(edge, biz)
    assert len([s for s in hub_db.writes if 'businesses' in s]) == (
        -(-len(rows) // (max_statement_params // num_cols)) +  # the rows
        -(-len(rows) // (max_statement_params // 5))  # their shadows
    )

    for r in rows[:17]:
        delete_row(edge, biz, r['id'])
    hub_db.reset_counts()
    assert check.not_none(sync_link_once(link).tail).deleted == 17
    assert read_rows(hub, biz) == read_rows(edge, biz) and len(read_rows(hub, biz)) == 6
    assert len([s for s in hub_db.writes if s.lstrip().lower().startswith('delete')]) == -(-17 // max_statement_params)


def check_fanout(hub: Node, n: Node, m: Node, schema: ReplicationSchema) -> None:
    """Two edges through one hub: each sees the other's rows with origins intact, and never re-uploads them."""

    for x in (hub, n, m):
        install_node(x, schema)
    biz = schema.table('businesses')

    a = _business('from n')
    b = _business('from m')
    insert_row(n, biz, a)
    insert_row(m, biz, b)

    ups = [_link(f'{x.name}_up', schema, x, hub) for x in (n, m)]
    downs = [_link(f'{x.name}_down', schema, hub, x, origins=OriginFilter.ALL_EXCEPT_TARGET) for x in (n, m)]
    for link in [*ups, *downs]:
        sync_link_sweep(link)

    for x in (hub, n, m):
        assert read_rows(x, biz) == {a['id']: a, b['id']: b}
        sh = read_shadow(x, biz)
        assert sh[a['id']].origin == n.node_id and sh[b['id']].origin == m.node_id

    # n's upload sweeps only its own rows, so m's row is never sent back up
    rep = sync_link_sweep(ups[0])
    assert rep.scanned == 1

    # a violated writer rule is caught: the hub somehow holds n's row at a version n never wrote
    with hub.db.connect() as conn:
        hub.backend.upsert_shadows(conn, hub.shadow_name(biz), {a['id']: ShadowState(version=9, origin=n.node_id, deleted=False)})  # noqa
    with pytest.raises(ReplicationConflictError):
        sync_link_sweep(ups[0])


def check_worker(edge: Node, hub: Node, broken_hub: Node, schema: ReplicationSchema) -> None:
    """A failing link backs off and never blocks a healthy one."""

    broken_db = check.isinstance(broken_hub.db, FailingDb)
    for x in (edge, hub, broken_hub):
        install_node(x, schema)
    biz = schema.table('businesses')
    insert_row(edge, biz, _business('w'))

    good = _link('good', schema, edge, hub)
    bad = _link('bad', schema, edge, broken_hub)
    broken_db.fail_when = lambda text: text.lstrip().startswith('insert')

    now = [1000.]
    slept: list[float] = []
    w = Worker([good, bad], backoff_s=1., max_backoff_s=8., clock=lambda: now[0], sleeper=slept.append)

    r1 = w.run_once()
    assert [r.link for r in r1.synced] == ['good'] and r1.failed == ['bad'] and not r1.waiting

    # still inside the backoff window: the bad link waits, the good one runs
    now[0] += 1.
    r2 = w.run_once()
    assert [r.link for r in r2.synced] == ['good'] and r2.waiting == ['bad']

    # past it: retried, fails again, backs off longer
    now[0] += 2.
    r3 = w.run_once()
    assert r3.failed == ['bad'] and w.failures('bad') == 2

    # once healed it runs and its failure count resets
    broken_db.fail_when = lambda _: False
    now[0] += 100.
    r4 = w.run_once()
    assert sorted(r.link for r in r4.synced) == ['bad', 'good'] and w.failures('bad') == 0
    assert read_rows(broken_hub, biz) == read_rows(edge, biz)

    assert not slept


##


def check_log_tail(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """The tail alone keeps a target fresh, never re-examines an entry, and leaves the sweep with nothing to do."""

    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    sink = schema.table('kitchen_sink')

    rows = [_business(f't{i}') for i in range(5)]
    for r in rows:
        insert_row(edge, biz, r)
    extra = _sink(s='logged')
    insert_row(edge, sink, extra)

    # a link carrying only businesses: sink entries are examined and ignored, and the position moves past them too
    link = _link('up', schema, edge, hub, tables=['businesses'], tail_batch_size=3)

    t1 = check.not_none(sync_link_tail(link))
    assert (t1.entries, t1.keys, t1.applied, t1.drained) == (3, 3, 3, False)
    t2 = check.not_none(sync_link_tail(link))
    assert (t2.entries, t2.keys, t2.applied, t2.drained) == (3, 2, 2, False)
    t3 = check.not_none(sync_link_tail(link))
    assert (t3.entries, t3.applied, t3.drained) == (0, 0, True)
    assert read_rows(hub, biz) == {r['id']: r for r in rows}
    assert not read_rows(hub, sink)
    assert link.cursors.read_log('up') == t2.seq == 6

    # an update and a delete arrive through the tail alone, and a repeated key is looked up once
    update_row(edge, biz, rows[0]['id'], {'name': 'again'})
    update_row(edge, biz, rows[0]['id'], {'name': 'and again'})
    delete_row(edge, biz, rows[1]['id'])
    t4 = check.not_none(sync_link_tail(link))
    assert (t4.entries, t4.keys, t4.applied, t4.deleted) == (3, 2, 1, 1)
    got = read_rows(hub, biz)
    assert got[rows[0]['id']]['name'] == 'and again' and rows[1]['id'] not in got
    assert read_shadow(hub, biz)[rows[1]['id']].state == ShadowState(version=2, origin=edge.node_id, deleted=True)

    # the sweep then finds everything already there
    rep = sync_link_sweep(link)
    assert all(t.applied == 0 and t.deleted == 0 for t in rep.tables)

    # a full step tails first, so the sweep batch sees the tail's work
    insert_row(edge, biz, _business('stepped'))
    step = sync_link_once(link)
    assert check.not_none(step.tail).applied == 1
    assert all(t.applied == 0 for t in step.tables)

    # pruning: the log goes, and a sweep told to takes the tombstone with it - at both ends, the hub having been given
    # it first - while the live rows stay
    later = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)
    position = link.cursors.read_log('up')
    prune_log(edge, keep_s=0, now=later)
    with edge.db.connect() as conn:
        assert [e.seq for e in edge.backend.read_log(conn, edge.log_table, after=0, limit=10)] == [position]

    # all but the newest entry, that is, so that the next is numbered on from it - and not, as it would be from nothing
    # on some dialects, from the start, behind the link's place in the log and unseen by it
    after_prune = _business('after prune')
    insert_row(edge, biz, after_prune)
    t5 = check.not_none(sync_link_tail(link))
    assert (t5.entries, t5.applied) == (1, 1) and t5.seq == position + 1
    assert after_prune['id'] in read_rows(hub, biz)
    rows.append(after_prune)
    assert rows[1]['id'] in read_shadow(edge, biz) and rows[1]['id'] in read_shadow(hub, biz)
    sync_link_sweep(link, prune_tombstones_before=later)
    for n in (edge, hub):
        sh = read_shadow(n, biz)
        assert rows[1]['id'] not in sh and len(sh) == len(rows)  # four originals plus the stepped one


def check_no_log(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """A node that keeps no log still captures and sweeps; a link from it simply has no tail."""

    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    row = _business('quiet')
    insert_row(edge, biz, row)

    link = _link('up', schema, edge, hub)
    assert sync_link_tail(link) is None
    step = sync_link_once(link)
    assert step.tail is None
    assert read_rows(hub, biz) == {row['id']: row}
    assert read_shadow(edge, biz)[row['id']].version == 1


def check_worker_maintenance(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """The worker prunes the log of every node it touches on its own interval, on a fake clock."""

    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    row = _business('m')
    insert_row(edge, biz, row)
    delete_row(edge, biz, row['id'])

    now = [0.]
    w = Worker(
        [_link('up', schema, edge, hub)],
        clock=lambda: now[0],
        wall_clock=lambda: datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60),
        maintenance_interval_s=100.,
        log_keep_s=0.,
    )

    # pruning runs on the first pass, then not again until the interval has elapsed
    r1 = w.run_once()
    assert sorted(m.node for m in r1.maintained) == sorted([edge.name, hub.name])
    now[0] += 50.
    assert not w.run_once().maintained
    now[0] += 60.
    assert len(w.run_once().maintained) == 2

    # a zero retention leaves nothing in the log behind but its newest entry
    with edge.db.connect() as conn:
        assert len(edge.backend.read_log(conn, edge.log_table, after=0, limit=10)) == 1


def check_worker_pacing(edge: Node, hub: Node, schema: ReplicationSchema) -> None:
    """
    A worker left alone settles down to nearly nothing, and wakes up when there is something to do: the tail by how
    lately its log was busy, the sweep a table's batch at a time - sooner for a table found to be behind - pruning
    tombstones as it goes. All on a fake clock.
    """

    edge_db = check.isinstance(edge.db, FailingDb)
    hub_db = check.isinstance(hub.db, FailingDb)
    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    num_tables = len(schema.tables)

    now = [1000.]
    w = Worker(
        [_link('up', schema, edge, hub, batch_size=10)],
        tail_pacing=TailPacing(min_interval_s=.5, max_interval_s=10., idle_ratio=.1),
        sweep_interval_s=60.,
        clock=lambda: now[0],
        wall_clock=lambda: datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60),
        maintenance_interval_s=None,
        tombstone_keep_s=0.,
    )

    def run_until(t: float) -> list[tuple[float, LinkSyncReport]]:
        """Runs the worker as `run` would, its sleeps being leaps of the clock, up to but not at a time."""

        out: list[tuple[float, LinkSyncReport]] = []
        while (due := w.next_due()) < t:
            now[0] = max(now[0], due)
            rep = w.run_once()
            assert not rep.failed
            out.extend((now[0], r) for r in rep.synced)
        now[0] = t
        return out

    # left alone, the log is looked at less and less - each wait a tenth of the quiet so far - down to every 10s
    quiet = run_until(1300.)
    tails = [t for t, r in quiet if r.tail is not None]
    gaps = [b - a for a, b in itertools.pairwise(tails)]
    assert gaps[0] == .5 and gaps[-1] == 10.
    assert gaps == sorted(gaps)
    assert all(b <= a * 1.1 + 1e-9 for a, b in itertools.pairwise(gaps) if a > .5)
    assert len(tails) < 70  # where every half second would have been six hundred

    # while each table gets a batch a minute, no two in the one pass
    sweeps = [(t, r.tables[0].table) for t, r in quiet if r.tables]
    assert all(len(r.tables) <= 1 for _, r in quiet)
    assert {n: len([t for t, tn in sweeps if tn == n]) for n in schema.table_names} == dict.fromkeys(schema.table_names, 5)  # noqa
    assert len({t for t, _ in sweeps}) == len(sweeps)

    # a look at a log with nothing new in it is the one query, to the source: the far end is not so much as connected to
    for _ in range(num_tables + 1):
        for db in (edge_db, hub_db):
            db.reset_counts()
        [(_, rep)] = run_until(w.next_due() + 1e-6)
        if not rep.tables:
            break
    assert rep.tail is not None and not rep.tail.entries and not rep.tables
    assert (edge_db.num_connects, len(edge_db.statements)) == (1, 1)
    assert (hub_db.num_connects, len(hub_db.statements)) == (0, 0)

    # nor does a sweep which finds everything in place read a single row: just shadows, and their states at the far end
    for db in (edge_db, hub_db):
        db.reset_counts()
    swept = [r for _, r in run_until(now[0] + 60.) if r.tables]
    assert len(swept) == num_tables
    assert not any('join' in s.lower() for s in edge_db.statements)

    # something in the log and it is back to the half second, easing off again from there
    rows = [_business(f'p{i}') for i in range(25)]
    for r in rows:
        insert_row(edge, biz, r)
    start = now[0]
    busy = run_until(start + 30.)
    busy_tails = [(t, r.tail) for t, r in busy if r.tail is not None]
    assert busy_tails[0][1].applied == len(rows)
    assert read_rows(hub, biz) == read_rows(edge, biz)
    busy_gaps = [b - a for (a, _), (b, _) in itertools.pairwise(busy_tails)]
    assert busy_gaps[0] == .5 and 1. < busy_gaps[-1] < 10.

    # a table found to be behind is not made to wait its minute: rows the log never told of - ones from before a node
    # kept one, or whose entries were pruned - go batch after batch, as fast as they are found
    with edge.db.connect() as conn:
        edge.backend.prune_log(conn, edge.log_table, before=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60))  # noqa
    with hub.db.connect() as conn:
        for t in (hub.table_name(biz), hub.shadow_name(biz)):
            qf.exec(conn, f'delete from {hub.backend.qname(t)}')  # noqa
    assert not read_rows(hub, biz)
    behind = [(t, r.tables[0]) for t, r in run_until(now[0] + 60.) if r.tables and r.tables[0].table == 'businesses']
    assert [tr.applied for _, tr in behind] == [10, 10, 5, 0]  # the one which finds nothing more ends the hurry
    assert len({t for t, _ in behind}) == 1
    assert read_rows(hub, biz) == read_rows(edge, biz)

    # and tombstones go as the sweep comes by them - at both ends, the far one having first been told of the delete -
    # which is by the stretch of keys a batch covered, never by a scan for them of its own
    delete_row(edge, biz, rows[0]['id'])
    assert read_shadow(edge, biz)[rows[0]['id']].deleted
    for db in (edge_db, hub_db):
        db.reset_counts()
    run_until(now[0] + 300.)  # time enough for a sweep to get all the way around
    assert rows[0]['id'] not in read_rows(hub, biz)
    assert all(rows[0]['id'] not in read_shadow(n, biz) for n in (edge, hub))
    assert len(read_shadow(edge, biz)) == len(read_shadow(hub, biz)) == len(rows) - 1
    for n, db in ((edge, edge_db), (hub, hub_db)):
        prunes = [x for x in db.writes if x.lstrip().lower().startswith(f'delete from {n.backend.qname(n.shadow_name(biz))}')]  # noqa
        assert len(prunes) >= 3 and all(f'{n.backend.quote("id")} >' in x or f'{n.backend.quote("id")} <=' in x for x in prunes)  # noqa
