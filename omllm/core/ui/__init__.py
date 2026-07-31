from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .text.display import (  # noqa
        TextDisplayer,
        NopTextDisplayer,
        PrintTextDisplayer,
    )

    from .text.json import (  # noqa
        JsonTextRendering,
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

    from .text.rich import (  # noqa
        RichTextRenderer,
    )

    from .text.types import (  # noqa
        CanText,

        TextColor,
        TextStyle,

        Text,
        StrText,
        ConcatText,
        StyleText,
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
