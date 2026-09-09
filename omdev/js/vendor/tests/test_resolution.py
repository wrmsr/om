import pytest

from ..models import RegistryPackage
from ..models import RegistryPackageVersion
from ..models import RootPackage
from ..models import VendorManifest
from ..models import VersionResolveRequest
from ..resolution import resolve_versions


##


def _version(
        name: str,
        version: str,
        *,
        dependencies: dict[str, str] | None = None,
        peers: dict[str, str] | None = None,
        optional_peers: frozenset[str] = frozenset(),
) -> RegistryPackageVersion:
    return RegistryPackageVersion(
        name=name,
        version=version,
        dependencies=dependencies or {},
        peer_dependencies=peers or {},
        optional_peer_dependencies=optional_peers,
    )


def _manifest(**roots: str) -> VendorManifest:
    return VendorManifest(
        format_version=2,
        roots=tuple(RootPackage(name=name.replace('_', '-'), version=version) for name, version in roots.items()),
    )


def test_resolve_versions_backtracks_to_one_compatible_version() -> None:
    packages = {
        'app-a': RegistryPackage(name='app-a', versions=(
            _version('app-a', '1.0.0', dependencies={'shared': '^1.0.0'}),
            _version('app-a', '2.0.0', dependencies={'shared': '^2.0.0'}),
        )),
        'app-b': RegistryPackage(name='app-b', versions=(
            _version('app-b', '1.0.0', dependencies={'shared': '^1.0.0'}),
        )),
        'shared': RegistryPackage(name='shared', versions=(
            _version('shared', '1.5.0'),
            _version('shared', '2.1.0'),
        )),
    }

    result = resolve_versions(VersionResolveRequest(
        manifest=_manifest(app_a='*', app_b='1.0.0'),
        packages=packages,
    ))

    assert [(package.name, package.version) for package in result.packages] == [
        ('app-a', '1.0.0'),
        ('app-b', '1.0.0'),
        ('shared', '1.5.0'),
    ]


def test_resolve_versions_includes_required_peer() -> None:
    packages = {
        'app': RegistryPackage(name='app', versions=(
            _version('app', '1.0.0', peers={'editor': '2.x'}),
        )),
        'editor': RegistryPackage(name='editor', versions=(
            _version('editor', '2.4.0'),
            _version('editor', '3.0.0'),
        )),
    }

    result = resolve_versions(VersionResolveRequest(manifest=_manifest(app='1.0.0'), packages=packages))

    assert [(package.name, package.version) for package in result.packages] == [
        ('app', '1.0.0'),
        ('editor', '2.4.0'),
    ]


def test_resolve_versions_does_not_install_optional_peer() -> None:
    packages = {
        'app': RegistryPackage(name='app', versions=(
            _version('app', '1.0.0', peers={'extra': '^1.0.0'}, optional_peers=frozenset({'extra'})),
        )),
    }

    result = resolve_versions(VersionResolveRequest(manifest=_manifest(app='1.0.0'), packages=packages))

    assert [(package.name, package.version) for package in result.packages] == [('app', '1.0.0')]


def test_resolve_versions_reports_single_version_conflict() -> None:
    packages = {
        'app-a': RegistryPackage(name='app-a', versions=(
            _version('app-a', '1.0.0', dependencies={'shared': '^1.0.0'}),
        )),
        'app-b': RegistryPackage(name='app-b', versions=(
            _version('app-b', '1.0.0', dependencies={'shared': '^2.0.0'}),
        )),
        'shared': RegistryPackage(name='shared', versions=(
            _version('shared', '1.5.0'),
            _version('shared', '2.1.0'),
        )),
    }

    with pytest.raises(ValueError, match='No single version satisfies'):
        resolve_versions(VersionResolveRequest(
            manifest=_manifest(app_a='1.0.0', app_b='1.0.0'),
            packages=packages,
        ))
