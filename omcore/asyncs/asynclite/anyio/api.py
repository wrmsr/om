from ..api import Asynclite
from ..eventpromises import EventAsynclitePromises
from .cancellation import AnyioAsyncliteCancellation
from .events import AnyioAsyncliteEvents
from .identities import AnyioAsyncliteIdentities
from .locks import AnyioAsyncliteLocks
from .queues import AnyioAsyncliteQueues
from .semaphores import AnyioAsyncliteSemaphores
from .sleeps import AnyioAsyncliteSleeps


##


class AnyioAsynclite(
    AnyioAsyncliteCancellation,
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
