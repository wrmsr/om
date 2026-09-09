import typing as ta

import pytest

from ..registry import parse_package_document
from ..registry import parse_version_document


##


# Shaped like the registry documents for chokidar 3.5.3, where the optional fsevents dependency is merged into
# `dependencies` as npm does on publish.
_VERSION_DOCUMENT: dict[str, ta.Any] = {
    'name': 'chokidar',
    'version': '3.5.3',
    'dependencies': {
        'anymatch': '~3.1.2',
        'fsevents': '~2.3.2',
        'readdirp': '~3.6.0',
    },
    'optionalDependencies': {'fsevents': '~2.3.2'},
    'dist': {'integrity': 'sha512-unused', 'tarball': 'https://example.invalid/chokidar-3.5.3.tgz'},
}

_PACKAGE_DOCUMENT: dict[str, ta.Any] = {
    'name': 'chokidar',
    'dist-tags': {'latest': '3.5.3'},
    'versions': {'3.5.3': _VERSION_DOCUMENT},
}


def test_parse_package_document_excludes_optional_dependencies() -> None:
    package = parse_package_document(_PACKAGE_DOCUMENT, 'chokidar')

    assert package.tags == {'latest': '3.5.3'}
    assert len(package.versions) == 1
    assert package.versions[0].dependencies == {'anymatch': '~3.1.2', 'readdirp': '~3.6.0'}


def test_parse_version_document_excludes_optional_dependencies_and_normalizes_license() -> None:
    package = parse_version_document({
        **_VERSION_DOCUMENT,
        'license': {'type': 'MIT', 'url': 'https://example.invalid/LICENSE'},
    }, 'chokidar', '3.5.3')

    assert package.dependencies == {'anymatch': '~3.1.2', 'readdirp': '~3.6.0'}
    assert package.license == 'MIT'


@pytest.mark.parametrize('license_value', [
    None,
    {'url': 'https://example.invalid/LICENSE'},
    ['MIT'],
])
def test_parse_version_document_rejects_unusable_licenses(license_value: object) -> None:
    with pytest.raises(TypeError, match='no SPDX license'):
        parse_version_document({
            **_VERSION_DOCUMENT,
            'license': license_value,
        }, 'chokidar', '3.5.3')


def test_parse_package_document_skips_versions_with_invalid_optional_dependencies() -> None:
    document = {
        **_PACKAGE_DOCUMENT,
        'versions': {
            **_PACKAGE_DOCUMENT['versions'],
            '3.5.4': {
                **_VERSION_DOCUMENT,
                'version': '3.5.4',
                'optionalDependencies': {'fsevents': None},
            },
        },
    }

    package = parse_package_document(document, 'chokidar')

    assert [version.version for version in package.versions] == ['3.5.3']
