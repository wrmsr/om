# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc
import typing as ta

from .state import BoundMethodData
from .state import BuiltinData
from .state import ExceptionData
from .values import _ELLIPSIS
from .values import _MISSING
from .values import _NOT_IMPLEMENTED
from .values import _SCALARS
from .values import BoundaryError
from .values import ObjectRef
from .values import Value
from .values import _GuestRaise


##


class SpaceObjects:
    def new(self, kind: str, data: ta.Any) -> ObjectRef:
        amount = len(data) if type(data) in (list, tuple, dict) else 1
        self.budget.allocate(amount + 1, object_count=1)
        return self.runtime.allocate(kind, data)

    def kind(self, value: Value) -> str:
        if type(value) is ObjectRef:
            return self.runtime.read(value).kind

        if type(value) in _SCALARS:
            return 'NoneType' if value is None else type(value).__name__

        if value is _ELLIPSIS or value is _NOT_IMPLEMENTED:
            return value.name

        raise BoundaryError('invalid value in guest object space')

    def data(self, value: ObjectRef) -> ta.Any:
        return self.runtime.read(value).data

    def error(self, name: str, *args: Value) -> ta.NoReturn:
        raise _GuestRaise(self.exception(name, tuple(args)))

    def exception(self, name: str, args: tuple[Value, ...]) -> ObjectRef:
        cls = self.types.get(name)

        if cls is None or not self.subclass(cls, self.types['BaseException']):
            raise BoundaryError(f'unknown guest exception type: {name}')

        return self.new('exception', ExceptionData(cls, args))

    def exception_name(self, ref: ObjectRef) -> str:
        return self.data(self.data(ref).cls).name

    def exception_matches(self, ref: ObjectRef, cls: Value) -> bool:
        if self.kind(cls) == 'tuple':
            return any(self.exception_matches(ref, c) for c in self.data(cls))

        if self.kind(cls) not in ('type', 'class') or not self.subclass(cls, self.types['BaseException']):
            self.error('TypeError', 'catching classes that do not inherit from BaseException is not allowed')

        return self.subclass(self.data(ref).cls, cls)

    def subclass(self, cls: ObjectRef, base: ObjectRef) -> bool:
        current: ObjectRef | None = cls

        while current is not None:
            self.budget.tick()

            if current == base:
                return True

            if self.kind(current) not in ('type', 'class'):
                return False

            current = self.data(current).base

        return False

    def type_of(self, value: Value) -> ObjectRef:
        kind = self.kind(value)

        if kind in ('instance', 'exception'):
            return self.data(value).cls

        if kind in ('class', 'type'):
            return self.types['type']

        if kind == 'namespace':
            return self.types['dict']

        if kind == 'adapter':
            return self.types['iterator']

        if kind in ('builtin', 'bound_method', 'capability'):
            return self.types['function']

        return self.types.get(kind, self.types['object'])

    def lookup_class(self, cls: ObjectRef, name: str) -> Value:
        while cls is not None:
            self.budget.tick()

            info = self.data(cls)

            namespace = self.data(info.namespace)
            if name in namespace:
                return namespace[name]

            cls = info.base

        return _MISSING

    def bind(
            self,
            value: Value,
            receiver: Value,
            cls: ObjectRef,
    ) -> Value:
        kind = self.kind(value)

        if kind == 'staticmethod':
            return self.data(value)

        if kind == 'classmethod':
            return self.new('bound_method', BoundMethodData(self.data(value), cls))

        if receiver is not _MISSING and kind == 'function':
            return self.new('bound_method', BoundMethodData(value, receiver))

        return value

    def special(self, value: Value, name: str) -> Value:
        kind = self.kind(value)

        if kind in ('instance', 'exception'):
            cls = self.data(value).cls
            found = self.lookup_class(cls, name)
            if found is not _MISSING:
                return self.bind(found, value, cls)

        if kind == 'host_object':
            methods = self.data(value)[1]
            if name in methods:
                return self.new('capability', methods[name])

        return _MISSING

    def get_attribute(self, value: Value, name: str) -> Value:
        if type(name) is not str:
            self.error('TypeError', 'attribute name must be a string')

        kind = self.kind(value)

        if name == '__class__':
            return self.type_of(value)

        if kind == 'instance':
            info = self.data(value)

            if name == '__dict__':
                return info.namespace

            own = self.data(info.namespace)
            if name in own:
                return own[name]

            found = self.lookup_class(info.cls, name)
            if found is not _MISSING:
                return self.bind(found, value, info.cls)

        elif kind in ('class', 'type'):
            info = self.data(value)

            if name == '__name__':
                return info.name

            if name == '__bases__':
                return self.new('tuple', () if info.base is None else (info.base,))

            # Do not return a writable class dictionary bypassing class attribute policy.
            found = self.lookup_class(value, name)
            if found is not _MISSING:
                return self.bind(found, _MISSING, value)

            if name == '__init__' and self.subclass(value, self.types['BaseException']):
                return self.new('builtin', BuiltinData('exception_init', value))

        elif kind == 'function':
            info = self.data(value)

            if name in ('__name__', '__qualname__'):
                return info.node.name if isinstance(info.node, ast.FunctionDef) else '<lambda>'

            if name == '__annotations__':
                return info.annotations

            if name == '__globals__':
                return info.environment.globals

            if name == '__defaults__':
                return self.new('tuple', info.defaults) if info.defaults else None

            if name == '__kwdefaults__':
                return self.make_dict(tuple(info.kwdefaults.items())) if info.kwdefaults else None

        elif kind == 'bound_method':
            if name == '__self__':
                return self.data(value).receiver

            if name == '__func__':
                return self.data(value).function

        elif kind == 'exception':
            info = self.data(value)

            if name == 'args':
                return self.new('tuple', info.args)

            if name == 'value' and self.subclass(info.cls, self.types['StopIteration']):
                return info.args[0] if info.args else None

            if name == '__cause__':
                return info.cause

            if name == '__context__':
                return info.context

            if name == '__suppress_context__':
                return info.suppress_context

            if name == '__traceback__':
                return self.traceback_value(value)

            if name == '__dict__':
                if info.namespace is None:
                    info = dc.replace(info, namespace=self.new('namespace', {}))
                    self.runtime.replace(value, info)
                return info.namespace

            if info.namespace is not None and name in self.data(info.namespace):
                return self.data(info.namespace)[name]

            found = self.lookup_class(info.cls, name)
            if found is not _MISSING:
                return self.bind(found, value, info.cls)

            if name == '__init__':
                return self.new('builtin', BuiltinData('exception_init_bound', value))

        elif kind == 'generator':
            info = self.data(value)

            if name == 'gi_running':
                return info.running

            if name == 'gi_suspended':
                return info.started and not info.closed and not info.running

            if name == 'gi_yieldfrom':
                for task in reversed(info.execution.tasks):
                    if task.kind == 'delegate_resume':
                        return task.data
                return None

        elif kind == 'range':
            if name in ('start', 'stop', 'step'):
                info = self.data(value)
                return {'start': info.start, 'stop': info.stop, 'step': info.step}[name]

        elif kind == 'slice':
            if name in ('start', 'stop', 'step'):
                return self.data(value)[{'start': 0, 'stop': 1, 'step': 2}[name]]

        elif kind == 'host_object':
            methods = self.data(value)[1]
            if name in methods:
                return self.new('capability', methods[name])

        elif kind == 'module':
            if name == '__dict__':
                return self.data(value)

            namespace = self.data(self.data(value))
            if name in namespace:
                return namespace[name]

        if name in self._METHODS.get(kind, ()):
            return self.new('builtin', BuiltinData(f'{kind}.{name}', value))

        return self.error('AttributeError', f'{kind} has no supported attribute {name!r}')

    def set_attribute(
            self,
            value: Value,
            name: str,
            item: Value,
            *,
            delete: bool = False,
    ) -> None:
        if type(name) is not str:
            self.error('TypeError', 'attribute name must be a string')

        kind = self.kind(value)

        if name in (
                '__class__',
                '__dict__',
                '__bases__',
                '__mro__',
        ):
            self.error('AttributeError', 'structural attribute is read-only')

        if kind == 'instance':
            namespace = self.data(value).namespace

        elif kind == 'exception':
            info = self.data(value)

            fields = {
                'args': 'args',
                '__cause__': 'cause',
                '__context__': 'context',
                '__suppress_context__': 'suppress_context',
                '__traceback__': 'traceback',
            }

            if name in fields:
                if delete:
                    self.error('TypeError', 'exception structural fields cannot be deleted')

                if name == 'args':
                    if self.kind(item) not in ('tuple', 'list'):
                        self.error('TypeError', 'exception args currently require a list or tuple')
                    item = tuple(self.data(item))

                elif name in ('__cause__', '__context__'):
                    if item is not None and self.kind(item) != 'exception':
                        self.error('TypeError', 'exception chain must contain guest exceptions')

                elif name == '__suppress_context__':
                    if type(item) is not bool:
                        self.error('TypeError', '__suppress_context__ must be a bool')

                elif name == '__traceback__':
                    if item is not None:
                        self.error('TypeError', 'only clearing a guest traceback is supported')
                    item = ()

                changes = {fields[name]: item}
                if name == '__cause__':
                    changes['suppress_context'] = True

                self.runtime.replace(value, dc.replace(info, **changes))
                return

            if info.namespace is None:
                info = dc.replace(info, namespace=self.new('namespace', {}))
                self.runtime.replace(value, info)

            namespace = info.namespace

        elif kind == 'class':
            if name in (
                    '__del__',
                    '__getattribute__',
                    '__getattr__',
                    '__setattr__',
                    '__delattr__',
                    '__new__',
            ):
                self.error('TypeError', f'{name} is not supported')

            namespace = self.data(value).namespace

        elif kind == 'module':
            namespace = self.data(value)

        else:
            self.error('AttributeError', f'{kind} attributes are not writable')

        if delete:
            if name not in self.data(namespace):
                self.error('AttributeError', name)
            self.runtime.delete(namespace, name)

        else:
            self.runtime.write(namespace, name, item)
