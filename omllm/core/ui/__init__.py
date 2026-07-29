from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .display import (  # noqa
        UiTextDisplayer,
        NopUiTextDisplayer,
        PrintUiTextDisplayer,
    )

    from .json import (  # noqa
        JsonUiTextRendering,

        render_obj_json_ui_text,

        render_json_ui_texts,
    )

    from .rich import (  # noqa
        ui_text_to_rich_text,
    )

    from .text import (  # noqa
        CanUiText,

        UiTextColor,
        UiTextStyle,

        UiText,
        StrUiText,
        ConcatUiText,
        StyleUiText,
        JsonUiText,
        MarkdownUiText,
        DiffUiText,
    )
