import pytest

from omcore import orm

from ..impl import StoreOrm
from ..models import orm_mappers
from .scenarios import check_orm_session_storage


@pytest.mark.asyncs('asyncio')
async def test_in_memory():
    await check_orm_session_storage(StoreOrm(
        registry=orm.registry(*orm_mappers()),
        store=orm.InMemoryStore(),
    ))
