import pytest

from .... import marshal as msh
from ....formats.json import all as json
from ...dtypes import STRING
from ...qualifiedname import QualifiedName
from ...qualifiedname import qn
from ..elements import Column
from ..elements import CreatedAtUpdatedAt
from ..elements import Elements
from ..elements import IdIntegerPrimaryKey
from ..lower import lower_table_elements
from ..tabledefs import TableDef
from ..tabledefs import table_def


def test_table_defs():
    users = TableDef(
        qn('users'),
        Elements(*[
            IdIntegerPrimaryKey(),
            CreatedAtUpdatedAt(),
            Column('name', STRING),
        ]),
    )
    print(users_json := json.dumps_pretty(msh.marshal(users)))

    users2 = msh.unmarshal(json.loads(users_json), TableDef)
    assert users2 == users

    users_lowered = lower_table_elements(users)
    print(json.dumps_pretty(msh.marshal(users_lowered)))

    print(users_lowered.elements[Column])

    # lowering is idempotent - the lowered elements (triggers included) pass straight through a second time
    assert lower_table_elements(users_lowered) == users_lowered


def test_names():
    # the canonical form takes only a QualifiedName; the helper coerces the loose forms, never splitting a bare str
    with pytest.raises(TypeError):
        TableDef('users', Elements())  # type: ignore[arg-type]

    assert table_def('users').name == qn('users')
    assert table_def('a.b').name == QualifiedName(('a.b',))
    assert table_def(['app', 'users']).name == qn('app', 'users')
    assert table_def(qn('app', 'users')).name == qn('app', 'users')

    assert qn('app', 'users').last == 'users'
    assert qn('app', 'users').sibling('users_ix') == qn('app', 'users_ix')
    assert qn('users').sibling('users_ix') == qn('users_ix')
