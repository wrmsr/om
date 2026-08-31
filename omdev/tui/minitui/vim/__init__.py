# fmt: off
# ruff: noqa: I001
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(
        globals(),
        # disable=True,
        # eager=True,
):
    ##

    from .modes import (  # noqa
        Mode,
        CmdlineKind,
    )

    from .status import (  # noqa
        VimStatus,
        Decoration,
        Decorations,

        SELECTION_TAG,
        CURSOR_TAG,
        SEARCH_MATCH_TAG,
        SEARCH_CURRENT_TAG,
    )

    from .registers import (  # noqa
        RegValue,
        Registers,
    )

    from .substitutes import (  # noqa
        SubstituteError,
        ExRange,
        SubstituteResult,
        SubstituteSpec,
        parse_ex_range,
        parse_substitute,
        apply_substitute,
    )

    from .options import (  # noqa
        VimOptions,
        DEFAULT_OPTIONS,
        get_language_options,
    )

    from .engine import (  # noqa
        ExHandler,
        VimEngine,
    )
