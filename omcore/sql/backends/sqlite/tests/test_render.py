from ....dtypes import STRING
from ....qualifiedname import qn
from ....tabledefs.elements import Column
from ....tabledefs.elements import CreatedAtUpdatedAt
from ....tabledefs.elements import Elements
from ....tabledefs.elements import IdIntegerPrimaryKey
from ....tabledefs.elements import Index
from ....tabledefs.lower import lower_table_elements
from ....tabledefs.rendering import Renderer
from ....tabledefs.tabledefs import TableDef
from ..tabledefs import SqliteTabledefRenderer


def _users(*name):
    return lower_table_elements(TableDef(qn(*name), Elements(
        IdIntegerPrimaryKey(),
        CreatedAtUpdatedAt(),
        Column('name', STRING),
        Index(['name']),
    )))


def test_render_golden():
    assert SqliteTabledefRenderer().render_create_statements(_users('users')) == [
        (
            'create table "users" (\n'
            '  "id" integer not null,\n'
            '  "created_at" datetime not null default (strftime(\'%Y-%m-%d %H:%M:%f\', \'now\')),\n'
            '  "updated_at" datetime not null default (strftime(\'%Y-%m-%d %H:%M:%f\', \'now\')),\n'
            '  "name" text not null,\n'
            '  primary key ("id")\n'
            ')'
        ),
        'create index "users__index__name" on "users" ("name")\n',
        (
            'create trigger "users__trigger__updated_at__updated_at"\n'
            'after update on "users"\n'
            'for each row\n'
            'when new."updated_at" = old."updated_at"\n'
            'begin\n'
            '  update "users"\n'
            '  set "updated_at" = max(strftime(\'%Y-%m-%d %H:%M:%f\', \'now\'), '
            'coalesce(strftime(\'%Y-%m-%d %H:%M:%f\', old."updated_at", \'+0.001 seconds\'), \'\'))\n'
            '  where "id" = new."id";\n'
            'end'
        ),
    ]


def test_render_qualified_golden():
    # sqlite qualifies the *created* object (table, index, trigger) but never the table an index or trigger is on
    stmts = SqliteTabledefRenderer().render_create_statements(
        _users('main', 'users'),
        Renderer.CreateOptions(if_not_exists=True),
    )

    assert stmts[0].startswith('create table if not exists "main"."users" (\n')
    assert stmts[1] == 'create index if not exists "main"."users__index__name" on "users" ("name")\n'
    assert stmts[2].startswith(
        'create trigger if not exists "main"."users__trigger__updated_at__updated_at"\n'
        'after update on "users"\n',
    )
