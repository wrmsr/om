import datetime
import typing as ta

from omcore import dataclasses as dc
from omcore import orm
from omcore import sql


##


@dc.dataclass(frozen=True)
class Container:
    id: str


##


@dc.dataclass(kw_only=True)
@dc.extra_class_params(install_class_field_attrs='instance')
class OrmContainer:
    _id: orm.Key[int] = dc.field(default_factory=orm.auto_key[int])

    id: orm.Key[str]

    created_at: datetime.datetime = orm.auto_value[datetime.datetime]()
    updated_at: datetime.datetime = orm.auto_value[datetime.datetime]()

    #

    json: Container


def orm_mappers() -> ta.Sequence[orm.Mapper]:
    return [

        orm.dataclass_mapper(
            OrmContainer,
            store_name='container',
            field_options=dict(
                created_at=[orm.CreatedAt()],
                updated_at=[orm.UpdatedAt()],
                container=[
                    orm.FieldCodec(orm.CompositeCodec(
                        orm.MarshalCodec(),
                        orm.JsonCodec(),
                    )),
                    orm.FieldSqlType(sql.td.String()),
                ],
            ),
            indexes=[
                orm.index(
                    'id',
                    options=[
                        orm.UniqueIndexOption(),
                    ],
                ),
                orm.index(
                    'created_at',
                    options=[
                        orm.SortedIndexOption(),
                    ],
                ),
            ],
        ),

    ]
