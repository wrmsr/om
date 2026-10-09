"""
Width-aware styled documents from parsed patch sets.

A document is a frame shared by every layout - the summary, each file's header, the special bodies of removed, binary
and renamed files, each hunk's header - around hunk lines laid out by a `DiffHunkLayout`: split, old and new side by
side, or unified, one beneath the other with every line given the full width.
"""
from .... import lang as _lang


with _lang.auto_proxy_init(globals()):
    from .highlighting import (  # noqa
        CodeHighlighter,
        HighlightedLines,
        DiffCodeHighlighter,
    )

    from .layouts import (  # noqa
        DiffFileLines,
        DiffHunkLayout,
    )

    from .options import (  # noqa
        DiffLayout,
        DIFF_LAYOUTS,
        DiffContextLimits,
        DiffStyledDocOptions,
    )

    from .rendering import (  # noqa
        build_diff_hunk_layout,
        DiffStyledDocRenderer,
        render_diff_styled_doc,
    )

    from .sources import (  # noqa
        DiffFileTexts,
        DiffFileSource,
        texts_match_hunks,
        DictDiffFileSource,
        FilesystemDiffFileSource,
    )

    from .split import (  # noqa
        SplitDiffHunkLayout,
    )

    from .unified import (  # noqa
        UnifiedDiffHunkLayout,
    )
