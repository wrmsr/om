# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""A raw rpc peer for wire-level tests: one pure driver running a full rpc pipeline, fed and read as envelopes."""
import typing as ta

from ...io.pipelines.drivers.pure.drivers import PureIoPipelineDriver
from ...io.pipelines.drivers.types import IoPipelineDriverState
from ..codecs import RpcValueEnvelopeCodec
from ..configs import RpcConfig
from ..messages import RpcEnvelope
from ..specs import rpc_build_pipeline_spec


##


class RawRpcPeer:
    def __init__(self, config: RpcConfig = RpcConfig.DEFAULT, **spec_kwargs: ta.Any) -> None:
        super().__init__()

        self.codec = RpcValueEnvelopeCodec()
        self.driver = PureIoPipelineDriver(rpc_build_pipeline_spec(config, **spec_kwargs))
        self.events: ta.List[ta.Any] = []
        self._buf = b''
        self.step()

    @property
    def is_live(self) -> bool:
        return self.driver.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING)

    def step(self) -> None:
        while self.is_live or self.driver.state is IoPipelineDriverState.NEW:
            out = self.driver.next(read=True, raise_on_stall=False)
            if out is None:
                break
            self.events.append(out)

    def frame(self, env: RpcEnvelope) -> bytes:
        data = self.codec.encode(env)
        return len(data).to_bytes(4, 'big') + data

    def send(self, *envs: RpcEnvelope) -> None:
        self.send_bytes(b''.join(self.frame(e) for e in envs))

    def send_bytes(self, data: bytes) -> None:
        self.driver.feed_input(data)
        self.step()

    def cmd(self, *cmds: ta.Any) -> None:
        self.driver.enqueue(*cmds)
        self.step()

    def eof(self) -> None:
        self.driver.feed_eof()
        self.step()

    def advance(self, delay_s: float) -> None:
        self.driver.advance_time(delay_s)
        self.step()

    def recv(self) -> ta.List[ta.Any]:
        """
        Accepts all output across the transport boundary, as a transport with room to spare would, and decodes it.
        Accepting output can complete flushes which release more, so this drains until nothing more comes.
        """

        while self.is_live:
            data = self.driver.drain_output()
            self._buf += data
            self.step()
            if not data:
                break

        out: ta.List[ta.Any] = []
        while len(self._buf) >= 4:
            n = int.from_bytes(self._buf[:4], 'big')
            if len(self._buf) < 4 + n:
                break
            out.append(self.codec.decode(self._buf[4:4 + n]))
            self._buf = self._buf[4 + n:]
        return out

    def take_events(self, *types: type) -> ta.List[ta.Any]:
        """Removes and returns the collected events, or only those of the given types."""

        if not types:
            evs, self.events = self.events, []
            return evs

        evs = [e for e in self.events if isinstance(e, types)]
        self.events = [e for e in self.events if not isinstance(e, types)]
        return evs
