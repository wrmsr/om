import posixpath
import typing as ta

from .models import PackageExports


##


_BROWSER_CONDITIONS = frozenset({
    'browser',
    'import',
    'module',
    'default',
})


def _validate_export_key(key: str, package: str, /) -> None:
    if key == '.':
        return
    if (
            not key.startswith('./') or
            '\\' in key or
            key.count('*') > 1 or
            any(part in ('', '.', '..', 'node_modules') for part in key[2:].split('/'))
    ):
        raise ValueError(f'Invalid export key for {package}: {key}')


def _validate_target(target: str, package: str, /) -> str:
    if (
            not target.startswith('./') or
            '\\' in target or
            '?' in target or
            '#' in target or
            any(part in ('', '.', '..', 'node_modules') for part in target[2:].split('/'))
    ):
        raise ValueError(f'Invalid browser export target for {package}: {target}')
    return target[2:]


def _select_target(value: ta.Any, package: str, /) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        return _validate_target(value, package)

    if isinstance(value, list):
        for item in value:
            target = _select_target(item, package)
            if target is not None:
                return target
        return None

    if isinstance(value, dict):
        if any(isinstance(key, str) and key.startswith('.') for key in value):
            raise ValueError(f'Nested subpath export map for {package}')

        for condition, item in value.items():
            if not isinstance(condition, str):
                raise TypeError(f'Invalid export condition for {package}')

            if condition in _BROWSER_CONDITIONS:
                target = _select_target(item, package)
                if target is not None:
                    return target

        return None

    raise TypeError(f'Invalid export target for {package}')


def _legacy_entry(metadata: ta.Mapping[str, ta.Any], package: str, /) -> str:
    browser = metadata.get('browser')
    module = metadata.get('module')
    main = metadata.get('main')

    if isinstance(browser, str):
        return _validate_target('./' + browser.removeprefix('./'), package)

    if isinstance(module, str):
        return _validate_target('./' + module.removeprefix('./'), package)

    if isinstance(main, str) and (metadata.get('type') == 'module' or main.endswith('.mjs')):
        return _validate_target('./' + main.removeprefix('./'), package)

    raise ValueError(f'Package contains no distributed browser ESM entry point: {package}')


def read_package_exports(metadata: ta.Mapping[str, ta.Any], package: str, /) -> PackageExports:
    if 'exports' not in metadata:
        return PackageExports(entries={'.': _legacy_entry(metadata, package)}, restricted=False)

    value = metadata['exports']
    entries: dict[str, str] = {}

    if isinstance(value, dict) and any(isinstance(key, str) and key.startswith('.') for key in value):
        if not all(isinstance(key, str) and key.startswith('.') for key in value):
            raise ValueError(f'Mixed export map keys for {package}')

        for key, item in value.items():
            _validate_export_key(key, package)
            target = _select_target(item, package)
            if target is not None:
                if '*' in target and '*' not in key:
                    raise ValueError(f'Export target wildcard has no matching key wildcard for {package}: {key}')
                entries[key] = target

    else:
        target = _select_target(value, package)
        if target is not None:
            if '*' in target:
                raise ValueError(f'Root export target contains a wildcard for {package}')
            entries['.'] = target

    if not entries:
        raise ValueError(f'Package exports no browser ESM: {package}')

    return PackageExports(entries=entries, restricted=True)


def output_module_path(path: str, /) -> str:
    return path.removeprefix('dist/') if path.startswith('dist/') else path


def output_package_exports(exports: PackageExports, /, *, root_alias: bool) -> PackageExports:
    entries = {
        key: output_module_path(target)
        for key, target in exports.entries.items()
    }
    if root_alias and '.' in entries:
        entries['.'] = 'index.js'
    return PackageExports(entries=entries, restricted=exports.restricted)


def resolve_package_export(exports: PackageExports, subpath: str, /) -> str:
    if subpath and (
            '\\' in subpath or
            '?' in subpath or
            '#' in subpath or
            any(part in ('', '.', '..', 'node_modules') for part in subpath.split('/'))
    ):
        raise ValueError(f'Invalid package subpath: {subpath}')

    key = '.' if not subpath else './' + subpath
    exact = exports.entries.get(key)
    if exact is not None:
        return exact

    matches = []
    for pattern, target in exports.entries.items():
        if '*' not in pattern:
            continue

        prefix, suffix = pattern.split('*')
        if key.startswith(prefix) and key.endswith(suffix) and len(key) >= len(prefix) + len(suffix):
            replacement = key[len(prefix):len(key) - len(suffix) if suffix else None]
            matches.append((len(prefix), len(suffix), pattern, target.replace('*', replacement)))

    if matches:
        target = max(matches)[3]
        if target != posixpath.normpath(target) or any(part in ('.', '..') for part in target.split('/')):
            raise ValueError(f'Invalid resolved package target: {target}')
        return target

    if not exports.restricted and subpath:
        target = posixpath.normpath(subpath)
        if target.startswith('../') or target in ('.', '..'):
            raise ValueError(f'Invalid package subpath: {subpath}')
        return target if posixpath.splitext(target)[1] else target + '.js'

    raise ValueError(f'Package subpath is not exported: {key}')
