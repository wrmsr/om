import base64
import dataclasses as dc
import enum
import gzip
import json
import re

from omcore import lang

from ..langs import LANG_BASH
from ..langs import LANG_BATS
from ..langs import LANG_MIR_BSD_KORN
from ..langs import LANG_POSIX
from ..langs import LANG_ZSH
from ..nodes import OptState
from ..nodes import Pos
from ..parser import Parser
from ..tokens import Token
from ..walk import walk


##


_LANGS = {
    'bash': LANG_BASH,
    'bats': LANG_BATS,
    'mksh': LANG_MIR_BSD_KORN,
    'posix': LANG_POSIX,
    'zsh': LANG_ZSH,
}

_TOKEN_VALUES = {token: value for value, token in enumerate(Token)}

_NORMALIZED_FIELDS = {
    ('CaseClause', 'braces'),
    ('CmdSubst', 'backquotes'),
    ('ForClause', 'braces'),
}


@lang.cached_function
def _corpus():
    compressed = lang.get_relative_resources(globals=globals())['parsercorpus.json.gz'].read_bytes()
    return json.loads(gzip.decompress(compressed))


def _encode(value, *, positions=False):
    if value is None:
        return None
    if isinstance(value, Pos):
        if positions and value.is_valid():
            return {
                'offset': value.offset(),
                'line': value.line(),
                'col': value.col(),
            }
        return None
    if isinstance(value, OptState):
        return int(value) or None
    if isinstance(value, enum.Enum):
        return _TOKEN_VALUES[value.value]
    if dc.is_dataclass(value):
        encoded = {'type': type(value).__name__}
        for field in dc.fields(value):
            if (type(value).__name__, field.name) in _NORMALIZED_FIELDS:
                continue
            field_value = _encode(getattr(value, field.name), positions=positions)
            if field_value is not None:
                encoded[field.name.removesuffix('_')] = field_value
        return encoded
    if isinstance(value, list):
        if not value:
            return None
        return [_encode(item, positions=positions) for item in value]
    if isinstance(value, bool):
        return value or None
    if isinstance(value, str):
        return value or None
    if isinstance(value, int):
        return value or None
    raise TypeError(type(value))


def _snake_case(name):
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def _normalize_expected(value):
    if isinstance(value, dict):
        normalized = {_snake_case(key): _normalize_expected(item) for key, item in value.items()}
        for type_name, field_name in _NORMALIZED_FIELDS:
            if normalized.get('type') == type_name:
                normalized.pop(field_name, None)
        return normalized
    if isinstance(value, list):
        return [_normalize_expected(item) for item in value]
    return value


def test_parser_corpus():
    corpus = _corpus()
    asts = [_normalize_expected(ast) for ast in corpus['asts']]
    position_asts = [_normalize_expected(ast) for ast in corpus['position_asts']]
    checked = 0
    for group_name in ('file_cases', 'error_cases'):
        for case_index, case in enumerate(corpus[group_name]):
            for lang_name, expected in case['by_lang'].items():
                parser = Parser(
                    lang=_LANGS[lang_name],
                    keep_comments=case.get('keep_comments', False),
                )
                for input_index, source_text in enumerate(case['inputs']):
                    encoded_source = case.get('input_bytes', {}).get(str(input_index))
                    source = base64.b64decode(encoded_source) if encoded_source is not None else source_text
                    context = f'{group_name}[{case_index}].inputs[{input_index}] ({lang_name}): {source!r}'
                    if expected['kind'] == 'error':
                        try:
                            parser.parse(source)
                        except Exception as exc:  # noqa: BLE001
                            assert str(exc) == expected['error'], context  # noqa: PT017
                        else:
                            raise AssertionError(f'expected parse error: {context}')
                    else:
                        file = parser.parse(source)
                        assert _encode(file) == asts[expected['ast_id']], context
                        if input_index == 0:
                            assert _encode(file, positions=True) == position_asts[expected['position_ast_id']], context
                    checked += 1
    assert checked == 4_396


def test_walk_corpus_covers_every_parser_node():
    expected = {
        'ArithmCmd', 'ArithmExp', 'ArrayElem', 'ArrayExpr', 'Assign',
        'BinaryArithm', 'BinaryCmd', 'BinaryTest', 'Block', 'CStyleLoop',
        'CallExpr', 'CaseClause', 'CaseItem', 'CmdSubst', 'Comment',
        'CoprocClause', 'DblQuoted', 'DeclClause', 'ExtGlob', 'File',
        'FlagsArithm', 'ForClause', 'FuncDecl', 'IfClause', 'LetClause',
        'Lit', 'ParamExp', 'ParenArithm', 'ParenTest', 'ProcSubst',
        'Redirect', 'SglQuoted', 'Stmt', 'Subshell', 'TestClause',
        'TestDecl', 'TimeClause', 'UnaryArithm', 'UnaryTest', 'WhileClause',
        'Word', 'WordIter',
    }
    seen = set()
    exit_visits = 0

    def visit(node):
        nonlocal exit_visits
        if node is None:
            exit_visits += 1
        else:
            seen.add(type(node).__name__)
        return True

    for group_name in ('file_cases', 'error_cases'):
        for case in _corpus()[group_name]:
            for lang_name, outcome in case['by_lang'].items():
                if outcome['kind'] == 'ok':
                    file = Parser(
                        lang=_LANGS[lang_name],
                        keep_comments=case.get('keep_comments', False),
                    ).parse(case['inputs'][0])
                    walk(file, visit)
                    break

    assert seen == expected
    assert exit_visits > len(expected)
