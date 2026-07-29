from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .display import (  # noqa
        TextDisplayer,
        NopTextDisplayer,
        PrintTextDisplayer,
    )

    from .json import (  # noqa
        JsonTextRendering,
        render_obj_json_text,
        render_json_texts,
    )

    from .rich import (  # noqa
        text_to_rich_text,
    )

    from .text import (  # noqa
        CanText,

        TextColor,
        TextStyle,

        Text,
        StrText,
        ConcatText,
        StyleText,
        JsonText,
        MarkdownText,
        DiffText,
    )

    from .quit import (  # noqa
        QuitSignal,
        RaiseQuitSignal,
    )
