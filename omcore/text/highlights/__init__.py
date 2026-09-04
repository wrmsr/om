from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .base import (  # noqa
        HighlightedLines,
        Highlighter,
        PythonHighlighter,
        DiffHighlighter,
        get_highlighter,
        highlight_code,
    )

    from .pygments import (  # noqa
        pygments_available,
        PygmentsHighlighter,
        get_pygments_highlighter,
    )
