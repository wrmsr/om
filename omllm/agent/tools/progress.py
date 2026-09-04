from ..types.progress import ToolProgressSink
from ..types.progress import ToolProgressUpdate


##


class NopToolProgressSink(ToolProgressSink):
    async def report(self, update: ToolProgressUpdate) -> None:
        pass
