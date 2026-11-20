import ast
import typing as ta

from ..state import Environment
from ..state import SourceModule
from ..state import Task
from ..values import BoundaryError
from ..values import Value
from ..values import _GuestRaise
from .base import MachineBase


##


class MachineImports(MachineBase):
    def _task_import_next(self, task: Task) -> None:
        node = ta.cast('ast.Import', task.node)

        if task.data < len(node.names):
            self._add('import_bound', task.env, node, task.data)
            self._add('import_module', task.env, data=node.names[task.data].name)

    def _task_import_bound(self, task: Task) -> None:
        node = ta.cast('ast.Import', task.node)

        alias = node.names[task.data]

        self._write_name(task.env, alias.asname or alias.name, self._pop())
        self._add('import_next', task.env, node, task.data + 1)

    def _task_from_import(self, task: Task) -> None:
        node = ta.cast('ast.ImportFrom', task.node)

        module = self._pop()

        for alias in node.names:
            try:
                value = self._space.get_attribute(module, alias.name)

            except _GuestRaise as exc:
                if self._space.exception_matches(exc.value, self._space.types['AttributeError']):
                    self._space.error('ImportError', 'cannot import name ' + alias.name)
                raise

            self._write_name(task.env, alias.asname or alias.name, value)

    def _task_import_module(self, task: Task) -> None:
        name = task.data

        if name in self._runtime.modules():
            self._push(self._runtime.modules()[name])
            return

        if name not in self._modules:
            self._space.error('ModuleNotFoundError', 'module is not granted: ' + name)

        source = self._modules[name]
        namespace = self._space.new('namespace', {'__name__': name, '__package__': ''})
        module = self._space.new('module', namespace)

        if type(source) is SourceModule:
            source_module = source
            program = self._frontend.prepare(source_module.source, filename=source_module.filename)
            self._programs.append(program)
            env = Environment(program, program.scopes[program.tree], namespace, namespace)
            self._runtime.set_module(name, module)
            self._add('module_end', env, data=(name, module))
            self._suite(ta.cast('ast.Module', program.tree).body, env)

        else:
            memo: dict[int, Value] = {}
            for key, value in ta.cast('ta.Mapping[str, object]', source).items():
                if type(key) is not str:
                    raise BoundaryError('intrinsic module names must be strings')
                self._runtime.write(namespace, key, self._space.import_value(value, capabilities=True, memo=memo))
            self._runtime.set_module(name, module)
            self._push(module)

    def _task_module_end(self, task: Task) -> None:
        self._push(task.data[1])
