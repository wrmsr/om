from ... import dataclasses as _dc


_dc.init_package(
    globals(),
    codegen=True,
)


##


from ..dtypes import (  # noqa
    Dtype,

    INTEGER_BITS,

    Integer,
    String,
    Datetime,
    Uuid,
    Boolean,
    Float,
    Bytes,

    INTEGER,
    STRING,
    DATETIME,
    UUID,
    BOOLEAN,
    FLOAT,
    BYTES,
)

from ..qualifiedname import (  # noqa
    CanStrictQualifiedName,
    CanQualifiedName,
    QualifiedName,
    qn,
)

from .elements import (  # noqa
    Element,

    Column,
    PrimaryKey,
    Index,

    index_name,

    Trigger,
    OpaqueTrigger,

    IdIntegerPrimaryKey,

    CreatedAt,
    UpdatedAt,
    UpdatedAtTrigger,
    CreatedAtUpdatedAt,

    Elements,
)

from .diffing import (  # noqa
    MigrationOp,

    AddColumn,
    DropColumn,
    AlterColumn,
    AddIndex,
    DropIndex,
    AddTrigger,
    DropTrigger,

    UnsupportedDiffError,

    dtypes_confidently_differ,
    diff_table,
)

from .lower import (  # noqa
    lower_table_elements,
    normalize_table,
    select_backend_options,
)

from .options import (  # noqa
    BackendOption,

    ColumnOption,
    IndexOption,
    TableOption,

    ColumnOptions,
    IndexOptions,
    TableOptions,
)

from ..syntax import (  # noqa
    CompareOp,
)

from .predicates import (  # noqa
    And,
    CanPredicate,
    Compare,
    IsNull,
    Not,
    Or,
    Predicate,
    RawPredicate,

    as_predicate,
)

from .rendering import (  # noqa
    IdentifierTooLongError,
    UnknownTriggerTypeError,
    UnsupportedMigrationError,

    Renderer,
)

from .tabledefs import (  # noqa
    TableDef,
    table_def,
)

from .triggers import (  # noqa
    TriggerRenderer,
)

from .values import (  # noqa
    SpecialValue,
    Now,

    SimpleValue,
)


##


from ... import marshal as _msh  # noqa

_msh.register_global_module_import('._marshal', __package__)
