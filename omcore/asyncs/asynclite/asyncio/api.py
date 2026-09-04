# @om-lite
from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .cancellation import AsyncioAsyncliteCancellation
from .events import AsyncioAsyncliteEvents
from .identities import AsyncioAsyncliteIdentities
from .locks import AsyncioAsyncliteLocks
from .queues import AsyncioAsyncliteQueues
from .semaphores import AsyncioAsyncliteSemaphores
from .sleeps import AsyncioAsyncliteSleeps


##


class AsyncioAsynclite(
    AsyncioAsyncliteCancellation,
    AsyncioAsyncliteEvents,
    AsyncioAsyncliteIdentities,
    AsyncioAsyncliteLocks,
    EventAsynclitePromises,
    AsyncioAsyncliteQueues,
    AsyncioAsyncliteSemaphores,
    AsyncioAsyncliteSleeps,

    Asynclite,
):
    pass
