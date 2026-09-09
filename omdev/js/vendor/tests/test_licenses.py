import pytest

from ..licenses import normalize_license
from ..licenses import validate_license
from ..models import ResolvedPackage


##


def _package(license_name: str) -> ResolvedPackage:
    return ResolvedPackage(
        name='example',
        version='1.2.3',
        license=license_name,
        integrity='sha512-unused',
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )


@pytest.mark.parametrize(('value', 'expected'), [
    ('MIT', 'MIT'),
    ({'type': 'BSD-3-Clause', 'url': 'https://example.invalid/LICENSE'}, 'BSD-3-Clause'),
    ({'url': 'https://example.invalid/LICENSE'}, None),
    ({'type': ['MIT']}, None),
    (['MIT'], None),
    (None, None),
])
def test_normalize_license(value: object, expected: str | None) -> None:
    assert normalize_license(value) == expected


def test_validate_license_accepts_legacy_object_form() -> None:
    validate_license(
        _package('MIT'),
        {'license': {'type': 'MIT', 'url': 'https://example.invalid/LICENSE'}},
        {'LICENSE': b'MIT'},
    )


@pytest.mark.parametrize('metadata', [
    {'license': {'type': 'GPL-3.0'}},
    {'license': 'GPL-3.0'},
    {'license': {'type': 'ISC'}},
    {},
])
def test_validate_license_rejects_mismatched_or_unapproved_licenses(metadata: dict[str, object]) -> None:
    with pytest.raises(ValueError, match='Unapproved license'):
        validate_license(_package('MIT'), metadata, {'LICENSE': b'MIT'})


def test_validate_license_requires_a_license_file() -> None:
    with pytest.raises(ValueError, match='no license file'):
        validate_license(_package('MIT'), {'license': 'MIT'}, {'index.js': b''})
