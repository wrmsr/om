import collections
import contextlib
import typing as ta

from ..sql import NotifyingSqlConn


##


class RecordingSqlConn(NotifyingSqlConn):
    """Records every statement it's given and hands back canned result sets in order."""

    def __init__(self, results: ta.Iterable[ta.Sequence[ta.Sequence[ta.Any]]] = ()) -> None:
        super().__init__()

        self._results = collections.deque(results)

        self.calls: list[tuple[str, list[ta.Any]]] = []
        self.transactions = 0
        self.closed = False

    def execute(self, sql: str, params: ta.Sequence[ta.Any] = ()) -> ta.Sequence[ta.Sequence[ta.Any]]:
        self.calls.append((sql, list(params)))
        return self._results.popleft() if self._results else []

    @contextlib.contextmanager
    def _transaction(self) -> ta.Iterator[None]:
        self.transactions += 1
        yield

    def transaction(self) -> ta.ContextManager[None]:
        return self._transaction()

    def fileno(self) -> int:
        raise NotImplementedError

    def drain_notifies(self) -> ta.Sequence[str]:
        return []

    def close(self) -> None:
        self.closed = True
