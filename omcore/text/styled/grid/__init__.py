"""
Fixed-width grid lowering of styled text.

Everything beneath this package is flow text: code points and spans, with no notion of display width. This package
measures text in terminal cells and lays it out into width-exact lines - the lowering a terminal screen or a
preformatted block needs, and one a reflowing target such as a browser must never see.
"""
from .... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .fitting import (  # noqa
        Alignment,
        fit,
        pad_left,
        pad_right,
        truncate,
    )

    from .indents import (  # noqa
        expand_tabs,
        indent_guides,
    )

    from .measuring import (  # noqa
        cell_width,
        fit_offset,
    )

    from .rules import (  # noqa
        rule,
    )

    from .wrapping import (  # noqa
        wrap,
        wrap_document,
    )
