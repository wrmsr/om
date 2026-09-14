from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import Boolean
from ...dtypes import Bytes
from ...dtypes import Float
from ...dtypes import Integer
from ...dtypes import String
from ...tabledefs.elements import Column
from ..mysql.tabledefs import MysqlTabledefRenderer
from ..postgres.tabledefs import PostgresTabledefRenderer
from ..sqlite.tabledefs import SqliteTabledefRenderer


def _types(r, *ts, **kwargs):
    return {t: r.column_type(Column('c', t), is_identity=False, **kwargs) for t in ts}


def test_new_dtypes_render_per_backend():
    ts = (Boolean(), Float(), Bytes())
    assert _types(SqliteTabledefRenderer(), *ts) == {Boolean(): 'boolean', Float(): 'real', Bytes(): 'blob'}
    assert _types(PostgresTabledefRenderer(), *ts) == {Boolean(): 'boolean', Float(): 'double precision', Bytes(): 'bytea'}  # noqa
    assert _types(MysqlTabledefRenderer(), *ts) == {Boolean(): 'tinyint(1)', Float(): 'double', Bytes(): 'blob'}


def test_integer_widths_render_per_backend():
    ts = (INTEGER, Integer(bits=16), Integer(bits=32), Integer(bits=64))
    assert list(_types(PostgresTabledefRenderer(), *ts).values()) == ['integer', 'smallint', 'integer', 'bigint']
    assert list(_types(MysqlTabledefRenderer(), *ts).values()) == ['integer', 'smallint', 'integer', 'bigint']
    assert list(_types(SqliteTabledefRenderer(), *ts).values()) == ['integer'] * 4

    # an identity column of unspecified width is 64-bit
    for r in (PostgresTabledefRenderer(), MysqlTabledefRenderer()):
        assert r.column_type(Column('id', INTEGER), is_identity=True) == 'bigint'
        assert r.column_type(Column('id', Integer(bits=32)), is_identity=True) == 'integer'


def test_string_lengths_render_per_backend():
    ts = (STRING, String(length=40))
    assert list(_types(PostgresTabledefRenderer(), *ts).values()) == ['text', 'varchar(40)']
    assert list(_types(SqliteTabledefRenderer(), *ts).values()) == ['text', 'varchar(40)']
    assert list(_types(MysqlTabledefRenderer(), *ts).values()) == ['text', 'varchar(40)']

    # mysql cannot index an unbounded text column, so an indexed one gets a default bound
    assert list(_types(MysqlTabledefRenderer(), *ts, indexed=True).values()) == ['varchar(255)', 'varchar(40)']
