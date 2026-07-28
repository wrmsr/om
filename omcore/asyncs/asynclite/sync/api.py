# @om-lite
from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .events import SyncAsyncliteEvents
from .identities import SyncAsyncliteIdentities
from .locks import SyncAsyncliteLocks
from .queues import SyncAsyncliteQueues
from .semaphores import SyncAsyncliteSemaphores
from .sleeps import SyncAsyncliteSleeps


##


class SyncAsynclite(
    SyncAsyncliteEvents,
    SyncAsyncliteIdentities,
    SyncAsyncliteLocks,
    EventAsynclitePromises,
    SyncAsyncliteQueues,
    SyncAsyncliteSemaphores,
    SyncAsyncliteSleeps,

    Asynclite,
):
    pass
