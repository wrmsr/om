from omcore.asyncs.asynclite import all as asl


##


class RecordingSleeps(asl.Sleeps):
    """Records each requested delay and returns at once, so backoff is asserted on rather than waited out."""

    def __init__(self) -> None:
        super().__init__()

        self.delays: list[float] = []

    async def sleep(self, delay: float) -> None:
        self.delays.append(delay)
