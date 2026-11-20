import typing as ta

from ..state import Environment
from ..state import Task
from ..values import InterpreterError
from ..values import Value
from .base import MachineBase


##


class MachineStrings(MachineBase):
    def _string_method(
            self,
            env: Environment,
            value: Value,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name == 'join':
            self._arity(name, args, kwargs, 1, 1)
            self._add('string_join', env, data=value)
            self._collect(env, args[0])
            return

        if kwargs:
            space.error('TypeError', 'string method keyword arguments are not supported')

        primitive = ta.cast('str | bytes', value)
        exported: list[object] = []

        for arg in args:
            if space.kind(arg) == 'tuple':
                parts = space.data(arg)
                if any(type(v) not in (str, bytes) for v in parts):
                    space.error('TypeError', 'string argument tuple must contain strings')
                exported.append(tuple(parts))

            elif type(arg) in (type(None), bool, int, str, bytes):
                exported.append(arg)

            else:
                space.error('TypeError', 'string methods accept only intrinsic data')

        self._budget.tick(len(primitive) // 64 + 1)
        if name in ('upper', 'lower', 'casefold', 'capitalize', 'title', 'swapcase'):
            self._budget.size(len(primitive) * 3, string=True)

        if name == 'replace' and len(exported) in (2, 3) and type(primitive) is str:
            old, new = exported[:2]
            if type(old) is str and type(new) is str:
                count = str.count(primitive, old)
                if len(exported) == 3:
                    limit = exported[2]
                    if type(limit) in (bool, int) and ta.cast(int, limit) >= 0:
                        count = min(count, ta.cast(int, limit))
                estimate = len(primitive) + max(0, len(new) - len(old)) * count
                self._budget.size(estimate, string=True)

        if name in ('split', 'rsplit', 'splitlines'):
            # Conservative preflight: avoids allocating an unbounded number of substrings in one host call.
            self._budget.size(len(primitive) + 1)

        primitive_type = str if type(primitive) is str else bytes

        # This lookup is constrained by the immutable method allowlist and an exact primitive receiver.
        if name not in space._METHODS[primitive_type.__name__]:  # noqa: SLF001
            raise InterpreterError('string method was not whitelisted')

        method = vars(primitive_type)[name]
        result = space.native(method, primitive, *exported)
        self._push(space.import_value(result))

    def _task_string_join(self, task: Task) -> None:
        values = self._space.data(self._pop())

        if any(type(v) is not str for v in values):
            self._space.error('TypeError', 'str.join requires strings')

        size = sum(map(len, values)) + max(0, len(values) - 1) * len(task.data)

        self._budget.size(size, string=True)
        self._budget.allocate(size)
        self._push(str.join(task.data, values))
