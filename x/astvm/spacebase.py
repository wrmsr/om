# mypy: disable-error-code=attr-defined
import operator
import typing as ta

from .budget import Budget
from .capabilities import Capabilities
from .runtime import Runtime
from .state import BuiltinData
from .state import ClassData
from .values import _ELLIPSIS
from .values import _NOT_IMPLEMENTED
from .values import ObjectRef
from .values import Value


##


class SpaceBase:
    _EXCEPTION_BASES: ta.ClassVar[dict[str, str]] = {
        'BaseException': 'object',
        'Exception': 'BaseException',
        'GeneratorExit': 'BaseException',
        'SystemExit': 'BaseException',
        'KeyboardInterrupt': 'BaseException',
        'ArithmeticError': 'Exception',
        'ZeroDivisionError': 'ArithmeticError',
        'OverflowError': 'ArithmeticError',
        'LookupError': 'Exception',
        'IndexError': 'LookupError',
        'KeyError': 'LookupError',
        'TypeError': 'Exception',
        'ValueError': 'Exception',
        'NameError': 'Exception',
        'UnboundLocalError': 'NameError',
        'AttributeError': 'Exception',
        'RuntimeError': 'Exception',
        'RecursionError': 'RuntimeError',
        'NotImplementedError': 'RuntimeError',
        'AssertionError': 'Exception',
        'StopIteration': 'Exception',
        'ImportError': 'Exception',
        'ModuleNotFoundError': 'ImportError',
        'OSError': 'Exception',
        'FileNotFoundError': 'OSError',
        'PermissionError': 'OSError',
        'EOFError': 'Exception',
    }

    _TYPE_NAMES = (
        'int',
        'bool',
        'float',
        'complex',
        'str',
        'bytes',
        'list',
        'tuple',
        'dict',
        'set',
        'frozenset',
        'range',
        'slice',
        'type',
        'NoneType',
        'function',
        'generator',
        'iterator',
        'module',
    )

    _FUNCTION_NAMES = (
        'len',
        'iter',
        'next',
        'repr',
        'ascii',
        'format',
        'abs',
        'round',
        'pow',
        'divmod',
        'min',
        'max',
        'sum',
        'all',
        'any',
        'enumerate',
        'zip',
        'reversed',
        'sorted',
        'map',
        'filter',
        'isinstance',
        'issubclass',
        'callable',
        'getattr',
        'setattr',
        'delattr',
        'hasattr',
        'globals',
        'locals',
        'vars',
        'id',
        'hash',
        'chr',
        'ord',
        'bin',
        'oct',
        'hex',
        'staticmethod',
        'classmethod',
    )

    _METHODS: ta.ClassVar[dict[str, frozenset[str]]] = {

        'list': frozenset({
            'append',
            'extend',
            'insert',
            'pop',
            'clear',
            'copy',
            'reverse',
            'remove',
            'count',
            'index',
        }),

        'dict': frozenset({
            'get',
            'keys',
            'values',
            'items',
            'pop',
            'popitem',
            'clear',
            'copy',
            'update',
            'setdefault',
        }),

        'namespace': frozenset({
            'get',
            'keys',
            'values',
            'items',
            'pop',
            'popitem',
            'clear',
            'copy',
            'update',
            'setdefault',
        }),

        'set': frozenset({
            'add',
            'discard',
            'remove',
            'pop',
            'clear',
            'copy',
            'update',
        }),

        'frozenset': frozenset({
            'copy',
        }),

        'tuple': frozenset({
            'count',
            'index',
        }),

        'str': frozenset({
            'upper',
            'lower',
            'casefold',
            'capitalize',
            'title',
            'swapcase',
            'strip',
            'lstrip',
            'rstrip',
            'split',
            'rsplit',
            'splitlines',
            'join',
            'replace',
            'startswith',
            'endswith',
            'find',
            'rfind',
            'index',
            'rindex',
            'count',
            'partition',
            'rpartition',
            'removeprefix',
            'removesuffix',
            'isalnum',
            'isalpha',
            'isascii',
            'isdecimal',
            'isdigit',
            'isidentifier',
            'islower',
            'isnumeric',
            'isprintable',
            'isspace',
            'istitle',
            'isupper',
        }),

        'bytes': frozenset({
            'hex',
            'upper',
            'lower',
            'strip',
            'lstrip',
            'rstrip',
            'startswith',
            'endswith',
            'find',
            'count',
        }),

        'generator': frozenset({
            'send',
            'throw',
            'close',
            '__iter__',
            '__next__',
        }),

        'iterator': frozenset({
            '__iter__',
            '__next__',
        }),

        'adapter': frozenset({
            '__iter__',
            '__next__',
        }),

        'range': frozenset({
            'count',
            'index',
        }),

    }

    _BINARY: ta.ClassVar[dict[str, ta.Callable[..., ta.Any]]] = {
        'Add': operator.add,
        'Sub': operator.sub,
        'Mult': operator.mul,
        'Div': operator.truediv,
        'FloorDiv': operator.floordiv,
        'Mod': operator.mod,
        'Pow': operator.pow,
        'LShift': operator.lshift,
        'RShift': operator.rshift,
        'BitOr': operator.or_,
        'BitXor': operator.xor,
        'BitAnd': operator.and_,
    }

    _ORDER: ta.ClassVar[dict[str, ta.Callable[..., ta.Any]]] = {
        'Lt': operator.lt,
        'LtE': operator.le,
        'Gt': operator.gt,
        'GtE': operator.ge,
    }

    def __init__(
            self,
            runtime: Runtime,
            budget: Budget,
            capabilities: Capabilities,
    ) -> None:
        super().__init__()

        self.runtime = runtime
        self.budget = budget
        self.capabilities = capabilities
        self._scalar_identities: dict[int, tuple[Value, int]] = {}
        self._host_objects = self.new('capability_cache', {})

        self.types: dict[str, ObjectRef] = {}
        self.builtins = self.new('namespace', {})
        self.types['object'] = self.new(
            'type',
            ClassData(
                'object',
                self.new(
                    'namespace',
                    {},
                ),
                None,
            ),
        )
        for name, base in self._EXCEPTION_BASES.items():
            self.types[name] = self.new(
                'type',
                ClassData(
                    name,
                    self.new(
                        'namespace',
                        {},
                    ),
                    self.types[base],
                ),
            )
        for name in self._TYPE_NAMES:
            base = self.types['int'] if name == 'bool' else self.types['object']
            self.types[name] = self.new(
                'type',
                ClassData(
                    name,
                    self.new(
                        'namespace',
                        {},
                    ),
                    base,
                ),
            )
        for name, value in self.types.items():
            self.runtime.write(self.builtins, name, value)

        for name in self._FUNCTION_NAMES:
            self.runtime.write(self.builtins, name, self.new('builtin', BuiltinData(name)))
        self.runtime.write(self.builtins, 'NotImplemented', _NOT_IMPLEMENTED)
        self.runtime.write(self.builtins, 'Ellipsis', _ELLIPSIS)
