import contextlib
import shutil
import tempfile
import typing as ta

from .runners import GitRunner


##


@contextlib.contextmanager
def git_upstream_source(
        url: str,
        *,
        from_path: str | None = None,
        timeout: float = 15. * 60.,
) -> ta.Generator[GitRunner]:
    """
    Yields a GitRunner for the upstream repo - either an existing local clone (used strictly read-only) or a temporary
    bare clone of `url` which is removed afterward.
    """

    if from_path is not None:
        yield GitRunner(from_path, timeout=timeout)
        return

    tmp_dir = tempfile.mkdtemp(prefix='om-git-vendor-')
    try:
        runner = GitRunner(tmp_dir, timeout=timeout)
        runner.run('clone', '--bare', '--quiet', '--', url, '.')
        yield runner
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
