from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .builders import (  # noqa
        StyledTextBuilder,
    )

    from .colors import (  # noqa
        Color,
        RgbColor,
        parse_rgb,
    )

    from .html import (  # noqa
        render_html,
        style_to_css,
    )

    from .plain import (  # noqa
        render_plain,
    )

    from .styles import (  # noqa
        DEFAULT_COLOR,
        EMPTY_STYLE_PATCH,
        EMPTY_STYLE_THEME,
        PLAIN_STYLE,
        ColorDefault,
        ResolvedStyle,
        StyleColor,
        StyleLike,
        StyleName,
        StyleNameLike,
        StylePatch,
        StyleRef,
        StyleTheme,
        as_style_ref,
    )

    from .text import (  # noqa
        ResolvedStyledTextRun,
        StyledText,
        StyledTextLike,
        StyledTextRun,
        StyleSpan,
    )
