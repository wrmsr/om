import os

import pytest

from ..models import GraphVerifyRequest
from ..models import PackageExports
from ..models import RewriteRequest
from ..modules import iter_import_specifiers
from ..modules import rewrite_module
from ..modules import verify_graph


##


def test_root_esm_helpers_receive_bare_import_rewriting() -> None:
    result = rewrite_module(RewriteRequest(
        source="export {EditorState} from '@codemirror/state'\n",
        source_path='packages/@example/root-esm/helper.js',
        package_names={'@example/root-esm', '@codemirror/state'},
    ))

    assert "from '../../@codemirror/state/index.js'" in result.source


def test_parser_handles_multiline_static_forms_without_matching_literals() -> None:
    source = """
        const pattern = /import("not-a-module")/;
        const text = "export * from 'also-not-a-module'";
        import {
            value,
        } from /* comment */ 'one';
        import 'two';
        export {
            value as other,
        } from "three";
        export * as namespace from 'four';
    """

    assert tuple(iter_import_specifiers(source)) == ('one', 'two', 'three', 'four')


def test_parser_does_not_treat_import_methods_as_dynamic_imports() -> None:
    source = 'class Loader { import() { return true } }\nconst object = {import() { return false }}\n'

    result = rewrite_module(RewriteRequest(
        source=source,
        source_path='packages/example/index.js',
        package_names={'example'},
    ))

    assert source in result.source


def test_rewrite_module_uses_exact_and_pattern_exports() -> None:
    result = rewrite_module(RewriteRequest(
        source="import {one} from 'dependency/feature'\nimport {two} from 'dependency/locale/en'\n",
        source_path='packages/example/index.js',
        package_names={'example', 'dependency'},
        package_exports={
            'dependency': PackageExports(
                entries={
                    '.': 'index.js',
                    './feature': 'browser/feature.mjs',
                    './locale/*': 'locales/*.js',
                },
                restricted=True,
            ),
        },
    ))

    assert "from '../dependency/browser/feature.mjs'" in result.source
    assert "from '../dependency/locales/en.js'" in result.source


def test_rewrite_module_adjusts_relative_imports_for_relocated_entry() -> None:
    result = rewrite_module(RewriteRequest(
        source="export {value} from './helper.js'\n",
        source_path='packages/example/index.js',
        source_origin='packages/example/browser/main.js',
        package_names={'example'},
    ))

    assert "from './browser/helper.js'" in result.source


@pytest.mark.parametrize('source', [
    "const loaded = import('./feature.js')\n",
    "const loaded = condition ? import ('./feature.js') : null\n",
    "const loaded = `value ${import('./feature.js')}`\n",
])
def test_rewrite_module_rejects_dynamic_import_anywhere(source: str) -> None:
    with pytest.raises(ValueError, match='Dynamic import'):
        rewrite_module(RewriteRequest(
            source=source,
            source_path='packages/example/index.js',
            package_names={'example'},
        ))


def test_rewrite_module_rejects_unexported_subpath() -> None:
    with pytest.raises(ValueError, match='not exported'):
        rewrite_module(RewriteRequest(
            source="import 'dependency/private.js'\n",
            source_path='packages/example/index.js',
            package_names={'example', 'dependency'},
            package_exports={
                'dependency': PackageExports(entries={'.': 'index.js'}, restricted=True),
            },
        ))


def test_verify_graph_rejects_escape_and_dynamic_import(tmp_path) -> None:
    root = os.path.join(tmp_path, 'vendor')
    os.makedirs(root)
    path = os.path.join(root, 'index.js')
    with open(path, 'w', encoding='utf-8') as file:
        file.write("import '../outside.js'\n")
    with pytest.raises(ValueError, match='escapes vendor tree'):
        verify_graph(GraphVerifyRequest(root=root))

    with open(path, 'w', encoding='utf-8') as file:
        file.write("const loaded = import('./feature.js')\n")
    with pytest.raises(ValueError, match='Dynamic import'):
        verify_graph(GraphVerifyRequest(root=root))


def test_verify_graph_rejects_symbolic_links(tmp_path) -> None:
    root = os.path.join(tmp_path, 'vendor')
    os.makedirs(root)
    target = os.path.join(tmp_path, 'target.js')
    with open(target, 'w', encoding='utf-8') as file:
        file.write('export const value = 1\n')
    os.symlink(target, os.path.join(root, 'linked.js'))

    with pytest.raises(ValueError, match='Symbolic link'):
        verify_graph(GraphVerifyRequest(root=root))
