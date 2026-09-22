"""
A field kept as json, both ways there are to: as the text of a document in a string column, written by a codec of the
field's own - which is no business of the store's - and as a document in a column which is one where the backend has
such a thing, which the store sees to by way of the backend's dtype codec.
"""
import typing as ta
import uuid

import pytest

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import orm
from ... import sql
from ...sql.testing.sandboxes import Sandbox
from ...sql.tests.harness import HarnessSandboxes


##


@dc.dataclass(frozen=True)
class Point:
    x: int
    y: int


@dc.dataclass(frozen=True)
class Shape:
    name: str
    points: ta.Sequence[Point] = ()


@dc.dataclass(kw_only=True)
@dc.extra_class_params(install_class_field_attrs='instance')
class Thing:
    id: orm.Key[uuid.UUID] = dc.field(default_factory=orm.key_wrapping(uuid.uuid7))

    name: str

    as_text: Shape  # marshaled, then written out as json by a codec, into a string column
    as_json: Shape  # marshaled, and left to the store to keep as the document it is
    raw_json: ta.Any | None = None  # nothing to marshal: already whatever json can say - or nothing at all


def _registry() -> orm.Registry:
    return orm.registry(
        orm.dataclass_mapper(
            Thing,
            store_name='things',
            field_options=dict(
                as_text=[
                    orm.FieldCodec(orm.CompositeCodec(orm.MarshalCodec(), orm.JsonCodec())),
                    orm.FieldSqlType(sql.td.String()),
                ],
                as_json=[
                    orm.FieldCodec(orm.MarshalCodec()),
                    orm.FieldSqlType(sql.td.Json()),
                ],
                raw_json=[
                    orm.FieldSqlType(sql.td.Json()),
                ],
            ),
            indexes=['name'],
        ),
    )


_SHAPE = Shape('triangle', (Point(0, 0), Point(1, 0), Point(0, 1)))
_RAW_DOCS: ta.Sequence[ta.Any] = [{'a': [1, None, 'ü']}, [1, 'two'], 'a str', 42, None]


async def _check_json(registry: orm.Registry, store: orm.Store) -> None:
    async with orm.session(registry, store):
        for i, raw in enumerate(_RAW_DOCS):
            await orm.add_one(Thing(name=f't{i}', as_text=_SHAPE, as_json=_SHAPE, raw_json=raw))

    async with orm.session(registry, store):
        for i, raw in enumerate(_RAW_DOCS):
            thing = check.not_none(await orm.query_one(Thing, name=f't{i}'))
            assert thing.as_text == thing.as_json == _SHAPE
            assert thing.raw_json == raw and type(thing.raw_json) is type(raw)

        # and what is there can be changed like anything else
        thing = check.not_none(await orm.query_one(Thing, name='t0'))
        thing.as_json = Shape('dot', (Point(2, 3),))
        thing.raw_json = {'b': 2}

    async with orm.session(registry, store):
        thing = check.not_none(await orm.query_one(Thing, name='t0'))
        assert thing.as_json == Shape('dot', (Point(2, 3),)) and thing.as_text == _SHAPE
        assert thing.raw_json == {'b': 2}


##


def test_in_memory() -> None:
    lang.sync_await(_check_json(_registry(), orm.InMemoryStore()))


def _check_sql(sb: Sandbox, backend: sql.be.Backend, name_of_shape_sql: str, column_type: str) -> None:
    registry = _registry()
    store = orm.SqlStore(
        registry,
        sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, sb.db()),
        tabledef_renderer=backend.tabledef_renderer,
        dtype_codec=backend.dtype_codec,
    )
    lang.sync_await(_check_json(registry, store))

    with sb.db().connect() as conn:
        # a document where the backend has them, down where it can be looked into
        assert sql.api.query_scalar(conn, f"select {name_of_shape_sql} from things where name = 't1'") == 'triangle'  # noqa

        # while the other is, and stays, the string it was written as
        text = sql.api.query_scalar(conn, "select as_text from things where name = 't1'")
        assert isinstance(text, str) and text.startswith('{"name":"triangle"')

    [td] = [td for td in orm.sql_table_defs(registry) if td.name.last == 'things']
    ddl = backend.tabledef_renderer.render_create_statements(sql.td.lower_table_elements(td))[0]
    assert f'as_json{backend.tabledef_renderer.ident_quote_style.quote("")[-1:]} {column_type}' in ddl


def test_sqlite(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        _check_sql(sb, sql.be.sqlite.backend.SqliteBackend(), "json_extract(as_json, '$.name')", 'text')


def test_postgres(harness) -> None:
    with harness[HarnessSandboxes].postgres().allocate() as sb:
        _check_sql(sb, sql.be.postgres.backend.PostgresBackend(), "as_json->>'name'", 'jsonb')


def test_mysql(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        _check_sql(sb, sql.be.mysql.backend.MysqlBackend(), "as_json->>'$.name'", 'json')


def test_json_takes_a_dtype_codec(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        with pytest.raises(TypeError):
            orm.SqlStore(
                _registry(),
                sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, sb.db()),
                tabledef_renderer=sql.be.sqlite.td.SqliteTabledefRenderer(),
            )
