import pytest

from omcore import orm
from omcore import sql
from omcore.sql.tests.harness import HarnessSandboxes

from ..models import orm_mappers
from ..sql import SqlOrm
from .scenarios import check_orm_session_storage


@pytest.mark.asyncs('asyncio')
async def test_postgres(harness):
    with harness[HarnessSandboxes].postgres().allocate() as sb:
        async with SqlOrm(
            registry=orm.registry(*orm_mappers()),
            db=sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, sb.db()),
            tabledef_renderer=sql.be.postgres.td.PostgresTabledefRenderer(),
        ) as sql_orm:
            await check_orm_session_storage(sql_orm)
