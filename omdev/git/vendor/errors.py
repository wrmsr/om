import typing as ta


##


class GitVendorError(Exception):
    pass


class GitVendorSubprocessError(GitVendorError):
    """Raised when an underlying git invocation fails unexpectedly."""

    def __init__(self, cmd: ta.Sequence[str], returncode: int, stderr: str) -> None:
        super().__init__(f'git command {list(cmd)!r} failed with returncode {returncode}: {stderr}')

        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr


class GitVendorDirtyError(GitVendorError):
    """Raised when the containing repo has changes which preclude beginning a vendor operation."""

    def __init__(self, paths: ta.Sequence[str]) -> None:
        super().__init__(f'Repo has blocking changes: {", ".join(paths)}')

        self.paths = paths


class GitVendorMergeInProgressError(GitVendorError):
    pass


class GitVendorNoMergeInProgressError(GitVendorError):
    pass


class GitVendorUpstreamRevError(GitVendorError):
    pass
