import base64
import hashlib
import json
import os
import typing as ta

import pytest

from omcore import dataclasses as dc

from ..generation import vendor
from ..manifests import load_lock
from ..models import ResolvedPackage
from ..models import RootPackage
from ..models import VendorLock
from ..models import VendorManifest
from ..models import VendorRequest
from ..models import VerifyRequest
from ..outputs import render_lock
from ..verification import verify
from .support import build_archive


##


def test_vendor_and_verify_headlessly(tmp_path) -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'module': './dist/index.js',
    }
    archive = build_archive({
        'package.json': json.dumps(metadata).encode(),
        'LICENSE': b'MIT',
        'dist/index.js': b'export const value = 1\n',
    })
    integrity = 'sha512-' + base64.b64encode(hashlib.sha512(archive).digest()).decode('ascii')
    root = RootPackage(
        name=metadata['name'],
        version=metadata['version'],
    )
    package = ResolvedPackage(
        name=metadata['name'],
        version=metadata['version'],
        license=metadata['license'],
        integrity=integrity,
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )
    manifest = VendorManifest(
        format_version=2,
        roots=(root,),
    )
    lock = VendorLock(
        format_version=2,
        roots=(root,),
        packages=(package,),
        files={},
    )
    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory)
    with open(os.path.join(cache_directory, 'example-1.2.3.tgz'), 'wb') as file:
        file.write(archive)

    destination = os.path.join(tmp_path, 'vendor')
    generated = vendor(VendorRequest(
        manifest=manifest,
        lock=lock,
        destination=destination,
        cache_directory=cache_directory,
    ))
    generated_lock = load_lock(os.path.join(destination, 'lock.json'))
    verified = verify(VerifyRequest(
        manifest=manifest,
        lock=generated_lock,
        destination=destination,
    ))

    assert generated.package_count == 1
    assert generated.file_count == 5
    assert generated_lock.roots == manifest.roots
    assert generated_lock.packages[0].url == package.url
    assert verified.package_count == 1
    assert verified.file_count == 5
    assert verified.module_count == 1

    lock_path = os.path.join(destination, 'lock.json')
    with open(lock_path, 'ab') as file:
        file.write(b'\n')
    with pytest.raises(ValueError, match='not the canonical requested lock'):
        verify(VerifyRequest(
            manifest=manifest,
            lock=generated_lock,
            destination=destination,
        ))
    with open(lock_path, 'wb') as file:
        file.write(render_lock(generated_lock))

    with open(os.path.join(destination, 'unexpected.txt'), 'w', encoding='utf-8') as file:
        file.write('not locked\n')
    with pytest.raises(ValueError, match=r'unexpected: unexpected\.txt'):
        verify(VerifyRequest(
            manifest=manifest,
            lock=generated_lock,
            destination=destination,
        ))
    os.unlink(os.path.join(destination, 'unexpected.txt'))

    extra_path = os.path.join(destination, 'extra.txt')
    with open(extra_path, 'w', encoding='utf-8') as file:
        file.write('locked but unowned\n')
    files = dict(generated_lock.files)
    with open(extra_path, 'rb') as file:
        files['extra.txt'] = hashlib.sha256(file.read()).hexdigest()
    extra_lock = dc.replace(generated_lock, files=files)
    with open(lock_path, 'wb') as file:
        file.write(render_lock(extra_lock))
    with pytest.raises(ValueError, match='outside locked package directories'):
        verify(VerifyRequest(
            manifest=manifest,
            lock=extra_lock,
            destination=destination,
        ))
    os.unlink(extra_path)

    metadata_path = os.path.join(destination, 'packages', 'example', 'package.json')
    metadata['version'] = '9.9.9'
    with open(metadata_path, 'w', encoding='utf-8') as file:
        json.dump(metadata, file)
    files = dict(generated_lock.files)
    with open(metadata_path, 'rb') as file:
        files['packages/example/package.json'] = hashlib.sha256(file.read()).hexdigest()
    tampered_lock = dc.replace(generated_lock, files=files)
    with open(lock_path, 'wb') as file:
        file.write(render_lock(tampered_lock))
    with pytest.raises(ValueError, match='identity does not match lock'):
        verify(VerifyRequest(
            manifest=manifest,
            lock=tampered_lock,
            destination=destination,
        ))


def test_vendor_preserves_existing_destination_when_generation_fails(tmp_path) -> None:
    metadata = {
        'name': 'example',
        'version': '1.2.3',
        'license': 'MIT',
        'type': 'module',
        'exports': {'import': './dist/index.js'},
    }
    archive = build_archive({
        'package.json': json.dumps(metadata).encode(),
        'LICENSE': b'MIT',
        'dist/index.js': b"const loaded = import('./feature.js')\n",
        'dist/feature.js': b'export const value = 1\n',
    })
    integrity = 'sha512-' + base64.b64encode(hashlib.sha512(archive).digest()).decode('ascii')
    root = RootPackage(name='example', version='1.2.3')
    package = ResolvedPackage(
        name='example',
        version='1.2.3',
        license='MIT',
        integrity=integrity,
        url='https://example.invalid/example.tgz',
        dependencies={},
        peer_dependencies={},
        optional_peer_dependencies=frozenset(),
    )
    manifest = VendorManifest(format_version=2, roots=(root,))
    lock = VendorLock(format_version=2, roots=(root,), packages=(package,), files={})
    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory)
    with open(os.path.join(cache_directory, 'example-1.2.3.tgz'), 'wb') as file:
        file.write(archive)
    destination = os.path.join(tmp_path, 'vendor')
    os.makedirs(destination)
    sentinel = os.path.join(destination, 'keep.txt')
    with open(sentinel, 'w', encoding='utf-8') as file:
        file.write('original\n')

    with pytest.raises(ValueError, match='Dynamic import'):
        vendor(VendorRequest(
            manifest=manifest,
            lock=lock,
            destination=destination,
            cache_directory=cache_directory,
        ))

    with open(sentinel, encoding='utf-8') as file:
        assert file.read() == 'original\n'
    assert os.listdir(destination) == ['keep.txt']


def test_vendor_resolves_exported_subpath_end_to_end(tmp_path) -> None:
    dependency_metadata = {
        'name': 'dependency',
        'version': '2.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': {
            '.': './dist/index.js',
            './feature': {'browser': './browser/feature.mjs'},
        },
    }
    dependency_archive = build_archive({
        'package.json': json.dumps(dependency_metadata).encode(),
        'LICENSE': b'MIT',
        'dist/index.js': b'export const root = true\n',
        'browser/feature.mjs': b'export const feature = true\n',
        'private.js': b'export const privateValue = true\n',
    })
    example_metadata = {
        'name': 'example',
        'version': '1.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': './dist/index.js',
        'dependencies': {'dependency': '^2.0.0'},
    }
    example_archive = build_archive({
        'package.json': json.dumps(example_metadata).encode(),
        'LICENSE': b'MIT',
        'dist/index.js': b"export {feature} from 'dependency/feature'\n",
    })

    def package(metadata: ta.Mapping[str, object], archive: bytes) -> ResolvedPackage:
        return ResolvedPackage(
            name=str(metadata['name']),
            version=str(metadata['version']),
            license='MIT',
            integrity='sha512-' + base64.b64encode(hashlib.sha512(archive).digest()).decode('ascii'),
            url=f"https://example.invalid/{metadata['name']}.tgz",
            dependencies={'dependency': '^2.0.0'} if metadata['name'] == 'example' else {},
            peer_dependencies={},
            optional_peer_dependencies=frozenset(),
        )

    dependency = package(dependency_metadata, dependency_archive)
    example = package(example_metadata, example_archive)
    root = RootPackage(name='example', version='1.0.0')
    manifest = VendorManifest(format_version=2, roots=(root,))
    lock = VendorLock(
        format_version=2,
        roots=(root,),
        packages=(dependency, example),
        files={},
    )
    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory)
    for name, version, archive in (
            ('dependency', '2.0.0', dependency_archive),
            ('example', '1.0.0', example_archive),
    ):
        with open(os.path.join(cache_directory, f'{name}-{version}.tgz'), 'wb') as archive_file:
            archive_file.write(archive)

    destination = os.path.join(tmp_path, 'vendor')
    generated = vendor(VendorRequest(
        manifest=manifest,
        lock=lock,
        destination=destination,
        cache_directory=cache_directory,
    ))

    with open(os.path.join(destination, 'packages', 'example', 'index.js'), encoding='utf-8') as module_file:
        assert "from '../dependency/browser/feature.mjs'" in module_file.read()
    assert os.path.isfile(os.path.join(destination, 'packages', 'dependency', 'browser', 'feature.mjs'))
    assert not os.path.exists(os.path.join(destination, 'packages', 'dependency', 'private.js'))
    assert generated.package_count == 2


def _vendor_archives(
        tmp_path: str,
        archives: ta.Mapping[str, tuple[ta.Mapping[str, ta.Any], ta.Mapping[str, bytes]]],
        *,
        roots: ta.Sequence[str],
) -> str:
    cache_directory = os.path.join(tmp_path, 'cache')
    os.makedirs(cache_directory, exist_ok=True)
    packages = []
    for name, (metadata, files) in archives.items():
        archive = build_archive({'package.json': json.dumps(metadata).encode(), 'LICENSE': b'MIT', **files})
        with open(os.path.join(cache_directory, f"{name}-{metadata['version']}.tgz"), 'wb') as archive_file:
            archive_file.write(archive)
        packages.append(ResolvedPackage(
            name=name,
            version=str(metadata['version']),
            license='MIT',
            integrity='sha512-' + base64.b64encode(hashlib.sha512(archive).digest()).decode('ascii'),
            url=f'https://example.invalid/{name}.tgz',
            dependencies=dict(metadata.get('dependencies', {})),
            peer_dependencies={},
            optional_peer_dependencies=frozenset(),
        ))

    root_packages = tuple(RootPackage(name=name, version=str(archives[name][0]['version'])) for name in roots)
    manifest = VendorManifest(format_version=2, roots=root_packages)
    lock = VendorLock(
        format_version=2,
        roots=root_packages,
        packages=tuple(sorted(packages, key=lambda package: package.name)),
        files={},
    )
    destination = os.path.join(tmp_path, 'vendor')
    vendor(VendorRequest(
        manifest=manifest,
        lock=lock,
        destination=destination,
        cache_directory=cache_directory,
    ))
    return destination


def _vendored_modules(destination: str) -> set[str]:
    modules = set()
    packages_root = os.path.join(destination, 'packages')
    for directory, _, names in os.walk(packages_root):
        for name in names:
            if name.endswith(('.js', '.mjs')):
                modules.add(os.path.relpath(os.path.join(directory, name), packages_root).replace(os.sep, '/'))
    return modules


def test_vendor_resolves_subpath_exports_lazily(tmp_path) -> None:
    dependency_metadata = {
        'name': 'dependency',
        'version': '2.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': {
            '.': './dist/index.js',
            './feature': './dist/feature.js',
            './compat/package.json': './compat/package.json',
            './scss/*': './scss/*',
            './bin/dependency': './bin/dependency.js',
            './*': './*',
        },
    }
    dependency_files = {
        'dist/index.js': b'export const root = true\n',
        'dist/feature.js': b"export {helper} from './helper.js'\n",
        'dist/helper.js': b'export const helper = true\n',
        'bin/dependency.js': b"#!/usr/bin/env node\nimport {readFile} from 'node:fs/promises'\n",
        'src/unbundled.js': b"import './extensionless'\n",
    }
    example_metadata = {
        'name': 'example',
        'version': '1.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': './index.js',
        'dependencies': {'dependency': '^2.0.0'},
    }
    example_files = {
        'index.js': b"export {helper} from 'dependency/feature'\n",
    }

    destination = _vendor_archives(
        tmp_path,
        {
            'dependency': (dependency_metadata, dependency_files),
            'example': (example_metadata, example_files),
        },
        roots=['example'],
    )

    assert _vendored_modules(destination) == {
        'example/index.js',
        'dependency/index.js',
        'dependency/feature.js',
        'dependency/helper.js',
    }


def test_vendor_materializes_imported_subpath_only_dependency(tmp_path) -> None:
    dependency_metadata = {
        'name': 'dependency',
        'version': '2.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': {'./mode/*': './mode/*.js'},
    }
    example_metadata = {
        'name': 'example',
        'version': '1.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': './index.js',
        'dependencies': {'dependency': '^2.0.0'},
    }

    destination = _vendor_archives(
        tmp_path,
        {
            'dependency': (dependency_metadata, {
                'mode/one.js': b'export const one = 1\n',
                'mode/two.js': b'export const two = 2\n',
            }),
            'example': (example_metadata, {'index.js': b"export {one} from 'dependency/mode/one'\n"}),
        },
        roots=['example'],
    )

    assert _vendored_modules(destination) == {'example/index.js', 'dependency/mode/one.js'}


def test_vendor_reports_colliding_vendor_paths_only_when_reached(tmp_path) -> None:
    metadata = {
        'name': 'example',
        'version': '1.0.0',
        'license': 'MIT',
        'type': 'module',
        'exports': {'.': './index.js', './util': './util.js'},
    }
    files = {
        'index.js': b'export const value = 1\n',
        'util.js': b'export const util = 1\n',
        'dist/util.js': b'export const util = 2\n',
    }

    destination = _vendor_archives(tmp_path, {'example': (metadata, files)}, roots=['example'])
    assert _vendored_modules(destination) == {'example/index.js'}

    files['index.js'] = b"export {util} from './util.js'\n"
    with pytest.raises(ValueError, match=r'same vendor path: packages/example/util\.js'):
        _vendor_archives(os.path.join(tmp_path, 'again'), {'example': (metadata, files)}, roots=['example'])
