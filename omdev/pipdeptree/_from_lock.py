"""
Read a PEP 751 lock file (``pylock.toml``) and render its dependency tree.

This is the engine behind the ``from-lock`` CLI subcommand. A PEP 751 lock is *already resolved* -- it carries the
pinned packages, their versions, and the forward edges between them -- so rendering it is purely a TOML to
:class:`~pipdeptree._models.PackageDAG` mapping. There is no resolver, no network, and no package index involved,
which is why ``from-lock`` works fully offline and needs no optional extra.

The lock's ``packages`` array becomes :class:`~pipdeptree._synthetic_dist.SyntheticDistribution` objects (the same
adapter), so the existing DAG and every renderer work unchanged. Each package's
``dependencies`` array lists only child *names*; the child's version is looked up in the ``packages`` array by PEP 503
canonical name so an edge ``Foo_Bar`` matches a package ``foo-bar``.
"""
import importlib.metadata
import os
import tomllib
import typing as ta

from ..packaging.names import NormalizedName
from ..packaging.names import canonicalize_name
from ._synthetic_dist import SyntheticDistribution


##


class FromLockError(ValueError):
    """Raised when a PEP 751 lock file is missing or cannot be parsed into a dependency tree."""


def load_lock(path: str | os.PathLike[str]) -> list[importlib.metadata.Distribution]:
    """
    Parse a PEP 751 ``pylock.toml`` into Distribution-like objects ready for the existing DAG pipeline.

    :param path: the ``pylock.toml`` lock file to read.
    :returns: a list of :class:`importlib.metadata.Distribution` look-alikes ready for
        :meth:`pipdeptree._models.PackageDAG.from_pkgs`.
    :raises FromLockError: if the file is missing, is not valid TOML, lacks a ``packages`` array, or has a package
        without a ``name``.
    """

    path = os.fspath(path)
    if not os.path.isfile(path):
        msg = f'lock file does not exist: {path}'
        raise FromLockError(msg)

    try:
        with open(path, 'rb') as file:  # noqa: PTH123
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        msg = f'not a valid PEP 751 lock file: {path} (malformed TOML: {exc})'
        raise FromLockError(msg) from exc
    except OSError as exc:
        msg = f'cannot read lock file: {path} ({exc})'
        raise FromLockError(msg) from exc

    packages = data.get('packages')
    if not isinstance(packages, list):
        msg = f"not a valid PEP 751 lock file: {path} (missing 'packages' array)"
        raise FromLockError(msg)

    # Versions are looked up by canonical name so an edge can reference a package under any casing/separator spelling;
    # a package may legitimately lack a version (VCS/local/directory pins), in which case its edges render unpinned.
    versions = {canonicalize_name(name): str(pkg.get('version', '')) for name, pkg in _named(packages, path)}
    return [
        SyntheticDistribution(name, str(pkg.get('version', '')), _children(pkg.get('dependencies', ()), versions))
        for name, pkg in _named(packages, path)
    ]


def _named(packages: list[ta.Any], path: str) -> list[tuple[str, dict[str, ta.Any]]]:
    named: list[tuple[str, dict[str, ta.Any]]] = []
    for pkg in packages:
        if not isinstance(pkg, dict) or 'name' not in pkg:
            msg = f"not a valid PEP 751 lock file: {path} (a package entry is missing 'name')"
            raise FromLockError(msg)
        named.append((str(pkg['name']), pkg))
    return named


def _children(dependencies: ta.Any, versions: dict[NormalizedName, str]) -> tuple[str, ...]:
    # A leaf omits the ``dependencies`` key entirely, so the default () yields no edges. Each edge carries only the
    # child name; pin it from the looked-up version when known, else emit a bare requirement.
    children: list[str] = []
    for dep in dependencies:
        child = str(dep['name'])
        children.append(f'{child}=={version}' if (version := versions.get(canonicalize_name(child))) else child)
    return tuple(children)
