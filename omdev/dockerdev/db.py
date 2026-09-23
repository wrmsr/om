import datetime
import os.path
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import lang
from omcore import orm
from omcore import sql

from ..home.paths import get_home_paths
from .config import Config
from .run import RunArgs


##


@dc.dataclass(frozen=True)
class Run:
    id: uuid.UUID

    container_id: str | None = None

    #

    cfg: Config | None = None
    sha: str | None = None
    args: RunArgs | None = None


##


@dc.dataclass(kw_only=True)
@dc.extra_class_params(install_class_field_attrs='instance')
class OrmRun:
    id: orm.Key[uuid.UUID] = dc.field()

    created_at: datetime.datetime = orm.auto_value[datetime.datetime]()
    updated_at: datetime.datetime = orm.auto_value[datetime.datetime]()

    #

    container_id: str | None = None

    json: Run


def orm_mappers() -> ta.Sequence[orm.Mapper]:
    return [

        orm.dataclass_mapper(
            OrmRun,
            store_name='run',

            field_options=dict(
                created_at=[orm.CreatedAt()],
                updated_at=[orm.UpdatedAt()],

                json=[
                    orm.FieldCodec(orm.CompositeCodec(
                        orm.MarshalCodec(),
                        orm.JsonCodec(),
                    )),
                    orm.FieldSqlType(sql.td.Json()),
                ],
            ),

            indexes=[
                orm.index(
                    'container_id',
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


##


DEFAULT_DB_FILE_NAME: ta.Final = 'runs.db'


def write_run_to_db(
        *,
        id: uuid.UUID,  # noqa

        cfg: Config | None = None,
        sha: str | None = None,
        args: RunArgs | None = None,

        db_file: str | None = None,
) -> None:
    run = Run(
        id=id,

        cfg=cfg,
        sha=sha,
        args=args,
    )

    #

    if db_file is None:
        db_file = os.path.join(
            get_home_paths().config_dir,
            'dockerdev',
            DEFAULT_DB_FILE_NAME,
        )

    db = sql.be.sqlite.connecting.sqlite_db(sql.be.sqlite.connecting.SqliteDbConfig(
        file_path=db_file,
    ))

    backend = sql.be.sqlite.backend.SqliteBackend()

    registry = orm.registry(*orm_mappers())

    store = orm.SqlStore(
        registry,
        sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, db),
        tabledef_renderer=backend.tabledef_renderer,
        dtype_codec=backend.dtype_codec,
    )

    async def do_write() -> None:
        async with orm.session(registry, store):
            await orm.add_one(OrmRun(
                id=orm.key(id),

                json=run,
            ))

    lang.sync_await(do_write())
