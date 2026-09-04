"""Width-aware, target-neutral presentation of parsed diffs."""
from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .rendering import (  # noqa
        CodeHighlighter,
        DiffRenderer,
        DiffRenderOptions,
        render_diff_document,
        simple_pluralise,
    )

    from .terminal import (  # noqa
        DIFF_TERMINAL_THEME,
        render_diff_ansi,
    )

    from .themes import (  # noqa
        DIFF_STYLE_THEME,
    )
