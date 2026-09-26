from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from .base import (  # noqa
    DateTime,
    MillisecondDateTime,
    Timestamp,

    Tag,
    TagList,

    ValueType,
    ListValueType,
    MapValueType,

    Enum,

    SHAPE_NAME,
    common_metadata,

    PAYLOAD_MEMBER,
    shape_metadata,
    ShapeInfo,
    Shape,

    MEMBER_NAME,
    SERIALIZATION_NAME,
    VALUE_TYPE,
    LOCATION,
    XML_NAMESPACE,
    XML_FLATTENED,
    XML_ATTRIBUTE,
    LIST_MEMBER_NAME,
    TIMESTAMP_FORMAT,
    STREAMING,
    field_metadata,

    Operation,
)


##


from omcore import marshal as _msh  # noqa

_msh.register_global_module_import('._marshal', __package__)
