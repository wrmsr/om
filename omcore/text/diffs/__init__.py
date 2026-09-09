from ... import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

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
        DiffStyledDocOptions,
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
