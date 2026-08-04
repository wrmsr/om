import difflib
import os.path

from .errors import GitVendorUpstreamRevError
from .specs import load_vendor_spec
from .upstreams import git_upstream_source


##


class GitVendorDiffer:
    """
    Renders a unified diff of the local vendored files against their pristine upstream contents at the spec's recorded
    rev - that is, the accumulated local patches. Requires upstream access (a local clone via `from_path`, or a
    temporary clone of the spec url) since pristine content is deliberately not stored in the repo.
    """

    def __init__(
            self,
            repo_dir: str,
            vendor_dir: str,
            *,
            from_path: str | None = None,
    ) -> None:
        super().__init__()

        self._repo_dir = repo_dir
        self._vendor_dir = vendor_dir.rstrip('/')
        self._from_path = from_path

        self._abs_vendor_dir = os.path.join(repo_dir, self._vendor_dir)

    def diff(self) -> str:
        spec = load_vendor_spec(self._abs_vendor_dir)
        if spec.rev is None:
            raise GitVendorUpstreamRevError(f'{self._vendor_dir} has no recorded rev - it has never been pulled')

        out: list[str] = []

        with git_upstream_source(spec.url, from_path=self._from_path) as upstream:
            if not upstream.has_object(spec.rev + '^{commit}'):
                raise GitVendorUpstreamRevError(f'Base rev {spec.rev!r} is not present in upstream {upstream.dir}')

            for path in spec.files:
                base = upstream.try_read_blob(spec.rev, path)

                try:
                    with open(os.path.join(self._abs_vendor_dir, path), 'rb') as f:
                        ours = f.read()
                except FileNotFoundError:
                    ours = None

                if base == ours:
                    continue

                out.extend(difflib.unified_diff(
                    (base or b'').decode('utf-8', errors='replace').splitlines(keepends=True),
                    (ours or b'').decode('utf-8', errors='replace').splitlines(keepends=True),
                    fromfile=f'a/{path}',
                    tofile=f'b/{path}',
                ))

        return ''.join(out)
