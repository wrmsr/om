"""
Translation of Go's text/template/funcs.go.

Python has no direct equivalents of Go's static reflection types. The implementation preserves template-visible
behavior for ordinary Python values and callables; operations whose result depends on an unavailable Go element type
(notably the zero value of a missing map entry) use None.
"""

# Copyright 2011 The Go Authors.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#      disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#      following disclaimer in the documentation and/or other materials provided with the distribution.
#    * Neither the name of Google LLC nor the names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import collections.abc
import math
import re
import typing as ta
import unicodedata
import urllib.parse

from omcore import dataclasses as dc

from .quoting import quote_go_rune
from .quoting import quote_go_string
from .quoting import quote_go_string_or_raw
from .values import is_missing


FuncMap: ta.TypeAlias = dict[str, ta.Callable[..., ta.Any]]


##


def builtins() -> FuncMap:
    return {
        'and': and_,
        'call': empty_call,
        'html': html_escaper,
        'index': index,
        'slice': slice_,
        'js': js_escaper,
        'len': length,
        'not': not_,
        'or': or_,
        'print': go_sprint,
        'printf': go_sprintf,
        'println': go_sprintln,
        'urlquery': url_query_escaper,
        # Comparisons.
        'eq': eq,
        'ge': ge,
        'gt': gt,
        'le': le,
        'lt': lt,
        'ne': ne,
    }


def add_value_funcs(out: FuncMap, funcs: ta.Mapping[str, ta.Any]) -> None:
    for name, fn in funcs.items():
        if not good_name(name):
            raise ValueError(f'function name {quote_go_string(name)} is not a valid identifier')
        if not callable(fn):
            raise TypeError(f'value for {name} not a function')
        good_func(name, fn)
        out[name] = fn


def add_funcs(out: FuncMap, funcs: ta.Mapping[str, ta.Callable[..., ta.Any]]) -> None:
    out.update(funcs)


def good_func(name: str, fn: ta.Callable[..., ta.Any]) -> None:
    # Go validates the number and types of return values here. Python return shapes are dynamic, so the corresponding
    # check happens after invocation in safe_call.
    if not callable(fn):
        raise TypeError(f'value for {name} not a function')


def good_name(name: str) -> bool:
    if not name:
        return False
    for i, char in enumerate(name):
        if char == '_':
            continue
        category = unicodedata.category(char)
        if i == 0 and not category.startswith('L'):
            return False
        if not category.startswith('L') and category != 'Nd':
            return False
    return True


def find_function(name: str, tmpl: ta.Any) -> tuple[ta.Callable[..., ta.Any] | None, bool]:
    common = getattr(tmpl, '_common', None)
    if common is not None:
        with common.funcs_lock:
            if (fn := common.exec_funcs.get(name)) is not None:
                return fn, False
    if (fn := builtins().get(name)) is not None:
        return fn, True
    return None, False


## Indexing


def _index_arg(value: ta.Any, cap: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        if value is None:
            raise TypeError('cannot index slice/array with nil')
        raise TypeError(f'cannot index slice/array with type {type(value).__name__}')
    if value < 0 or value >= cap:
        raise IndexError(f'index out of range: {value}')
    return value


def map_zero_value(item: collections.abc.Mapping[ta.Any, ta.Any]) -> ta.Any:
    if not item:
        return None
    value_types = {type(value) for value in item.values()}
    if len(value_types) != 1:
        return None
    typ = next(iter(value_types))
    if typ in (bool, int, float, complex, str, bytes, bytearray, list, tuple, dict):
        return typ()
    return None


def index(item: ta.Any, *indexes: ta.Any) -> ta.Any:
    if item is None or is_missing(item):
        raise TypeError('index of untyped nil')
    for key in indexes:
        if item is None:
            raise TypeError('index of nil pointer')
        if isinstance(item, str):
            data = item.encode()
            item = data[_index_arg(key, len(data))]
        elif isinstance(item, (bytes, bytearray, list, tuple)):
            item = item[_index_arg(key, len(item))]
        elif isinstance(item, collections.abc.Mapping):
            key_types = {type(existing) for existing in item}
            if len(key_types) == 1 and type(key) not in key_types:
                raise TypeError(f'value has type {type(key).__name__}; should be {next(iter(key_types)).__name__}')
            try:
                item = item[key] if key in item else map_zero_value(item)
            except (TypeError, ValueError) as exc:
                raise TypeError(f'value has type {type(key).__name__}; cannot be used as map key') from exc
        else:
            raise TypeError(f"can't index item of type {type(item).__name__}")
    return item


## Slicing


def _slice_index(value: ta.Any, cap: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        if value is None:
            raise TypeError('cannot index slice/array with nil')
        raise TypeError(f'cannot index slice/array with type {type(value).__name__}')
    if value < 0 or value > cap:
        raise IndexError(f'index out of range: {value}')
    return value


def slice_(item: ta.Any, *indexes: ta.Any) -> ta.Any:
    if item is None or is_missing(item):
        raise TypeError('slice of untyped nil')
    if len(indexes) > 3:
        raise ValueError(f'too many slice indexes: {len(indexes)}')
    if isinstance(item, str):
        if len(indexes) == 3:
            raise TypeError('cannot 3-index slice a string')
        source: ta.Any = item.encode()
    elif isinstance(item, (bytes, bytearray, list, tuple)):
        source = item
    else:
        raise TypeError(f"can't slice item of type {type(item).__name__}")

    cap = len(source)
    idx = [0, len(source), cap]
    for i, value in enumerate(indexes):
        idx[i] = _slice_index(value, cap)
    if idx[0] > idx[1]:
        raise IndexError(f'invalid slice index: {idx[0]} > {idx[1]}')
    if len(indexes) == 3 and idx[1] > idx[2]:
        raise IndexError(f'invalid slice index: {idx[1]} > {idx[2]}')
    result = source[idx[0] : idx[1]]
    if isinstance(item, str):
        # A Go string can hold invalid UTF-8 after slicing through a rune. Python str cannot. surrogateescape preserves
        # those bytes for round trips rather than silently changing boundaries.
        return result.decode(errors='surrogateescape')
    return result


## Length


def length(item: ta.Any) -> int:
    if item is None or is_missing(item):
        raise TypeError('len of nil pointer')
    if isinstance(item, str):
        return len(item.encode())
    if isinstance(item, (bytes, bytearray, list, tuple, collections.abc.Mapping)):
        return len(item)
    raise TypeError(f'len of type {type(item).__name__}')


## Function invocation


def empty_call(*args: ta.Any) -> ta.NoReturn:
    raise RuntimeError('unreachable')


def safe_call(fn: ta.Callable[..., ta.Any], args: ta.Sequence[ta.Any]) -> ta.Any:
    result = fn(*args)
    # Python has no multiple return values. A pair whose second item is None or an exception is the natural spelling of
    # Go's (value, error) convention; all other tuples remain ordinary single values.
    if isinstance(result, tuple) and len(result) == 2 and (result[1] is None or isinstance(result[1], BaseException)):
        value, error = result
        if error is not None:
            raise error
        return value
    return result


def call(name: str, fn: ta.Any, *args: ta.Any) -> ta.Any:
    if fn is None or is_missing(fn):
        raise TypeError('call of nil')
    if not callable(fn):
        raise TypeError(f'non-function {name} of type {type(fn).__name__}')
    return safe_call(fn, [None if is_missing(arg) else arg for arg in args])


## Boolean logic


def truth(arg: ta.Any) -> bool:
    if arg is None or is_missing(arg):
        return False
    if isinstance(arg, bool):
        return arg
    if isinstance(arg, (int, float, complex)):
        return arg != 0
    if isinstance(arg, (str, bytes, bytearray, list, tuple, collections.abc.Mapping)):
        return len(arg) > 0
    return True


def and_(arg0: ta.Any, *args: ta.Any) -> ta.Any:
    value = arg0
    for value in (arg0, *args):
        if not truth(value):
            return value
    return value


def or_(arg0: ta.Any, *args: ta.Any) -> ta.Any:
    value = arg0
    for value in (arg0, *args):
        if truth(value):
            return value
    return value


def not_(arg: ta.Any) -> bool:
    return not truth(arg)


## Comparison


class ComparisonError(TypeError):
    pass


def _basic_kind(value: ta.Any) -> str | None:
    if isinstance(value, bool):
        return 'bool'
    if isinstance(value, int):
        return 'int'
    if isinstance(value, float):
        return 'float'
    if isinstance(value, complex):
        return 'complex'
    if isinstance(value, str):
        return 'string'
    return None


def _equal(arg1: ta.Any, arg2: ta.Any) -> bool:
    if is_missing(arg1):
        arg1 = None
    if is_missing(arg2):
        arg2 = None
    kind1 = _basic_kind(arg1)
    kind2 = _basic_kind(arg2)
    if kind1 != kind2:
        if arg1 is not None and arg2 is not None:
            raise ComparisonError(
                f'incompatible types for comparison: {type(arg1).__name__} and {type(arg2).__name__}',
            )
        return arg1 is None and arg2 is None
    if kind1 is not None:
        return bool(arg1 == arg2)
    if arg1 is None or arg2 is None:
        return arg1 is arg2
    if type(arg1) is not type(arg2):
        raise ComparisonError(
            f'incompatible types for comparison: {type(arg1).__name__} and {type(arg2).__name__}',
        )
    if isinstance(arg1, (bytes, bytearray, list, dict, set)) or callable(arg1):
        raise ComparisonError(f'non-comparable type {type(arg1).__name__}')
    if isinstance(arg1, tuple):
        for left, right in zip(arg1, arg2, strict=True):
            _equal(left, right)
    try:
        return bool(arg1 == arg2)
    except Exception as exc:
        raise ComparisonError(f'non-comparable type {type(arg1).__name__}') from exc


def eq(arg1: ta.Any, *arg2: ta.Any) -> bool:
    if not arg2:
        raise ComparisonError('missing argument for comparison')
    return any(_equal(arg1, arg) for arg in arg2)


def ne(arg1: ta.Any, arg2: ta.Any) -> bool:
    return not eq(arg1, arg2)


def lt(arg1: ta.Any, arg2: ta.Any) -> bool:
    kind1 = _basic_kind(arg1)
    kind2 = _basic_kind(arg2)
    if kind1 is None or kind1 in ('bool', 'complex'):
        raise ComparisonError('invalid type for comparison')
    if kind1 != kind2:
        raise ComparisonError(
            f'incompatible types for comparison: {type(arg1).__name__} and {type(arg2).__name__}',
        )
    return bool(arg1 < arg2)


def le(arg1: ta.Any, arg2: ta.Any) -> bool:
    return lt(arg1, arg2) or eq(arg1, arg2)


def gt(arg1: ta.Any, arg2: ta.Any) -> bool:
    return not le(arg1, arg2)


def ge(arg1: ta.Any, arg2: ta.Any) -> bool:
    return not lt(arg1, arg2)


## Printing


def _split_decimal(value: str) -> tuple[str, int]:
    if 'e' in value:
        mantissa, _, exponent_text = value.partition('e')
        exp = int(exponent_text)
    else:
        mantissa, exp = value, 0
    if '.' in mantissa:
        integer, fraction = mantissa.split('.')
    else:
        integer, fraction = mantissa, ''
    digits = (integer + fraction).lstrip('0')
    if not digits:
        return '0', 0
    exponent = len(integer) - 1 + exp - (len(integer + fraction) - len(digits))
    return digits.rstrip('0') or '0', exponent


def go_format_float(value: float) -> str:
    if math.isnan(value):
        return 'NaN'
    if math.isinf(value):
        return '+Inf' if value > 0 else '-Inf'
    rendered = repr(value)
    negative = rendered.startswith('-')
    if negative:
        rendered = rendered[1:]
    digits, exponent = _split_decimal(rendered)
    sign = '-' if negative else ''
    if exponent < -4 or exponent >= 6:
        mantissa = digits[0] if len(digits) == 1 else f'{digits[0]}.{digits[1:]}'
        return f"{sign}{mantissa}e{'+' if exponent >= 0 else '-'}{abs(exponent):02d}"
    if exponent >= len(digits) - 1:
        return sign + digits + '0' * (exponent - len(digits) + 1)
    if exponent >= 0:
        return f'{sign}{digits[: exponent + 1]}.{digits[exponent + 1 :]}'
    return f"{sign}0.{'0' * (-exponent - 1)}{digits}"


def _sorted_mapping_items(value: collections.abc.Mapping[ta.Any, ta.Any]) -> list[tuple[ta.Any, ta.Any]]:
    try:
        return sorted(value.items(), key=lambda item: item[0])
    except TypeError:
        return sorted(value.items(), key=lambda item: (type(item[0]).__name__, repr(item[0])))


def go_format_value(value: ta.Any) -> str:
    if is_missing(value):
        return '<no value>'
    if value is None:
        return '<nil>'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return go_format_float(value)
    if isinstance(value, complex):
        real = go_format_float(value.real)
        imag = go_format_float(abs(value.imag))
        sign = '+' if math.copysign(1, value.imag) > 0 else '-'
        return f'({real}{sign}{imag}i)'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return '[' + ' '.join(str(byte) for byte in value) + ']'
    if isinstance(value, collections.abc.Mapping):
        body = ' '.join(f'{go_format_value(key)}:{go_format_value(item)}' for key, item in _sorted_mapping_items(value))
        return f'map[{body}]'
    if isinstance(value, (list, tuple)):
        return '[' + ' '.join(go_format_value(item) for item in value) + ']'
    if dc.is_dataclass(value) and not isinstance(value, type):
        return '{' + ' '.join(go_format_value(getattr(value, field.name)) for field in dc.fields(value)) + '}'
    return str(value)


def go_sprint(*args: ta.Any) -> str:
    out: list[str] = []
    previous_was_string = False
    for i, arg in enumerate(args):
        is_string = isinstance(arg, str)
        if i and not previous_was_string and not is_string:
            out.append(' ')
        out.append(go_format_value(arg))
        previous_was_string = is_string
    return ''.join(out)


def go_sprintln(*args: ta.Any) -> str:
    return ' '.join(go_format_value(arg) for arg in args) + '\n'


_FORMAT_DIRECTIVE = re.compile(
    r'%(?P<index>\[\d+])?(?P<flags>[+#0\- ]*)(?P<width>\d+|\*)?(?:\.(?P<precision>\d+|\*))?(?P<verb>.)',
    re.DOTALL,
)


def _format_type(value: ta.Any) -> str:
    if value is None:
        return '<nil>'
    if isinstance(value, bool):
        return 'bool'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, int):
        return 'int'
    if isinstance(value, float):
        return 'float64'
    if isinstance(value, complex):
        return 'complex128'
    return type(value).__name__


def _apply_width(value: str, flags: str, width: int | None) -> str:
    if width is None or len(value) >= width:
        return value
    padding = '0' if '0' in flags and '-' not in flags else ' '
    amount = width - len(value)
    if '-' in flags:
        return value + padding * amount
    if padding == '0':
        sign = value[:1] if value[:1] in ('+', '-', ' ') else ''
        unsigned = value[len(sign) :]
        prefix = unsigned[:2] if unsigned.startswith(('0b', '0x', '0X')) else ''
        if sign or prefix:
            return sign + prefix + padding * amount + unsigned[len(prefix) :]
    return padding * amount + value


def _format_directive(value: ta.Any, verb: str, flags: str, precision: int | None) -> str:
    if verb == 'v':
        if '#' in flags:
            return repr(value)
        return go_format_value(value)
    if verb == 'T':
        return _format_type(value)
    if verb == 't' and isinstance(value, bool):
        return 'true' if value else 'false'
    if verb == 's' and isinstance(value, (str, bytes, bytearray)):
        rendered = value if isinstance(value, str) else bytes(value).decode(errors='replace')
        return rendered if precision is None else rendered[:precision]
    if verb == 'q' and isinstance(value, str):
        value = value if precision is None else value[:precision]
        if '#' in flags:
            return quote_go_string_or_raw(value)
        return quote_go_string(value)
    if verb == 'q' and isinstance(value, int) and not isinstance(value, bool):
        if not 0 <= value <= 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            return quote_go_rune('\ufffd')
        return quote_go_rune(chr(value))
    if verb == 'c' and isinstance(value, int) and not isinstance(value, bool):
        if not 0 <= value <= 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            return '\ufffd'
        return chr(value)
    if verb == 'U' and isinstance(value, int) and not isinstance(value, bool):
        return f'U+{value:04X}'
    if verb in 'dboxX' and isinstance(value, int) and not isinstance(value, bool):
        spec = {'d': 'd', 'b': 'b', 'o': 'o', 'x': 'x', 'X': 'X'}[verb]
        rendered = format(abs(value), spec)
        if precision is not None:
            rendered = rendered.rjust(precision, '0')
        if '#' in flags:
            prefix = {'b': '0b', 'o': '' if rendered.startswith('0') else '0', 'x': '0x', 'X': '0X', 'd': ''}[verb]
            rendered = prefix + rendered
        if value < 0:
            rendered = '-' + rendered
        elif '+' in flags:
            rendered = '+' + rendered
        elif ' ' in flags:
            rendered = ' ' + rendered
        return rendered
    if verb in 'xX' and isinstance(value, (str, bytes, bytearray)):
        data = value.encode() if isinstance(value, str) else bytes(value)
        rendered = data.hex()
        return rendered.upper() if verb == 'X' else rendered
    if verb in 'eEfFgG' and isinstance(value, complex):
        real = _format_directive(value.real, verb, flags, precision)
        imag = _format_directive(abs(value.imag), verb, '', precision)
        sign = '+' if math.copysign(1, value.imag) > 0 else '-'
        return f'({real}{sign}{imag}i)'
    if verb in 'eEfFgG' and isinstance(value, float):
        digits = 6 if precision is None else precision
        rendered = format(float(value), f'.{digits}{verb}')
        if verb in 'gG' and precision is None:
            rendered = go_format_float(float(value))
            if verb == 'G':
                rendered = rendered.upper()
        if value >= 0 and '+' in flags:
            rendered = '+' + rendered
        elif value >= 0 and ' ' in flags:
            rendered = ' ' + rendered
        return rendered
    return f'%!{verb}({_format_type(value)}={go_format_value(value)})'


def go_sprintf(format_string: str, *args: ta.Any) -> str:
    out: list[str] = []
    pos = 0
    arg_index = 0
    while pos < len(format_string):
        percent = format_string.find('%', pos)
        if percent < 0:
            out.append(format_string[pos:])
            break
        out.append(format_string[pos:percent])
        if percent + 1 < len(format_string) and format_string[percent + 1] == '%':
            out.append('%')
            pos = percent + 2
            continue
        match = _FORMAT_DIRECTIVE.match(format_string, percent)
        if match is None:
            out.append('%!(NOVERB)')
            break
        index = match.group('index')
        if index is not None:
            arg_index = int(index[1:-1]) - 1
        flags = match.group('flags')
        width_text = match.group('width')
        precision_text = match.group('precision')
        if width_text == '*':
            if arg_index >= len(args) or not isinstance(args[arg_index], int):
                out.append('%!(BADWIDTH)')
                pos = match.end()
                continue
            width = args[arg_index]
            arg_index += 1
        else:
            width = int(width_text) if width_text else None
        if precision_text == '*':
            if arg_index >= len(args) or not isinstance(args[arg_index], int):
                out.append('%!(BADPREC)')
                pos = match.end()
                continue
            precision = args[arg_index]
            arg_index += 1
        else:
            precision = int(precision_text) if precision_text else None
        verb = match.group('verb')
        if arg_index >= len(args):
            out.append(f'%!{verb}(MISSING)')
        else:
            rendered = _format_directive(args[arg_index], verb, flags, precision)
            arg_index += 1
            out.append(_apply_width(rendered, flags, width))
        pos = match.end()
    return ''.join(out)


## HTML escaping


_HTML_ESCAPES = {
    '\x00': '\ufffd',
    '"': '&#34;',
    "'": '&#39;',
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
}


def html_escape_string(value: str) -> str:
    return ''.join(_HTML_ESCAPES.get(char, char) for char in value)


def html_escape(wr: ta.TextIO, data: bytes) -> None:
    wr.write(html_escape_string(data.decode(errors='replace')))


def html_escaper(*args: ta.Any) -> str:
    return html_escape_string(go_sprint(*args))


## JavaScript escaping


_JS_ESCAPES = {
    '\\': r'\\',
    "'": r"\'",
    '"': r'\"',
    '<': r'\u003C',
    '>': r'\u003E',
    '&': r'\u0026',
    '=': r'\u003D',
}


def js_escape_string(value: str) -> str:
    out: list[str] = []
    for char in value:
        if (escaped := _JS_ESCAPES.get(char)) is not None:
            out.append(escaped)
        elif ord(char) < 0x20:
            out.append(f'\\u00{ord(char):02X}')
        elif char.isprintable():
            out.append(char)
        elif ord(char) <= 0xFFFF:
            out.append(f'\\u{ord(char):04X}')
        else:
            # Go's fmt with %04X emits all required hexadecimal digits for code points above the BMP.
            out.append(f'\\u{ord(char):04X}')
    return ''.join(out)


def js_escape(wr: ta.TextIO, data: bytes) -> None:
    wr.write(js_escape_string(data.decode(errors='replace')))


def js_escaper(*args: ta.Any) -> str:
    return js_escape_string(go_sprint(*args))


def url_query_escaper(*args: ta.Any) -> str:
    return urllib.parse.quote_plus(go_sprint(*args), safe='')
