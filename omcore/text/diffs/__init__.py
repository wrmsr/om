# fmt: off
# ruff: noqa: I001
from ... import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from ... import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .newlines import (  # noqa
        split_newlines,
    )

    from .parsing import (  # noqa
        DiffParseError,

        ReconstructedFileView,
        ReconstructedFilePair,
        reconstruct_file_pair_from_hunks,
        apply_hunks_to_old_lines,
        parse_patch,
    )

    from .rendering import (  # noqa
        PatchRenderOptions,
        PatchSetRenderer,
    )

    from .styled import (  # noqa
        DiffLayout,
        DIFF_LAYOUTS,
        DiffStyledDocOptions,

        DiffHunkLayout,
        SplitDiffHunkLayout,
        UnifiedDiffHunkLayout,

        DiffFileTexts,
        DiffFileSource,
        DictDiffFileSource,
        FilesystemDiffFileSource,

        DiffStyledDocRenderer,
        render_diff_styled_doc,
    )

    from .term import (  # noqa
        render_diff_ansi,
    )

    from . import themes  # noqa

    from .types import (  # noqa
        HunkLineKind,
        ExtendedHeaderKind,
        SourceSpan,
        ExtendedHeader,
        DiffGitHeader,
        IndexHeader,
        ModeHeader,
        PathHeader,
        ScoreHeader,
        BinaryFilesHeader,
        GitBinaryPatchHeader,
        FileHeader,
        HunkLine,
        Hunk,
        GitBinaryPatchRecord,
        GitBinaryPatchData,
        FilePatch,
        PatchSet,
    )
