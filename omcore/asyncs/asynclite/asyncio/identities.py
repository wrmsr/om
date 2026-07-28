# @om-lite
import asyncio
import typing as ta

from ..identities import AsyncliteIdentities


##


class AsyncioAsyncliteIdentities(AsyncliteIdentities):
    def current_identity(self) -> ta.Any:
        try:
            return asyncio.current_task()
        except RuntimeError:  # no running event loop
            return None
