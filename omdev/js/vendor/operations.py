from .manifests import validate_lock
from .manifests import validate_manifest
from .models import AddRequest
from .models import ManifestUpdateResult
from .models import OutdatedPackage
from .models import OutdatedRequest
from .models import OutdatedResult
from .models import PackageArgument
from .models import RegistryConfig
from .models import RegistryPackage
from .models import RegistryPackageRequest
from .models import RemoveRequest
from .models import ResolveRequest
from .models import RootPackage
from .models import UpdateRequest
from .models import VendorManifest
from .registry import fetch_package
from .resolution import resolve
from .semver import satisfies
from .semver import sort_versions


##


def parse_package_argument(value: str, /) -> PackageArgument:
    separator = value.find('@', 1 if value.startswith('@') else 0)
    if separator < 0:
        name = value
        version = None
    else:
        name = value[:separator]
        version = value[separator + 1:]

    if not name or (name.startswith('@') and '/' not in name) or version == '':
        raise ValueError(f'Invalid package argument: {value}')
    return PackageArgument(name=name, version=version)


def _fetch(name: str, registry: RegistryConfig, /) -> RegistryPackage:
    return fetch_package(RegistryPackageRequest(name=name, config=registry))


def _tag(package: RegistryPackage, name: str, /) -> str:
    try:
        version = package.tags[name]
    except KeyError:
        raise ValueError(f'npm package has no {name!r} tag: {package.name}') from None
    if version not in {item.version for item in package.versions}:
        raise ValueError(f'npm package tag refers to an unavailable version: {package.name}@{name}')
    return version


def _requirement(argument: PackageArgument, registry: RegistryConfig, /) -> str:
    package = _fetch(argument.name, registry)
    if argument.version is None:
        return _tag(package, 'latest')
    if argument.version in package.tags:
        return _tag(package, argument.version)
    try:
        compatible = any(satisfies(item.version, argument.version) for item in package.versions)
    except ValueError as exc:
        raise ValueError(f'Invalid version requirement for {argument.name}: {argument.version}') from exc
    if not compatible:
        raise ValueError(f'No published version satisfies: {argument.name}@{argument.version}')
    return argument.version


def _resolved(manifest: VendorManifest, registry: RegistryConfig, /) -> ManifestUpdateResult:
    result = resolve(ResolveRequest(manifest=manifest, registry=registry))
    return ManifestUpdateResult(manifest=manifest, lock=result.lock)


def add(request: AddRequest, /) -> ManifestUpdateResult:
    validate_manifest(request.manifest)
    if not request.packages:
        raise ValueError('Add requires at least one package')

    roots = list(request.manifest.roots)
    names = {root.name for root in roots}
    for argument in request.packages:
        if argument.name in names:
            raise ValueError(f'Package is already a root; use update: {argument.name}')
        roots.append(RootPackage(
            name=argument.name,
            version=_requirement(argument, request.registry),
        ))
        names.add(argument.name)
    return _resolved(VendorManifest(format_version=2, roots=tuple(roots)), request.registry)


def update(request: UpdateRequest, /) -> ManifestUpdateResult:
    validate_manifest(request.manifest)
    roots = {root.name: root for root in request.manifest.roots}
    arguments = request.packages or tuple(PackageArgument(name=root.name) for root in request.manifest.roots)
    replacements: dict[str, RootPackage] = {}
    for argument in arguments:
        if argument.name not in roots:
            raise ValueError(f'Package is not a root; use add: {argument.name}')
        if argument.name in replacements:
            raise ValueError(f'Duplicate package argument: {argument.name}')
        replacements[argument.name] = RootPackage(
            name=argument.name,
            version=_requirement(argument, request.registry),
        )

    manifest = VendorManifest(
        format_version=2,
        roots=tuple(replacements.get(root.name, root) for root in request.manifest.roots),
    )
    return _resolved(manifest, request.registry)


def remove(request: RemoveRequest, /) -> ManifestUpdateResult:
    validate_manifest(request.manifest)
    if not request.packages:
        raise ValueError('Remove requires at least one package')
    if len(set(request.packages)) != len(request.packages):
        raise ValueError('Remove contains duplicate package names')

    roots = {root.name for root in request.manifest.roots}
    missing = [name for name in request.packages if name not in roots]
    if missing:
        raise ValueError(f'Package is not a root: {missing[0]}')
    removed = set(request.packages)
    manifest = VendorManifest(
        format_version=2,
        roots=tuple(root for root in request.manifest.roots if root.name not in removed),
    )
    return _resolved(manifest, request.registry)


def outdated(request: OutdatedRequest, /) -> OutdatedResult:
    validate_lock(request.manifest, request.lock)
    roots = {root.name: root for root in request.manifest.roots}
    names = request.packages or tuple(roots)
    if len(set(names)) != len(names):
        raise ValueError('Outdated contains duplicate package names')
    missing = [name for name in names if name not in roots]
    if missing:
        raise ValueError(f'Package is not a root: {missing[0]}')

    current = {package.name: package.version for package in request.lock.packages}
    packages = []
    for name in names:
        root = roots[name]
        package = _fetch(name, request.registry)
        compatible = [item.version for item in package.versions if satisfies(item.version, root.version)]
        if not compatible:
            raise ValueError(f'No published version satisfies: {root.name}@{root.version}')
        wanted = sort_versions(compatible, reverse=True)[0]
        latest = _tag(package, 'latest')
        if current[name] != wanted or current[name] != latest:
            packages.append(OutdatedPackage(
                name=name,
                requirement=root.version,
                current=current[name],
                wanted=wanted,
                latest=latest,
            ))
    return OutdatedResult(packages=tuple(packages))
