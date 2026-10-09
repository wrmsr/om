import typing as ta

from ..endpoints import EndpointListener
from ..peers import PeerSink


##


class RecordingSink(PeerSink):
    def __init__(self) -> None:
        super().__init__()

        self.events: list[str] = []

    def wake_send(self) -> None:
        self.events.append('send')

    def wake_recv(self) -> None:
        self.events.append('recv')

    def close(self) -> None:
        self.events.append('close')

    def take(self) -> list[str]:
        out, self.events = self.events, []
        return out


class RecordingListener(EndpointListener):
    def __init__(self) -> None:
        super().__init__()

        self.events: list[str] = []

    def on_readable(self) -> None:
        self.events.append('readable')

    def on_writable(self) -> None:
        self.events.append('writable')

    def take(self) -> list[str]:
        out, self.events = self.events, []
        return out


def drain(endpoint: ta.Any, peer: ta.Any) -> list[ta.Any]:
    out = []
    while (m := endpoint.take_output(peer)) is not None:
        out.append(m)
    return out
