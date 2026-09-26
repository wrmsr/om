class LsmError(Exception):
    pass


class LsmCorruptionError(LsmError):
    pass


class LsmFencedError(LsmError):
    """Another writer has taken over this database. This writer's unflushed data is lost, and it must not be reused."""


class LsmBrokenError(LsmError):
    """A manifest commit's outcome could not be determined. The writer must not be reused - reopen instead."""


class LsmSnapshotExpiredError(LsmError):
    """A reader's snapshot referenced an SST which garbage collection has since deleted."""
