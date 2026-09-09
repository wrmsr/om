import base64

import pytest

from ..manifests import validate_lock
from ..models import ResolvedPackage
from ..models import RootPackage
from ..models import VendorLock
from ..models import VendorManifest


##


def test_validate_lock_rejects_unresolved_root() -> None:
    root = RootPackage(name='example', version='1.2.3')
    manifest = VendorManifest(format_version=2, roots=(root,))
    lock = VendorLock(format_version=2, roots=(root,), packages=(), files={})

    with pytest.raises(ValueError, match='does not resolve root package'):
        validate_lock(manifest, lock)


def test_validate_lock_rejects_stale_root_snapshot() -> None:
    manifest = VendorManifest(
        format_version=2,
        roots=(RootPackage(name='example', version='1.2.3'),),
    )
    lock = VendorLock(
        format_version=2,
        roots=(RootPackage(name='example', version='1.2.2'),),
        packages=(),
        files={},
    )

    with pytest.raises(ValueError, match='roots do not match'):
        validate_lock(manifest, lock)


def _package(name: str) -> ResolvedPackage:
    return ResolvedPackage(
        name=name,
        version='1.2.3',
        license='MIT',
        integrity='sha512-' + base64.b64encode(bytes(64)).decode('ascii'),
        url=f'https://example.invalid/{name}.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )


def test_validate_lock_rejects_packages_outside_dependency_closure() -> None:
    root = RootPackage(name='example', version='1.2.3')
    manifest = VendorManifest(format_version=2, roots=(root,))
    lock = VendorLock(
        format_version=2,
        roots=(root,),
        packages=(_package('example'), _package('extra')),
        files={},
    )

    with pytest.raises(ValueError, match='outside the resolved closure: extra'):
        validate_lock(manifest, lock)


@pytest.mark.parametrize(('files', 'message'), [
    ({'../outside.js': '0' * 64}, 'Unsafe file path'),
    ({'inside.js': 'not-a-digest'}, 'Invalid file checksum'),
])
def test_validate_lock_rejects_invalid_file_records(files: dict[str, str], message: str) -> None:
    root = RootPackage(name='example', version='1.2.3')
    manifest = VendorManifest(format_version=2, roots=(root,))
    lock = VendorLock(
        format_version=2,
        roots=(root,),
        packages=(_package('example'),),
        files=files,
    )

    with pytest.raises(ValueError, match=message):
        validate_lock(manifest, lock)
