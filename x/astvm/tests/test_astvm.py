"""The CPython oracle executes only the fixed/generated test fixtures, never untrusted input."""
import ast
import dataclasses as dc
import io
import os
import random
import sys
import textwrap
import types

import pytest

from .. import astvm


## Differential helpers


def check(source, *, initial=None):
    source = textwrap.dedent(source)
    namespace = dict(initial or {})
    exec(source, namespace)
    vm = astvm.Interpreter()
    for key, value in (initial or {}).items():
        vm.set(key, value)
    vm.execute(source)
    assert vm.get('result') == namespace['result']
    return vm


def check_expression(expression):
    expected = eval(expression)
    vm = astvm.Interpreter()
    assert vm.evaluate(expression) == expected
    return vm


def guest_error(source, name):
    vm = astvm.Interpreter()
    with pytest.raises(astvm.GuestError) as caught:
        vm.execute(textwrap.dedent(source))
    assert caught.value.name == name
    return vm, caught.value


## Expressions and intrinsic values


@pytest.mark.parametrize('expression', [
    'None', 'True', 'False', '42', '-42', '3.125', '2+3j', "'hello'", "b'hello'", '...',
    '1 + 2 * 3', '(1 + 2) * 3', '-9 // 4', '-9 % 4', '5 / 2', '2 ** 40', '2 ** -3',
    '1 << 50', '(1 << 50) >> 47', '12 & 10', '12 | 10', '12 ^ 10', '~10', '+4',
    'not []', 'not [1]', '0 or 9', '[] or [2]', '[1] and [2]', '0 and 1 / 0', '1 or 1 / 0',
    '1 < 2 < 3', '1 > 2 < 1/0', '1 == 1.0', '1 != 2', 'None is None', 'True is not False',
    '1 if [1] else 2', '2 if [] else 3', '[1, 2] == [1.0, 2]', '[1, 2] < [1, 3]',
    '() < (1,)', "'abc' < 'abd'", '(1, [2]) == (1, [2.0])',
    "'abc' + 'def'", "'abc' * 4", "4 * 'abc'", "b'ab' * 3", '[1, 2] * 3', '(1, 2) * 2',
    '[1, 2] + [3]', '(1, 2) + (3,)', '[1, 2, 3][-1]', '[1, 2, 3][::-1]',
    "'abcdef'[1:5:2]", '(1, 2, 3)[:2]', 'b"abc"[1]', 'range(10)[2:8:2]',
    '[0, *range(3), 4]', '(0, *[1, 2])', '{0, *range(3)}', "{'a': 1, **{'b': 2}, 'a': 3}",
    '{True: 1, 1: 2}', '{(1, 2): 3}[(1.0, 2)]', '{1, 2} | {2, 3}',
    '{1, 2} & {2, 3}', '{1, 2} ^ {2, 3}', '{1, 2} - {2, 3}',
    "{'a': 1} | {'a': 2, 'b': 3}", '2 in [1, 2, 3]', '4 not in iter([1, 2, 3])',
    "'a' in {'a': 1}", '2 in {1, 2}', "'b' in 'abc'", '98 in b"abc"', '123456 in range(10**9)',
    'len([])', 'len(range(10, 0, -2))', 'bool(range(0))', 'list(range(5))', 'tuple(range(5))',
    'set([2, 2, 1])', 'frozenset([1, 2])', "dict([('a', 1), ('b', 2)], c=3)",
    'int()', "int('ff', 16)", "int('10', base=2)", 'float("1.25")', 'complex(1, 2)',
    'str(12)', 'str([1, 2])', 'bytes([0, 128, 255])', 'bytes(3)', 'bool()',
    'abs(-3)', 'round(1.234, 2)', 'pow(2, 8)', 'pow(3, -1, 11)', 'divmod(13, 4)',
    'min([3, 1, 2])', 'max(3, 1, 2)', 'min([], default=99)', 'sum(range(10))', 'sum([[1], [2]], [])',
    'all([1, 2, 3])', 'any([0, 0, 3])', 'all([])', 'any([])',
    'list(enumerate("abc", 5))', 'list(enumerate("abc", start=5))', 'list(zip(range(3), "abcde"))',
    'list(zip())', 'list(zip([1, 2], [3, 4], strict=True))', 'list(reversed(range(5)))',
    'list(map(lambda x: x * 2, range(4)))', 'list(map(lambda x, y: x + y, [1, 2], [3, 4]))',
    'list(filter(None, [0, 1, 0, 2]))', 'list(filter(lambda x: x % 2, range(8)))',
    'sorted([5, 2, 4, 1, 3])', 'sorted([5, 2, 4, 1, 3], reverse=True)',
    'sorted([5, 2, 4, 1, 3], key=lambda x: x % 2)',
    'sorted([5, 2, 4, 1, 3], key=lambda x: x % 2, reverse=True)',
    'min([5, 2, 4, 1, 3], key=lambda x: x % 2)', 'max([5, 2, 4, 1, 3], key=lambda x: x % 2)',
    'chr(9731)', "ord('a')", 'bin(17)', 'oct(17)', 'hex(17)',
    "' Hello '.strip().lower()", "'a,b,c'.split(',')", "'a,b,c'.rsplit(',', 1)",
    r"'a\nb\n'.splitlines()", "'-'.join(str(x) for x in range(4))", "'aaa'.replace('a', 'bb', 2)",
    "'abcdef'.startswith(('ab', 'cd'))", "'abcdef'.endswith('ef')", "'abcdef'.find('cd')",
    "'a,b'.partition(',')", "'abc'.removeprefix('ab')", "'123'.isdigit()", "b'abc'.hex()",
    "format(1.234, '.2f')", "f'{12:04d}'", "f'{3.14159:.{2}f}'", "f'{[1, 2]!r}'",
    "f'{chr(9731)!a}'", "f'value={2+3}'",
])
def test_expression_differential(expression):
    check_expression(expression)


@pytest.mark.parametrize('source', [
    '''
    a = b = []
    a.append(1)
    result = (a is b, b)
    ''',
    '''
    a, (b, *c), d = [1, range(4), 5]
    result = a, b, c, d
    ''',
    '''
    a = [0, 1, 2, 3, 4]
    a[1:4] = (i + 8 for i in range(2))
    a[::2] = [9, 8]
    del a[-1]
    result = a
    ''',
    '''
    a = [1, 2]
    b = a
    a += (x for x in [3, 4])
    a *= 2
    result = (a is b, a)
    ''',
    '''
    a = [1, 2]
    a.extend(a)
    result = a
    ''',
    '''
    a = [1, 2]
    a += a
    result = a
    ''',
    '''
    a = {'a': 1}
    b = a
    a |= [('b', 2)]
    result = (a is b, b)
    ''',
    '''
    a = {1, 2}
    b = a
    a |= {3}
    a &= {2, 3}
    a ^= {3, 4}
    result = (a is b, a)
    ''',
    '''
    a = [1, 2, 1, 3]
    result = [a.count(1), a.index(1, 1), a.pop()]
    a.insert(-20, 9)
    a.remove(1)
    a.reverse()
    result.append(a.copy())
    a.clear()
    result.append(a)
    ''',
    '''
    d = {'a': 1}
    result = [d.get('x'), d.setdefault('b', 2), d.setdefault('b', 3), d.pop('a')]
    d.update([('c', 3)], d=4)
    result += [d.popitem(), list(d.keys()), list(d.values()), list(d.items()), d.copy()]
    d.clear()
    result.append(d)
    ''',
    '''
    d = {'a': 1, 'b': 2}
    view = d.items()
    d['c'] = 3
    iterator = iter(view)
    first = next(iterator)
    d['b'] = 20
    result = first, next(iterator), len(view)
    ''',
    '''
    a = []
    it = iter(a)
    result = [next(it, 'end')]
    a.append(1)
    result.append(next(it, 'still-end'))
    ''',
    '''
    events = []
    def v(x):
        events.append(x)
        return x
    result = v(1) < v(2) < v(3), v(4) > v(5) < v(6), events
    ''',
    '''
    events = []
    a = [2]
    def obj():
        events.append('obj')
        return a
    def index():
        events.append('index')
        return 0
    def rhs():
        events.append('rhs')
        return 3
    obj()[index()] += rhs()
    result = a, events
    ''',
    '''
    events = []
    def values():
        for i in range(10):
            events.append(i)
            yield i
    try:
        a, b = values()
    except ValueError:
        pass
    result = events
    ''',
    '''
    values = [1]
    def items():
        yield 2
        raise ValueError('stop')
    try:
        values.extend(items())
    except ValueError:
        pass
    result = values
    ''',
])
def test_data_and_evaluation_order(source):
    check(source)


## Control flow and lexical environments


@pytest.mark.parametrize('source', [
    '''
    result = []
    for i in range(5):
        if i == 1:
            continue
        if i == 4:
            break
        result.append(i)
    else:
        result.append('bad')
    for j in []:
        result.append('bad')
    else:
        result.append('empty')
    i = 0
    while i < 3:
        i += 1
        if i == 2:
            continue
        result.append(i)
    else:
        result.append('while-else')
    ''',
    '''
    result = []
    for i in range(3):
        for j in range(3):
            if j == i:
                break
            result.append((i, j))
        else:
            result.append('bad')
    ''',
    '''
    def f(a, /, b=2, *args, c=3, **kw):
        return a, b, args, c, kw
    result = f(1, 4, 5, 6, c=7, d=8, a=9)
    ''',
    '''
    def f(a=[], *, b=[]):
        a.append(len(a))
        b.append(len(b))
        return a.copy(), b.copy()
    result = f(), f(), f.__defaults__[0], f.__kwdefaults__['b']
    ''',
    '''
    x = 1
    def outer():
        x = 2
        def read():
            return x
        def write(v):
            nonlocal x
            x = v
        write(3)
        return read
    f = outer()
    result = f(), x
    ''',
    '''
    def outer():
        def middle():
            def inner():
                return x
            return inner
        x = 42
        return middle()
    result = outer()()
    ''',
    '''
    x = 1
    def f():
        global x
        x += 1
    f()
    result = x
    ''',
    '''
    def f():
        x = 1
        def g():
            nonlocal x
            del x
        g()
        try:
            return x
        except UnboundLocalError:
            return 'unbound'
    result = f()
    ''',
    '''
    def f(n):
        if n < 2:
            return n
        return f(n - 1) + f(n - 2)
    result = f(9)
    ''',
    '''
    events = []
    def decorator(n):
        events.append(('decorator', n))
        def apply(fn):
            events.append(('apply', n))
            return lambda *a, **kw: fn(*a, **kw) + n
        return apply
    def default():
        events.append('default')
        return 4
    @decorator(1)
    @decorator(2)
    def f(x=default()):
        return x
    result = f(), events
    ''',
    '''
    events = []
    def value(x):
        events.append(x)
        return x
    def f(*a, **kw):
        return a, kw
    result = f(c=value(3), *[value(1), value(2)], **{'d': value(4)}), events
    ''',
    '''
    result = []
    def f(**kw):
        return kw
    try:
        f(a=1, **{'a': 2})
    except TypeError:
        result.append('duplicate')
    ''',
    '''
    x = 100
    result = [x * y for x in range(5) if x % 2 for y in range(x) if y != 1], x
    ''',
    '''
    x = -1
    result = [(x := i) for i in range(4)], x
    ''',
    '''
    result = {x: x*x for x in range(5)}, {x % 3 for x in range(8)}
    ''',
    '''
    functions = [lambda: i for i in range(4)]
    result = [f() for f in functions]
    ''',
    '''
    events = []
    def iterable():
        events.append('created')
        return range(3)
    g = (x * 2 for x in iterable())
    events.append('before-next')
    result = next(g), list(g), events
    ''',
    '''
    def f():
        x = 1
        d = locals()
        d['x'] = 9
        d['z'] = 8
        return x, 'z' in locals()
    result = f()
    ''',
    '''
    def f():
        return globals()
    f.__globals__['x'] = 42
    result = f() is globals(), x
    ''',
])
def test_control_and_functions(source):
    check(source)


@pytest.mark.parametrize('source, name', [
    ('x = x', 'NameError'),
    ('def f():\n x += 1\nf()', 'UnboundLocalError'),
    ('x = 1\ndef f():\n x\n x = 2\nf()', 'UnboundLocalError'),
    ('def f(a): pass\nf()', 'TypeError'),
    ('def f(a): pass\nf(1, 2)', 'TypeError'),
    ('def f(a, /): pass\nf(a=1)', 'TypeError'),
    ('def f(*, a): pass\nf()', 'TypeError'),
    ('def f(a): pass\nf(1, a=2)', 'TypeError'),
    ('def f(): pass\nf(a=1)', 'TypeError'),
    ('[1][9]', 'IndexError'),
    ('{}[1]', 'KeyError'),
    ('1 / 0', 'ZeroDivisionError'),
    ('1 << -1', 'ValueError'),
    ('range(1, 2, 0)', 'ValueError'),
    ('len(1)', 'TypeError'),
    ('next([1])', 'TypeError'),
    ('a, b = [1]', 'ValueError'),
    ('a, b = [1, 2, 3]', 'ValueError'),
    ('a = [1,2,3]\na[::2] = [1]', 'ValueError'),
    ('{[]: 1}', 'TypeError'),
    ('min([])', 'ValueError'),
    ('list(zip([1, 2], [3], strict=True))', 'ValueError'),
    ('list(zip([1], [2, 3], strict=True))', 'ValueError'),
    ('bool(NotImplemented)', 'TypeError'),
    ('raise 1', 'TypeError'),
    ('raise', 'RuntimeError'),
])
def test_guest_errors(source, name):
    guest_error(source, name)


## Exceptions and structured unwinding


@pytest.mark.parametrize('source', [
    '''
    result = []
    try:
        1 / 0
    except (ValueError, ZeroDivisionError) as e:
        result.append(type(e).__name__)
    else:
        result.append('bad')
    finally:
        result.append('finally')
    result.append('e' in globals())
    ''',
    '''
    result = []
    try:
        result.append('body')
    except Exception:
        result.append('bad')
    else:
        result.append('else')
    finally:
        result.append('finally')
    ''',
    '''
    result = []
    def f():
        try:
            return 1
        finally:
            result.append('cleanup')
    result.append(f())
    ''',
    '''
    def f():
        try:
            return 1
        finally:
            return 2
    result = f()
    ''',
    '''
    def f():
        try:
            1 / 0
        finally:
            return 3
    result = f()
    ''',
    '''
    result = []
    for i in range(4):
        try:
            if i == 1:
                continue
            if i == 2:
                break
        finally:
            result.append(i)
    else:
        result.append('bad')
    ''',
    '''
    result = []
    for i in range(2):
        try:
            break
        finally:
            result.append(i)
            continue
    else:
        result.append('else')
    ''',
    '''
    def f():
        try:
            1 / 0
        except ZeroDivisionError:
            try:
                raise ValueError('inner')
            except ValueError:
                pass
            raise
    try:
        f()
    except Exception as e:
        result = type(e).__name__
    ''',
    '''
    def f():
        raise
    try:
        raise ValueError('x')
    except ValueError:
        try:
            f()
        except ValueError as e:
            result = e.args
    ''',
    '''
    try:
        try:
            raise ValueError('first')
        except ValueError:
            raise TypeError('second') from KeyError('cause')
    except TypeError as e:
        result = e.args, e.__context__.args, e.__cause__.args, e.__suppress_context__
    ''',
    '''
    try:
        try:
            raise ValueError('first')
        finally:
            raise KeyError('second')
    except KeyError as e:
        result = e.args, type(e.__context__).__name__
    ''',
    '''
    try:
        try:
            1 / 0
        except ZeroDivisionError:
            raise ValueError('x') from None
    except ValueError as e:
        result = e.__cause__, e.__suppress_context__, type(e.__context__).__name__
    ''',
    '''
    result = []
    try:
        try:
            raise ValueError('x')
        except 1:
            pass
        finally:
            result.append('cleanup')
    except TypeError:
        result.append('invalid-handler')
    ''',
    '''
    x = 'old'
    try:
        raise ValueError('x')
    except ValueError as x:
        del x
    result = 'x' in globals()
    ''',
    '''
    result = []
    def f():
        try:
            raise ValueError('x')
        except ValueError as e:
            return lambda: e
    g = f()
    try:
        g()
    except NameError:
        result.append('deleted-cell')
    ''',
    '''
    result = []
    try:
        assert False, 'bad'
    except AssertionError as e:
        result.append(e.args)
    assert True, 1 / 0
    ''',
])
def test_exception_unwinding(source):
    check(source)


## Minimal classes and special methods


@pytest.mark.parametrize('source', [
    '''
    class C:
        n = 2
        def __init__(self, x):
            self.x = x
        def plus(self, n=1):
            self.x += n
            return self.x
    c = C(3)
    f = c.plus
    result = C.n, f(4), C.plus(c), f.__self__ is c, f.__func__ is C.plus
    ''',
    '''
    class A:
        def f(self):
            return 1
    class B(A):
        def f(self):
            return A.f(self) + 2
    b = B()
    result = b.f(), isinstance(b, A), isinstance(b, B), issubclass(B, A), B.__bases__[0] is A
    ''',
    '''
    class C:
        n = 4
        @staticmethod
        def twice(n):
            return n * 2
        @classmethod
        def total(cls, x):
            return cls.n + x
    result = C.twice(3), C().twice(4), C.total(5), C().total(6)
    ''',
    '''
    class C:
        def __init__(self):
            self.values = [1, 2]
        def __getitem__(self, i):
            return self.values[i]
        def __setitem__(self, i, v):
            self.values[i] = v
        def __delitem__(self, i):
            del self.values[i]
        def __len__(self):
            return len(self.values)
    c = C()
    c[0] += 5
    result = c[0], len(c), bool(c)
    del c[1]
    result += (c.values,)
    ''',
    '''
    class Counter:
        def __init__(self, n):
            self.n = n
            self.i = 0
        def __iter__(self):
            return self
        def __next__(self):
            if self.i == self.n:
                raise StopIteration
            self.i += 1
            return self.i
    result = list(Counter(4))
    ''',
    '''
    class C:
        def __init__(self, n):
            self.n = n
        def __bool__(self):
            return self.n > 0
        def __call__(self, x):
            return x + self.n
        def __add__(self, x):
            return self.n + x
        def __radd__(self, x):
            return x + self.n
        def __neg__(self):
            return -self.n
        def __contains__(self, x):
            return x == self.n
        def __str__(self):
            return 'C:' + str(self.n)
        def __repr__(self):
            return 'C(' + str(self.n) + ')'
    c = C(3)
    result = bool(c), c(4), c+5, 5+c, -c, 3 in c, 4 not in c, str(c), repr(c), f'{c!r}'
    ''',
    '''
    events = []
    class A:
        def __add__(self, other):
            events.append('A.add')
            return NotImplemented
    class B(A):
        def __radd__(self, other):
            events.append('B.radd')
            return 5
    result = A() + B(), events
    ''',
    '''
    class C:
        def __init__(self, n):
            self.n = n
        def __iadd__(self, x):
            self.n += x
            return self
    a = C(1)
    b = a
    a += 2
    result = a is b, b.n
    ''',
    '''
    class C:
        def __eq__(self, other):
            return [1]
        def __lt__(self, other):
            return 0
    a = C()
    b = C()
    result = a == b, a != b, a < b, a in [b]
    ''',
    '''
    class C:
        def __format__(self, spec):
            return '<' + spec + '>'
    result = f'{C():hello}'
    ''',
    '''
    class C:
        x = 1
    c = C()
    c.x = 2
    c.__dict__['y'] = 3
    del c.x
    result = c.x, c.y, vars(c), hasattr(c, 'z'), getattr(c, 'z', 4)
    ''',
    '''
    x = 'global'
    def outer():
        x = 'outer'
        class C:
            x = 'class'
            def method(self):
                return x
        return C
    result = outer()().method()
    ''',
    '''
    class E(ValueError):
        pass
    try:
        raise E('custom')
    except ValueError as e:
        result = type(e).__name__, e.args, isinstance(e, Exception)
    ''',
])
def test_classes(source):
    check(source)


@pytest.mark.parametrize('source, name', [
    ('class C:\n def __init__(self): return 1\nC()', 'TypeError'),
    ('class C:\n def __bool__(self): return 1\nbool(C())', 'TypeError'),
    ('class C:\n def __len__(self): return -1\nbool(C())', 'ValueError'),
    ('class C:\n def __iter__(self): return []\niter(C())', 'TypeError'),
    ('class C:\n def __repr__(self): return 1\nrepr(C())', 'TypeError'),
    ('class C:\n pass\nC().__class__ = C', 'AttributeError'),
    ('class C:\n def __del__(self): pass', 'TypeError'),
    ('class C:\n def __getattribute__(self, name): pass', 'TypeError'),
    ('class C(int): pass', 'TypeError'),
])
def test_class_restrictions(source, name):
    guest_error(source, name)


## Context managers, including partial entry and cleanup errors


_CONTEXT = '''
events = []
class Manager:
    def __init__(self, name, suppress=False, fail=False):
        self.name = name
        self.suppress = suppress
        self.fail = fail
    def __enter__(self):
        events.append(('enter', self.name))
        if self.fail:
            raise ValueError('enter')
        return self
    def __exit__(self, typ, value, tb):
        events.append(('exit', self.name, None if typ is None else typ.__name__))
        return self.suppress
'''


@pytest.mark.parametrize('body', [
    '''
    with Manager('a') as a, Manager('b') as b:
        events.append(('body', a.name, b.name))
    result = events
    ''',
    '''
    with Manager('a', True):
        raise ValueError('body')
    result = events
    ''',
    '''
    def f():
        with Manager('a'):
            return 4
    result = f(), events
    ''',
    '''
    try:
        with Manager('a'), Manager('b', fail=True):
            pass
    except ValueError:
        events.append('caught')
    result = events
    ''',
    '''
    try:
        with Manager('a') as (x, y):
            pass
    except TypeError:
        events.append('unpack-failed')
    result = events
    ''',
    '''
    for i in range(3):
        with Manager(str(i)):
            if i == 0:
                continue
            break
    result = events
    ''',
    '''
    class Bad(Manager):
        def __exit__(self, *args):
            raise TypeError('exit')
    try:
        with Bad('a'):
            raise ValueError('body')
    except TypeError as e:
        result = type(e.__context__).__name__, events
    ''',
    '''
    class Reraise(Manager):
        def __exit__(self, *args):
            raise
    try:
        with Reraise('a'):
            raise ValueError('body')
    except ValueError as e:
        result = e.args, events
    ''',
])
def test_context_managers(body):
    check(_CONTEXT + textwrap.dedent(body))


## Generator protocol and suspension inside complex control flow


@pytest.mark.parametrize('source', [
    '''
    def g():
        yield 1
        x = yield 2
        yield x
        return 9
    a = g()
    result = [next(a), a.send(None), a.send(8)]
    try:
        next(a)
    except StopIteration as e:
        result.append(e.value)
    result.append(next(a, 'closed'))
    ''',
    '''
    def g():
        yield 1 + (yield 2) * 3
    a = g()
    result = next(a), a.send(4), next(a, 'end')
    ''',
    '''
    def g():
        a = [(yield 1), (yield 2)]
        yield a
    a = g()
    result = next(a), a.send(10), a.send(20)
    ''',
    '''
    def f(a, b):
        return a + b
    def g():
        yield f((yield 1), (yield 2))
    a = g()
    result = next(a), a.send(3), a.send(4)
    ''',
    '''
    def g():
        try:
            yield 1
        except ValueError as e:
            yield e.args
            yield 3
        finally:
            events.append('finally')
    events = []
    a = g()
    result = [next(a), a.throw(ValueError('x')), next(a), next(a, 'end'), events]
    ''',
    '''
    events = []
    def g():
        try:
            yield 1
        finally:
            events.append('finally')
    a = g()
    result = [next(a), a.close(), a.close(), next(a, 'end'), events]
    ''',
    '''
    events = []
    def g():
        try:
            yield 1
        finally:
            events.append('finally')
    a = g()
    a.close()
    result = events, next(a, 'end')
    ''',
    '''
    events = []
    def g():
        try:
            yield 1
        finally:
            events.append('finally')
    a = g()
    try:
        a.throw(ValueError('x'))
    except ValueError as e:
        result = e.args, events, next(a, 'end')
    ''',
    '''
    def g():
        yield 1
    a = g()
    try:
        a.send(1)
    except TypeError:
        pass
    result = next(a)
    ''',
    '''
    def g():
        raise StopIteration('oops')
        yield
    try:
        next(g())
    except RuntimeError as e:
        result = type(e.__cause__).__name__, e.__cause__.args
    ''',
    '''
    def g():
        try:
            yield 1
        except GeneratorExit:
            yield 2
            return 3
    a = g()
    result = [next(a)]
    try:
        a.close()
    except RuntimeError:
        result.append('ignored')
    try:
        next(a)
    except StopIteration as e:
        result.append(e.value)
    ''',
    '''
    def g():
        try:
            next(a)
        except ValueError:
            yield 'reentrant'
    a = g()
    result = list(a)
    ''',
    '''
    def sub():
        x = yield 1
        try:
            yield x + 1
        except ValueError:
            yield 99
        return 7
    def outer():
        r = yield from sub()
        yield r
        return 8
    a = outer()
    result = [next(a), a.send(8), a.throw(ValueError), next(a)]
    try:
        next(a)
    except StopIteration as e:
        result.append(e.value)
    ''',
    '''
    def g():
        x = yield from [1, 2]
        yield x
    result = list(g())
    ''',
    '''
    def g():
        try:
            yield from [1, 2]
        except ValueError as e:
            yield e.args
    a = g()
    result = next(a), a.throw(ValueError, 'oops'), next(a, 'end')
    ''',
    '''
    events = []
    def a():
        try:
            yield 1
        finally:
            events.append('a')
    def b():
        try:
            yield from a()
        finally:
            events.append('b')
    def c():
        try:
            yield from b()
        finally:
            events.append('c')
    g = c()
    result = [next(g), g.close(), events]
    ''',
    '''
    def g():
        try:
            return 10
        finally:
            yield 1
            yield 2
    a = g()
    result = [next(a), next(a)]
    try:
        next(a)
    except StopIteration as e:
        result.append(e.value)
    ''',
    '''
    def g():
        try:
            raise ValueError('pending')
        finally:
            yield 'cleanup'
    a = g()
    result = [next(a)]
    try:
        next(a)
    except ValueError as e:
        result.append(e.args)
    ''',
    '''
    def g():
        for i in range(3):
            try:
                yield i
                if i == 1:
                    break
            finally:
                yield -i
        else:
            yield 'else'
    result = list(g())
    ''',
    '''
    def g():
        try:
            raise ValueError('inside')
        except ValueError:
            yield 1
            raise
    a = g()
    next(a)
    try:
        raise TypeError('outside')
    except TypeError:
        try:
            next(a)
        except ValueError as e:
            result = e.args
    ''',
    '''
    def g():
        try:
            yield 1
        except (TypeError, ValueError) as e:
            yield e.args
    a = g()
    next(a)
    result = a.throw(ValueError, ('a', 'b'), None)
    ''',
    '''
    events = []
    class C:
        def __iter__(self):
            return self
        def __next__(self):
            return 1
        def send(self, value):
            return value + 2
        def throw(self, exc):
            events.append(exc.args)
            raise StopIteration(8)
        def close(self):
            events.append('closed')
    def g():
        yield (yield from C())
    a = g()
    result = next(a), a.send(3), a.throw(ValueError('v')), events
    ''',
])
def test_generators(source):
    check(source)


def test_generator_with_manager():
    check(_CONTEXT + textwrap.dedent('''
    def g():
        with Manager('a'):
            yield 1
            yield 2
    a = g()
    result = [next(a), list(events)]
    a.close()
    result.append(events)
    '''))


def test_close_return_value():
    vm = astvm.Interpreter()
    vm.execute('''
def g():
    try:
        yield 1
    except GeneratorExit:
        return 42
a = g()
next(a)
result = a.close()
''')
    assert vm.get('result') == 42


## Deferred annotations. These expectations intentionally target 3.14, also on a 3.13 host.


def test_deferred_function_annotations_cache():
    vm = astvm.Interpreter()
    vm.execute('''
events = []
T = 1
def annotation():
    events.append(T)
    return T
def f(a: annotation(), *b: T, c: T = 3, **d: T) -> annotation():
    return a
before = list(events)
T = 9
one = f.__annotations__
T = 10
two = f.__annotations__
result = before, one, two is one, events
''')
    assert vm.get('result') == ([], {'a': 9, 'b': 9, 'c': 9, 'd': 9, 'return': 9}, True, [9, 9])


def test_annotation_failure_is_retryable():
    vm = astvm.Interpreter()
    vm.execute('''
def f(x: Missing): pass
try:
    f.__annotations__
except NameError:
    pass
Missing = 7
result = f.__annotations__
''')
    assert vm.get('result') == {'x': 7}


def test_annotation_closure_and_class_scope():
    vm = astvm.Interpreter()
    vm.execute('''
def outer():
    T = 1
    def f(x: T): pass
    T = 2
    return f
class C:
    T = 3
    def f(self, x: T): pass
    T = 4
result = outer().__annotations__, C.f.__annotations__
''')
    assert vm.get('result') == ({'x': 2}, {'x': 4})


def test_local_annotations_are_not_evaluated():
    check('''
    def f():
        x: 1 / 0 = 3
        y: Missing
        return x
    result = f()
    ''')


def test_module_and_class_annotation_basics():
    vm = astvm.Interpreter()
    vm.execute('''
T = 1
x: T = 3
T = 2
a = __annotations__
class C:
    T = 4
    x: T = 3
    T = 5
result = a, C.__annotations__
''')
    assert vm.get('result') == ({'x': 2}, {'x': 5})


## Intrinsic/source imports, with an isolated cache and no host import fallback


def test_source_modules_and_isolated_globals():
    vm = astvm.Interpreter(modules={
        'numbers': astvm.SourceModule('''
counter = 0
def square(x):
    global counter
    counter += 1
    return x*x
'''),
        'constants': {'answer': 42, 'data': [1, 2]},
    })
    vm.execute('''
import numbers
import numbers as same
from numbers import square
from constants import answer
result = numbers is same, square(3), numbers.counter, answer
''')
    assert vm.get('result') == (True, 9, 1, 42)
    with pytest.raises(KeyError):
        vm.get('counter')


def test_circular_source_imports():
    vm = astvm.Interpreter(modules={
        'a': astvm.SourceModule('value = 1\nimport b\nother = b.value'),
        'b': astvm.SourceModule('import a\nvalue = a.value + 1'),
    })
    vm.execute('import a\nresult = a.value, a.other')
    assert vm.get('result') == (1, 2)


def test_failed_source_import_removed_from_cache():
    effects = []
    module = astvm.HostObject({'record': effects.append})
    vm = astvm.Interpreter(modules={
        'effects': {'sink': module},
        'bad': astvm.SourceModule("from effects import sink\nsink.record(1)\nraise ValueError('bad')"),
    })
    vm.execute('''
for i in range(2):
    try:
        import bad
    except ValueError:
        pass
''')
    assert effects == [1, 1]


@pytest.mark.parametrize('source', ['import os', 'import sys', 'from builtins import exec', 'from os import system'])
def test_import_denied(source):
    guest_error(source, 'ModuleNotFoundError')


## Closed object boundary and explicit effects


@pytest.mark.parametrize('expression', [
    "().__class__.__bases__[0].__subclasses__()",
    "(lambda: 0).__code__", "(lambda: 0).__closure__", "(lambda: 0).__dict__['host']",
    "(x for x in ()).gi_frame", "(x for x in ()).gi_code", "len.__self__", "len.__globals__",
    "[].__getattribute__", "[].__reduce__", "object.__subclasses__", "type.__call__", "type.__mro__",
    "'x'.format", "'x'.format_map", "'x'.__reduce_ex__", "int.__new__", "object.__getattribute__",
])
def test_no_native_introspection(expression):
    vm = astvm.Interpreter()
    with pytest.raises(astvm.GuestError) as caught:
        vm.evaluate_value(expression)
    assert caught.value.name in ('AttributeError', 'KeyError')


@pytest.mark.parametrize('name', ['open', 'exec', 'eval', 'compile', '__import__', 'input', 'help', 'breakpoint', 'print', 'super'])
def test_no_ambient_authority(name):
    guest_error(name, 'NameError')


def test_guest_globals_are_only_guest_globals():
    vm = astvm.Interpreter()
    vm.execute('''
def f(): return 1
f.__globals__['exec'] = lambda x: 'guest only'
result = exec('ignored'), '__builtins__' in f.__globals__, hasattr(f, '__code__')
''')
    assert vm.get('result') == ('guest only', False, False)


def test_plain_inputs_copy_preserving_aliases_and_cycles():
    data = []
    data.append(data)
    pair = [data, data]
    vm = astvm.Interpreter()
    vm.set('a', pair)
    vm.execute("a[0].append(3)\nresult = a[0] is a[1], a[0][0] is a[0]")
    assert vm.get('result') == (True, True)
    assert len(data) == 1
    exported = vm.get('a')
    assert exported[0] is exported[1]
    assert exported[0][0] is exported[0]
    assert exported[0][1] == 3


def test_native_subclass_is_rejected_without_dispatch():
    events = []

    class Trap(list):
        def __iter__(self):
            events.append('iter')
            raise AssertionError

        def __getattribute__(self, name):
            if name != '__class__':
                events.append(name)
            return list.__getattribute__(self, name)

    vm = astvm.Interpreter()
    with pytest.raises(astvm.BoundaryError):
        vm.set('x', Trap([1, 2]))
    assert events == []


@pytest.mark.parametrize('value', [object(), len, int, io.StringIO('secret'), types.SimpleNamespace(x=1)])
def test_arbitrary_native_values_rejected(value):
    with pytest.raises(astvm.BoundaryError):
        astvm.Interpreter().set('x', value)


def test_capability_plain_data_roundtrip():
    calls = []

    def calculate(a, *, multiplier=1):
        calls.append((a, multiplier))
        return {'answer': sum(a) * multiplier}

    vm = astvm.Interpreter()
    vm.grant('calculate', calculate)
    vm.execute('result = calculate([1,2,3], multiplier=2)')
    assert vm.get('result') == {'answer': 12}
    assert calls == [([1, 2, 3], 2)]


def test_capability_cannot_receive_guest_functions_as_native_callables():
    calls = []
    vm = astvm.Interpreter()
    vm.grant('host', calls.append)
    with pytest.raises(astvm.BoundaryError):
        vm.execute('host(lambda: 1)')
    assert not calls


def test_capability_cannot_smuggle_native_objects():
    vm = astvm.Interpreter()
    vm.grant('host', lambda: io.StringIO('secret'))
    with pytest.raises(astvm.BoundaryError):
        vm.execute('''
try:
    host()
except BaseException:
    caught = True
''')
    with pytest.raises(astvm.InterpreterError):
        vm.execute('x=1')


def test_capability_exception_translation_is_explicit():
    def expected_failure():
        raise astvm.CapabilityFailure('ValueError', 'expected')

    vm = astvm.Interpreter()
    vm.grant('host', expected_failure)
    vm.execute('''
try:
    host()
except ValueError as e:
    result = e.args, type(e).__name__
''')
    assert vm.get('result') == (('expected',), 'ValueError')


def test_unexpected_capability_failure_is_not_guest_catchable():
    def bad():
        raise ValueError('host bug')

    vm = astvm.Interpreter()
    vm.grant('host', bad)
    with pytest.raises(astvm.CapabilityError):
        vm.execute('''
try:
    host()
except BaseException:
    result = 'caught'
''')


def test_host_object_has_only_granted_methods():
    stream = io.StringIO('hello')
    handle = astvm.HostObject({'read': stream.read, 'close': stream.close})
    vm = astvm.Interpreter()
    vm.grant('acquire', lambda: handle)
    vm.execute("f=acquire()\nresult=f.read(2), hasattr(f, 'getvalue'), hasattr(f.read, '__self__')")
    assert vm.get('result') == ('he', False, False)
    assert stream.tell() == 2


def test_real_open_can_be_explicitly_adapted(tmp_path):
    path = os.path.join(str(tmp_path), 'data.txt')
    with open(path, 'w') as out:
        out.write('hello')
    handles = []

    def open_text(name):
        if name != 'data':
            raise astvm.CapabilityFailure('PermissionError', name)
        stream = open(path)
        handles.append(stream)
        handle = astvm.HostObject({
            'read': stream.read,
            '__enter__': lambda: handle,
            '__exit__': lambda *args: stream.close(),
        })
        return handle

    vm = astvm.Interpreter()
    vm.grant('open', open_text)
    vm.execute("with open('data') as f:\n result = f.read()")
    assert vm.get('result') == 'hello'
    assert handles[0].closed


def test_reentrancy_from_capability_is_rejected():
    vm = astvm.Interpreter()
    vm.grant('again', lambda: vm.execute('x=1'))
    with pytest.raises(astvm.CapabilityError):
        vm.execute('again()')


def test_host_reference_cannot_cross_interpreters():
    one = astvm.Interpreter()
    two = astvm.Interpreter()
    function = one.evaluate_value('lambda: 1')
    with pytest.raises(astvm.BoundaryError):
        two.call_value(function)


## Checkpoints restore execution, aliases, closures, iterators and suspended generators


def test_heap_rollback_preserves_aliases():
    vm = astvm.Interpreter()
    vm.execute('a=[]\nb=a\na.append(a)')
    checkpoint = vm.checkpoint()
    vm.execute('a.append(2)\nb=[3]')
    vm.restore(checkpoint)
    assert vm.evaluate('a is b and a[0] is a and len(a)==1') is True


def test_suspended_generator_rollback():
    vm = astvm.Interpreter()
    vm.execute('''
events=[]
def g():
    try:
        x = yield 1
        events.append(x)
        yield x+1
    finally:
        events.append('finally')
a=g()
next(a)
''')
    checkpoint = vm.checkpoint()
    vm.execute("result=a.send(5)\na.close()")
    assert vm.get('result') == 6
    assert vm.get('events') == [5, 'finally']
    vm.restore(checkpoint)
    vm.execute("result=a.send(9)\na.close()")
    assert vm.get('result') == 10
    assert vm.get('events') == [9, 'finally']


def test_closure_and_iterator_rollback():
    vm = astvm.Interpreter()
    vm.execute('''
def outer():
    n=0
    def f():
        nonlocal n
        n+=1
        return n
    return f
f=outer()
it=iter([1,2,3])
''')
    checkpoint = vm.checkpoint()
    assert vm.evaluate('(f(), next(it))') == (1, 1)
    assert vm.evaluate('(f(), next(it))') == (2, 2)
    vm.restore(checkpoint)
    assert vm.evaluate('(f(), next(it))') == (1, 1)


_REPLAY_PROGRAM = '''
events=[]
class C:
    def __enter__(self):
        events.append('enter')
        return self
    def __exit__(self, *args):
        events.append('exit')
def child():
    try:
        x=yield 2
        yield x+1
        return 9
    finally:
        events.append('child-finally')
def parent():
    with C():
        r=yield from child()
        yield r
        return 10
g=parent()
result=[next(g), g.send(5), next(g)]
g.close()
result.append(events)
'''


@pytest.mark.parametrize('offset', [0, 1, 2, 5, 10, 20, 30, 50, 80, 100, 125, 150, 175, 200, 250, 300])
def test_mid_execution_checkpoint_replay(offset):
    vm = astvm.Interpreter()
    vm.start(_REPLAY_PROGRAM)
    vm.step(offset)
    snapshot = vm.checkpoint()
    before = vm.steps_used
    vm.run()
    expected = vm.get('result')
    used = vm.steps_used
    vm.restore(snapshot)
    assert vm.steps_used >= used >= before
    vm.run()
    assert vm.get('result') == expected


def test_checkpoint_is_reusable_and_cannot_alias_live_state():
    vm = astvm.Interpreter()
    vm.execute('a=[]')
    snapshot = vm.checkpoint()
    for i in range(3):
        vm.restore(snapshot)
        vm.execute('a.append(1)')
        assert vm.get('a') == [1]


def test_discarded_future_refs_stay_stale():
    vm = astvm.Interpreter()
    snapshot = vm.checkpoint()
    old = vm.evaluate_value('lambda: 1')
    vm.restore(snapshot)
    new = vm.evaluate_value('lambda: 2')
    assert old.serial != new.serial
    with pytest.raises(astvm.BoundaryError):
        vm.call_value(old)
    assert vm.call(new) == 2


def test_foreign_checkpoint_rejected():
    one = astvm.Interpreter()
    two = astvm.Interpreter()
    with pytest.raises(astvm.BoundaryError):
        two.restore(one.checkpoint())


def test_io_is_not_rolled_back_or_deduplicated():
    effects = []
    vm = astvm.Interpreter()
    vm.grant('emit', effects.append)
    vm.start('emit(1)')
    snapshot = vm.checkpoint()
    vm.run()
    assert effects == [1]
    vm.restore(snapshot)
    assert effects == [1]
    vm.run()
    assert effects == [1, 1]


def test_no_host_generators_or_guest_native_functions_in_execution_state():
    runtime = astvm.DictRuntime()
    vm = astvm.Interpreter(runtime=runtime)
    vm.start(_REPLAY_PROGRAM)
    vm.step(200)
    snapshot = vm.checkpoint()
    todo = [snapshot.objects, snapshot.thread]
    seen = set()
    while todo:
        value = todo.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        assert not isinstance(value, (types.FunctionType, types.GeneratorType, types.CoroutineType, types.FrameType))
        if dc.is_dataclass(value) and not isinstance(value, type):
            todo.extend(getattr(value, field.name) for field in dc.fields(value))
        elif isinstance(value, dict):
            todo.extend(value.keys())
            todo.extend(value.values())
        elif isinstance(value, (tuple, list, set, frozenset)):
            todo.extend(value)
        elif isinstance(value, ast.AST):
            todo.extend(field for _, field in ast.iter_fields(value))


## Resource budgets and fail-closed validation


@pytest.mark.parametrize('source', [
    'while True: pass',
    'def f():\n return f()\nf()',
    'sum(i for i in range(10**9))',
    'list(range(10**9))',
    "'x' * 10**9",
    '2 ** 1000000000',
    '1 << 1000000000',
    "format(1, '999999999d')",
    "'x'.replace('', 'y' * 1000)",
])
def test_resource_exhaustion_is_host_visible(source):
    limits = astvm.Limits(steps=5000, container=100, string=2000, call_depth=30)
    vm = astvm.Interpreter(limits=limits)
    with pytest.raises(astvm.ResourceLimitError):
        vm.execute(source)


def test_budget_abort_not_catchable_and_does_not_run_unbounded_cleanup():
    effects = []
    vm = astvm.Interpreter(limits=astvm.Limits(steps=3000))
    vm.grant('emit', effects.append)
    with pytest.raises(astvm.ResourceLimitError):
        vm.execute('''
try:
    while True:
        pass
except BaseException:
    emit('caught')
finally:
    emit('cleanup')
    while True:
        pass
''')
    assert effects == []


def test_step_limit_cannot_be_reset_by_checkpoint():
    vm = astvm.Interpreter(limits=astvm.Limits(steps=5000))
    vm.start('x=1')
    snapshot = vm.checkpoint()
    for _ in range(10):
        before = vm.steps_used
        vm.run()
        vm.restore(snapshot)
        assert vm.steps_used > before


@pytest.mark.parametrize('source', [
    'async def f(): pass',
    'match x:\n case _: pass',
    'try:\n pass\nexcept* Exception:\n pass',
    'class C(A, B): pass',
    'class C(metaclass=M): pass',
    'def f[T](x): pass',
    'type X = int',
    'from .x import y',
    'from x import *',
    'import x.y',
])
def test_unsupported_syntax_rejected_before_side_effects(source):
    calls = []
    vm = astvm.Interpreter()
    vm.grant('effect', calls.append)
    with pytest.raises(astvm.UnsupportedSyntaxError):
        vm.execute('effect(1)\n' + source)
    assert calls == []


@pytest.mark.parametrize('source', [
    'return 1', 'yield 1', 'yield from []', 'break', 'continue',
    'def f():\n nonlocal missing',
    'def f():\n x=1\n global x',
    'while True:\n def f():\n  break',
])
def test_invalid_context_rejected(source):
    with pytest.raises(SyntaxError):
        astvm.Interpreter().execute(source)


def test_no_guest_exec_eval_compile_or_host_generator_implementation():
    with open(astvm.__file__) as file:
        tree = ast.parse(file.read())
    assert not any(isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ('exec', 'eval', 'compile')


def test_deep_guest_recursion_does_not_consume_host_call_stack():
    vm = astvm.Interpreter(limits=astvm.Limits(call_depth=1600, steps=1_000_000))
    vm.execute('''
def f(n):
    if n == 0:
        return 0
    return 1 + f(n-1)
result = f(1200)
''')
    assert vm.get('result') == 1200


## Deterministic generated differential tests


@pytest.mark.parametrize('seed', range(25))
def test_generated_integer_expressions(seed):
    rng = random.Random(seed)
    expressions = [str(rng.randrange(-20, 21)) for _ in range(12)]
    for _ in range(15):
        left, right = rng.sample(expressions, 2)
        op = rng.choice(['+', '-', '*', '&', '|', '^'])
        expression = f'({left} {op} {right})'
        if len(expression) < 1000:
            expressions.append(expression)
    for expression in expressions:
        check_expression(expression)


@pytest.mark.parametrize('exit_kind', ['normal', 'return', 'raise', 'break', 'continue'])
@pytest.mark.parametrize('cleanup_kind', ['normal', 'return', 'raise', 'break', 'continue'])
def test_generated_finally_completion_matrix(exit_kind, cleanup_kind):
    statements = {
        'normal': "events.append('normal')",
        'return': 'return 7',
        'raise': "raise ValueError('boom')",
        'break': 'break',
        'continue': 'continue',
    }
    source = f'''
events=[]
def f():
    for i in range(2):
        try:
            {statements[exit_kind]}
        finally:
            events.append(('finally', i))
            {statements[cleanup_kind]}
    else:
        events.append('else')
    return 9
try:
    answer=f()
except ValueError as exc:
    answer=exc.args
result=answer,events
'''
    check(source)


## Runtime write-barrier and semantic regressions


@pytest.mark.parametrize('source', [
    '''
    events = []
    class Problem(Exception):
        def __init__(self, text='default', *, code=3):
            events.append(text)
            Exception.__init__(self, text, code)
            self.code = code
    e = Problem('custom', code=9)
    try:
        raise Problem
    except Problem as caught:
        result = e.args, e.code, caught.args, caught.code, events
    ''',
    '''
    events = []
    class A(Exception):
        def __init__(self):
            events.append('A')
            self.args = ('one',)
    class B(Exception):
        def __init__(self):
            events.append('B')
            self.args = ['two']
    try:
        raise A from B
    except A as e:
        result = e.args, e.__cause__.args, events
    ''',
    '''
    class Broken(Exception):
        def __init__(self):
            raise ValueError('construction failed')
    try:
        raise Broken
    except ValueError as e:
        result = e.args
    ''',
    '''
    class Problem(Exception):
        def __init__(self, a=1, b=2):
            self.code = a + b
            Exception.__init__(self, self.code)
    def gen():
        while True:
            try:
                yield 'ready'
            except Problem as e:
                yield e.args, e.code
    g = gen()
    a = next(g)
    b = g.throw(Problem)
    c = next(g)
    d = g.throw(Problem, (10, 20))
    result = a, b, c, d
    ''',
    '''
    e = ValueError('a')
    e.custom = [1]
    e.__dict__['other'] = 2
    e.__cause__ = TypeError('b')
    e.__context__ = RuntimeError('c')
    e.__suppress_context__ = False
    e.__init__('changed')
    del e.other
    result = e.args, e.custom, hasattr(e, 'other'), e.__cause__.args, e.__context__.args, e.__suppress_context__
    ''',
    '''
    x = 1
    def f():
        global x
        try:
            raise ValueError()
        except ValueError as x:
            return 2
    a = f()
    result = a, 'x' in globals()
    ''',
    '''
    def outer():
        x = 1
        def f():
            nonlocal x
            try:
                raise ValueError()
            except ValueError as x:
                return 2
        a = f()
        try:
            return x
        except NameError:
            return a, 'deleted'
    result = outer()
    ''',
])
def test_exception_lifecycle_regressions(source):
    check(source)


def test_host_handle_identity_is_stable_and_rollbackable():
    vm = astvm.Interpreter()
    obj = astvm.HostObject({'__enter__': lambda: obj, '__exit__': lambda *args: False})
    vm.grant('acquire', lambda: obj)
    before = vm.checkpoint()
    vm.execute('a = acquire()\nwith a as b:\n    result = a is b and b is acquire()')
    assert vm.get('result') is True
    discarded = vm.get_value('a')
    vm.restore(before)
    vm.execute('a = acquire()\nresult = a is acquire()')
    assert vm.get('result') is True
    assert vm.get_value('a') != discarded
    with pytest.raises(astvm.BoundaryError):
        vm.export(discarded)
    stable = vm.checkpoint()
    vm.execute('a = acquire()')
    vm.restore(stable)
    assert vm.evaluate('a is acquire()') is True


def test_runtime_read_copies_cannot_hide_unmediated_writes():
    import copy

    class CopyOnReadRuntime(astvm.DictRuntime):
        def __init__(self):
            super().__init__()
            self.memo = lambda: {}
            self.reads = 0
            self.edits = 0

        def read(self, ref):
            self.reads += 1
            return copy.deepcopy(super().read(ref), self.memo())

        def read_thread(self):
            return copy.deepcopy(super().read_thread(), self.memo())

        def modules(self):
            return dict(super().modules())

        def edit_thread(self):
            self.edits += 1
            return super().edit_thread()

        def edit_generator(self, ref):
            self.edits += 1
            return super().edit_generator(ref)

    runtime = CopyOnReadRuntime()
    vm = astvm.Interpreter(runtime=runtime, modules={'m': astvm.SourceModule('counter = [1]')})
    runtime.memo = vm._snapshot_memo
    vm.execute('''
import m
log = []
class C:
    def __init__(self):
        self.items = [1]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.items.append(3)
        return False
c = C()
def outer():
    count = 0
    def g():
        nonlocal count
        with c:
            try:
                count += 1
                yield count
                c.items.extend([4, 5])
                yield count + 1
            finally:
                log.append(count)
    return g()
g = outer()
first = next(g)
d = {'a': 1}
d['b'] = 2
d.update(c=3)
d.pop('a')
s = {1}
s.add(2)
s.remove(1)
m.counter.append(2)
''')
    checkpoint = vm.checkpoint()
    for _ in range(2):
        vm.execute('''
second = next(g)
g.close()
result = first, second, c.items, log, d, s, m.counter
''')
        assert vm.get('result') == (1, 2, [1, 4, 5, 3], [1], {'b': 2, 'c': 3}, {2}, [1, 2])
        vm.restore(checkpoint)
    assert runtime.reads > 50
    assert runtime.edits > 50


@pytest.mark.skipif(sys.version_info < (3, 14), reason='requires the Python 3.14 parser')
def test_314_template_strings_explicitly_rejected():
    with pytest.raises(astvm.UnsupportedSyntaxError):
        astvm.Interpreter().prepare("value = t'hello {1 + 2}'")


@pytest.mark.skipif(sys.version_info < (3, 14), reason='requires the Python 3.14 annotation oracle')
def test_314_deferred_annotation_differential():
    check('''
    calls = []
    T = 1
    def annotation():
        calls.append(T)
        return T
    def f(x: annotation()) -> T:
        return x
    before = list(calls)
    T = 2
    a = f.__annotations__
    T = 3
    result = before, a, a is f.__annotations__, calls
    ''')


@pytest.mark.parametrize('source', [
    '''
    x = 1
    def outer():
        x = 2
        def middle():
            global x
            def inner():
                return x
            return inner
        return middle()
    result = outer()()
    ''',
    '''
    x = 10
    def f():
        a = [(lambda: (x := 1))() for i in range(3)]
        return a, x
    result = f()
    ''',
    '''
    def f():
        a = [(lambda default=(x := i): default)() for i in range(3)]
        return a, x
    result = f()
    ''',
])
def test_comprehension_and_closure_binding_regressions(source):
    check(source)


@pytest.mark.parametrize('suppress', [False, True])
def test_host_context_manager_receives_explicit_guest_exception_handles(suppress):
    events = []

    def exit_method(cls, exception, traceback):
        assert type(cls) is astvm.ObjectRef
        assert type(exception) is astvm.ObjectRef
        assert traceback is None or type(traceback) is astvm.ObjectRef
        events.append('exit')
        return suppress

    handle = astvm.HostObject({
        '__enter__': lambda: handle,
        '__exit__': astvm.HostCall(exit_method, guest_arguments=True),
    })
    vm = astvm.Interpreter()
    vm.grant_object('manager', handle)
    vm.execute('''
result = 'suppressed'
try:
    with manager as same:
        assert same is manager
        raise ValueError('guest exception')
except ValueError:
    result = 'propagated'
''')
    assert vm.get('result') == ('suppressed' if suppress else 'propagated')
    assert events == ['exit']


def test_raw_argument_capability_cannot_return_a_native_object_or_a_reference():
    for result in (object(), lambda: 1):
        vm = astvm.Interpreter()
        vm.grant('bad', astvm.HostCall(lambda value: result, guest_arguments=True))
        with pytest.raises(astvm.BoundaryError):
            vm.execute('bad([])')
    vm = astvm.Interpreter()
    vm.grant('echo', astvm.HostCall(lambda value: value, guest_arguments=True))
    with pytest.raises(astvm.BoundaryError):
        vm.execute('echo([])')


def test_normal_execution_does_not_create_checkpoints():
    class NoSnapshotsRuntime(astvm.DictRuntime):
        def checkpoint(self, memo):
            raise AssertionError('normal execution must not snapshot')

    vm = astvm.Interpreter(runtime=NoSnapshotsRuntime())
    vm.execute('''
def g():
    for i in range(10):
        yield i * i
result = list(g())
''')
    assert vm.get('result') == [i * i for i in range(10)]


def test_granted_file_closes_when_guest_body_raises(tmp_path):
    path = tmp_path / 'note.txt'
    path.write_text('hello', encoding='utf-8')
    opened = []

    def open_note():
        file = open(path, encoding='utf-8')
        opened.append(file)
        handle = astvm.HostObject({
            'read': file.read,
            'close': file.close,
            '__enter__': lambda: handle,
            '__exit__': astvm.HostCall(lambda *args: file.close() or False, guest_arguments=True),
        })
        return handle

    vm = astvm.Interpreter()
    vm.grant('open_note', open_note)
    vm.execute('''
try:
    with open_note() as f:
        text = f.read()
        raise ValueError('body failed')
except ValueError:
    result = text
''')
    assert vm.get('result') == 'hello'
    assert len(opened) == 1 and opened[0].closed


## Public embedding entry points


def test_host_calls_convert_arguments_and_preserve_aliases():
    vm = astvm.Interpreter()
    vm.execute('''
def f(a, b, *, c=0):
    a.append(c)
    return a is b, a, b
''')
    original = []
    same, a, b = vm.call(vm.get_value('f'), original, original, c=3)
    assert same and a is b and a == [3]
    assert original == []


def test_host_resume_send_throw_close_and_checkpoint():
    vm = astvm.Interpreter()
    vm.execute('''
def f():
    try:
        value = yield 1
        yield value
    except ValueError:
        yield 9
    return 42
g = f()
''')
    generator = vm.get_value('g')
    assert vm.resume_value(generator) == 1
    checkpoint = vm.checkpoint()
    assert vm.resume_value(generator, mode='send', value=7) == 7
    with pytest.raises(astvm.GuestError) as caught:
        vm.resume_value(generator)
    assert caught.value.name == 'StopIteration'
    assert caught.value.message == '42'
    vm.restore(checkpoint)
    exception = vm.evaluate_value('ValueError()')
    assert vm.resume_value(generator, mode='throw', value=exception) == 9
    assert vm.resume_value(generator, mode='close') is None
    with pytest.raises(ValueError):
        vm.resume_value(generator, mode='invalid')
    with pytest.raises(ValueError):
        vm.resume_value(generator, mode='throw', value=3)


def test_prepared_program_shared_across_interpreters_preserves_ast_identity_on_restore():
    compiler = astvm.Interpreter()
    program = compiler.prepare('''
def f(x):
    def inner():
        return x + 1
    return inner
callback = f(10)
''', filename='shared-guest.py')
    vm = astvm.Interpreter()
    vm.execute(program)
    checkpoint = vm.checkpoint()
    assert vm.call(vm.get_value('callback')) == 11
    vm.restore(checkpoint)
    assert vm.call(vm.get_value('callback')) == 11
    vm.execute(program)
    assert vm.call(vm.get_value('callback')) == 11
