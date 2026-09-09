import typing as ta
import urllib.error
import urllib.parse
import urllib.request

from omcore.formats.json import all as json

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


def fetch_package(request: RegistryPackageRequest, /) -> RegistryPackage:
    value = _get_json(request.config, _package_path(request.name), accept=_INSTALL_ACCEPT)
    if (
            value.get('name') != request.name or
            not isinstance(value.get('versions'), dict) or
            not isinstance(value.get('dist-tags'), dict)
    ):
        raise ValueError(f'Invalid npm package metadata for {request.name}')

    versions = []
    for version, metadata in value['versions'].items():
        if not isinstance(version, str) or not isinstance(metadata, dict):
            continue
        try:
            parse(version)
            versions.append(RegistryPackageVersion(
                name=request.name,
                version=version,
                dependencies=_requirements(metadata.get('dependencies'), 'dependencies', request.name),
                peer_dependencies=_requirements(metadata.get('peerDependencies'), 'peerDependencies', request.name),
                optional_peer_dependencies=_optional_peers(metadata.get('peerDependenciesMeta'), request.name),
            ))
        except (TypeError, ValueError):
            continue

    if not versions:
        raise ValueError(f'npm package has no usable semantic versions: {request.name}')
    return RegistryPackage(
        name=request.name,
        versions=tuple(versions),
        tags=_requirements(value['dist-tags'], 'dist-tags', request.name),
    )


def fetch_version(request: RegistryVersionRequest, /) -> ResolvedPackage:
    path = _package_path(request.name) + '/' + urllib.parse.quote(request.version, safe='')
    value = _get_json(request.config, path)
    if value.get('name') != request.name or value.get('version') != request.version:
        raise ValueError(f'Invalid npm version metadata for {request.name}@{request.version}')

    license_value = value.get('license')
    if isinstance(license_value, dict):
        license_value = license_value.get('type')
    if not isinstance(license_value, str):
        raise TypeError(f'npm version has no SPDX license: {request.name}@{request.version}')

    dist = value.get('dist')
    if not isinstance(dist, dict):
        raise TypeError(f'npm version has no distribution metadata: {request.name}@{request.version}')
    integrity = dist.get('integrity')
    url = dist.get('tarball')
    if not isinstance(integrity, str) or not integrity.startswith('sha512-') or not isinstance(url, str):
        raise ValueError(f'npm version has no SHA-512 archive: {request.name}@{request.version}')

    return ResolvedPackage(
        name=request.name,
        version=request.version,
        license=license_value,
        integrity=integrity,
        url=url,
        dependencies=_requirements(value.get('dependencies'), 'dependencies', request.name),
        peer_dependencies=_requirements(value.get('peerDependencies'), 'peerDependencies', request.name),
        optional_peer_dependencies=_optional_peers(value.get('peerDependenciesMeta'), request.name),
    )
