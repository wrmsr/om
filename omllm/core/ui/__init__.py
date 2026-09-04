from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .text.display import (  # noqa
        TextDisplayer,
        NopTextDisplayer,
        PrintTextDisplayer,
    )

    from .text.json import (  # noqa
        JsonTokenKind,
        render_json_tokens,
        render_obj_json_text,
        render_json_texts,
    )

    from .text.plain import (  # noqa
        PlainTextRenderer,
        render_plain_text,
    )

    from .text.rendering import (  # noqa
        TextRenderer,
        TextRenderingOptions,
    )

    from .text.styled import (  # noqa
        StyledJsonStyles,
        StyledTextBlock,
        StyledTextPart,
        StyledTextRendering,
        StyledTextRenderer,
    )

    from .text.types import (  # noqa
        CanText,

        TextColor,
        TextStyle,

        Text,
        StrText,
        ConcatText,
        StyleText,

        JsonTextStyle,
        JsonText,

        BlockText,
        MarkdownText,
        DiffText,
    )

    ##

    from .quit import (  # noqa
        QuitSignal,
        RaiseQuitSignal,
    )
