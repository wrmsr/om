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


def test_nan_scalar_equality_differential():
    check('''
    value = float('nan')
    result = value == value, value != value
    ''')


def test_nan_container_identity_differential():
    check('''
    value = float('nan')
    left = [value]
    right = [value]
    result = left == right, left < [value, 1], {'x': value} == {'x': value}
    ''')


def test_class_getattr_fallback_differential():
    check('''
    calls = []
    class Fallback:
        def __init__(self):
            self.known = 3
        def __getattr__(self, name):
            calls.append(name)
            if name == 'missing':
                raise AttributeError(name)
            return '<' + name + '>'
    obj = Fallback()
    result = obj.known, obj.other, getattr(obj, 'missing', 9), hasattr(obj, 'foo'), calls
    ''')


def test_inherited_getattr_tracks_class_mutation_differential():
    check('''
    class Base:
        pass
    class Child(Base):
        pass
    child = Child()
    def fallback(self, name):
        return name.upper()
    Base.__getattr__ = fallback
    first = child.answer
    del Base.__getattr__
    result = first, hasattr(child, 'answer')
    ''')


def test_class_sequence_iteration_fallback_differential():
    check('''
    class Sequence:
        def __init__(self):
            self.values = [4, 5, 6]
            self.indices = []
        def __getitem__(self, index):
            self.indices.append(index)
            return self.values[index]
    sequence = Sequence()
    iterator = iter(sequence)
    first = next(iterator)
    rest = list(iterator)
    sequence.values.append(7)
    result = first, rest, sequence.indices, list(iterator)
    ''')


def test_class_sequence_stop_iteration_is_sticky_differential():
    check('''
    class Sequence:
        def __init__(self):
            self.calls = []
        def __getitem__(self, index):
            self.calls.append(index)
            raise StopIteration
    sequence = Sequence()
    iterator = iter(sequence)
    result = next(iterator, 'end'), next(iterator, 'end'), sequence.calls
    ''')


def test_class_index_protocol_differential():
    check('''
    calls = []
    class Index:
        def __init__(self, value):
            self.value = value
        def __index__(self):
            calls.append(self.value)
            return self.value
    index = Index(1)
    values = [10, 20, 30]
    first = values[index]
    values[index] = 99
    del values[index]
    result = first, values, list(range(index, 4, 2)), calls
    ''')


def test_class_index_protocol_rejects_non_integer_result():
    guest_error('''
    class Index:
        def __index__(self):
            return 1.5
    result = [1, 2][Index()]
    ''', 'TypeError')


def test_class_index_protocol_in_slices_differential():
    check('''
    calls = []
    class Index:
        def __init__(self, name, value):
            self.name = name
            self.value = value
        def __index__(self):
            calls.append(self.name)
            return self.value
    values = [0, 1, 2, 3, 4, 5]
    read = values[Index('start', 1):Index('stop', 5):Index('step', 2)]
    values[Index('start', 0):Index('stop', 4):Index('step', 2)] = [8, 9]
    del values[Index('start', 0):Index('stop', 2):Index('step', 1)]
    result = read, values, calls
    ''')


def test_class_index_protocol_in_repetition_differential():
    check('''
    class Index:
        def __index__(self):
            return 3
    index = Index()
    values = [1]
    original = values
    values *= index
    result = 'ab' * index, index * (4,), values, values is original
    ''')


def test_class_index_protocol_in_constructors_and_builtins_differential():
    check('''
    calls = []
    class Index:
        def __index__(self):
            calls.append('index')
            return 3
    value = Index()
    result = int(value), bytes(value), chr(value), bin(value), oct(value), hex(value), list(enumerate('ab', value)), calls
    ''')


def test_class_index_protocol_in_list_methods_differential():
    check('''
    calls = []
    class Index:
        def __init__(self, name, value):
            self.name = name
            self.value = value
        def __index__(self):
            calls.append(self.name)
            return self.value
    values = [4, 5, 6, 5]
    found = values.index(5, Index('start', 2), Index('stop', 4))
    values.insert(Index('insert', 1), 8)
    popped = values.pop(Index('pop', -2))
    tuple_found = (4, 5, 6).index(5, Index('tuple_start', 1))
    result = found, popped, tuple_found, values, calls
    ''')


def test_class_index_protocol_in_round_and_bytes_items_differential():
    check('''
    calls = []
    class Index:
        def __init__(self, value):
            self.value = value
        def __index__(self):
            calls.append(('index', self.value))
            return self.value
    class Source:
        def __iter__(self):
            for value in [65, 66]:
                calls.append(('yield', value))
                yield Index(value)
    result = round(1.2345, Index(2)), bytes(Source()), calls
    ''')


def test_class_reversed_sequence_fallback_differential():
    check('''
    calls = []
    class Sequence:
        def __len__(self):
            calls.append('len')
            return 4
        def __getitem__(self, index):
            calls.append(index)
            if index == 1:
                raise IndexError(index)
            return index * 10
    iterator = reversed(Sequence())
    first = next(iterator)
    second = next(iterator)
    third = next(iterator, 'done')
    fourth = next(iterator, 'done')
    result = first, second, third, fourth, calls
    ''')


def test_class_mapping_protocol_for_dict_and_update_differential():
    check('''
    calls = []
    class Mapping:
        def keys(self):
            calls.append('keys')
            return ['a', 'b']
        def __getitem__(self, key):
            calls.append(key)
            return {'a': 2, 'b': 3}[key]
    first = dict(Mapping(), c=4)
    second = {'z': 1}
    second.update(Mapping(), d=5)
    result = first, second, calls
    ''')


def test_class_iterable_pairs_fallback_for_dict_differential():
    check('''
    calls = []
    class Pairs:
        def __getattr__(self, name):
            calls.append(name)
            raise AttributeError(name)
        def __iter__(self):
            return iter([('x', 2), ('y', 3)])
    result = dict(Pairs()), calls
    ''')


def test_class_mapping_protocol_for_keyword_expansion_differential():
    check('''
    calls = []
    class Mapping:
        def keys(self):
            calls.append('keys')
            return ['a', 'b']
        def __getitem__(self, key):
            calls.append(key)
            return {'a': 2, 'b': 3}[key]
    def f(**kwargs):
        return kwargs
    result = f(**Mapping()), calls
    ''')


def test_class_keyword_expansion_rejects_non_string_and_duplicate_keys():
    guest_error('''
    class Mapping:
        def keys(self):
            return [1]
        def __getitem__(self, key):
            return 3
    def f(**kwargs):
        pass
    f(**Mapping())
    ''', 'TypeError')
    guest_error('''
    class Mapping:
        def keys(self):
            return ['a']
        def __getitem__(self, key):
            return 3
    def f(**kwargs):
        pass
    f(a=2, **Mapping())
    ''', 'TypeError')


def test_class_mapping_protocol_for_dict_unpacking_differential():
    check('''
    calls = []
    class Mapping:
        def keys(self):
            calls.append('keys')
            return ['x', 'y']
        def __getitem__(self, key):
            calls.append(key)
            return {'x': 2, 'y': 3}[key]
    result = {'w': 0, **Mapping(), 'x': 4}, calls
    ''')


def test_class_mapping_keys_are_collected_before_value_lookup_differential():
    check('''
    calls = []
    class Mapping:
        def keys(self):
            def names():
                for name in ['a', 'b']:
                    calls.append(('key', name))
                    yield name
            return names()
        def __getitem__(self, name):
            calls.append(('value', name))
            return name.upper()
    first = dict(Mapping())
    second = {}
    second.update(Mapping())
    third = {**Mapping()}
    def f(**kwargs):
        return kwargs
    fourth = f(**Mapping())
    result = first, second, third, fourth, calls
    ''')


def test_class_dict_unpacking_requires_mapping():
    guest_error('''
    class Pairs:
        def __iter__(self):
            return iter([('x', 2)])
    result = {**Pairs()}
    ''', 'TypeError')


def test_class_methods_in_container_comparison_differential():
    check('''
    calls = []
    class Item:
        def __init__(self, value):
            self.value = value
        def __eq__(self, other):
            calls.append(('eq', self.value, other.value))
            return self.value == other.value
        def __lt__(self, other):
            calls.append(('lt', self.value, other.value))
            return self.value < other.value
    equal_list = [Item(2)] == [Item(2)]
    equal_dict = {'x': Item(2)} == {'x': Item(2)}
    less_tuple = (Item(1),) < (Item(2),)
    result = equal_list, equal_dict, less_tuple, calls
    ''')


def test_nested_container_comparison_uses_guest_truth_differential():
    check('''
    calls = []
    class Truth:
        def __bool__(self):
            calls.append('bool')
            return True
    class Item:
        def __eq__(self, other):
            calls.append('eq')
            return Truth()
    a, b = Item(), Item()
    result = [[a]] == [[b]], {'x': [a]} == {'x': [b]}, [[a]] != [[b]], calls
    ''')


def test_container_comparison_observes_guest_mutation_differential():
    check('''
    class Item:
        def __eq__(self, other):
            left.append(2)
            right.append(3)
            return True
    left, right = [Item()], [Item()]
    equal = left == right
    result = equal, len(left), len(right), left[1], right[1]
    ''')


def test_nested_container_representation_calls_guest_repr_differential():
    check('''
    calls = []
    class Item:
        def __repr__(self):
            calls.append('repr')
            return 'Item(3)'
    item = Item()
    values = [item]
    values.append(values)
    result = repr(values), str({'x': (item,)}), ascii([item]), calls
    ''')


def test_container_representation_observes_guest_mutation_differential():
    check('''
    class Item:
        def __repr__(self):
            values.append(2)
            mapping['y'] = 3
            return 'Item()'
    item = Item()
    values = [item]
    mapping = {'x': item}
    first = repr(values)
    second = repr(mapping)
    result = first, second, len(values), len(mapping)
    ''')


def test_container_protocol_calls_resume_after_checkpoint():
    vm = astvm.Interpreter()
    vm.execute('''
calls = []
class Item:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        calls.append('repr')
        return 'Item(' + str(self.value) + ')'
    def __eq__(self, other):
        calls.append('eq')
        return self.value == other.value
''')
    vm.start('result = repr([Item(1)]), [Item(1)] == [Item(1)]')
    for _ in range(200):
        thread = vm._runtime.read_thread()
        if any(task.kind == 'representation_next' for execution in thread.executions for task in execution.tasks):
            break
        vm.step()
    else:
        raise AssertionError('container representation did not start')

    checkpoint = vm.checkpoint()
    for _ in range(2):
        vm.run()
        assert vm.get('result') == ('[Item(1)]', True)
        assert vm.get('calls') == ['repr', 'eq']
        vm.restore(checkpoint)


def test_class_private_name_mangling_differential():
    check('''
    class Vault:
        __base = 7
        def __init__(self, __value):
            self.__value = __value
        def __method(self):
            return self.__value + self.__base
        def read(self):
            return self.__method()
        class __Nested:
            __number = 4
            def read(self):
                return self.__number
    value = Vault(5)
    nested = Vault._Vault__Nested()
    result = (
        value.read(), value._Vault__value, Vault._Vault__base,
        nested.read(), Vault._Vault__Nested.__name__,
    )
    ''')


def test_class_private_names_in_nested_scopes_differential():
    check('''
    class __Container:
        def f(self):
            __value = 3
            def inner():
                return __value
            return inner(), [__value + i for i in range(2)]
    result = __Container().f()
    ''')


def test_class_private_names_in_global_and_nonlocal_declarations_differential():
    check('''
    _C__global = 1
    class C:
        def change_global(self):
            global __global
            __global = 4
        def nested(self):
            __local = 2
            def change():
                nonlocal __local
                __local += 3
            change()
            return __local
    value = C()
    value.change_global()
    result = _C__global, value.nested()
    ''')


def test_class_and_function_qualified_names_differential():
    check('''
    def outer():
        class Inner:
            def method(self):
                def nested():
                    pass
                return nested.__qualname__
        return Inner, Inner().method()
    class Container:
        class Nested:
            pass
        def method(self):
            return (lambda: None).__qualname__
    inner, nested_name = outer()
    result = (
        outer.__qualname__, inner.__qualname__, inner.__name__, nested_name,
        Container.__qualname__, Container.Nested.__qualname__,
        Container.method.__qualname__, Container().method(),
    )
    ''')


def test_class_descriptors_read_write_delete_differential():
    check('''
    calls = []
    class Descriptor:
        def __get__(self, obj, cls):
            calls.append(('get', obj is None))
            return self if obj is None else obj._value
        def __set__(self, obj, value):
            calls.append(('set', value))
            obj._value = value
        def __delete__(self, obj):
            calls.append(('delete',))
            del obj._value
    class Example:
        field = Descriptor()
    item = Example()
    item.field = 3
    first = item.field
    class_access = Example.field is Example.field
    item.__dict__['field'] = 99
    second = item.field
    del item.field
    result = first, second, class_access, calls
    ''')


def test_class_nondata_descriptor_override_and_getattr_differential():
    check('''
    calls = []
    class Descriptor:
        def __get__(self, obj, cls):
            calls.append('get')
            if obj is None:
                return self
            raise AttributeError('missing')
    class Example:
        field = Descriptor()
        def __getattr__(self, name):
            calls.append('getattr')
            return 7
    item = Example()
    first = item.field
    item.__dict__['field'] = 8
    result = first, item.field, calls
    ''')


def test_property_getter_setter_deleter_differential():
    check('''
    calls = []
    class Example:
        def __init__(self):
            self._value = 2
        @property
        def value(self):
            calls.append('get')
            return self._value
        @value.setter
        def value(self, new):
            calls.append('set')
            self._value = new
        @value.deleter
        def value(self):
            calls.append('delete')
            del self._value
    item = Example()
    first = item.value
    item.value = 5
    item.__dict__['value'] = 99
    second = item.value
    del item.value
    result = first, second, Example.value.fget.__name__, calls
    ''')


def test_class_function_and_property_docstrings_differential():
    check('''
    class Example:
        """An example class."""

        @property
        def value(self):
            """The current value."""

            return 3
        def method(self):
            """A method."""

            return self.value
    result = Example.__doc__, Example.value.__doc__, Example.method.__doc__, Example().value
    ''')


def test_property_replacement_getter_updates_inherited_docstring_differential():
    check('''
    def original(self):
        """Original doc."""

        return 1
    def replacement(self):
        """Replacement doc."""

        return 2
    inherited = property(original).getter(replacement)
    explicit = property(original, doc='Explicit doc.').getter(replacement)
    result = inherited.__doc__, explicit.__doc__
    ''')


def test_readonly_property_rejects_assignment():
    guest_error('''
    class Example:
        @property
        def value(self):
            return 3
    item = Example()
    item.value = 5
    ''', 'AttributeError')


def test_property_attribute_error_uses_getattr_fallback_differential():
    check('''
    calls = []
    class Example:
        @property
        def value(self):
            calls.append('property')
            raise AttributeError('missing')
        def __getattr__(self, name):
            calls.append(('getattr', name))
            return 7
    result = Example().value, calls
    ''')


def test_inherited_descriptor_tracks_class_mutation_differential():
    check('''
    calls = []
    class Descriptor:
        def __get__(self, obj, cls):
            calls.append(cls.__name__)
            return 3
    class Base:
        value = Descriptor()
    class Child(Base):
        pass
    child = Child()
    first = child.value
    Base.value = 8
    result = first, child.value, calls
    ''')


def test_exception_subclass_descriptor_differential():
    check('''
    calls = []
    class Descriptor:
        def __get__(self, obj, cls):
            calls.append('get')
            return obj._value
        def __set__(self, obj, value):
            calls.append('set')
            obj._value = value
        def __delete__(self, obj):
            calls.append('delete')
            del obj._value
    class Problem(Exception):
        field = Descriptor()
    error = Problem()
    error.field = 5
    first = error.field
    del error.field
    result = first, calls
    ''')


def test_default_instance_identity_keys_differential():
    check('''
    class Item:
        pass
    first, second = Item(), Item()
    mapping = {first: 3, second: 4}
    values = {first, second, first}
    result = mapping[first], mapping[second], len(mapping), len(values), first in values, Item() in values
    ''')


def test_custom_equality_without_hash_is_unhashable():
    guest_error('''
    class Item:
        def __eq__(self, other):
            return True
    result = {Item(): 3}
    ''', 'TypeError')


def test_descriptor_set_name_before_class_decorator_differential():
    check('''
    calls = []
    class Field:
        def __set_name__(self, owner, name):
            calls.append(('set_name', owner.__name__, name))
            self.name = name
        def __get__(self, obj, cls):
            return self.name
    def decorate(cls):
        calls.append(('decorate', cls.__name__))
        return cls
    @decorate
    class Example:
        first = Field()
        second = Field()
    result = Example().first, Example().second, calls
    ''')


def test_private_property_and_descriptor_names_differential():
    check('''
    calls = []
    class Field:
        def __set_name__(self, owner, name):
            calls.append(name)
    class Example:
        __field = Field()
        @property
        def __value(self):
            return self._value
        @__value.setter
        def __value(self, value):
            self._value = value
    item = Example()
    item._Example__value = 7
    result = item._Example__value, calls
    ''')


def test_init_subclass_after_set_name_before_decorator_differential():
    check('''
    calls = []
    class Field:
        def __set_name__(self, owner, name):
            calls.append(('set_name', name))
    class Base:
        def __init_subclass__(cls):
            calls.append(('init_subclass', cls.__name__))
            cls.ready = True
    def decorate(cls):
        calls.append(('decorate', cls.ready))
        return cls
    @decorate
    class Child(Base):
        field = Field()
    result = Child.ready, calls
    ''')


def test_inherited_explicit_classmethod_init_subclass_differential():
    check('''
    calls = []
    class Base:
        @classmethod
        def __init_subclass__(cls):
            calls.append(cls.__name__)
    class Middle(Base):
        pass
    class Child(Middle):
        pass
    result = calls
    ''')


def test_class_creation_hooks_resume_after_checkpoint():
    vm = astvm.Interpreter()
    vm.start('''
events = []
class Field:
    def __set_name__(self, owner, name):
        events.append(('field', name))
class Base:
    def __init_subclass__(cls):
        events.append(('subclass', cls.__name__))
class Child(Base):
    value = Field()
result = events
''')
    for _ in range(300):
        thread = vm._runtime.read_thread()
        if any(
            task.kind == 'class_set_name_next' and vm._space.data(task.data[0]).name == 'Child'
            for execution in thread.executions for task in execution.tasks
        ):
            break
        vm.step()
    else:
        raise AssertionError('class creation did not reach descriptor hooks')

    checkpoint = vm.checkpoint()
    vm.run()
    assert vm.get('result') == [('field', 'value'), ('subclass', 'Child')]
    vm.restore(checkpoint)
    vm.run()
    assert vm.get('result') == [('field', 'value'), ('subclass', 'Child')]


def test_guest_new_initialization_and_foreign_return_differential():
    check('''
    calls = []
    class Example:
        def __new__(cls, value):
            calls.append(('new', value))
            instance = object.__new__(cls)
            instance.before = value
            return instance
        def __init__(self, value):
            calls.append(('init', value))
            self.after = value + 1
    class Foreign:
        def __new__(cls):
            calls.append(('foreign_new',))
            return 42
        def __init__(self):
            calls.append(('foreign_init',))
    item = Example(3)
    other = Foreign()
    result = item.before, item.after, other, calls
    ''')


def test_inherited_guest_new_and_object_initializer_differential():
    check('''
    calls = []
    class Base:
        def __new__(cls, value):
            calls.append(('new', cls.__name__))
            return object.__new__(cls)
    class Child(Base):
        def __init__(self, value):
            object.__init__(self)
            calls.append(('init', value))
            self.value = value
    item = Child(4)
    result = item.value, calls, object.__init__(3)
    ''')


def test_guest_new_returning_subclass_uses_subclass_initializer_differential():
    check('''
    calls = []
    class Parent:
        def __new__(cls):
            return object.__new__(Child)
        def __init__(self):
            calls.append('parent')
    class Child(Parent):
        def __init__(self):
            calls.append('child')
    value = Parent()
    result = type(value).__name__, calls
    ''')


def test_guest_new_resumes_after_checkpoint():
    vm = astvm.Interpreter()
    vm.start('''
calls = []
class Example:
    def __new__(cls, value):
        calls.append('new')
        return object.__new__(cls)
    def __init__(self, value):
        calls.append('init')
        self.value = value
item = Example(5)
result = item.value, calls
''')
    for _ in range(200):
        thread = vm._runtime.read_thread()
        if any(task.kind == 'class_new_result' for execution in thread.executions for task in execution.tasks):
            break
        vm.step()
    else:
        raise AssertionError('class construction did not reach __new__')

    checkpoint = vm.checkpoint()
    vm.run()
    assert vm.get('result') == (5, ['new', 'init'])
    vm.restore(checkpoint)
    vm.run()
    assert vm.get('result') == (5, ['new', 'init'])


def test_class_sequence_iteration_can_resume_after_checkpoint():
    vm = astvm.Interpreter()
    vm.execute('''
class Sequence:
    def __init__(self):
        self.indices = []
    def __getitem__(self, index):
        self.indices.append(index)
        return [4, 5][index]
sequence = Sequence()
iterator = iter(sequence)
''')
    vm.start('result = next(iterator)')
    for _ in range(100):
        thread = vm._runtime.read_thread()
        if any(task.kind == 'sequence_next_guard' for execution in thread.executions for task in execution.tasks):
            break
        vm.step()
    else:
        raise AssertionError('sequence iterator did not enter guest indexing')

    checkpoint = vm.checkpoint()
    vm.run()
    assert vm.get('result') == 4
    assert vm.evaluate('sequence.indices') == [0]

    vm.restore(checkpoint)
    vm.run()
    assert vm.get('result') == 4
    assert vm.evaluate('sequence.indices') == [0]


@pytest.mark.parametrize('expression', [
    'sum([1e16, 1.0, -1e16])',
    'sum([1e16, 1, -1e16])',
    'sum([1e16, -1e16, 1.0])',
    'sum([1e308, 1e308, -1e308])',
    'sum([1e16, 1.0, -1e16, 2 + 3j])',
    'sum([1e16, 1.0, -1e16], 5.0)',
])
def test_floating_sum_differential(expression):
    check_expression(expression)


def test_floating_sum_falls_back_to_guest_addition_differential():
    check('''
    class Right:
        def __radd__(self, other):
            return other + 10
    result = sum([1e16, 1.0, -1e16, Right()])
    ''')


def test_floating_sum_compensation_survives_checkpoint():
    vm = astvm.Interpreter()
    vm.start('result = sum([1e16, 1.0, -1e16])')
    for _ in range(200):
        thread = vm._runtime.read_thread()
        if any(
            isinstance(task.data, astvm.ReductionState) and task.data.compensation == 1.0
            for execution in thread.executions for task in execution.tasks
        ):
            break
        vm.step()
    else:
        raise AssertionError('sum did not reach a compensated intermediate state')

    checkpoint = vm.checkpoint()
    vm.run()
    assert vm.get('result') == 1.0
    vm.restore(checkpoint)
    vm.run()
    assert vm.get('result') == 1.0


@pytest.mark.parametrize('source', [
    'result = dict(None)',
    'value = {}\nvalue.update(None)',
])
def test_explicit_none_is_not_an_omitted_mapping_argument(source):
    with pytest.raises(TypeError):
        exec(source, {})
    guest_error(source, 'TypeError')


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
    directory = os.path.dirname(astvm.__file__)
    for name in os.listdir(directory):
        if not name.endswith('.py') or name.endswith('_dataclasses.py'):
            continue
        with open(os.path.join(directory, name)) as file:
            tree = ast.parse(file.read())
        assert not any(
            isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await, ast.AsyncFunctionDef))
            for node in ast.walk(tree)
        )
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
