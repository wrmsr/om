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


T = ta.TypeVar('T')


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


async def _update_db(
        fn: ta.Callable[[orm.Session], ta.Awaitable[T]],
        *,
        db_file: str | None = None,
) -> T:
    if db_file is None:
        db_file = os.path.join(
            get_home_paths().state_dir,
            'dockerdev',
            DEFAULT_DB_FILE_NAME,
        )

    # FIXME: shouldn't need to specify SQLITE lol
    spec = sql.DbSpec(
        'dockerdev_runs',
        sql.DbFamilies.SQLITE,
        sql.be.sqlite.connecting.SqliteDbConfig(file_path=db_file),
    )

    # FIXME: why tf do we need a name
    db_sets = sql.DbSets({'dockerdev_runs': sql.DbSet(writer=spec)})

    async with sql.AsyncDbs(db_sets) as dbs:
        db = await dbs.db('dockerdev_runs')

        backend = sql.be.sqlite.backend.SqliteBackend()

        registry = orm.registry(*orm_mappers())

        store = orm.SqlStore(
            registry,
            db,
            tabledef_renderer=backend.tabledef_renderer,
            dtype_codec=backend.dtype_codec,
        )

        await store.ensure_schema()

        async with orm.session(registry, store) as session:
            return await fn(session)


#


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

    async def do_write(session: orm.Session) -> None:
        await orm.add_one(OrmRun(
            id=orm.key(id),

            json=run,
        ))

    lang.sync_await(_update_db(
        do_write,
        db_file=db_file,
    ))
