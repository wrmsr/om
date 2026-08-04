import os.path
import subprocess
import tempfile

from omcore import dataclasses as dc
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from .errors import GitVendorSubprocessError


##


@dc.dataclass(frozen=True, kw_only=True)
class GitMergeFileResult:
    content: bytes
    conflicted: bool


def run_git_merge_file(
        base: bytes,
        ours: bytes,
        theirs: bytes,
        *,
        labels: tuple[str, str, str] = ('ours', 'base', 'theirs'),
        timeout: float = 5. * 60.,
) -> GitMergeFileResult:
    """
    Three-way merges the given file contents via `git merge-file -p`, returning the merged content - with standard
    conflict markers if conflicted. An empty `base` yields a two-way whole-file conflict, matching git's 'both added'
    behavior.
    """

    ours_label, base_label, theirs_label = labels

    with tempfile.TemporaryDirectory() as tmp_dir:
        names = []
        for name, data in [('ours', ours), ('base', base), ('theirs', theirs)]:
            file_path = os.path.join(tmp_dir, name)
            with open(file_path, 'wb') as f:
                f.write(data)
            names.append(file_path)

        proc = subprocess.run(  # noqa
            subprocess_maybe_shell_wrap_exec(
                'git',
                'merge-file',
                '-p',
                '-L', ours_label,
                '-L', base_label,
                '-L', theirs_label,
                *names,
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

    # merge-file's returncode is the number of conflicts, or negative (observed as >127) on error.
    if proc.returncode > 127:
        raise GitVendorSubprocessError(
            ['git', 'merge-file'],
            proc.returncode,
            proc.stderr.decode(errors='replace').strip(),
        )

    return GitMergeFileResult(
        content=proc.stdout,
        conflicted=proc.returncode != 0,
    )
