import select
import socket


##


class Waker:
    """
    A socketpair the loop selects on alongside the db socket, so a send or stop from any thread interrupts a wait
    immediately - on polling backends too. Wakes coalesce: many wakes, one readable byte.
    """

    def __init__(self) -> None:
        super().__init__()

        self._r, self._w = socket.socketpair()
        self._r.setblocking(False)
        self._w.setblocking(False)

    def fileno(self) -> int:
        return self._r.fileno()

    def wake(self) -> None:
        try:
            self._w.send(b'\0')
        except BlockingIOError:
            pass  # buffer full means a wake is already pending

    def drain(self) -> None:
        try:
            while self._r.recv(4096):
                pass
        except BlockingIOError:
            pass

    def wait(self, timeout: float) -> bool:
        """An interruptible sleep. Returns whether it was woken rather than timing out."""

        r, _, _ = select.select([self._r], [], [], timeout)
        if not r:
            return False
        self.drain()
        return True

    def close(self) -> None:
        self._r.close()
        self._w.close()
