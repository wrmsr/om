from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .css import (  # noqa
        style_to_css,
    )

    from .rendering import (  # noqa
        render_html,
    )
