import pytest

from ..exports import output_package_exports
from ..exports import read_package_exports
from ..exports import resolve_package_export
from ..models import PackageExports


##


def test_read_package_exports_selects_browser_import_conditions() -> None:
    exports = read_package_exports({
        'exports': {
            '.': {
                'types': './dist/index.d.ts',
                'browser': {'import': './browser/index.js'},
                'default': './dist/index.js',
            },
            './feature': {'node': './node.js', 'import': './dist/feature.js'},
            './locale/*': './dist/locale/*.mjs',
        },
    }, 'example')

    assert exports == PackageExports(
        entries={
            '.': 'browser/index.js',
            './feature': 'dist/feature.js',
            './locale/*': 'dist/locale/*.mjs',
        },
        restricted=True,
    )
    assert resolve_package_export(exports, 'feature') == 'dist/feature.js'
    assert resolve_package_export(exports, 'locale/en') == 'dist/locale/en.mjs'


def test_read_package_exports_uses_legacy_esm_fields() -> None:
    exports = read_package_exports({'type': 'module', 'main': 'lib/main.js'}, 'example')

    assert exports == PackageExports(entries={'.': 'lib/main.js'}, restricted=False)
    assert resolve_package_export(exports, 'helpers/one') == 'helpers/one.js'


@pytest.mark.parametrize('metadata', [
    {'exports': {'import': '../outside.js'}},
    {'exports': {'.': './index.js', 'import': './other.js'}},
    {'exports': {'./feature': './dist/*.js'}},
    {'main': 'index.cjs'},
])
def test_read_package_exports_rejects_unsafe_or_non_esm_metadata(metadata: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        read_package_exports(metadata, 'example')


def test_resolve_package_export_enforces_explicit_subpaths() -> None:
    exports = PackageExports(entries={'.': 'index.js'}, restricted=True)

    with pytest.raises(ValueError, match='not exported'):
        resolve_package_export(exports, 'private.js')

    with pytest.raises(ValueError, match='Invalid package subpath'):
        resolve_package_export(
            PackageExports(entries={'./*': 'dist/*.js'}, restricted=True),
            '../private',
        )


def test_blocked_export_keys_shadow_broader_patterns() -> None:
    exports = read_package_exports({
        'exports': {
            '.': './index.js',
            './internal/*': None,
            './node-only': {'node': './node.js'},
            './*': './*',
        },
    }, 'example')

    assert exports.entries == {
        '.': 'index.js',
        './internal/*': None,
        './node-only': None,
        './*': '*',
    }
    assert resolve_package_export(exports, 'public.js') == 'public.js'

    with pytest.raises(ValueError, match='not exported'):
        resolve_package_export(exports, 'internal/secret.js')

    with pytest.raises(ValueError, match='not exported'):
        resolve_package_export(exports, 'node-only')


def test_read_package_exports_rejects_maps_with_only_blocked_keys() -> None:
    with pytest.raises(ValueError, match='exports no browser ESM'):
        read_package_exports({'exports': {'.': None, './feature': {'node': './node.js'}}}, 'example')


def test_output_package_exports_preserves_blocked_keys() -> None:
    exports = output_package_exports(
        PackageExports(entries={'.': 'dist/main.js', './blocked': None}, restricted=True),
        root_alias=True,
    )

    assert exports.entries == {'.': 'index.js', './blocked': None}
