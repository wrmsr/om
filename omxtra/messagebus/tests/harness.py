import contextlib
import typing as ta

from ..bus import Bus
from ..loop import LoopConfig


##


# Long intervals on purpose: in these tests delivery has to come from a wakeup or the initial poll, never the timer.
CONFIG = LoopConfig(poll_interval=60., heartbeat_interval=60., reconnect_backoff=0.)

TIMEOUT = 10.


@contextlib.contextmanager
def running(*buses: Bus) -> ta.Iterator[None]:
    for b in buses:
        b.start()
    try:
        yield
    finally:
        for b in buses:
            b.stop(timeout=TIMEOUT)
