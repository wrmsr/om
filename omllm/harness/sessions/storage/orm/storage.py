import typing as ta

from omcore import orm

from ...entries import SessionEntry
from ...types import SessionId
from ..types import SessionNotFoundError
from ..types import SessionStorage
from .models import OrmSession
from .models import OrmSessionEntry
from .types import Orm


##


class OrmSessionStorage(SessionStorage):
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
            if (orm_session := await orm.get(OrmSession, self._session_id.v)) is None:
                raise SessionNotFoundError(str(self._session_id.v))

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

        async with self._orm.new_session():
            orm_session = await self._get_orm_session()

            for e in entries:
                await orm.add_one(OrmSessionEntry(
                    id=orm.key(e.id),

                    session=orm.ref(orm_session),
                    seq=orm_session.num_entries + 1,

                    entry=e,
                ))

                orm_session.num_entries += 1
