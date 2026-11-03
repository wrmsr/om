import os.path
import typing as ta

from omcore import cached


##


class LiteSourceMirror:
    """
    Mirrors source roots into a scratch directory such that lite modules can be imported under an old interpreter
    without executing the non-lite `__init__.py` modules above them.

    Directories which are lite packages (their `__init__.py` is itself lite-marked), or which contain no lite files at
    all, are symlinked wholesale. Any other directory with lite files somewhere beneath it is recreated for real, with
    its `__init__.py` replaced by an empty file and its remaining entries symlinked - non-lite siblings included, so a
    lite module importing one still fails as it should.

    All paths are relative to `src_dir`, which defaults to the current directory.
    """

    def __init__(
            self,
            roots: ta.Sequence[str],
            lite_files: ta.Iterable[str],
            *,
            src_dir: str | None = None,
    ) -> None:
        super().__init__()

        if isinstance(roots, str):
            raise TypeError(roots)

        self._roots = [os.path.normpath(r) for r in roots]
        self._lite_files = frozenset(os.path.normpath(f) for f in lite_files)
        self._src_dir = os.path.abspath(src_dir if src_dir is not None else os.getcwd())

    @property
    def roots(self) -> ta.Sequence[str]:
        return self._roots

    @property
    def lite_files(self) -> ta.AbstractSet[str]:
        return self._lite_files

    @property
    def src_dir(self) -> str:
        return self._src_dir

    #

    @cached.property
    def lite_package_dirs(self) -> ta.AbstractSet[str]:
        return frozenset(
            os.path.dirname(f)
            for f in self._lite_files
            if os.path.basename(f) == '__init__.py'
        )

    def is_in_lite_package(self, path: str) -> bool:
        return any(
            path == p or path.startswith(p + os.sep)
            for p in self.lite_package_dirs
        )

    @cached.property
    def materialized_dirs(self) -> ta.AbstractSet[str]:
        ret: set[str] = set()

        for f in self._lite_files:
            d = os.path.dirname(f)
            while d:
                if not self.is_in_lite_package(d):
                    ret.add(d)
                d = os.path.dirname(d)

        return frozenset(ret)

    #

    def _write_empty_init(self, dst_dir: str) -> None:
        with open(os.path.join(dst_dir, '__init__.py'), 'w'):
            pass

    def _mirror_dir(self, rel: str, dst: str) -> None:
        src = os.path.join(self._src_dir, rel)

        if rel not in self.materialized_dirs:
            os.symlink(src, dst)
            return

        os.mkdir(dst)

        with os.scandir(src) as it:
            entries = sorted(it, key=lambda e: e.name)

        for e in entries:
            e_dst = os.path.join(dst, e.name)

            if e.name == '__pycache__':
                continue

            elif e.is_dir():
                self._mirror_dir(os.path.join(rel, e.name), e_dst)

            elif e.name == '__init__.py':
                self._write_empty_init(dst)

            else:
                os.symlink(e.path, e_dst)

    def build(self, dst_dir: str) -> None:
        for root in self._roots:
            # The parents of a nested root are not mirrored, just created as bare packages leading down to it.
            parent_rel = ''
            for part in os.path.dirname(root).split(os.sep):
                if not part:
                    continue

                parent_rel = os.path.join(parent_rel, part)
                parent_dst = os.path.join(dst_dir, parent_rel)
                if not os.path.lexists(parent_dst):
                    os.mkdir(parent_dst)
                    self._write_empty_init(parent_dst)

            dst = os.path.join(dst_dir, root)
            if not os.path.lexists(dst):
                self._mirror_dir(root, dst)
