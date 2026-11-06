import glob
import os.path
import typing as ta

from omcore import dataclasses as dc

from .. import magic


##


@dc.dataclass(frozen=True)
class LiteSourceTarget:
    path: str
    kind: ta.Literal['script', 'module']


@dc.dataclass(frozen=True)
class LiteSourceDiscovery:
    lite_files: ta.AbstractSet[str]
    targets: ta.Sequence[LiteSourceTarget]


def discover_lite_sources(roots: ta.Sequence[str]) -> LiteSourceDiscovery:
    lite_files = frozenset(magic.find_magic_files(
        magic.PY_MAGIC_STYLE,
        roots,
        keys=['@om-lite'],
    ))

    # A module both carrying its own marker and sitting under a lite-marked package is reached both ways, hence the set.
    targets: set[LiteSourceTarget] = set()

    for fp in sorted(lite_files):
        with open(fp) as f:
            src = f.read()

        is_script = '# @om-script' in src.splitlines()

        if is_script:
            targets.add(LiteSourceTarget(fp, 'script'))

        elif fp.endswith('__init__.py'):
            for g in glob.glob(os.path.join(os.path.dirname(fp), '**/*.py'), recursive=True):
                targets.add(LiteSourceTarget(g, 'module'))

        else:
            targets.add(LiteSourceTarget(fp, 'module'))

    return LiteSourceDiscovery(
        lite_files,
        sorted(targets, key=lambda t: (t.path, t.kind)),
    )
