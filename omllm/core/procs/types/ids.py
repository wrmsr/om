import abc
import itertools
import typing as ta

from omcore import lang


##


ProcessId = ta.NewType('ProcessId', str)


class ProcessIdGenerator(lang.Abstract):
    @abc.abstractmethod
    def next_id(self) -> ProcessId:
        raise NotImplementedError


class CountingProcessIdGenerator(ProcessIdGenerator):
    """Short, human and llm friendly ids: p1, p2, ... Unique per manager instance."""

    def __init__(self, prefix: str = 'p') -> None:
        super().__init__()

        self._prefix = prefix
        self._counter = itertools.count(1)

    def next_id(self) -> ProcessId:
        return ProcessId(f'{self._prefix}{next(self._counter)}')
