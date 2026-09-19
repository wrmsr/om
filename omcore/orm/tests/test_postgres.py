import urllib.parse

from ... import check
from ... import lang
from ... import sql
from ...sql.tests.harness import HarnessDbs
from ...testing import pytest as ptu
from ..registries import Registry
from ..sql import SqlStore
from . import test_uuids
from .models import build_registry
from .test_orm import _test_orm


##


def _pg8000_store(harness, registry: Registry) -> SqlStore:
    url = check.isinstance(check.isinstance(harness[HarnessDbs].specs()['postgres'].loc, sql.UrlDbLoc).url, str)
    p_u = urllib.parse.urlparse(url)

    import pg8000

    db = sql.api.DbapiDb(
        sql.api.ClosingDbapiConnector(
            pg8000.connect,
            p_u.username,
            host=p_u.hostname,
            port=p_u.port,
            password=p_u.password,
        ),
        adapter=sql.be.postgres.adapters.postgres_adapter(),
    )

    adb = sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, db)

    return SqlStore(
        registry,
        adb,
        tabledef_renderer=sql.be.postgres.td.PostgresTabledefRenderer(),
        tabledef_create_options=sql.td.Renderer.CreateOptions(
            drop_if_exists=True,
        ),
    )


@ptu.skip.if_cant_import('pg8000')
def test_pg8000(harness, exit_stack) -> None:
    registry = build_registry()
    lang.sync_await(_test_orm(_pg8000_store(harness, registry), registry))


@ptu.skip.if_cant_import('pg8000')
def test_pg8000_uuids(harness, exit_stack) -> None:
    # Uuid fields are native uuid columns here, not text: what goes in as a string has to come back out as a uuid.
    lang.sync_await(test_uuids._test_uuids(_pg8000_store(harness, test_uuids.registry())))  # noqa
