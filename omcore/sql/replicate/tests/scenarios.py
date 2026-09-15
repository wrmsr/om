"""The behaviors every dialect and every dialect pair must exhibit, written once against nodes. Not a test module."""
import datetime
import typing as ta
import uuid

import pytest

from .... import check
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
    return {'id': uuid.uuid7(), 'name': name}


def _sink(**kw: ta.Any) -> dict[str, ta.Any]:
    return {'id': uuid.uuid7(), 'i': None, 's': None, 'd': None, 'u': None, 'b': None, 'f': None, 'y': None, **kw}


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
