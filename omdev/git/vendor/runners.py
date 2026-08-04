import subprocess
import typing as ta

from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from .errors import GitVendorSubprocessError


##


class GitRunner:
    """Runs git commands against a single repo directory. Never mutates anything outside that repo."""

    def __init__(
            self,
            dir: str,  # noqa
            *,
            timeout: float = 5. * 60.,
    ) -> None:
        super().__init__()

        self._dir = dir
        self._timeout = timeout

    @property
    def dir(self) -> str:
        return self._dir

    def run(
            self,
            *args: str,
            input: bytes | None = None,  # noqa
            check_rc: bool = True,
    ) -> subprocess.CompletedProcess:
        proc = subprocess.run(  # noqa
            subprocess_maybe_shell_wrap_exec('git', *args),
            cwd=self._dir,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self._timeout,
        )

        if check_rc and proc.returncode != 0:
            raise GitVendorSubprocessError(
                ['git', *args],
                proc.returncode,
                proc.stderr.decode(errors='replace').strip(),
            )

        return proc

    def output(self, *args: str, input: bytes | None = None) -> bytes:  # noqa
        return self.run(*args, input=input).stdout

    def output_str(self, *args: str) -> str:
        return self.output(*args).decode().strip()

    #

    def rev_parse(self, rev: str) -> str:
        return self.output_str('rev-parse', '--verify', '--end-of-options', rev)

    def has_object(self, spec: str) -> bool:
        return self.run('cat-file', '-e', spec, check_rc=False).returncode == 0

    def try_read_blob(self, rev: str, path: str) -> bytes | None:
        if not self.has_object(f'{rev}:{path}'):
            return None
        return self.output('cat-file', 'blob', f'{rev}:{path}')

    def tree_mode(self, rev: str, path: str) -> str | None:
        out = self.output_str('ls-tree', '--full-tree', rev, '--', path)
        if not out:
            return None
        return out.split(' ', 1)[0]

    def write_blob(self, data: bytes) -> str:
        return self.output('hash-object', '-w', '--stdin', input=data).decode().strip()

    def update_index_info(self, lines: ta.Iterable[str]) -> None:
        self.run('update-index', '--index-info', input=''.join([f'{l}\n' for l in lines]).encode())
