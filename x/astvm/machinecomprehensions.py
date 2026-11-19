# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc

from .state import ComprehensionState
from .state import Environment
from .state import Execution
from .state import GeneratorData
from .state import Outcome
from .state import Task


##


class MachineComprehensions:
    def _task_comprehension_outer(self, task: Task) -> None:
        self._add('comprehension_created', task.env, task.node)
        self._operation('iter', task.env, self._pop())

    def _task_comprehension_created(self, task: Task) -> None:
        iterator = self._pop()
        node = task.node

        env = Environment(
            task.env.program,
            task.env.program.scopes[node],
            self._space.new('namespace', {}),
            task.env.globals,
            task.env,
        )

        if isinstance(node, ast.GeneratorExp):
            state = ComprehensionState(node, None, iterator=iterator)
            execution = Execution(tasks=[Task('generator_end', env, node), Task('comprehension_next', env, data=state)])
            ref = self._space.new('generator', GeneratorData(execution))
            execution.generator = ref
            self._push(ref)

        else:
            kind = {ast.ListComp: 'list', ast.SetComp: 'set', ast.DictComp: 'dict'}[type(node)]
            result = self._space.new(kind, [] if kind == 'list' else {})
            self._add('comprehension_next', env, data=ComprehensionState(node, result, iterator=iterator))

    def _task_comprehension_next(self, task: Task) -> None:
        self._pull(
            task.env,
            task.data.iterator,
            Task('comprehension_item', task.env, data=task.data),
            Task('comprehension_stop', task.env, data=task.data),
        )

    def _task_comprehension_item(self, task: Task) -> None:
        state = task.data
        item = self._pop()

        self._add('comprehension_next', task.env, data=state)
        self._add('comprehension_condition', task.env, data=dc.replace(state, condition=0))
        self._add('assign', task.env, state.node.generators[state.level].target, (item, False))

    def _task_comprehension_condition(self, task: Task) -> None:
        state = task.data
        gen = state.node.generators[state.level]

        if state.condition < len(gen.ifs):
            self._add('comprehension_condition_value', task.env, data=state)
            self._evaluate(gen.ifs[state.condition], task.env)

        elif state.level + 1 < len(state.node.generators):
            self._add('comprehension_inner', task.env, data=state)
            self._evaluate(state.node.generators[state.level + 1].iter, task.env)

        else:
            self._add('comprehension_emit', task.env, data=state)
            if isinstance(state.node, ast.DictComp):
                self._many((state.node.key, state.node.value), task.env)
            else:
                self._evaluate(state.node.elt, task.env)

    def _task_comprehension_condition_value(self, task: Task) -> None:
        self._add('comprehension_condition_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_comprehension_condition_test(self, task: Task) -> None:
        if self._pop():
            state = dc.replace(task.data, condition=task.data.condition + 1)
            self._add('comprehension_condition', task.env, data=state)

    def _task_comprehension_inner(self, task: Task) -> None:
        self._add('comprehension_inner_iterator', task.env, data=task.data)
        self._operation('iter', task.env, self._pop())

    def _task_comprehension_inner_iterator(self, task: Task) -> None:
        state = dc.replace(task.data, level=task.data.level + 1, condition=0, iterator=self._pop())

        self._add('comprehension_next', task.env, data=state)

    def _task_comprehension_emit(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        if isinstance(state.node, ast.GeneratorExp):
            self._add('discard', task.env)
            self._suspend(value, waiting='yield')

        elif isinstance(state.node, ast.ListComp):
            self._space.append(state.result, value)

        elif isinstance(state.node, ast.DictComp):
            key, item = self._space.data(value)
            self._space.set_item(state.result, key, item)

        else:
            self._space.set_item(state.result, value, None)

    def _task_comprehension_stop(self, task: Task) -> None:
        self._pop()

        if task.data.level == 0:
            if isinstance(task.data.node, ast.GeneratorExp):
                self._unwind(Outcome('return'))
            else:
                self._push(task.data.result)
