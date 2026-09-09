import base64
import binascii
import posixpath
import re
import typing as ta
import urllib.parse

from omcore.formats.json import all as json

from .models import ResolvedPackage
from .models import RootPackage
from .models import VendorLock
from .models import VendorManifest
from .semver import parse
from .semver import satisfies


##


def load_manifest(path: str, /) -> VendorManifest:
    with open(path, encoding='utf-8') as file:
        value = json.load(file)

    if (
            not isinstance(value, dict) or
            value.get('format_version') != 2 or
            not isinstance(value.get('roots'), list)
    ):
        raise ValueError('Unsupported vendor manifest')

    return VendorManifest(
        format_version=2,
        roots=tuple(RootPackage(**package) for package in value['roots']),
    )


def render_manifest(manifest: VendorManifest, /) -> bytes:
    value = {
        'format_version': manifest.format_version,
        'roots': [
            {
                'name': root.name,
                'version': root.version,
            }
            for root in manifest.roots
        ],
    }
    return (json.dumps_pretty(value) + '\n').encode()


def load_lock(path: str, /) -> VendorLock:
    with open(path, encoding='utf-8') as file:
        value = json.load(file)

    if (
            not isinstance(value, dict) or
            value.get('format_version') != 2 or
            not isinstance(value.get('roots'), list) or
            not isinstance(value.get('packages'), list) or
            not isinstance(value.get('files'), dict)
    ):
        raise ValueError('Unsupported vendor lock')

    return VendorLock(
        format_version=2,
        roots=tuple(RootPackage(**package) for package in value['roots']),
        packages=tuple(ResolvedPackage(
            name=package['name'],
            version=package['version'],
            license=package['license'],
            integrity=package['integrity'],
            url=package['url'],
            dependencies=package.get('dependencies', {}),
            peer_dependencies=package.get('peer_dependencies', {}),
            optional_peer_dependencies=frozenset(package.get('optional_peer_dependencies', ())),
        ) for package in value['packages']),
        files=value['files'],
    )


def validate_manifest(manifest: VendorManifest, /) -> None:
    if manifest.format_version != 2:
        raise ValueError('Unsupported vendor manifest version')

    root_names: set[str] = set()
    for root in manifest.roots:
        _validate_package_name(root.name)
        if not isinstance(root.version, str) or not root.version:
            raise ValueError(f'Invalid root package requirement for {root.name}')
        try:
            satisfies('0.0.0', root.version)
        except ValueError as exc:
            raise ValueError(f'Invalid root package requirement for {root.name}: {root.version}') from exc
        if root.name in root_names:
            raise ValueError(f'Duplicate root package in vendor manifest: {root.name}')
        root_names.add(root.name)


def _validate_package_name(name: str, /) -> None:
    if not isinstance(name, str):
        raise TypeError('Package name is not a string')
    parts = name.split('/')
    if name.startswith('@'):
        valid = len(parts) == 2 and len(parts[0]) > 1 and bool(parts[1])
    else:
        valid = len(parts) == 1 and bool(name) and not name.startswith('@')
    if (
            not valid or
            len(name) > 214 or
            any(re.fullmatch(r'@?[A-Za-z0-9._~-]+', part) is None for part in parts) or
            any(part in ('.', '..') for part in parts)
    ):
        raise ValueError(f'Invalid npm package name: {name}')


def _validate_requirements(value: object, field: str, package: str, /) -> None:
    if not isinstance(value, ta.Mapping):
        raise TypeError(f'Invalid {field} in vendor lock for {package}')
    if not all(isinstance(name, str) and isinstance(expression, str) for name, expression in value.items()):
        raise TypeError(f'Invalid {field} in vendor lock for {package}')
    for name, expression in value.items():
        _validate_package_name(name)
        try:
            satisfies('0.0.0', expression)
        except ValueError as exc:
            raise ValueError(f'Invalid {field} requirement in vendor lock for {package}: {name}@{expression}') from exc


def _validate_package(package: ResolvedPackage, /) -> None:
    _validate_package_name(package.name)
    parse(package.version)
    if not isinstance(package.license, str) or not package.license:
        raise ValueError(f'Invalid license in vendor lock for {package.name}')
    try:
        algorithm, encoded = package.integrity.split('-', 1)
        digest = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f'Invalid archive integrity in vendor lock for {package.name}') from exc
    if algorithm != 'sha512' or len(digest) != 64:
        raise ValueError(f'Invalid archive integrity in vendor lock for {package.name}')
    parsed_url = urllib.parse.urlsplit(package.url)
    if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
        raise ValueError(f'Invalid archive URL in vendor lock for {package.name}: {package.url}')
    _validate_requirements(package.dependencies, 'dependencies', package.name)
    _validate_requirements(package.peer_dependencies, 'peer dependencies', package.name)
    if not all(isinstance(name, str) for name in package.optional_peer_dependencies):
        raise TypeError(f'Invalid optional peers in vendor lock for {package.name}')


def _validate_files(files: object, /) -> None:
    if not isinstance(files, ta.Mapping):
        raise TypeError('Invalid files in vendor lock')
    for relative, digest in files.items():
        if (
                not isinstance(relative, str) or
                not relative or
                relative == 'lock.json' or
                relative.startswith('/') or
                '\\' in relative or
                relative != posixpath.normpath(relative) or
                any(part in ('', '.', '..') for part in relative.split('/'))
        ):
            raise ValueError(f'Unsafe file path in vendor lock: {relative}')
        if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            raise ValueError(f'Invalid file checksum in vendor lock: {relative}')


def validate_lock(manifest: VendorManifest, lock: VendorLock, /) -> None:
    validate_manifest(manifest)
    if lock.format_version != 2:
        raise ValueError('Unsupported vendor lock version')
    if lock.roots != manifest.roots:
        raise ValueError('Vendor lock roots do not match the source manifest')
    _validate_files(lock.files)

    versions: dict[str, str] = {}
    for package in lock.packages:
        _validate_package(package)
        if package.name in versions:
            raise ValueError(f'Duplicate package in vendor lock: {package.name}')
        versions[package.name] = package.version
    if [package.name for package in lock.packages] != sorted(versions):
        raise ValueError('Vendor lock packages are not sorted by name')

    for root in manifest.roots:
        resolved = versions.get(root.name)
        if resolved is None or not satisfies(resolved, root.version):
            raise ValueError(f'Vendor lock does not resolve root package: {root.name}@{root.version}')

    for package in lock.packages:
        if not package.optional_peer_dependencies <= package.peer_dependencies.keys():
            raise ValueError(f'Vendor lock has invalid optional peers for {package.name}@{package.version}')
        requirements = (
            *package.dependencies.items(),
            *(
                (name, expression)
                for name, expression in package.peer_dependencies.items()
                if name not in package.optional_peer_dependencies or name in versions
            ),
        )
        for name, expression in requirements:
            resolved = versions.get(name)
            if resolved is None or not satisfies(resolved, expression):
                raise ValueError(
                    f'Vendor lock does not resolve requirement: '
                    f'{package.name}@{package.version} requires {name}@{expression}',
                )

    packages = {package.name: package for package in lock.packages}
    reachable = {root.name for root in manifest.roots}
    pending = list(reachable)
    while pending:
        package = packages[pending.pop()]
        required_names = set(package.dependencies)
        required_names.update(
            name
            for name in package.peer_dependencies
            if name not in package.optional_peer_dependencies or name in versions
        )
        for name in required_names - reachable:
            reachable.add(name)
            pending.append(name)
    extras = sorted(versions.keys() - reachable)
    if extras:
        raise ValueError(f'Vendor lock contains packages outside the resolved closure: {", ".join(extras)}')
