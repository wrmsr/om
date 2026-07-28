from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .events import AnyioAsyncliteEvents
from .identities import AnyioAsyncliteIdentities
from .locks import AnyioAsyncliteLocks
from .queues import AnyioAsyncliteQueues
from .semaphores import AnyioAsyncliteSemaphores
from .sleeps import AnyioAsyncliteSleeps


##


class AnyioAsynclite(
    AnyioAsyncliteEvents,
    AnyioAsyncliteIdentities,
    AnyioAsyncliteLocks,
    EventAsynclitePromises,
    AnyioAsyncliteQueues,
    AnyioAsyncliteSemaphores,
    AnyioAsyncliteSleeps,

    Asynclite,
):
    pass
