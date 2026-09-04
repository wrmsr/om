"""The terminal backend for styled text: terminal palettes and depth, SGR emission and parsing, headless ANSI output."""
from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .colors import (  # noqa
        ColorDepth,
        NamedColor,
        IndexedColor,

        detect_color_depth,

        BLACK,
        RED,
        GREEN,
        YELLOW,
        BLUE,
        MAGENTA,
        CYAN,
        WHITE,
        BRIGHT_BLACK,
        BRIGHT_RED,
        BRIGHT_GREEN,
        BRIGHT_YELLOW,
        BRIGHT_BLUE,
        BRIGHT_MAGENTA,
        BRIGHT_CYAN,
        BRIGHT_WHITE,

        NAMED_COLOR_RGBS,
        indexed_color_rgb,
        rgb_to_indexed,
        downgrade_color,
    )

    from .parsing import (  # noqa
        ANSI_ESCAPE_PAT,
        apply_sgr_params,
        parse_ansi_text,
        strip_ansi_escapes,
    )

    from .rendering import (  # noqa
        render_ansi,
        render_ansi_runs,
    )

    from .sgr import (  # noqa
        RESET_SGR,
        style_sgr_params,
        style_sgr,
        sgr_transition,
    )
