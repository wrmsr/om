import ast

import pytest

from ..minifying import minify
from ..minifying import print_minified
from ..verification import verify_roundtrip


def roundtrip(src):
    tree = ast.parse(src)
    out = print_minified(tree)
    verify_roundtrip(tree, out)
    return out.rstrip('\n')


##


@pytest.mark.parametrize(('src', 'expected'), [
    ('x = 1\ny = 2\nz = 3\n', 'x=1;y=2;z=3'),
    ('if x:\n    y = 3\n    z = 4\nelse:\n    pass\n', 'if x:y=3;z=4\nelse:pass'),
    ('if a:\n    if b:\n        pass\n    else:\n        if c:\n            pass\n', 'if a:\n if b:pass\n elif c:pass'),
    ('def f(a, b=1, /, c=2, *args, d, e=3, **kw) -> int:\n    return a\n', 'def f(a,b=1,/,c=2,*args,d,e=3,**kw)->int:return a'),  # noqa
    ('def f(*, a): pass\n', 'def f(*,a):pass'),
    ('class A(B, metaclass=M):\n    x: int = 1\n', 'class A(B,metaclass=M):x:int=1'),
    ('@dec\n@dec2(1)\ndef f(): pass\n', '@dec\n@dec2(1)\ndef f():pass'),
    ('try:\n    pass\nexcept (A, B) as e:\n    raise X from e\nelse:\n    pass\nfinally:\n    pass\n', 'try:pass\nexcept(A,B)as e:raise X from e\nelse:pass\nfinally:pass'),  # noqa
    ('async def g():\n    async with a as b, c as (d, e):\n        await x\n    async for i in y:\n        yield i\n', 'async def g():\n async with a as b,c as(d,e):await x\n async for i in y:yield i'),  # noqa
    ('from . import a\nfrom .. import b\nfrom ...c import d as e, f\nimport os.path as p, sys\n', 'from.import a;from..import b;from...c import d as e,f;import os.path as p,sys'),  # noqa
    ('def f():\n    global a, b\n    nonlocal c\n', 'def f():global a,b;nonlocal c'),
    ('for x in a, b:\n    continue\nelse:\n    break\n', 'for x in a,b:continue\nelse:break'),
    ('while x:\n    del a, b\n', 'while x:del a,b'),
    ('assert x, "m"\n', "assert x,'m'"),
])
def test_statements(src, expected):
    assert roundtrip(src) == expected


@pytest.mark.parametrize(('src', 'expected'), [
    ('-1 ** 2', '-1**2'),
    ('(-1) ** 2', '(-1)**2'),
    ('2 ** -1', '2**-1'),
    ('2 ** -x ** 2', '2**-x**2'),
    ('(a ** b) ** c', '(a**b)**c'),
    ('a - (b - c)', 'a-(b-c)'),
    ('a - b - c', 'a-b-c'),
    ('a * (b + c)', 'a*(b+c)'),
    ('not (a and b)', 'not(a and b)'),
    ('not a and b', 'not a and b'),
    ('a or (b and c)', 'a or b and c'),
    ('(a or b) and c', '(a or b)and c'),
    ('a or (b or c)', 'a or(b or c)'),
    ('(a < b) < c', '(a<b)<c'),
    ('a < b < c', 'a<b<c'),
    ('a is not b', 'a is not b'),
    ('a not in b', 'a not in b'),
    ('x if y else z', 'x if y else z'),
    ('(x if y else z) + 1', '(x if y else z)+1'),
    ('x if (y if z else w) else v', 'x if(y if z else w)else v'),
    ('x if y else (z if w else v)', 'x if y else z if w else v'),
    ('lambda a, /, b, *, c: (yield)', 'lambda a,/,b,*,c:(yield)'),
    ('(lambda: 1)()', '(lambda:1)()'),
    ('f(a=lambda: 1)', 'f(a=lambda:1)'),
    ('f(x for x in y)', 'f(x for x in y)'),
    ('f((x for x in y), 1)', 'f((x for x in y),1)'),
    ('f(*a, **b, c=1)', 'f(*a,**b,c=1)'),
    ('f(*(a or b))', 'f(*(a or b))'),
    ('[x for x in (a if b else c) if d]', '[x for x in(a if b else c)if d]'),
    ('[(a, b) for a, b in c]', '[(a,b)for a,b in c]'),
    ('{k: v for k, v in x}', '{k:v for k,v in x}'),
    ('{**a, "b": 1}', "{**a,'b':1}"),
    ('{**(a or b)}', '{**(a or b)}'),
    ('{*a}', '{*a}'),
    ('(a,)', 'a,'),
    ('()', '()'),
    ('x[1:2, ::3]', 'x[1:2,::3]'),
    ('x[(1, 2)]', 'x[1,2]'),
    ('x[(1,)]', 'x[1,]'),
    ('x[()]', 'x[()]'),
    ('x[(*a, b)]', 'x[(*a,b)]'),
    ('x[a := 1]', 'x[(a:=1)]'),
    ('x[(yield)]', 'x[(yield)]'),
    ('(1).real', '(1).real'),
    ('(...).x', '(...).x'),
    ('1.5.real', '1.5.real'),
    ('(-1).real', '(-1).real'),
    ('"a".join(b)', "'a'.join(b)"),
    ('1 if x else 2', '1 if x else 2'),
    ('0x1f if z else 1e5', '31 if z else 100000.0'),
    ('1 in f"x"', "1 in f'x'"),
    ('await x', 'await x'),
    ('(await x)()', '(await x)()'),
    ('await (-x)', 'await(-x)'),
    ('a if b else c', 'a if b else c'),
    ('(a if b else c)(d)', '(a if b else c)(d)'),
    ('a.b(c)[d].e', 'a.b(c)[d].e'),
    ('1_000_000', '1000000'),
    ('1e400', '1e999'),
    ('1e400j', '1e999j'),
    ('u"x"', "u'x'"),
    ('b"y"', "b'y'"),
    ("'a' 'b'", "'ab'"),
    ("'''multi\nline'''", "'multi\\nline'"),
])
def test_expressions(src, expected):
    assert roundtrip(src) == expected


@pytest.mark.parametrize(('src', 'expected'), [
    ('x = yield', 'x=yield'),
    ('x += yield', 'x+=yield'),
    ('x: int = yield 1, 2', 'x:int=yield 1,2'),
    ('yield a, b', 'yield a,b'),
    ('yield', 'yield'),
    ('return (yield)', 'return(yield)'),
    ('z = (yield), 1', 'z=(yield),1'),
    ('x = yield from g()', 'x=yield from g()'),
    ('return 1, 2', 'return 1,2'),
    ('return *a, b', 'return*a,b'),
    ('x = *a, b', 'x=*a,b'),
    ('*a, b = x', '*a,b=x'),
    ('(x := 1)', '(x:=1)'),
    ('x = (y := 2)', 'x=(y:=2)'),
    ('if (x := f()):\n    pass\n', 'if(x:=f()):pass'),
    ('for i in (*a, b):\n    pass\n', 'for i in(*a,b):pass'),
    ('for i in (yield):\n    pass\n', 'for i in(yield):pass'),
    ('del (a, b), c', 'del(a,b),c'),
    ('(y): int', '(y):int'),
    ('a.b: int', 'a.b:int'),
    ('a = b = c', 'a=b=c'),
    ('(*a, b)', '(*a,b)'),
    ('a, b', 'a,b'),
])
def test_statement_contexts(src, expected):
    assert roundtrip(src) == expected


@pytest.mark.parametrize(('src', 'expected'), [
    ('f"{x!r:>{w}} {d[\'k\']} {{lit}} {x=}"', 'f"{x!r:>{w}} {d[\'k\']} {{lit}} x={x!r}"'),
    ("f'{ {1: 2} }'", "f'{ {1:2}}'"),
    ("f'''{d['k']} {e[\"j\"]}'''", 'f"{d[\'k\']} {e[\'j\']}"'),
    ("f'{f\"{z}\"}'", 'f"{f\'{z}\'}"'),
    ("f'a'", "f'a'"),
    ("f''", "f''"),
    ("f'\\n{x}\\t'", "f'\\n{x}\\t'"),
    ("f'{x if y else z}'", "f'{(x if y else z)}'"),
    ("f'{(lambda: 1)}'", "f'{(lambda:1)}'"),
    ("f'{a!=b}'", "f'{a!=b}'"),
    ("f'{x:{\"<\"}10}'", 'f"{x:{\'<\'}10}"'),
    ("'a' f'{b}' 'c'", "f'a{b}c'"),
    ("f'{x}' 'it\\'s'", 'f"{x}it\'s"'),
    ("f'{x}' 'it\\'s \"and\"'", "f'{x}it\\'s \"and\"'"),
])
def test_fstrings(src, expected):
    assert roundtrip(src) == expected


def test_literal_statements():
    src = '"""doc"""\nclass A:\n    """doc"""\ndef f():\n    """doc"""\n    ...\n    x = 1\n    "note"\n'
    assert minify(src) == 'class A:0\ndef f():x=1\n'
    assert minify(src, keep_literal_statements=True) == "'doc'\nclass A:'doc'\ndef f():'doc';...;x=1;'note'\n"


def test_shebang():
    src = '#!/usr/bin/env python3\n# comment\nx = 1\n'
    assert minify(src) == '#!/usr/bin/env python3\nx=1\n'
    assert minify(src, no_shebang=True) == 'x=1\n'
