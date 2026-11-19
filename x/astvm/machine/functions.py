# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc
import typing as ta

from ..state import AnnotationData
from ..state import ClassData
from ..state import Environment
from ..state import Execution
from ..state import FunctionData
from ..state import GeneratorData
from ..state import Task
from ..values import _MISSING
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value


##


class MachineFunctions:
    def _define_function(self, node: ast.FunctionDef | ast.Lambda, env: Environment) -> None:
        decorators = node.decorator_list if isinstance(node, ast.FunctionDef) else []
        defaults = [*node.args.defaults, *(v for v in node.args.kw_defaults if v is not None)]

        self._add('function_values', env, node, len(decorators))
        self._many([*decorators, *defaults], env)

    def _task_function_values(self, task: Task) -> None:
        values = self._space.data(self._pop())
        args = task.node.args
        decorators = values[:task.data]
        defaults = values[task.data:task.data + len(args.defaults)]
        kwvalues = iter(values[task.data + len(args.defaults):])
        kwdefaults = {
            arg.arg: next(kwvalues)
            for arg, default in zip(args.kwonlyargs, args.kw_defaults)
            if default is not None
        }

        annotations = []
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            if arg.annotation is not None:
                annotations.append((arg.arg, arg.annotation))
        for arg in (args.vararg, args.kwarg):
            if arg is not None and arg.annotation is not None:
                annotations.append((arg.arg, arg.annotation))
        if isinstance(task.node, ast.FunctionDef) and task.node.returns is not None:
            annotations.append(('return', task.node.returns))

        thunk = self._space.new('annotations', AnnotationData(task.env, tuple(annotations)))

        function = self._space.new(
            'function',
            FunctionData(
                task.node,
                task.env,
                defaults,
                kwdefaults,
                thunk,
                self._space.data(task.env.globals).get('__name__', '__main__'),
            ),
        )

        self._add('decorate', task.env, data=(decorators, function))

    def _task_decorate(self, task: Task) -> None:
        decorators, value = task.data

        if not decorators:
            self._push(value)
        else:
            self._add('decorated', task.env, data=decorators[:-1])
            self._invoke(task.env, decorators[-1], (value,))

    def _task_decorated(self, task: Task) -> None:
        self._add('decorate', task.env, data=(task.data, self._pop()))

    def _task_bind_definition(self, task: Task) -> None:
        self._write_name(task.env, task.data, self._pop())

    def _bind_arguments(
            self,
            info: FunctionData,
            values: tuple[Value, ...],
            keywords: ta.Mapping[str, Value],
    ) -> Environment:
        args = info.node.args
        positional = [*args.posonlyargs, *args.args]
        bindings: dict[str, Value] = {}

        if len(values) > len(positional) and args.vararg is None:
            self._space.error('TypeError', 'too many positional arguments')

        for arg, value in zip(positional, values):
            bindings[arg.arg] = value

        extra = {}
        posonly = {arg.arg for arg in args.posonlyargs}
        accepted = {arg.arg for arg in [*args.args, *args.kwonlyargs]}

        for name, value in keywords.items():
            if name in accepted:
                if name in bindings:
                    self._space.error('TypeError', f'multiple values for argument {name!r}')
                bindings[name] = value

            elif args.kwarg is not None:
                extra[name] = value

            else:
                message = (
                    'positional-only argument passed as keyword' if name in posonly else 'unexpected keyword argument'
                )
                self._space.error('TypeError', f'{message}: {name}')

        default_start = len(positional) - len(info.defaults)

        for index, arg in enumerate(positional):
            if arg.arg not in bindings:
                if index < default_start:
                    self._space.error('TypeError', f'missing positional argument {arg.arg}')
                bindings[arg.arg] = info.defaults[index - default_start]

        for arg in args.kwonlyargs:
            if arg.arg not in bindings:
                if arg.arg not in info.kwdefaults:
                    self._space.error('TypeError', f'missing keyword-only argument {arg.arg}')
                bindings[arg.arg] = info.kwdefaults[arg.arg]

        if args.vararg is not None:
            bindings[args.vararg.arg] = self._space.new('tuple', values[len(positional):])

        if args.kwarg is not None:
            bindings[args.kwarg.arg] = self._space.make_dict(tuple(extra.items()))

        namespace = self._space.new('namespace', bindings)
        parent = info.environment
        first_args = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        first_arg = first_args[0] if first_args else args.vararg or args.kwarg

        return Environment(
            parent.program,
            parent.program.scopes[info.node],
            namespace,
            parent.globals,
            parent,
            first_arg_name=first_arg.arg if first_arg is not None else None,
        )

    def _enter_function(
            self,
            function: ObjectRef,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        info = self._space.data(function)
        env = self._bind_arguments(info, args, kwargs)

        tasks = [Task('generator_end' if env.scope.generator else 'function_end', env, info.node)]
        if isinstance(info.node, ast.Lambda):
            tasks.extend([Task('return_value', env, info.node), Task('eval', env, info.node.body)])
        else:
            tasks.extend(Task('exec', env, node) for node in reversed(info.node.body))

        if env.scope.generator:
            execution = Execution(tasks=tasks)
            generator = self._space.new('generator', GeneratorData(execution))
            self._runtime.edit_generator(generator).execution.generator = generator
            self._push(generator)

        else:
            if self._thread.call_depth >= self._budget.limits.call_depth:
                self._budget.fail('guest call depth limit')
            self._thread.call_depth += 1
            tasks[0] = dc.replace(tasks[0], base=len(self._execution().values))
            self._execution().tasks.extend(tasks)

    def _task_function_end(self, task: Task) -> None:
        self._thread.call_depth -= 1
        self._push(None)

    def _task_class_values(self, task: Task) -> None:
        if not isinstance(task.node, ast.ClassDef):
            raise InterpreterError('class task lacks a class definition')
        values = tuple(self._space.data(self._pop()))
        self._add('class_keyword_next', task.env, task.node, (values, 0, ()))

    def _class_keyword_add(
            self,
            keywords: tuple[tuple[str, Value], ...],
            name: Value,
            value: Value,
    ) -> tuple[tuple[str, Value], ...]:
        if type(name) is not str:
            self._space.error('TypeError', 'keywords must be strings')
        name = ta.cast(str, name)
        if name == 'metaclass':
            self._space.error('TypeError', 'custom metaclasses are not supported')
        if any(existing == name for existing, _ in keywords):
            self._space.error('TypeError', f'multiple values for keyword argument {name!r}')
        self._budget.size(len(keywords) + 1)
        return (*keywords, (name, value))

    def _task_class_keyword_next(self, task: Task) -> None:
        values, index, keywords = task.data
        node = ta.cast(ast.ClassDef, task.node)
        if index == len(node.keywords):
            self._begin_class_body(task, values, dict(keywords))
            return
        self._add('class_keyword_value', task.env, node, task.data)
        self._evaluate(node.keywords[index].value, task.env)

    def _task_class_keyword_value(self, task: Task) -> None:
        values, index, keywords = task.data
        node = ta.cast(ast.ClassDef, task.node)
        name = node.keywords[index].arg
        value = self._pop()
        if name is not None:
            updated = self._class_keyword_add(keywords, name, value)
            self._add('class_keyword_next', task.env, task.node, (values, index + 1, updated))
        elif self._space.kind(value) in ('instance', 'exception'):
            self._add('class_kwargs_guard', task.env, task.node, (values, index, keywords, value))
            self._operation('getattr', task.env, value, 'keys')
        else:
            for key, item in self._space.mapping_pairs(value):
                keywords = self._class_keyword_add(keywords, key, item)
            self._add('class_keyword_next', task.env, task.node, (values, index + 1, keywords))

    def _task_class_kwargs_guard(self, task: Task) -> None:
        self._add('class_kwargs_keys', task.env, task.node, task.data)
        self._invoke(task.env, self._pop(), ())

    def _task_class_kwargs_keys(self, task: Task) -> None:
        self._add('class_kwargs_entries_start', task.env, task.node, task.data)
        self._collect(task.env, self._pop())

    def _task_class_kwargs_entries_start(self, task: Task) -> None:
        self._add('class_kwargs_entries', task.env, task.node, (*task.data, self._pop(), 0))

    def _task_class_kwargs_entries(self, task: Task) -> None:
        values, index, keywords, source, keys, key_index = task.data
        entries = self._space.data(keys)
        if key_index == len(entries):
            self._add('class_keyword_next', task.env, task.node, (values, index + 1, keywords))
            return
        name = entries[key_index]
        if type(name) is not str:
            self._space.error('TypeError', 'keywords must be strings')
        if any(existing == name for existing, _ in keywords):
            self._space.error('TypeError', f'multiple values for keyword argument {name!r}')
        self._add('class_kwargs_item', task.env, task.node, task.data)
        self._operation('getitem', task.env, source, name)

    def _task_class_kwargs_item(self, task: Task) -> None:
        values, index, keywords, source, keys, key_index = task.data
        name = self._space.data(keys)[key_index]
        updated = self._class_keyword_add(keywords, name, self._pop())
        self._add('class_kwargs_entries', task.env, task.node, (values, index, updated, source, keys, key_index + 1))

    def _begin_class_body(self, task: Task, values: tuple[Value, ...], keywords: dict[str, Value]) -> None:
        node = ta.cast(ast.ClassDef, task.node)
        count = len(node.decorator_list)
        decorators = values[:count]
        bases = values[count:] or (self._space.types['object'],)

        namespace = self._space.new('namespace', {
            '__module__': self._space.data(task.env.globals).get('__name__', '__main__'),
            '__qualname__': getattr(node, '_astvm_qualname', node.name),
            '__doc__': ast.get_docstring(node, clean=False),
        })

        env = Environment(
            task.env.program,
            task.env.program.scopes[node],
            namespace,
            task.env.globals,
            task.env,
            class_cell=self._space.new('cell', _MISSING),
        )

        self._add('class_end', env, node, (bases, decorators, keywords))
        self._suite(node.body, env)

    _TASK_CLASS_END_UNSUPPORTED: ta.ClassVar = frozenset({
        '__del__',
        '__slots__',
        '__class_getitem__',
    })

    def _task_class_end(self, task: Task) -> None:
        namespace = self._space.data(task.env.namespace)
        unsupported = self._TASK_CLASS_END_UNSUPPORTED

        bad = unsupported.intersection(namespace)
        if bad:
            self._space.error('TypeError', 'unsupported class hooks: ' + ', '.join(sorted(bad)))

        if type(namespace.get('__qualname__')) is not str:
            self._space.error('TypeError', 'class qualified name must be a string')

        if '__classcell__' in namespace:
            if not task.env.scope.class_cell:
                self._space.error('TypeError', '__classcell__ must be a nonlocal cell')
            self._runtime.delete(task.env.namespace, '__classcell__')

        if '__eq__' in namespace and '__hash__' not in namespace:
            self._runtime.write(task.env.namespace, '__hash__', None)

        new_method = namespace.get('__new__', _MISSING)
        if new_method is not _MISSING and self._space.kind(new_method) == 'function':
            self._runtime.write(task.env.namespace, '__new__', self._space.new('staticmethod', new_method))

        subclass_method = namespace.get('__init_subclass__', _MISSING)
        if subclass_method is not _MISSING and self._space.kind(subclass_method) == 'function':
            self._runtime.write(
                task.env.namespace, '__init_subclass__', self._space.new('classmethod', subclass_method),
            )

        bases, decorators, keywords = task.data

        for base in bases:
            if self._space.kind(base) not in ('class', 'type'):
                self._space.error('TypeError', 'base must be a guest class')

            if self._space.kind(base) == 'type' and base != self._space.types['object']:
                if not self._space.subclass(base, self._space.types['BaseException']):
                    self._space.error('TypeError', 'subclassing intrinsic types is not supported')

        mro_tail = self._space.mro_tail(bases)

        cls = self._space.new('class', ClassData(task.node.name, task.env.namespace, bases))
        self._runtime.replace(cls, dc.replace(self._space.data(cls), mro=(cls, *mro_tail)))
        self._runtime.replace(task.env.class_cell, cls)

        self._add('decorate', task.env.parent, data=(decorators, cls))
        self._add('class_init_subclass', task.env, data=(cls, keywords))
        self._add('class_set_name_next', task.env, data=(cls, tuple(namespace.items()), 0))

    def _task_class_init_subclass(self, task: Task) -> None:
        cls, keywords = task.data
        method = self._space.lookup_super(cls, cls, '__init_subclass__', cls)
        if method is _MISSING:
            return

        if (
            self._space.kind(method) == 'builtin' and
            self._space.data(method).name == 'object_init_subclass' and not keywords
        ):
            return
        self._add('discard', task.env)
        getter = self._space.special(method, '__get__')
        if getter is not _MISSING:
            self._add('class_init_subclass_bound', task.env, data=keywords)
            self._invoke(task.env, getter, (None, cls))
        else:
            self._invoke(task.env, self._space.bind(method, _MISSING, cls), (), keywords)

    def _task_class_init_subclass_bound(self, task: Task) -> None:
        self._invoke(task.env, self._pop(), (), task.data)

    def _task_class_set_name_next(self, task: Task) -> None:
        cls, entries, index = task.data
        if index == len(entries):
            return

        name, value = entries[index]
        self._add('class_set_name_next', task.env, data=(cls, entries, index + 1))
        method = self._space.special(value, '__set_name__')
        if method is not _MISSING:
            self._add('discard', task.env)
            self._invoke_special_method(task.env, value, method, (cls, name))

    def _task_instance_initialized(self, task: Task) -> None:
        if self._pop() is not None:
            self._space.error('TypeError', '__init__() must return None')
        self._push(task.data)

    def _resolve(self, value: Value, env: Environment) -> None:
        if self._space.kind(value) != 'annotations':
            self._push(value)
            return

        info = self._space.data(value)
        if info.cached is not None:
            self._push(info.cached)
        else:
            self._add('annotation_next', info.environment, data=(value, 0, self._space.new('dict', {})))

    def _task_annotation_next(self, task: Task) -> None:
        ref, index, result = task.data
        info = self._space.data(ref)

        if index == len(info.entries):
            self._runtime.replace(ref, dc.replace(info, cached=result))
            self._push(result)
        else:
            self._add('annotation_value', task.env, data=task.data)
            self._evaluate(info.entries[index][1], info.environment)

    def _task_annotation_value(self, task: Task) -> None:
        ref, index, result = task.data
        name = self._space.data(ref).entries[index][0]

        self._space.set_item(result, name, self._pop())
        self._add('annotation_next', task.env, data=(ref, index + 1, result))
