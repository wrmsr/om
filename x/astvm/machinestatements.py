# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc

from .state import AnnotationData
from .state import Environment
from .state import LoopState
from .state import Outcome
from .state import Task
from .values import _MISSING
from .values import InterpreterError


##


class MachineStatements:
    def _task_exec(self, task: Task) -> None:
        node, env = task.node, task.env

        if isinstance(node, ast.Expr):
            self._add('discard', env)
            self._evaluate(node.value, env)

        elif isinstance(node, (ast.Pass, ast.Global, ast.Nonlocal)):
            pass

        elif isinstance(node, ast.Assign):
            self._add('assignment_value', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._add('annotated_done', env, node)
                self._add('assignment_value', env, node)
                self._evaluate(node.value, env)
            else:
                self._add('annotated_done', env, node)

        elif isinstance(node, ast.AugAssign):
            self._add('aug_location', env, node)
            self._location(node.target, env)

        elif isinstance(node, ast.Delete):
            for target in reversed(node.targets):
                self._add('assign', env, target, (_MISSING, True))

        elif isinstance(node, ast.If):
            self._add('if_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.While):
            self._add('loop', env, data=LoopState(node))

        elif isinstance(node, ast.For):
            self._add('for_iterable', env, node)
            self._evaluate(node.iter, env)

        elif isinstance(node, ast.Break):
            self._unwind(Outcome('break'))

        elif isinstance(node, ast.Continue):
            self._unwind(Outcome('continue'))

        elif isinstance(node, ast.Return):
            self._add('return_value', env, node)
            if node.value is None:
                self._push(None)
            else:
                self._evaluate(node.value, env)

        elif isinstance(node, ast.FunctionDef):
            self._add('bind_definition', env, node, node.name)
            self._define_function(node, env)

        elif isinstance(node, ast.ClassDef):
            self._add('bind_definition', env, node, node.name)
            self._add('class_values', env, node)
            self._many((*node.decorator_list, *node.bases), env)

        elif isinstance(node, ast.Try):
            if node.finalbody:
                self._add('finally', env, data=tuple(node.finalbody))
            if node.handlers:
                self._add('except', env, node)
            self._suite(node.body, env)

        elif isinstance(node, ast.Raise):
            if node.exc is None:
                exc = self._active_exception()
                if exc is None:
                    self._space.error('RuntimeError', 'No active exception to reraise')
                self._unwind(Outcome('raise', exc))
            else:
                self._add('raise_values', env, node)
                self._many((node.exc,) if node.cause is None else (node.exc, node.cause), env)

        elif isinstance(node, ast.Assert):
            self._add('assert_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.With):
            self._add('with_item', env, node, 0)

        elif isinstance(node, ast.Import):
            self._add('import_next', env, node, 0)

        elif isinstance(node, ast.ImportFrom):
            self._add('from_import', env, node)
            self._add('import_module', env, data=node.module)

        else:
            raise InterpreterError(f'validated statement has no evaluator: {type(node).__name__}')

    def _task_assignment_value(self, task: Task) -> None:
        value = self._pop()
        targets = task.node.targets if isinstance(task.node, ast.Assign) else [task.node.target]

        for target in reversed(targets):
            self._add('assign', task.env, target, (value, False))

    def _task_assign(self, task: Task) -> None:
        node, env = task.node, task.env
        value, delete = task.data

        if isinstance(node, ast.Name):
            self._write_name(env, node.id, value, delete=delete)

        elif isinstance(node, (ast.Tuple, ast.List)):
            if delete:
                for target in reversed(node.elts):
                    self._add('assign', env, target, (_MISSING, True))

            else:
                stars = sum(isinstance(n, ast.Starred) for n in node.elts)
                if stars > 1:
                    self._space.error('ValueError', 'multiple starred assignment targets')
                self._add('unpack_values', env, node)
                self._collect(env, value, None if stars else len(node.elts) + 1)

        elif isinstance(node, (ast.Attribute, ast.Subscript)):
            self._add('store_location', env, data=(value, delete))
            self._location(node, env)

        else:
            raise InterpreterError('invalid assignment target')

    def _task_unpack_values(self, task: Task) -> None:
        values = self._space.data(self._pop())
        targets = task.node.elts

        star = next((i for i, n in enumerate(targets) if isinstance(n, ast.Starred)), None)
        if star is None:
            if len(values) != len(targets):
                self._space.error('ValueError', 'wrong number of values to unpack')
            assignments = list(zip(targets, values))

        else:
            if len(values) < len(targets) - 1:
                self._space.error('ValueError', 'not enough values to unpack')
            tail = len(targets) - star - 1
            middle = values[star:len(values) - tail]
            assignments = [*zip(targets[:star], values[:star])]
            assignments.append((targets[star].value, self._space.new('list', list(middle))))
            if tail:
                assignments.extend(zip(targets[star + 1:], values[-tail:]))

        for target, value in reversed(assignments):
            self._add('assign', task.env, target, (value, False))

    def _location(self, node: ast.expr, env: Environment) -> None:
        if isinstance(node, ast.Name):
            self._push(self._space.new('location', ('name', env, node.id)))

        elif isinstance(node, ast.Attribute):
            self._add('attribute_location', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Subscript):
            self._add('subscript_location', env, node)
            self._many((node.value, node.slice), env)

        else:
            raise InterpreterError('invalid augmented-assignment location')

    def _task_attribute_location(self, task: Task) -> None:
        self._push(self._space.new('location', ('attribute', self._pop(), task.node.attr)))

    def _task_subscript_location(self, task: Task) -> None:
        value, key = self._space.data(self._pop())

        self._push(self._space.new('location', ('item', value, key)))

    def _task_store_location(self, task: Task) -> None:
        location = self._space.data(self._pop())
        value, delete = task.data
        kind, receiver, key = location

        if kind == 'name':
            self._write_name(receiver, key, value, delete=delete)

        elif kind == 'attribute':
            self._space.set_attribute(receiver, key, value, delete=delete)

        else:
            self._add('discard', task.env)
            self._operation('delitem' if delete else 'setitem', task.env, receiver, key, value)

    def _task_aug_location(self, task: Task) -> None:
        location = self._pop()
        kind, receiver, key = self._space.data(location)

        self._add('aug_old_value', task.env, task.node, location)

        if kind == 'name':
            self._push(self._read_name(receiver, key))
        elif kind == 'attribute':
            self._operation('getattr', task.env, receiver, key)
        else:
            self._operation('getitem', task.env, receiver, key)

    def _task_aug_old_value(self, task: Task) -> None:
        self._add('aug_rhs', task.env, task.node, (task.data, self._pop()))
        self._evaluate(task.node.value, task.env)

    def _task_aug_rhs(self, task: Task) -> None:
        location, old = task.data
        rhs = self._pop()

        self._add('aug_result', task.env, data=location)
        self._operation('inplace:' + type(task.node.op).__name__, task.env, old, rhs)

    def _task_aug_result(self, task: Task) -> None:
        value = self._pop()

        self._push(task.data)
        self._add('store_location', task.env, data=(value, False))

    def _task_annotated_done(self, task: Task) -> None:
        node = task.node

        if task.env.scope.kind in ('module', 'class') and node.simple and isinstance(node.target, ast.Name):
            namespace = self._space.data(task.env.namespace)

            annotations = namespace.get('__annotations__')
            if annotations is None or self._space.kind(annotations) != 'annotations':
                annotations = self._space.new('annotations', AnnotationData(task.env, ()))
                self._runtime.write(task.env.namespace, '__annotations__', annotations)

            info = self._space.data(annotations)
            self._runtime.replace(annotations, dc.replace(
                info, entries=(*info.entries, (node.target.id, node.annotation)), cached=None,
            ))
