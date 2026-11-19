# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc

from .state import CallArguments
from .state import Task
from .values import _ELLIPSIS
from .values import InterpreterError


##


class MachineExpressions:
    def _task_eval(self, task: Task) -> None:
        node, env = task.node, task.env
        space = self._space

        if isinstance(node, ast.Constant):
            self._push(_ELLIPSIS if node.value is Ellipsis else node.value)

        elif isinstance(node, ast.Name):
            self._resolve(self._read_name(env, node.id), env)

        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            self._add('literal_next', env, node, (0, space.new('list', [])))

        elif isinstance(node, ast.Dict):
            self._add('dict_next', env, node, (0, space.new('dict', {})))

        elif isinstance(node, ast.BinOp):
            self._add('binary_values', env, node, type(node.op).__name__)
            self._many((node.left, node.right), env)

        elif isinstance(node, ast.UnaryOp):
            self._add('unary_value', env, node, type(node.op).__name__)
            self._evaluate(node.operand, env)

        elif isinstance(node, ast.BoolOp):
            self._add('bool_value', env, node, 0)
            self._evaluate(node.values[0], env)

        elif isinstance(node, ast.Compare):
            self._add('compare_left', env, node)
            self._evaluate(node.left, env)

        elif isinstance(node, ast.IfExp):
            self._add('ifexpr_value', env, node)
            self._evaluate(node.test, env)

        elif isinstance(node, ast.NamedExpr):
            self._add('named_value', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Attribute):
            self._add('attribute_value', env, node, node.attr)
            self._evaluate(node.value, env)

        elif isinstance(node, ast.Subscript):
            self._add('subscript_values', env, node)
            self._many((node.value, node.slice), env)

        elif isinstance(node, ast.Slice):
            parts = (node.lower, node.upper, node.step)
            self._add('slice_values', env, node)
            self._many(tuple(n if n is not None else ast.Constant(None) for n in parts), env)

        elif isinstance(node, ast.Call):
            self._add('call_function', env, node)
            self._evaluate(node.func, env)

        elif isinstance(node, ast.Lambda):
            self._define_function(node, env)

        elif isinstance(node, ast.Yield):
            self._add('yield_value', env, node)
            if node.value is None:
                self._push(None)
            else:
                self._evaluate(node.value, env)

        elif isinstance(node, ast.YieldFrom):
            self._add('yieldfrom_iterable', env, node)
            self._evaluate(node.value, env)

        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            self._add('comprehension_outer', env, node)
            self._evaluate(node.generators[0].iter, env)

        elif isinstance(node, ast.JoinedStr):
            self._add('joined_values', env, node)
            self._many(node.values, env)

        elif isinstance(node, ast.FormattedValue):
            self._add('formatted_values', env, node)
            self._many((node.value, node.format_spec or ast.Constant('')), env)

        else:
            raise InterpreterError(f'validated expression has no evaluator: {type(node).__name__}')

    def _task_literal_next(self, task: Task) -> None:
        index, result = task.data

        if index == len(task.node.elts):
            kind = {ast.List: 'list', ast.Tuple: 'tuple', ast.Set: 'set'}[type(task.node)]

            if kind == 'list':
                self._push(result)

            elif kind == 'tuple':
                self._push(self._space.new('tuple', tuple(self._space.data(result))))

            else:
                output = self._space.new('set', {})
                for value in self._space.data(result):
                    self._space.set_item(output, value, None)
                self._push(output)

            return

        node = task.node.elts[index]
        self._add('literal_value', task.env, task.node, (index, result, isinstance(node, ast.Starred)))
        self._evaluate(node.value if isinstance(node, ast.Starred) else node, task.env)

    def _task_literal_value(self, task: Task) -> None:
        index, result, starred = task.data
        value = self._pop()

        if starred:
            self._add('literal_extend', task.env, task.node, (index, result))
            self._collect(task.env, value)

        else:
            self._space.append(result, value)
            self._add('literal_next', task.env, task.node, (index + 1, result))

    def _task_literal_extend(self, task: Task) -> None:
        index, result = task.data

        for value in self._space.data(self._pop()):
            self._budget.tick()
            self._space.append(result, value)

        self._add('literal_next', task.env, task.node, (index + 1, result))

    def _task_dict_next(self, task: Task) -> None:
        index, result = task.data

        if index == len(task.node.keys):
            self._push(result)
            return

        key = task.node.keys[index]
        self._add('dict_value', task.env, task.node, task.data)

        if key is None:
            self._evaluate(task.node.values[index], task.env)
        else:
            self._many((key, task.node.values[index]), task.env)

    def _task_dict_value(self, task: Task) -> None:
        index, result = task.data
        value = self._pop()

        if task.node.keys[index] is None:
            if self._space.kind(value) in ('instance', 'exception'):
                self._add('dict_next', task.env, task.node, (index + 1, result))
                self._add('dict_unpack_guard', task.env, data=(result, value))
                self._operation('getattr', task.env, value, 'keys')
                return
            for key, item in self._space.mapping_pairs(value):
                self._budget.tick()
                self._space.set_item(result, key, item)

        else:
            key, item = self._space.data(value)
            self._space.set_item(result, key, item)

        self._add('dict_next', task.env, task.node, (index + 1, result))

    def _task_dict_unpack_guard(self, task: Task) -> None:
        self._add('mapping_keys_iterable', task.env, data=task.data)
        self._invoke(task.env, self._pop(), ())

    def _task_binary_values(self, task: Task) -> None:
        left, right = self._space.data(self._pop())

        self._operation('binary:' + task.data, task.env, left, right)

    def _task_unary_value(self, task: Task) -> None:
        self._operation('unary:' + task.data, task.env, self._pop())

    def _task_bool_value(self, task: Task) -> None:
        value = self._pop()

        if task.data + 1 == len(task.node.values):
            self._push(value)
            return

        self._add('bool_test', task.env, task.node, (task.data, value))
        self._operation('truth', task.env, value)

    def _task_bool_test(self, task: Task) -> None:
        index, value = task.data
        truth = self._pop()

        if truth == isinstance(task.node.op, ast.Or):
            self._push(value)

        else:
            self._add('bool_value', task.env, task.node, index + 1)
            self._evaluate(task.node.values[index + 1], task.env)

    def _task_compare_left(self, task: Task) -> None:
        self._add('compare_right', task.env, task.node, (0, self._pop()))
        self._evaluate(task.node.comparators[0], task.env)

    def _task_compare_right(self, task: Task) -> None:
        index, left = task.data
        right = self._pop()

        self._add('compare_result', task.env, task.node, (index, right))
        self._operation('compare:' + type(task.node.ops[index]).__name__, task.env, left, right)

    def _task_compare_result(self, task: Task) -> None:
        value = self._pop()
        index, right = task.data

        if index + 1 == len(task.node.ops):
            self._push(value)
            return

        self._add('compare_test', task.env, task.node, (index, right, value))
        self._operation('truth', task.env, value)

    def _task_compare_test(self, task: Task) -> None:
        index, right, result = task.data

        if not self._pop():
            self._push(result)

        else:
            self._add('compare_right', task.env, task.node, (index + 1, right))
            self._evaluate(task.node.comparators[index + 1], task.env)

    def _task_ifexpr_value(self, task: Task) -> None:
        self._add('ifexpr_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_ifexpr_test(self, task: Task) -> None:
        self._evaluate(task.node.body if self._pop() else task.node.orelse, task.env)

    def _task_named_value(self, task: Task) -> None:
        value = self._pop()
        env = task.env

        while env.scope.kind == 'comprehension':
            env = env.parent

        self._write_name(env, task.node.target.id, value)
        self._push(value)

    def _task_attribute_value(self, task: Task) -> None:
        self._operation('getattr', task.env, self._pop(), task.data)

    def _task_subscript_values(self, task: Task) -> None:
        value, key = self._space.data(self._pop())

        self._operation('getitem', task.env, value, key)

    def _task_slice_values(self, task: Task) -> None:
        self._push(self._space.new('slice', self._space.data(self._pop())))

    def _task_joined_values(self, task: Task) -> None:
        values = self._space.data(self._pop())

        if any(type(v) is not str for v in values):
            raise InterpreterError('f-string component was not converted to a string')

        size = sum(map(len, values))

        self._budget.size(size, string=True)
        self._budget.allocate(size)
        self._push(''.join(values))

    def _task_formatted_values(self, task: Task) -> None:
        value, spec = self._space.data(self._pop())

        if task.node.conversion == -1:
            self._operation('format', task.env, value, spec)

        else:
            conversion = {ord('r'): 'repr', ord('s'): 'str', ord('a'): 'ascii'}[task.node.conversion]
            self._add('format_converted', task.env, data=spec)
            self._operation(conversion, task.env, value)

    def _task_format_converted(self, task: Task) -> None:
        self._operation('format', task.env, self._pop(), task.data)

    def _task_call_function(self, task: Task) -> None:
        self._add('call_argument', task.env, task.node, CallArguments(self._pop()))

    def _task_call_argument(self, task: Task) -> None:
        state = task.data
        node = task.node

        if state.index < len(node.args):
            arg = node.args[state.index]
            self._add('call_argument_value', task.env, node, state)
            self._evaluate(arg.value if isinstance(arg, ast.Starred) else arg, task.env)

        elif state.index < len(node.args) + len(node.keywords):
            kw = node.keywords[state.index - len(node.args)]
            self._add('call_keyword_value', task.env, node, state)
            self._evaluate(kw.value, task.env)

        else:
            self._invoke(task.env, state.function, state.positional, dict(state.keywords))

    def _task_call_argument_value(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        if isinstance(task.node.args[state.index], ast.Starred):
            self._add('call_star_values', task.env, task.node, state)
            self._collect(task.env, value)

        else:
            self._add('call_argument', task.env, task.node, dc.replace(
                state,
                index=state.index + 1,
                positional=(*state.positional, value),
            ))

    def _task_call_star_values(self, task: Task) -> None:
        state = task.data
        values = self._space.data(self._pop())

        self._budget.size(len(state.positional) + len(values))
        self._add('call_argument', task.env, task.node, dc.replace(
            state,
            index=state.index + 1,
            positional=(*state.positional, *values),
        ))

    def _task_call_keyword_value(self, task: Task) -> None:
        state = task.data
        key = task.node.keywords[state.index - len(task.node.args)].arg
        value = self._pop()
        if key is None and self._space.kind(value) in ('instance', 'exception'):
            self._add('call_kwargs_guard', task.env, task.node, (state, value))
            self._operation('getattr', task.env, value, 'keys')
            return
        pairs = [(key, value)] if key is not None else self._space.mapping_pairs(value)
        keywords = dict(state.keywords)

        for name, item in pairs:
            if type(name) is not str:
                self._space.error('TypeError', 'keywords must be strings')
            if name in keywords:
                self._space.error('TypeError', f'multiple values for keyword argument {name!r}')
            keywords[name] = item

        self._budget.size(len(keywords))
        self._add('call_argument', task.env, task.node, dc.replace(
            state, index=state.index + 1, keywords=tuple(keywords.items()),
        ))

    def _task_call_kwargs_guard(self, task: Task) -> None:
        self._add('call_kwargs_keys', task.env, task.node, task.data)
        self._invoke(task.env, self._pop(), ())

    def _task_call_kwargs_keys(self, task: Task) -> None:
        self._add('call_kwargs_entries_start', task.env, task.node, task.data)
        self._collect(task.env, self._pop())

    def _task_call_kwargs_entries_start(self, task: Task) -> None:
        state, source = task.data
        self._add('call_kwargs_entries', task.env, task.node, (state, source, self._pop(), 0, state.keywords))

    def _task_call_kwargs_entries(self, task: Task) -> None:
        state, source, keys, index, keywords = task.data
        keys = self._space.data(keys)

        if index == len(keys):
            self._budget.size(len(keywords))
            self._add('call_argument', task.env, task.node, dc.replace(
                state, index=state.index + 1, keywords=keywords,
            ))
            return

        name = keys[index]
        if type(name) is not str:
            self._space.error('TypeError', 'keywords must be strings')
        if name in dict(keywords):
            self._space.error('TypeError', f'multiple values for keyword argument {name!r}')

        self._add('call_kwargs_item', task.env, task.node, task.data)
        self._operation('getitem', task.env, source, name)

    def _task_call_kwargs_item(self, task: Task) -> None:
        state, source, keys, index, keywords = task.data
        name = self._space.data(keys)[index]
        self._add(
            'call_kwargs_entries', task.env, task.node,
            (state, source, keys, index + 1, (*keywords, (name, self._pop()))),
        )
