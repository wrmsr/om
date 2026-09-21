"""The behaviors every dialect and every dialect pair must exhibit, written once against nodes. Not a test module."""
import datetime
import typing as ta
import uuid

import pytest

from .... import check
from .... import dataclasses as dc
from ...api import querierfuncs as qf
from ...tabledefs.diffing import AddTrigger
from ...tabledefs.diffing import DropTrigger
from ..config import CursorSide
from ..config import LinkSpec
from ..config import OriginFilter
from ..config import ReplicationSchema
from ..errors import ReplicationConflictError
from ..install import install_node
from ..links import Link
from ..links import sync_link_once
from ..links import sync_link_sweep
from ..links import sync_link_tail
from ..maintenance import prune_log
from ..maintenance import prune_tombstones
from ..nodes import Node
from ..rows import ShadowState
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
    r3 = install_node(node, schema, capture_trigger_version=2)
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
        hub.backend.upsert_shadow(conn, hub.shadow_name(biz), a['id'], ShadowState(version=9, origin=n.node_id, deleted=False))  # noqa
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
    w = Worker([good, bad], interval_s=1., max_backoff_s=8., clock=lambda: now[0], sleeper=slept.append)

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

    # pruning: the log empties, the tombstone goes, the live rows stay
    prune_log(edge, keep_s=0, now=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60))
    with edge.db.connect() as conn:
        assert not edge.backend.read_log(conn, edge.log_table, after=0, limit=10)
    prune_tombstones(edge, schema, keep_s=0, now=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60))
    sh = read_shadow(edge, biz)
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
    """The worker prunes every node it touches on its own interval, on a fake clock."""

    for n in (edge, hub):
        install_node(n, schema)
    biz = schema.table('businesses')
    row = _business('m')
    insert_row(edge, biz, row)
    delete_row(edge, biz, row['id'])

    now = [0.]
    w = Worker(
        [_link('up', schema, edge, hub)],
        interval_s=1.,
        clock=lambda: now[0],
        sleeper=lambda _: None,
        maintenance_interval_s=100.,
        log_keep_s=0.,
        tombstone_keep_s=0.,
    )

    # pruning runs on the first pass, then not again until the interval has elapsed
    r1 = w.run_once()
    assert sorted(m.node for m in r1.maintained) == sorted([edge.name, hub.name])
    now[0] += 50.
    assert not w.run_once().maintained
    now[0] += 60.
    assert len(w.run_once().maintained) == 2

    # a zero retention leaves no log entries and no tombstones behind (a tiny clock skew is tolerated by waiting)
    with edge.db.connect() as conn:
        assert not edge.backend.read_log(conn, edge.log_table, after=0, limit=10)
    assert row['id'] not in read_shadow(edge, biz)
