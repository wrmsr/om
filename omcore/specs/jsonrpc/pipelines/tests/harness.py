"""A deterministic test harness driving a JSON-RPC pipeline with the pure driver: no sockets, no sleeps."""
import typing as ta

from ..... import check
from .....formats.json import all as json
from .....io.pipelines import all as ipl
from ...parsing import dumps_payload
from ...types import Payload
from ..configs import JsonrpcPipelineConfig
from ..messages import JsonrpcPipelineMessages as Jpm
from ..sessions import JsonrpcSessionHandler
from ..specs import build_jsonrpc_pipeline_spec


class Harness:
    def __init__(
            self,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            driver_config: ipl.PureDriver.Config | None = None,
            **spec_kwargs: ta.Any,
    ) -> None:
        self.config = config
        self.spec = build_jsonrpc_pipeline_spec(config, **spec_kwargs)
        self.drv = ipl.PureDriver(self.spec, driver_config)
        self.all_events: list = []
        self.sent: list = []
        self.raised: list = []
        self._out_buf = bytearray()

    @property
    def session(self) -> JsonrpcSessionHandler:
        return check.not_none(self.drv.pipeline.find_single_handler_of_type(JsonrpcSessionHandler)).handler

    def events(self, *, read: bool = True) -> list:
        """
        Step the driver until it settles, collecting events. Output is drained as it appears (the pure driver will
        not read transport input while output is queued) and accumulated for `out()`.
        """

        out: list = []
        while True:
            if not self.drv.is_running and self.drv.state is not ipl.DriverState.NEW:
                break
            if (ev := self.drv.next(read=read, raise_on_stall=False)) is not None:
                # Sent events and raw exception outputs are bookkept separately so tests can focus on the rest.
                if isinstance(ev, Jpm.Sent):
                    self.sent.append(ev.command)
                elif isinstance(ev, BaseException):
                    self.raised.append(ev)
                else:
                    out.append(ev)
                continue
            if self.drv.has_pending_output:
                self._out_buf += self.drv.drain_output()
                continue
            break
        self.all_events.extend(out)
        return out

    def send(self, *cmds: Jpm.Command) -> list:
        self.drv.enqueue(*cmds)
        return self.events()

    def recv_bytes(self, data: bytes) -> list:
        self.drv.feed_input(data)
        return self.events()

    def recv(self, *objs: ta.Any) -> list:
        """Feed JSON values as newline-delimited frames."""

        return self.recv_bytes(b''.join(json.dumps_compact(o).encode('utf-8') + b'\n' for o in objs))

    def eof(self) -> list:
        self.drv.feed_eof()
        return self.events()

    def tick(self, delay_s: float) -> list:
        self.drv.advance_time(delay_s)
        return self.events()

    def out_bytes(self) -> bytes:
        """Take all output accumulated since the last call."""

        self.events()
        data = bytes(self._out_buf)
        self._out_buf.clear()
        return data

    def out(self) -> list:
        """Take accumulated output and parse it as newline-delimited JSON values."""

        data = self.out_bytes()
        return [json.loads(line) for line in data.split(b'\n') if line.strip()]

    @property
    def closed(self) -> bool:
        return self.drv.state in (ipl.DriverState.CLOSED, ipl.DriverState.FAILED)


def only(evs: list, ty: type) -> list:
    return [e for e in evs if isinstance(e, ty)]


def one(evs: list, ty: type):
    lst = only(evs, ty)
    assert len(lst) == 1, (ty, evs)
    return lst[0]


def encode_payload(p: Payload) -> bytes:
    return dumps_payload(p).encode('utf-8') + b'\n'
