import pytest

from ..parsing import parse_module


##


def _specifiers(source: str) -> tuple[str, ...]:
    return tuple(specifier.value for specifier in parse_module(source).specifiers)


def test_export_list_without_semicolon_does_not_adopt_a_later_source() -> None:
    result = parse_module("export { x }\nexport * from 'dep'\n")

    assert [(specifier.value, specifier.start, specifier.end) for specifier in result.specifiers] == [('dep', 28, 31)]


def test_export_list_followed_by_from_identifier_is_not_a_source() -> None:
    assert _specifiers("export { x }\nconst from = 1\nimport 'dep'\n") == ('dep',)


def test_export_source_must_immediately_follow_the_clause() -> None:
    assert _specifiers("export {\n  a,\n  b as c,\n}\nfrom 'dep'\n") == ('dep',)
    assert _specifiers("export { a as \"from\", b as 'other' }\nexport * as ns from 'other'\n") == ('other',)


@pytest.mark.parametrize('source', [
    'export *\n',
    "export * as ns\nlet from = 'dep'\n",
    'export * from\n',
    'export {x} from dep\n',
])
def test_export_source_errors(source: str) -> None:
    with pytest.raises(ValueError, match='export source'):
        parse_module(source)


def test_shebang_line_is_skipped() -> None:
    assert _specifiers("#!/usr/bin/env node\nimport {readFile} from 'node:fs'\n") == ('node:fs',)
    assert _specifiers('#!/usr/bin/env node') == ()


@pytest.mark.parametrize('source', [
    "let i = 0\ni++ / 2\ni-- / 'x'.length\n",
    "let i = 0\n++i / 2\n--i / 'x'.length\n",
    "const z = (a + b) / 'c'.length\n",
    "const o = {a: 1} / 'c'.length\n",
    "'(' / 2\n\"[\" / 'x'.length\n",
    "const r = /a/ / 'x'.length\n",
    "const t = `a` / 'x'.length\n",
    "const t = `${'('}` / 'x'.length\n",
    "f(/a/) / 'x'.length\n",
])
def test_division_is_not_read_as_a_regular_expression(source: str) -> None:
    assert _specifiers(source + "import 'dep'\n") == ('dep',)


@pytest.mark.parametrize('source', [
    "if (x) /'/.test(y)\n",
    "while (x) /'/.test(y)\n",
    "for (;;) /'/.test(y)\n",
    "if (x) { y() }\n/'/.test(y)\n",
    "function f() { return 1 }\n/'/.test(y)\n",
    "const f = x => /'/.test(x)\n",
    "const r = x ? /'/ : /\"/\n",
    "return /'/\n",
    "typeof /'/\n",
    "const a = [/'/, /\"/]\n",
    "const r = /[/']/\n",
    "if (x) /'/.test(y)\nelse /\"/.test(y)\n",
])
def test_regular_expression_is_not_read_as_division(source: str) -> None:
    assert _specifiers(source + "import 'dep'\n") == ('dep',)


def test_minified_statement_forms() -> None:
    source = "if(a)/x/.test(b);var c=(d+e)/2,f=g++/h;for(;;)/y/.test(i);import j from 'j'"

    assert _specifiers(source) == ('j',)


def test_punctuation_inside_literals_does_not_nest_declarations() -> None:
    source = 'const s = "{"\nconst r = /(/\nconst t = `[`\nimport \'dep\'\n'

    assert _specifiers(source) == ('dep',)


def test_regular_expression_context_resets_inside_template_expressions() -> None:
    assert _specifiers("const t = `${/'/.test(x)}` + `${ {a: `${b}`}.a }`\nimport 'dep'\n") == ('dep',)


def test_import_meta_and_dynamic_import_are_distinguished() -> None:
    result = parse_module("const u = import.meta.url\nimport 'dep'\n")
    assert [specifier.value for specifier in result.specifiers] == ['dep']
    assert not result.dynamic_import

    result = parse_module("const m = await import('./x.js')\n")
    assert result.specifiers == ()
    assert result.dynamic_import
