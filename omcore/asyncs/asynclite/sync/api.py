# @om-lite
from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .cancellation import SyncAsyncliteCancellation
from .events import SyncAsyncliteEvents
from .identities import SyncAsyncliteIdentities
from .locks import SyncAsyncliteLocks
from .queues import SyncAsyncliteQueues
from .semaphores import SyncAsyncliteSemaphores
from .sleeps import SyncAsyncliteSleeps


##


class SyncAsynclite(
    SyncAsyncliteCancellation,
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
