import typing as ta

from omcore import dataclasses as dc

from .manifests import validate_lock
from .manifests import validate_manifest
from .models import RegistryConfig
from .models import RegistryPackage
from .models import RegistryPackageRequest
from .models import RegistryPackageVersion
from .models import RegistryVersionRequest
from .models import ResolveRequest
from .models import ResolveResult
from .models import VendorLock
from .models import VersionResolveRequest
from .models import VersionResolveResult
from .registry import fetch_package
from .registry import fetch_version
from .semver import satisfies
from .semver import sort_versions


##


@dc.dataclass(frozen=True)
class _Constraint:
    expression: str
    source: str


class _ResolutionConflictError(Exception):
    pass


class _RegistryPackages(ta.Mapping[str, RegistryPackage]):
    def __init__(self, config: RegistryConfig) -> None:
        self._config = config
        self._packages: dict[str, RegistryPackage] = {}

    def __getitem__(self, name: str) -> RegistryPackage:
        try:
            return self._packages[name]
        except KeyError:
            package = fetch_package(RegistryPackageRequest(name=name, config=self._config))
            self._packages[name] = package
            return package

    def __iter__(self) -> ta.Iterator[str]:
        return iter(self._packages)

    def __len__(self) -> int:
        return len(self._packages)


def _matches(version: str, constraints: tuple[_Constraint, ...], /) -> bool:
    for constraint in constraints:
        try:
            if not satisfies(version, constraint.expression):
                return False
        except ValueError as exc:
            raise ValueError(
                f'Invalid npm version requirement from {constraint.source}: {constraint.expression}',
            ) from exc

    return True


def _candidates(
        package: RegistryPackage,
        constraints: tuple[_Constraint, ...],
) -> tuple[RegistryPackageVersion, ...]:
    by_version = {version.version: version for version in package.versions}
    return tuple(
        by_version[version]
        for version in sort_versions(list(by_version), reverse=True)
        if _matches(version, constraints)
    )


def _add_constraint(
        constraints: dict[str, tuple[_Constraint, ...]],
        name: str,
        expression: str,
        source: str,
) -> None:
    constraints[name] = (*constraints.get(name, ()), _Constraint(expression=expression, source=source))


def _verify_assignments(
        assignments: dict[str, RegistryPackageVersion],
        constraints: dict[str, tuple[_Constraint, ...]],
        optional_constraints: dict[str, tuple[_Constraint, ...]],
) -> bool:
    return all(
        _matches(
            package.version,
            (*constraints[name], *optional_constraints.get(name, ())),
        )
        for name, package in assignments.items()
    )


def _solve(
        packages: ta.Mapping[str, RegistryPackage],
        assignments: dict[str, RegistryPackageVersion],
        constraints: dict[str, tuple[_Constraint, ...]],
        optional_constraints: dict[str, tuple[_Constraint, ...]],
) -> dict[str, RegistryPackageVersion]:
    unresolved = [name for name in constraints if name not in assignments]
    if not unresolved:
        return assignments

    choices = []
    for name in unresolved:
        applicable = (*constraints[name], *optional_constraints.get(name, ()))
        candidates = _candidates(packages[name], applicable)
        if not candidates:
            description = '; '.join(f'{item.source} requires {name}@{item.expression}' for item in applicable)
            raise _ResolutionConflictError(f'No single version satisfies: {description}')
        choices.append((len(candidates), name, candidates))

    _, name, candidates = min(choices, key=lambda item: (item[0], item[1]))
    last_conflict: _ResolutionConflictError | None = None
    for candidate in candidates:
        next_assignments = {**assignments, name: candidate}
        next_constraints = constraints.copy()
        next_optional = optional_constraints.copy()
        source = f'{candidate.name}@{candidate.version}'

        for dependency, expression in candidate.dependencies.items():
            _add_constraint(next_constraints, dependency, expression, source)
        for peer, expression in candidate.peer_dependencies.items():
            if peer in candidate.optional_peer_dependencies:
                _add_constraint(next_optional, peer, expression, f'{source} (optional peer)')
            else:
                _add_constraint(next_constraints, peer, expression, f'{source} (peer)')

        if not _verify_assignments(next_assignments, next_constraints, next_optional):
            continue

        try:
            return _solve(packages, next_assignments, next_constraints, next_optional)
        except _ResolutionConflictError as exc:
            last_conflict = exc

    if last_conflict is not None:
        raise last_conflict

    raise _ResolutionConflictError(f'No viable version of {name} satisfies the complete dependency graph')


def resolve_versions(request: VersionResolveRequest, /) -> VersionResolveResult:
    validate_manifest(request.manifest)
    constraints: dict[str, tuple[_Constraint, ...]] = {}
    for root in request.manifest.roots:
        _add_constraint(constraints, root.name, root.version, 'root manifest')

    try:
        assignments = _solve(request.packages, {}, constraints, {})
    except _ResolutionConflictError as exc:
        raise ValueError(str(exc)) from None

    return VersionResolveResult(
        packages=tuple(assignments[name] for name in sorted(assignments)),
    )


def resolve(request: ResolveRequest, /) -> ResolveResult:
    selected = resolve_versions(VersionResolveRequest(
        manifest=request.manifest,
        packages=_RegistryPackages(request.registry),
    ))

    packages = tuple(
        fetch_version(RegistryVersionRequest(
            name=package.name,
            version=package.version,
            config=request.registry,
        ))
        for package in selected.packages
    )

    lock = VendorLock(
        format_version=2,
        roots=request.manifest.roots,
        packages=packages,
        files={},
    )

    validate_lock(request.manifest, lock)

    return ResolveResult(lock=lock)
