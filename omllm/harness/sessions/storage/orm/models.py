import datetime
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import orm
from omcore import sql

from ...entries import SessionEntry


##


@dc.dataclass(kw_only=True)
@dc.extra_class_params(install_class_field_attrs='instance')
class OrmSession:
    id: orm.Key[uuid.UUID] = dc.field()

    created_at: datetime.datetime = orm.auto_value[datetime.datetime]()
    updated_at: datetime.datetime = orm.auto_value[datetime.datetime]()

    #

    name: str | None = None

    num_entries: int = 0

    entries: ta.ClassVar[orm.Backref[OrmSessionEntry]] = orm.backref(lambda: OrmSessionEntry.session)  # type: ignore[misc]  # noqa


@dc.dataclass(kw_only=True)
@dc.extra_class_params(install_class_field_attrs='instance')
class OrmSessionEntry:
    id: orm.Key[uuid.UUID] = dc.field()

    created_at: datetime.datetime = orm.auto_value[datetime.datetime]()
    updated_at: datetime.datetime = orm.auto_value[datetime.datetime]()

    #

    session: orm.Ref[OrmSession, uuid.UUID]
    seq: int

    entry: SessionEntry


##


def orm_mappers() -> ta.Sequence[orm.Mapper]:
    """Fresh each call: a mapper belongs to the one registry it is given to."""

    return [

        orm.dataclass_mapper(
            OrmSession,
            store_name='sessions',
            field_options=dict(
                created_at=[orm.CreatedAt()],
                updated_at=[orm.UpdatedAt()],
            ),
            indexes=['name'],
        ),

        orm.dataclass_mapper(
            OrmSessionEntry,
            store_name='session_entries',
            field_options=dict(
                created_at=[orm.CreatedAt()],
                updated_at=[orm.UpdatedAt()],
                entry=[
                    orm.FieldCodec(orm.CompositeCodec(
                        orm.MarshalCodec(),
                        orm.JsonCodec(),
                    )),
                    orm.FieldSqlType(sql.td.String()),
                ],
            ),
            indexes=[
                # Wants to be the clustered key, but for now that would make it the primary key too - and the tables are
                # replicated, which needs them keyed by their ids alone.
                orm.index(
                    ['session', 'seq'],
                    options=[
                        orm.UniqueIndexOption(),
                        orm.SortedIndexOption(),
                        orm.ClusteredIndexOption(),
                    ],
                ),
            ],
        ),

    ]
