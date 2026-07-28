# @om-lite
from ...lite.abstract import Abstract
from .events import AsyncliteEvents
from .identities import AsyncliteIdentities
from .locks import AsyncliteLocks
from .promises import AsynclitePromises
from .queues import AsyncliteQueues
from .semaphores import AsyncliteSemaphores
from .sleeps import AsyncliteSleeps


##


class Asynclite(
    AsyncliteEvents,
    AsyncliteIdentities,
    AsyncliteLocks,
    AsynclitePromises,
    AsyncliteQueues,
    AsyncliteSemaphores,
    AsyncliteSleeps,

    Abstract,
):
    pass
