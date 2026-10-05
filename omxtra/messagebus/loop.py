import logging
import time

from omcore import dataclasses as dc

from .errors import IdentityLockError
from .handlers import MessageHandler
from .outbox import Outbox
from .sessions import BusSession
from .sessions import BusSessionFactory
from .types import WorkerId
from .waker import Waker


##


log = logging.getLogger(__name__)


@dc.dataclass(frozen=True)
class LoopConfig:
    poll_interval: float = 5.
    heartbeat_interval: float = 15.
    poll_limit: int = 100
    flush_batch_size: int = 100
    connect_timeout: float = 30.
    reconnect_backoff: float = 2.


class BusLoop:
    """
    The single thread that owns the session. Sends from other threads arrive through the outbox and the waker; nothing
    else ever touches the connection.
    """

    def __init__(
            self,
            *,
            worker_id: WorkerId,
            name: str,
            session_factory: BusSessionFactory,
            handler: MessageHandler,
            outbox: Outbox,
            waker: Waker,
            config: LoopConfig | None = None,
    ) -> None:
        super().__init__()

        self._worker_id = worker_id
        self._name = name
        self._session_factory = session_factory
        self._handler = handler
        self._outbox = outbox
        self._waker = waker
        self._config = config if config is not None else LoopConfig()

        self._stopped = False

    def stop(self) -> None:
        self._stopped = True
        self._waker.wake()

    def _flush(self, sess: BusSession) -> None:
        batch = self._outbox.take_batch(self._config.flush_batch_size)
        with sess.transaction():
            for msg in batch.messages:
                sess.store.insert_message(msg)
            sess.store.update_seqs(self._worker_id, batch.seqs_after)
            sess.signaling.notify(batch.dst_ids)
        self._outbox.commit(batch)

    def _poll_and_dispatch(self, sess: BusSession) -> int:
        msgs = sess.store.select_messages(self._worker_id, limit=self._config.poll_limit)
        for msg in msgs:
            self._handler.handle(msg)
            sess.store.delete_message(msg)  # at-least-once: dying between these two lines redelivers on restart
        return len(msgs)

    def _run_session(self, sess: BusSession) -> None:
        if not sess.lock.try_acquire():
            raise IdentityLockError(self._worker_id)

        sess.store.register_worker(self._worker_id, self._name)
        self._outbox.reconcile(sess.store.load_seqs(self._worker_id))
        sess.signaling.listen(self._waker)

        cfg = self._config
        next_heartbeat = time.monotonic() + cfg.heartbeat_interval

        while not self._stopped:
            if self._outbox.has_pending():
                self._flush(sess)
                next_heartbeat = time.monotonic() + cfg.heartbeat_interval  # a flush bumps heartbeat_at too

            n = self._poll_and_dispatch(sess)

            now = time.monotonic()
            if now >= next_heartbeat:
                sess.store.heartbeat(self._worker_id)
                next_heartbeat = now + cfg.heartbeat_interval

            if n >= cfg.poll_limit or self._outbox.has_pending():
                continue

            sess.signaling.wait(min(cfg.poll_interval, max(0., next_heartbeat - now)))

    def run(self) -> None:
        cfg = self._config

        while not self._stopped:
            try:
                sess = self._session_factory.open(self._worker_id, timeout=cfg.connect_timeout)
            except Exception:  # noqa  FIXME: narrow to the sql layer's connection errors
                log.exception('Bus connect failed: %s', self._worker_id)
                self._waker.wait(cfg.reconnect_backoff)
                continue

            try:
                self._run_session(sess)

            except IdentityLockError:
                raise

            except Exception:  # noqa  FIXME: same
                log.exception('Bus session failed: %s', self._worker_id)
                self._waker.wait(cfg.reconnect_backoff)

            finally:
                try:
                    sess.close()
                except Exception:  # noqa
                    log.exception('Bus session close failed: %s', self._worker_id)
