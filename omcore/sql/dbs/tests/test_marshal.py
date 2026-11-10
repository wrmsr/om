from .... import marshal as msh
from ...backends.sqlite.connecting import SqliteDbConfig
from ..sets import DbSet
from ..specs import DbFamilies
from ..specs import DbSpec


def test_marshal():
    db_set = DbSet({
        'reader': DbSpec(
            'reader',
            DbFamilies.SQLITE,
            SqliteDbConfig(':memory:'),
        ),
    })

    mv = msh.marshal(db_set)
    print(mv)

    uv = msh.unmarshal(mv, DbSet)
    print(uv)
