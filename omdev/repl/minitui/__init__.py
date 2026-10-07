# fmt: off
# ruff: noqa: I001
from omcore import lang as _lang


with _lang.auto_proxy_init(
        globals(),
):
    from .app import (  # noqa
        ReplApp,
    )

    from .console import (  # noqa
        CommitFn,
        Console,
    )

    from .highlighting import (  # noqa
        RetaggedHighlighter,
        get_language_highlighter,
    )

    from .rendering import (  # noqa
        SegmentRows,
        render_echo,
        render_output,
        render_note,
    )

    from .styles import (  # noqa
        CODE_TAG_PREFIX,
        REPL_STYLES,
        REPL_THEME,
    )
