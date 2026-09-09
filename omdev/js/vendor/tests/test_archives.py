import json

import pytest

from ..archives import read_archive
from ..models import DownloadedPackage
from ..models import ResolvedPackage
from .support import build_archive


##


def _package(name: str, version: str) -> ResolvedPackage:
    return ResolvedPackage(
        name=name,
        version=version,
        license='MIT',
        integrity='sha512-unused',
        url=f'https://example.invalid/{name}.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )


def test_read_archive_ignores_non_esm_subpath_export_targets() -> None:
    # Modeled on real export maps: preact exports a nested package.json, highlight.js a stylesheet pattern, marked a
    # Node CLI with a shebang, and katex a catch-all which also matches the license file.
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {
            '.': './dist/index.js',
            './compat/package.json': './compat/package.json',
            './scss/*': './scss/*',
            './bin/example': './bin/example.js',
            './*': './*',
        },
    }

    extracted = read_archive(DownloadedPackage(
        package=_package('example', '1.2.3'),
        data=build_archive({
            'package.json': json.dumps(metadata).encode(),
            'LICENSE': b"Don't worry, this apostrophe is not JavaScript\n",
            'dist/index.js': b'export const value = 1\n',
            'bin/example.js': b"#!/usr/bin/env node\nimport {readFile} from 'node:fs/promises'\n",
            'src/unbundled.js': b"import './extensionless'\n",
        }),
    ))

    assert extracted.exports.entries == {
        '.': 'index.js',
        './compat/package.json': 'compat/package.json',
        './scss/*': 'scss/*',
        './bin/example': 'bin/example.js',
        './*': '*',
    }
    assert set(extracted.files) == {'package.json', 'LICENSE', 'dist/index.js', 'bin/example.js', 'src/unbundled.js'}


def test_read_archive_validates_only_the_root_closure() -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {
            '.': './index.js',
            './broken': './broken.js',
        },
    }
    files = {
        'package.json': json.dumps(metadata).encode(),
        'LICENSE': b'MIT',
        'index.js': b"export {value} from './helper.js'\n",
        'helper.js': b'export const value = 1\n',
        'broken.js': b"export {missing} from './missing.js'\n",
    }

    extracted = read_archive(DownloadedPackage(package=_package('example', '1.2.3'), data=build_archive(files)))
    assert 'broken.js' in extracted.files

    files['helper.js'] = b"export {value} from './missing.js'\n"
    with pytest.raises(ValueError, match=r'Relative import target does not exist: helper\.js'):
        read_archive(DownloadedPackage(package=_package('example', '1.2.3'), data=build_archive(files)))


def test_read_archive_requires_the_root_export_target() -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {'.': './dist/index.js', './other': './other.js'},
    }

    with pytest.raises(ValueError, match='Browser export target does not exist'):
        read_archive(DownloadedPackage(
            package=_package('example', '1.2.3'),
            data=build_archive({
                'package.json': json.dumps(metadata).encode(),
                'LICENSE': b'MIT',
                'other.js': b'export const other = 1\n',
            }),
        ))


def test_read_archive_accepts_subpath_only_export_maps() -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {'./mode/*': './mode/*.js'},
    }

    extracted = read_archive(DownloadedPackage(
        package=_package('example', '1.2.3'),
        data=build_archive({
            'package.json': json.dumps(metadata).encode(),
            'LICENSE': b'MIT',
            'mode/one.js': b'export const one = 1\n',
        }),
    ))

    assert extracted.exports.entries == {'./mode/*': 'mode/*.js'}
    assert 'mode/one.js' in extracted.files


def test_read_archive_normalizes_root_esm_entry() -> None:
    metadata = {
        'name': '@example/root-esm',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'main': './main.js',
    }
    package = ResolvedPackage(
        name=metadata['name'],
        version=metadata['version'],
        license=metadata['license'],
        integrity='sha512-unused',
        url='https://example.invalid/root-esm.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )
    extracted = read_archive(DownloadedPackage(
        package=package,
        data=build_archive({
            'package.json': json.dumps(metadata).encode(),
            'LICENSE': b'MIT',
            'main.js': b"export {value} from './helper.js'\n",
            'helper.js': b'export const value = 1\n',
        }),
    ))

    assert extracted.metadata == metadata
    assert extracted.files['dist/index.js'] == b"export {value} from './helper.js'\n"
    assert extracted.files['helper.js'] == b'export const value = 1\n'
    assert extracted.module_origins['dist/index.js'] == 'main.js'
    assert extracted.exports.entries == {'.': 'index.js'}


def test_read_archive_follows_conditional_and_subpath_exports() -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {
            '.': {
                'types': './dist/index.d.ts',
                'browser': {'import': './browser/main.js'},
                'default': './dist/index.js',
            },
            './feature': './features/feature.js',
        },
    }
    package = ResolvedPackage(
        name='example',
        version='1.2.3',
        license='MIT',
        integrity='sha512-unused',
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )

    extracted = read_archive(DownloadedPackage(
        package=package,
        data=build_archive({
            'package.json': json.dumps(metadata).encode(),
            'LICENSE': b'MIT',
            'browser/main.js': b"export {value} from './helper.js'\n",
            'browser/helper.js': b'export const value = 1\n',
            'features/feature.js': b'export const feature = true\n',
            'dist/index.js': b'export const wrong = true\n',
            'unpublished.js': b'export const unpublished = true\n',
        }),
    ))

    assert extracted.exports.entries == {'.': 'index.js', './feature': 'features/feature.js'}
    assert 'browser/helper.js' in extracted.files
    assert 'features/feature.js' in extracted.files
    assert 'dist/index.js' in extracted.files
    assert extracted.module_origins['dist/index.js'] == 'browser/main.js'

    # Every module remains a candidate for lazy subpath resolution; generation decides what is materialized.
    assert 'unpublished.js' in extracted.files
    assert extracted.module_origins['unpublished.js'] == 'unpublished.js'


def test_read_archive_rejects_missing_relative_module() -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': './index.js',
    }
    package = ResolvedPackage(
        name='example',
        version='1.2.3',
        license='MIT',
        integrity='sha512-unused',
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )

    with pytest.raises(ValueError, match='Relative import target does not exist'):
        read_archive(DownloadedPackage(
            package=package,
            data=build_archive({
                'package.json': json.dumps(metadata).encode(),
                'LICENSE': b'MIT',
                'index.js': b"export {value} from './missing.js'\n",
            }),
        ))


def test_read_archive_rejects_parent_archive_member() -> None:
    package = ResolvedPackage(
        name='example',
        version='1.2.3',
        license='MIT',
        integrity='sha512-unused',
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )

    with pytest.raises(ValueError, match='Unsafe archive member'):
        read_archive(DownloadedPackage(
            package=package,
            data=build_archive({
                'package.json': json.dumps({
                    'name': 'example',
                    'version': '1.2.3',
                    'license': 'MIT',
                    'type': 'module',
                    'main': './index.js',
                }).encode(),
                'LICENSE': b'MIT',
                'index.js': b'export const value = 1\n',
                '../outside.js': b'unsafe\n',
            }),
        ))
