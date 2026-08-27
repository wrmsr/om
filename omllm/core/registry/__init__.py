from .globals import (  # noqa
    get_global_registry,

    register_type,
    get_registry_cls,
    registry_new,

    registry_of,
)

from .reflect import (  # noqa
    RegistryTypeName,

    get_annotated_registry_type_name,
    registry_type_repr,

    strip_registry_annotations,
)

from .registry import (  # noqa
    Registry,
)
