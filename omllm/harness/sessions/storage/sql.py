import abc
import datetime
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import lang
from omcore import orm
from omcore import sql

from ..entries import SessionEntry
from ..types import SessionId
from .types import SessionStorage


##


class Orm(lang.Abstract):
    @abc.abstractmethod
    def new_session(self) -> ta.AsyncContextManager[orm.Session]:
        raise NotImplementedError

    @abc.abstractmethod
    def ensure_session(self) -> ta.AsyncContextManager[orm.Session]:
        raise NotImplementedError


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


#


def orm_mappers() -> ta.Sequence[orm.Mapper]:
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
                entries=[
                    orm.FieldCodec(orm.CompositeCodec(
                        orm.MarshalCodec(),
                        orm.JsonCodec(),
                    )),
                    orm.FieldSqlType(sql.td.String()),
                ],
            ),
            indexes=[
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


##


class SqlSessionStorage(SessionStorage):
    def __init__(
            self,
            session_id: SessionId,
            orm_: Orm,
    ) -> None:
        super().__init__()

        self._session_id = session_id
        self._orm = orm_

    #

    async def _get_orm_session(self) -> OrmSession:
        if (orm_session := await orm.get(OrmSession, self._session_id.v)) is not None:
            return orm_session

        return await orm.add_one(OrmSession(
            id=orm.key(self._session_id.v),
        ))

    async def get_entries(self) -> ta.Sequence[SessionEntry]:
        async with self._orm.new_session():
            orm_session = await self._get_orm_session()

            orm_entries = await orm_session.entries()

            entries = [
                orm_e.entry
                for orm_e in sorted(
                    orm_entries,
                    key=lambda orm_e: orm_e.seq,
                )
            ]

        return entries

    async def add_entry(self, *entries: SessionEntry) -> None:
        if not entries:
            return

        async with self._orm.new_session() as sess:  # noqa
            orm_session = await self._get_orm_session()

            for e in entries:
                await orm.add_one(OrmSessionEntry(
                    id=orm.key(e.id),

                    session=orm.ref(orm_session),
                    seq=orm_session.num_entries + 1,

                    entry=e,
                ))

                orm_session.num_entries += 1
