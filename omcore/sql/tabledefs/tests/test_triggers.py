"""
A foreign trigger type + per-'dialect' renderer, standing in for what another package (replication, say) would define
without tabledefs knowing of it.
"""
import pytest

from .... import dataclasses as dc
from .... import lang
from ...dtypes import INTEGER
from ...qualifiedname import QualifiedName
from ...qualifiedname import qn
from ..diffing import AddTrigger
from ..diffing import DropTrigger
from ..diffing import diff_table
from ..elements import Column
from ..elements import Elements
from ..elements import OpaqueTrigger
from ..elements import PrimaryKey
from ..elements import Trigger
from ..elements import UpdatedAtTrigger
from ..rendering import Renderer
from ..rendering import UnknownTriggerTypeError
from ..tabledefs import TableDef
from ..triggers import TriggerRenderer


##


@dc.dataclass(frozen=True)
class _CaptureTrigger(Trigger, lang.Final):
    version: int

    @classmethod
    def trigger_name_prefix(cls, table_name: QualifiedName) -> str:
        return f'_xyz_{table_name.last}__capture__'

    def trigger_name_suffix(self) -> str:
        return f'v{self.version}'


class _CaptureTriggerRenderer(TriggerRenderer[_CaptureTrigger]):
    @property
    def trigger_cls(self):
        return _CaptureTrigger

    def create_statements(self, r, tbl, t, opts):
        pk = tbl.elements.get(PrimaryKey)
        return [f'create trigger {r.quote(t.trigger_name(tbl.name))} on {r.qname(tbl.name)} /* pk {pk.columns[0]} */']

    def drop_statements(self, r, table_name, name):
        return [f'drop trigger {r.quote(name)} on {r.qname(table_name)}']


class _R(Renderer):
    def column_type(self, c, *, is_identity, indexed=False):
        return 'text'


##


def _td(*els):
    return TableDef(qn('t'), Elements(Column('id', INTEGER), PrimaryKey(['id']), *els))


def test_plugin_renders_create():
    r = _R(trigger_renderers=[_CaptureTriggerRenderer()])
    stmts = r.render_create_statements(_td(_CaptureTrigger(1)))
    assert stmts[-1] == 'create trigger "_xyz_t__capture__v1" on "t" /* pk id */'


def test_unregistered_type_fails_closed():
    with pytest.raises(UnknownTriggerTypeError):
        _R().render_create_statements(_td(_CaptureTrigger(1)))

    # the built-in updated-at trigger is no different: the base renderer registers nothing
    with pytest.raises(UnknownTriggerTypeError):
        _R().render_create_statements(_td(UpdatedAtTrigger('updated_at')))


def test_duplicate_registration_refused():
    with pytest.raises(Exception):  # noqa
        _R(trigger_renderers=[_CaptureTriggerRenderer(), _CaptureTriggerRenderer()])


def test_opaque_never_created():
    r = _R(trigger_renderers=[_CaptureTriggerRenderer()])
    with pytest.raises(TypeError):
        r.render_create_statements(_td(OpaqueTrigger('_xyz_t__capture__v1')))


def test_version_bump_is_drop_then_add():
    # the body of a trigger is invisible to the differ; a change is surfaced by versioning the name
    cur = _td(_CaptureTrigger(2))
    ex = _td(OpaqueTrigger('_xyz_t__capture__v1'), OpaqueTrigger('t__trigger__updated_at__updated_at'))

    ops = diff_table(cur, ex)
    assert [type(o) for o in ops] == [AddTrigger, DropTrigger]
    assert ops[1] == DropTrigger(qn('t'), '_xyz_t__capture__v1', _CaptureTrigger)

    r = _R(trigger_renderers=[_CaptureTriggerRenderer()])
    assert [s for op in ops for s in r.render_migration(op)] == [
        'create trigger "_xyz_t__capture__v2" on "t" /* pk id */',
        'drop trigger "_xyz_t__capture__v1" on "t"',
    ]


def test_drop_dispatches_to_owning_plugin():
    r = _R(trigger_renderers=[_CaptureTriggerRenderer()])
    assert r.render_migration(DropTrigger(qn('s', 't'), '_xyz_t__capture__v1', _CaptureTrigger)) == [
        'drop trigger "_xyz_t__capture__v1" on "s"."t"',
    ]
    with pytest.raises(UnknownTriggerTypeError):
        r.render_migration(DropTrigger(qn('t'), 't__trigger__updated_at__x', UpdatedAtTrigger))
