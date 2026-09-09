import typing as ta
import urllib.error
import urllib.parse
import urllib.request

from omcore.formats.json import all as json

from .licenses import normalize_license
from .models import RegistryConfig
from .models import RegistryPackage
from .models import RegistryPackageRequest
from .models import RegistryPackageVersion
from .models import RegistryVersionRequest
from .models import ResolvedPackage
from .semver import parse


##


_INSTALL_ACCEPT = 'application/vnd.npm.install-v1+json; q=1.0, application/json; q=0.8, */*'


def _requirements(value: ta.Any, field: str, package: str, /) -> dict[str, str]:
    if value is None:
        return {}
    if (
            not isinstance(value, dict) or
            not all(isinstance(name, str) and isinstance(item, str) for name, item in value.items())
    ):
        raise ValueError(f'Invalid {field} metadata for {package}')
    return dict(sorted(value.items()))


def _dependencies(metadata: ta.Mapping[str, ta.Any], package: str, /) -> dict[str, str]:
    # The registry merges `optionalDependencies` into `dependencies` when a package is published, but the archived
    # package.json keeps them apart. Optional dependencies are never required, so they are removed here to keep the
    # lock consistent with the archive and out of the resolved closure.
    optional = _requirements(metadata.get('optionalDependencies'), 'optionalDependencies', package)
    return {
        name: expression
        for name, expression in _requirements(metadata.get('dependencies'), 'dependencies', package).items()
        if name not in optional
    }


def _optional_peers(value: ta.Any, package: str, /) -> frozenset[str]:
    if value is None:
        return frozenset()
    if not isinstance(value, dict):
        raise TypeError(f'Invalid peerDependenciesMeta metadata for {package}')
    return frozenset(
        name
        for name, metadata in value.items()
        if isinstance(name, str) and isinstance(metadata, dict) and metadata.get('optional') is True
    )


def _get_json(
        config: RegistryConfig,
        path: str,
        /,
        *,
        accept: str = 'application/json',
) -> ta.Mapping[str, ta.Any]:
    url = config.url.rstrip('/') + '/' + path
    request = urllib.request.Request(url, headers={  # noqa: S310
        'Accept': accept,
        'User-Agent': 'jsvendor/1',
    })
    try:
        with urllib.request.urlopen(request, timeout=config.timeout) as response:  # noqa: S310
            value = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise ValueError(f'npm registry request failed ({exc.code}): {url}') from exc
    except urllib.error.URLError as exc:
        raise ValueError(f'npm registry request failed: {url}: {exc.reason}') from exc

    if not isinstance(value, dict):
        raise TypeError(f'Invalid npm registry response: {url}')
    return value


def _package_path(name: str, /) -> str:
    return urllib.parse.quote(name, safe='')


def parse_package_document(value: ta.Mapping[str, ta.Any], name: str, /) -> RegistryPackage:
    if (
            value.get('name') != name or
            not isinstance(value.get('versions'), dict) or
            not isinstance(value.get('dist-tags'), dict)
    ):
        raise ValueError(f'Invalid npm package metadata for {name}')

    versions = []
    for version, metadata in value['versions'].items():
        if not isinstance(version, str) or not isinstance(metadata, dict):
            continue
        try:
            parse(version)
            versions.append(RegistryPackageVersion(
                name=name,
                version=version,
                dependencies=_dependencies(metadata, name),
                peer_dependencies=_requirements(metadata.get('peerDependencies'), 'peerDependencies', name),
                optional_peer_dependencies=_optional_peers(metadata.get('peerDependenciesMeta'), name),
            ))
        except (TypeError, ValueError):
            continue

    if not versions:
        raise ValueError(f'npm package has no usable semantic versions: {name}')
    return RegistryPackage(
        name=name,
        versions=tuple(versions),
        tags=_requirements(value['dist-tags'], 'dist-tags', name),
    )


def fetch_package(request: RegistryPackageRequest, /) -> RegistryPackage:
    value = _get_json(request.config, _package_path(request.name), accept=_INSTALL_ACCEPT)
    return parse_package_document(value, request.name)


def parse_version_document(value: ta.Mapping[str, ta.Any], name: str, version: str, /) -> ResolvedPackage:
    if value.get('name') != name or value.get('version') != version:
        raise ValueError(f'Invalid npm version metadata for {name}@{version}')

    license_value = normalize_license(value.get('license'))
    if license_value is None:
        raise TypeError(f'npm version has no SPDX license: {name}@{version}')

    dist = value.get('dist')
    if not isinstance(dist, dict):
        raise TypeError(f'npm version has no distribution metadata: {name}@{version}')
    integrity = dist.get('integrity')
    url = dist.get('tarball')
    if not isinstance(integrity, str) or not integrity.startswith('sha512-') or not isinstance(url, str):
        raise ValueError(f'npm version has no SHA-512 archive: {name}@{version}')

    return ResolvedPackage(
        name=name,
        version=version,
        license=license_value,
        integrity=integrity,
        url=url,
        dependencies=_dependencies(value, name),
        peer_dependencies=_requirements(value.get('peerDependencies'), 'peerDependencies', name),
        optional_peer_dependencies=_optional_peers(value.get('peerDependenciesMeta'), name),
    )


def fetch_version(request: RegistryVersionRequest, /) -> ResolvedPackage:
    path = _package_path(request.name) + '/' + urllib.parse.quote(request.version, safe='')
    value = _get_json(request.config, path)
    return parse_version_document(value, request.name, request.version)
