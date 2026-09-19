from ...api.dialects import Dialect


##


class SqliteDialect(Dialect):
    def __init__(
            self,
            *,
            immediate: bool = False,
    ) -> None:
        super().__init__()

        self._immediate = immediate

    @property
    def supports_returning(self) -> bool:
        return True

    @property
    def begin_query(self) -> str:
        # A deferred transaction - sqlite's default - takes the write lock only at its first write. If it has read by
        # then, and another connection has written since, that fails on the spot: the busy timeout does not cover a
        # stale snapshot. An immediate one takes the lock up front, waiting its turn for it, so a database with more
        # than one writer wants its read-then-write transactions immediate.
        return 'begin immediate' if self._immediate else 'begin'
