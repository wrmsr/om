# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc
import typing as ta

from .state import AnnotationData
from .state import ClassData
from .state import Environment
from .state import Execution
from .state import FunctionData
from .state import GeneratorData
from .state import Task
from .values import ObjectRef
from .values import Value


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

        return Environment(
            parent.program,
            parent.program.scopes[info.node],
            namespace,
            parent.globals,
            parent,
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
        values = self._space.data(self._pop())
        count = len(task.node.decorator_list)
        decorators = values[:count]
        base = values[count] if len(values) > count else self._space.types['object']

        if self._space.kind(base) not in ('class', 'type'):
            self._space.error('TypeError', 'base must be a guest class')

        if self._space.kind(base) == 'type' and base != self._space.types['object']:
            if not self._space.subclass(base, self._space.types['BaseException']):
                self._space.error('TypeError', 'subclassing intrinsic types is not supported')

        namespace = self._space.new('namespace', {
            '__module__': self._space.data(task.env.globals).get('__name__', '__main__'),
            '__qualname__': task.node.name,
        })

        env = Environment(
            task.env.program,
            task.env.program.scopes[task.node],
            namespace,
            task.env.globals,
            task.env,
        )

        self._add('class_end', env, task.node, (base, decorators))
        self._suite(task.node.body, env)

    _TASK_CLASS_END_UNSUPPORTED: ta.ClassVar = frozenset({
        '__del__',
        '__slots__',
        '__getattribute__',
        '__getattr__',
        '__setattr__',
        '__delattr__',
        '__new__',
        '__init_subclass__',
        '__class_getitem__',
        '__set_name__',
        '__get__',
        '__set__',
        '__delete__',
    })

    def _task_class_end(self, task: Task) -> None:
        namespace = self._space.data(task.env.namespace)
        unsupported = self._TASK_CLASS_END_UNSUPPORTED

        bad = unsupported.intersection(namespace)
        if bad:
            self._space.error('TypeError', 'unsupported class hooks: ' + ', '.join(sorted(bad)))

        base, decorators = task.data

        cls = self._space.new('class', ClassData(task.node.name, task.env.namespace, base))

        self._add('decorate', task.env.parent, data=(decorators, cls))

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
