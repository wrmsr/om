import pytest

from .... import lang
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...qualifiedname import qn
from ...syntax import QuoteStyles
from ..diffing import AddColumn
from ..diffing import DropColumn
from ..diffing import DropIndex
from ..elements import Column
from ..elements import Elements
from ..elements import Index
from ..elements import PrimaryKey
from ..rendering import IdentifierTooLongError
from ..rendering import Renderer
from ..tabledefs import TableDef


class _R(Renderer):
    def column_type(self, c, *, is_identity, indexed=False):
        return 'text'


class _ShortR(_R):
    max_identifier_length = 8


class _BacktickR(_R):
    quote_style = QuoteStyles.BACKTICK


def test_quoting():
    r = _R()
    assert r.quote('users') == '"users"'
    assert r.quote('we"ird') == '"we""ird"'
    assert r.qname(qn('users')) == '"users"'
    assert r.qname(qn('app', 'users')) == '"app"."users"'
    assert _BacktickR().qname(qn('app', 'users')) == '`app`.`users`'


def test_identifier_length_guard():
    r = _ShortR()
    assert r.quote('12345678') == '"12345678"'
    with pytest.raises(IdentifierTooLongError):
        r.quote('123456789')
    with pytest.raises(IdentifierTooLongError):
        r.quote('é' * 5)  # bytes, not characters - this is 10 bytes of utf-8


def test_render_qualified():
    td = TableDef(qn('app', 'users'), Elements(
        Column('id', INTEGER),
        PrimaryKey(['id']),
        Column('name', STRING, nullable=True),
        Index(['name']),
    ))

    stmts = _R().render_create_statements(td, Renderer.CreateOptions(drop_if_exists=True))
    assert stmts == [
        'drop table if exists "app"."users"',
        (
            'create table "app"."users" (\n'
            '  "id" text not null,\n'
            '  "name" text,\n'
            '  primary key ("id")\n'
            ')'
        ),
        'create index "users__index__name" on "app"."users" ("name")\n',
    ]


def test_render_migrations_qualified():
    r = _R()
    t = qn('app', 'users')
    assert r.render_migration(AddColumn(t, Column('email', STRING, nullable=True))) == [
        'alter table "app"."users" add column "email" text',
    ]
    assert r.render_migration(DropColumn(t, 'email')) == ['alter table "app"."users" drop column "email"']
    # an index lives in its table's schema, so its drop is qualified the same way
    assert r.render_migration(DropIndex(t, 'users__index__name')) == ['drop index "app"."users__index__name"']
    assert r.render_migration(DropIndex(qn('users'), 'users__index__name')) == ['drop index "users__index__name"']


def test_unspecified_lang_final_renderer_ok():
    # a Final renderer subclass is fine - only the abstract hooks must be implemented
    class _F(_R, lang.Final):
        pass

    assert _F().quote('x') == '"x"'
