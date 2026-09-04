# fmt: off
# ruff: noqa: I001
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(
        globals(),
        # disable=True,
        # eager=True,
):
    ##
    # controls

    from .controls.base import (  # noqa
        Control,
    )

    from .controls.static import (  # noqa
        Static,
    )

    from .controls.stacks import (  # noqa
        StackRegion,
        StackLayout,
        stack_layout,
        stack_frame,
    )

    from .controls.status import (  # noqa
        StatusBar,
    )

    from .controls.spinners import (  # noqa
        Spinner,
    )

    from .controls.textarea import (  # noqa
        LINENR_TAG,
        TextArea,
    )

    from .controls.history import (  # noqa
        InputHistory,
    )

    from .controls.suggestions import (  # noqa
        SuggestionItem,
        SuggestionsPopup,
    )

    from .controls.cards import (  # noqa
        CardState,
        TERMINAL_CARD_STATES,
        Card,
    )

    from .controls.markdown import (  # noqa
        MarkdownTail,
    )

    ##
    # docs

    from .docs.positions import (  # noqa
        Pos,
        SpanKind,
        Span,
    )

    from .docs.edits import (  # noqa
        TextEdit,
        AppliedEdit,
        remap_pos,
        remap_pos_through,
    )

    from .docs.documents import (  # noqa
        DocumentListener,
        Document,
    )

    from .docs.cursors import (  # noqa
        Cursor,
    )

    from .docs.searching import (  # noqa
        find_matches,
        next_match,
    )

    from .docs.highlighting import (  # noqa
        IncrementalHighlighter,
    )

    from .docs.treesitter import (  # noqa
        tree_sitter_available,
        TreeSitterHighlighter,
        get_tree_sitter_highlighter,
    )

    ##
    # events

    from .events.keys import (  # noqa
        Key,
        KeySpecError,
        parse_key,
        key_from_char,
        key_text,
    )

    from .events.types import (  # noqa
        Event,
        KeyEvent,
        PasteEvent,
        MouseEventKind,
        MouseEvent,
        FocusEvent,
        ResizeEvent,
        SuspendEvent,
        ResumeEvent,
        InputEofEvent,
        CursorPositionEvent,
        ModeReportEvent,
        KittyFlagsEvent,
        UnknownSequenceEvent,
    )

    from .events.parsing import (  # noqa
        ParseTimeoutError,
        EventParser,
    )

    from .events.xterm import (  # noqa
        ESCAPE_TIMEOUT_S,
        XtermEventParser,
    )

    from .events.keymaps import (  # noqa
        DEFAULT_CHORD_TIMEOUT_S,
        KeymapMatch,
        Keymap,
        KeymapMatcher,
    )

    ##
    # runtime

    from .runtime.asyncio import (  # noqa
        AsyncioTimer,
        AsyncioTimers,
        AsyncioDriver,
    )

    from .runtime.base import (  # noqa
        App,
    )

    from .runtime.jobcontrol import (  # noqa
        JobControl,
    )

    from .runtime.sync import (  # noqa
        SyncDriver,
    )

    from .runtime.timers import (  # noqa
        Timer,
        Timers,
    )

    ##
    # screens

    from .screens.cells import (  # noqa
        CursorXY,
        Cell,
        Line,
        EMPTY_LINE,
        Frame,
        EMPTY_FRAME,

        cells_from_text,
        line_from_segments,
        render_cells,
    )

    from .screens.diffs import (  # noqa
        LineUpdate,
        diff_lines,
        FrameDiff,
        diff_frames,
    )

    ##
    # surfaces

    from .surfaces.base import (  # noqa
        Surface,
    )

    from .surfaces.inlines import (  # noqa
        InlineSurface,
    )

    from .surfaces.alts import (  # noqa
        AltSurface,
    )

    from .surfaces.writers import (  # noqa
        TermWriter,
    )

    ##
    # text

    from .text.highlights.base import (  # noqa
        Highlighter,
        PythonHighlighter,
        DiffHighlighter,
        get_highlighter,
        highlight_code,
    )

    from .text.highlights.pygments import (  # noqa
        pygments_available,
        PygmentsHighlighter,
        get_pygments_highlighter,
    )

    #

    from .text.markdown.backends import (  # noqa
        MARKDOWN_BACKEND_NAMES,
        get_markdown_stream,
        parse_markdown_with,
    )

    from .text.markdown.base import (  # noqa
        MdBlock,
        MdHeading,
        MdParagraph,
        MdCode,
        MdQuote,
        MdListItem,
        MdList,
        MdRule,
        MdTableAlign,
        MdTableRow,
        MdTable,

        parse_markdown_lines,
        parse_markdown,
        parse_markdown_inlines,

        MarkdownStreamBackend,
        MarkdownStream,

        MarkdownCodeHighlighter,
        render_markdown_block,
        render_markdown_blocks,
    )

    from .text.markdown.markdownit import (  # noqa
        markdown_it_available,
        MarkdownItStream,
    )

    from .text.markdown.pdcmark import (  # noqa
        PdcmarkStream,
    )

    #

    from .text.colors import (  # noqa
        ColorDepth,
        Color,
        NamedColor,
        IndexedColor,
        RgbColor,

        parse_rgb,
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

    from .text.parts import (  # noqa
        TextParts,
        parts_to_segment_lines,
    )

    from .text.styles import (  # noqa
        Style,
        EMPTY_STYLE,
        StyleLike,
        Theme,
        EMPTY_THEME,
    )

    from .text.themes import (  # noqa
        PRIMARY,
        SECONDARY,
        FOREGROUND,
        BACKGROUND,
        SURFACE,
        WARNING,
        ERROR,

        TEXT_PRIMARY,
        TEXT_SECONDARY,
        TEXT_WARNING,
        TEXT_ERROR,

        MUTED,
        SUCCESS,
        STRING_GREEN,
        COMMENT_GREY,

        CODE_FG,
        CODE_INLINE_FG,
        CODE_INLINE_BG,
        QUOTE_BORDER,

        DARK_THEME,
        DEFAULT_THEME,
    )

    from .text.segments import (  # noqa
        Segments,
        SegmentRows,
        Segment,

        segments_text,
        split_segment_lines,
        styled_text_to_segment_lines,
    )

    from .text.rendering import (  # noqa
        render_ansi_segments,
        render_ansi_segment_rows,
        render_ansi_styled_text,
        render_ansi_styled_document,
    )

    from .text.wrap import (  # noqa
        wrap_segments,
    )

    from .text.sgr import (  # noqa
        RESET_SGR,
        style_sgr_params,
        style_sgr,
        sgr_transition,

        ANSI_ESCAPE_PAT,
        apply_sgr_params,
        parse_ansi_segments,
    )

    ##
    # tty

    from .tty.terminals import (  # noqa
        Tty,
    )

    ##
    # vim

    from . import vim  # noqa
