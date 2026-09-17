from .types import WorkerId


##


class BusError(Exception):
    pass


class IdentityLockError(BusError):
    """Another live session already owns this worker identity. Fatal - never retried."""

    def __init__(self, worker_id: WorkerId) -> None:
        super().__init__(worker_id)

        self.worker_id = worker_id


class BusStoppedError(BusError):
    pass
