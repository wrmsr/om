import gzip
import json
import re

from omcore import lang

from ..pattern import PatternSyntaxError
from ..pattern import _replace_posix_classes
from ..pattern import has_meta
from ..pattern import quote_meta
from ..pattern import regexp


##


@lang.cached_function
def _corpus():
    compressed = lang.get_relative_resources(globals=globals())['patterncorpus.json.gz'].read_bytes()
    return json.loads(gzip.decompress(compressed))


def _python_regexp(expression):
    if expression.startswith('(?sU)'):
        expression = expression.replace('(?sU)', '(?s)', 1)
        prefix_end = expression.find(')') + 1
        result = [expression[:prefix_end]]
        in_class = False
        escaped = False
        for char in expression[prefix_end:]:
            result.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '[':
                in_class = True
            elif char == ']':
                in_class = False
            elif not in_class and char in ('*', '+', '?'):
                result.append('?')
        expression = ''.join(result)
    return _replace_posix_classes(expression).replace('[[]', r'[\[]')


def test_regexp_corpus():
    for index, case in enumerate(_corpus()['regexp']):
        context = f'regexp[{index}]: pattern={case["pattern"]!r}, mode={case["mode"]:#b}'
        if want_error := case.get('want_error'):
            try:
                regexp(case['pattern'], case['mode'])
            except PatternSyntaxError as exc:
                assert re.fullmatch(want_error, str(exc)), context  # noqa: PT017
            else:
                raise AssertionError(f'expected pattern syntax error: {context}')
            continue
        expression = regexp(case['pattern'], case['mode'])
        expected = _python_regexp(case['want'])
        assert expression == expected, context
        compiled = re.compile(expression)
        for value in case.get('must_match', []):
            assert compiled.search(value), f'{context}, must match {value!r}'
        for value in case.get('must_not_match', []):
            assert not compiled.search(value), f'{context}, must not match {value!r}'


def test_meta_corpus():
    for index, case in enumerate(_corpus()['meta']):
        context = f'meta[{index}]: pattern={case["pattern"]!r}'
        assert has_meta(case['pattern']) == case['want_has'], context
        assert quote_meta(case['pattern']) == case['want_quote'], context
