import threading

from omcore import check

from .errors import BusStoppedError
from .handlers import MessageHandler
from .loop import BusLoop
from .loop import LoopConfig
from .outbox import Outbox
from .sessions import BusSessionFactory
from .types import OutgoingMessage
from .types import Payload
from .types import WorkerId
from .waker import Waker


##


class Bus:
    """
    The public face: one worker identity, one background thread, `send` from anywhere. The rpc layer sits on `send` and
    `MessageHandler` and never sees a connection.
    """

    def __init__(
            self,
            *,
            worker_id: WorkerId,
            session_factory: BusSessionFactory,
            handler: MessageHandler,
            name: str = '',
            config: LoopConfig | None = None,
    ) -> None:
        super().__init__()

        self._worker_id = worker_id

        self._outbox = Outbox(worker_id)
        self._waker = Waker()
        self._loop = BusLoop(
            worker_id=worker_id,
            name=name,
            session_factory=session_factory,
            handler=handler,
            outbox=self._outbox,
            waker=self._waker,
            config=config,
        )

        self._thread: threading.Thread | None = None
        self._stopped = False

    @property
    def worker_id(self) -> WorkerId:
        return self._worker_id

    def start(self) -> None:
        check.none(self._thread)

        self._thread = threading.Thread(target=self._loop.run, name=f'bus-{self._worker_id}', daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 30.) -> None:
        self._stopped = True
        self._loop.stop()
        if (t := self._thread) is not None:
            t.join(timeout)
        self._waker.close()

    def send(self, dst_id: WorkerId, payload: Payload) -> None:
        # Safe from any thread: one atomic deque append, then a poke at the loop.
        if self._stopped:
            raise BusStoppedError
        self._outbox.enqueue(OutgoingMessage(dst_id, payload))
        self._waker.wake()
