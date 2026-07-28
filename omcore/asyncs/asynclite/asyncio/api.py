# @om-lite
from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .events import AsyncioAsyncliteEvents
from .identities import AsyncioAsyncliteIdentities
from .locks import AsyncioAsyncliteLocks
from .queues import AsyncioAsyncliteQueues
from .semaphores import AsyncioAsyncliteSemaphores
from .sleeps import AsyncioAsyncliteSleeps


##


class AsyncioAsynclite(
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
