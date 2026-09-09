import hashlib
import os
import stat
import typing as ta

from omcore.formats.json import all as json

from .exports import output_package_exports
from .exports import read_package_exports
from .licenses import validate_license
from .manifests import validate_lock
from .models import GraphVerifyRequest
from .models import ResolvedPackage
from .models import VerifyRequest
from .models import VerifyResult
from .modules import package_directory
from .modules import verify_graph
from .outputs import build_notices
from .outputs import render_lock


##


def _walk_files(root: str, /) -> frozenset[str]:
    files: set[str] = set()
    for directory, directories, names in os.walk(root):
        for name in (*directories, *names):
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root).replace(os.sep, '/')
            mode = os.stat(path, follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f'Symbolic link is not allowed in vendor tree: {relative}')
            if name in names and not stat.S_ISREG(mode):
                raise ValueError(f'Special file is not allowed in vendor tree: {relative}')
        files.update(
            os.path.relpath(os.path.join(directory, name), root).replace(os.sep, '/')
            for name in names
        )
    return frozenset(files)


def _read(root: str, relative: str, /) -> bytes:
    with open(os.path.join(root, *relative.split('/')), 'rb') as file:
        return file.read()


def _requirements(metadata: ta.Mapping[str, ta.Any], field: str, package: str, /) -> dict[str, str]:
    value = metadata.get(field, {})
    if not isinstance(value, dict) or not all(
            isinstance(name, str) and isinstance(expression, str)
            for name, expression in value.items()
    ):
        raise ValueError(f'Invalid {field} in vendored package metadata: {package}')
    return value


def _optional_peers(metadata: ta.Mapping[str, ta.Any], package: str, /) -> frozenset[str]:
    value = metadata.get('peerDependenciesMeta', {})
    if not isinstance(value, dict):
        raise TypeError(f'Invalid peerDependenciesMeta in vendored package metadata: {package}')
    return frozenset(
        name
        for name, peer_metadata in value.items()
        if isinstance(name, str) and isinstance(peer_metadata, dict) and peer_metadata.get('optional') is True
    )


def _verify_root_export(
        package: ResolvedPackage,
        metadata: ta.Mapping[str, ta.Any],
        package_files: ta.AbstractSet[str],
) -> None:
    exports = read_package_exports(metadata, package.name)
    exports = output_package_exports(exports, root_alias='.' in exports.entries)
    modules = {name for name in package_files if name.endswith(('.js', '.mjs'))}
    root_target = exports.entries.get('.')
    if root_target is None:
        raise ValueError(f'Root package has no browser export: {package.name}')
    if root_target not in modules:
        raise ValueError(f'Vendored root export does not exist for {package.name}: {root_target}')


def _verify_package(
        root: str,
        package: ResolvedPackage,
        files: ta.AbstractSet[str],
        *,
        root_package: bool,
) -> None:
    package_root = package_directory(package.name)
    prefix = package_root + '/'
    package_files = {
        relative.removeprefix(prefix)
        for relative in files
        if relative.startswith(prefix)
    }
    metadata_path = prefix + 'package.json'

    try:
        metadata = json.loads(_read(root, metadata_path))
    except (KeyError, json.DecodeError) as exc:
        raise ValueError(f'Invalid vendored package metadata for {package.name}') from exc

    if not isinstance(metadata, dict):
        raise TypeError(f'Invalid vendored package metadata for {package.name}')

    if (
            metadata.get('name') != package.name or
            metadata.get('version') != package.version or
            metadata.get('license') != package.license
    ):
        raise ValueError(f'Vendored package identity does not match lock: {package.name}')

    if _requirements(metadata, 'dependencies', package.name) != package.dependencies:
        raise ValueError(f'Vendored package dependencies do not match lock: {package.name}')

    if _requirements(metadata, 'peerDependencies', package.name) != package.peer_dependencies:
        raise ValueError(f'Vendored package peer dependencies do not match lock: {package.name}')

    if _optional_peers(metadata, package.name) != package.optional_peer_dependencies:
        raise ValueError(f'Vendored package optional peers do not match lock: {package.name}')

    package_data = {
        relative: _read(root, prefix + relative)
        for relative in package_files
    }

    validate_license(package, metadata, package_data)

    if root_package:
        _verify_root_export(package, metadata, package_files)


def _verify_layout(packages: tuple[ResolvedPackage, ...], files: ta.AbstractSet[str], /) -> None:
    prefixes = tuple(package_directory(package.name) + '/' for package in packages)
    unowned = sorted(
        relative
        for relative in files
        if relative != 'THIRD_PARTY.md' and not any(relative.startswith(prefix) for prefix in prefixes)
    )
    if unowned:
        raise ValueError(f'Vendored files are outside locked package directories: {", ".join(unowned)}')


def verify(request: VerifyRequest, /) -> VerifyResult:
    validate_lock(request.manifest, request.lock)
    if os.path.islink(request.destination) or not os.path.isdir(request.destination):
        raise ValueError(f'Vendor destination is not a regular directory: {request.destination}')

    actual_files = _walk_files(request.destination)
    if 'lock.json' not in actual_files:
        raise ValueError('Vendored lock file is missing')
    if _read(request.destination, 'lock.json') != render_lock(request.lock):
        raise ValueError('Vendored lock file is not the canonical requested lock')

    files = set(request.lock.files)
    unlocked_files = actual_files - {'lock.json'}
    if unlocked_files != files:
        missing = sorted(files - unlocked_files)
        unexpected = sorted(unlocked_files - files)
        details = []
        if missing:
            details.append(f'missing: {", ".join(missing)}')
        if unexpected:
            details.append(f'unexpected: {", ".join(unexpected)}')
        raise ValueError(f'Vendored file set does not match lock ({"; ".join(details)})')

    for relative, digest in request.lock.files.items():
        actual_digest = hashlib.sha256(_read(request.destination, relative)).hexdigest()
        if actual_digest != digest:
            raise ValueError(f'Vendored file checksum mismatch: {relative}')

    _verify_layout(request.lock.packages, files)

    if _read(request.destination, 'THIRD_PARTY.md') != build_notices(request.lock):
        raise ValueError('Vendored third-party notice does not match lock')

    root_names = {root.name for root in request.manifest.roots}
    for package in request.lock.packages:
        _verify_package(
            request.destination,
            package,
            files,
            root_package=package.name in root_names,
        )

    expected_metadata = {
        package_directory(package.name) + '/package.json'
        for package in request.lock.packages
    }
    actual_metadata = {
        relative
        for relative in files
        if relative.startswith('packages/') and relative.endswith('/package.json')
    }
    if actual_metadata != expected_metadata:
        raise ValueError('Vendored package metadata set does not match lock')

    graph = verify_graph(GraphVerifyRequest(root=request.destination))
    return VerifyResult(
        destination=request.destination,
        package_count=len(request.lock.packages),
        file_count=len(files) + 1,
        module_count=graph.module_count,
        import_count=graph.import_count,
    )
