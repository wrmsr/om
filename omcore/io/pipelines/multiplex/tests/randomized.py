# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""Reproducible end-to-end sessions with varied framing, windows, batching, and transport fragmentation."""
import dataclasses as dc
import random
import typing as ta

from ...drivers.pure import PureIoPipelineDriver
from ...drivers.types import IoPipelineDriverState
from ...ssl.tests.test_halfclose import _ssl_handlers
from ...yielding import CountingIoPipelineYieldPolicy
from ..children import MultiplexChildConfig
from ..handlers import MultiplexConfig
from ..types import MultiplexMessages
from .apps import AppFactory
from .apps import StreamApp
from .apps import app_spec
from .apps import payload
from .h2like import H2LikeAdapter
from .h2like import Headers
from .h2like import h2_like_spec
from .links import PureLink
from .loopback import Outcome
from .sshlike import ChannelExtData
from .sshlike import ChannelRequest
from .sshlike import SshLikeAdapter
from .sshlike import SshOpenInfo
from .sshlike import ssh_like_spec


##


class _ShuffledLink(PureLink):
    def __init__(self, *args, seed, **kwargs):
        super().__init__(*args, **kwargs)

        self._rng = random.Random(seed)

    def pump(self, max_rounds=100_000, *, until=None):
        for _ in range(max_rounds):
            if until is not None and until():
                return
            drivers = [self.a, self.b]
            self._rng.shuffle(drivers)
            progressed = False
            for driver in drivers:
                progressed |= self._step(driver)
            directions = [(self.a, self.b), (self.b, self.a)]
            self._rng.shuffle(directions)
            for source, destination in directions:
                progressed |= self._move(source, destination)
            if not progressed:
                if until is not None and not until():
                    raise RuntimeError('link quiesced before condition')
                return
        raise RuntimeError('link did not quiesce')


def run_session(tc, seed, *, protocol, tls=False):
    rng = random.Random(seed)
    count = rng.randint(1, 8)
    windows = [rng.randint(64, 8192) for _ in range(2)]
    units = [rng.randint(16, 2048) for _ in range(2)]
    requests = [payload((seed, 'request', i), rng.randint(0, 16384)) for i in range(count)]
    responses = [payload((seed, 'response', i), rng.randint(0, 16384)) for i in range(count)]
    extended = [payload((seed, 'extended', i), rng.randint(0, 2048)) for i in range(count)]
    configs = [MultiplexConfig(
        child=MultiplexChildConfig(
            read_batch_max_bytes=rng.randint(1, 8192),
            write_high_watermark=256,
            write_low_watermark=64,
        ),
        turn_output_budget=rng.randint(1, 4096),
        yield_policy=CountingIoPipelineYieldPolicy(rng.randint(1, 8)),
    ) for _ in range(2)]

    def index(opening):
        return int(opening.info if protocol == 'h2' else opening.info.info.decode())

    factory = AppFactory(
        lambda o: StreamApp(
            respond=responses[index(o)],
            respond_messages=[Headers('done')] if protocol == 'h2' else [ChannelRequest('done')],
            manual_read=bool(index(o) % 2),
            chunk_size=units[1],
        ),
        auto_read=lambda o: not bool(index(o) % 2),
    )
    unused_factory = AppFactory(lambda o: StreamApp())
    specs = []
    muxes = []
    connection_window = rng.randint(64, 16384)
    replenish_on: ta.Literal['receive', 'consume'] = rng.choice(['receive', 'consume'])
    roles: ta.Sequence[ta.Literal['client', 'server']] = ('client', 'server')
    for side, role in enumerate(roles):
        if protocol == 'h2':
            spec, mux = h2_like_spec(
                role,
                unused_factory if side == 0 else factory,
                adapter=H2LikeAdapter(
                    role,
                    initial_window=windows[side],
                    peer_initial_window=windows[1 - side],
                    max_frame=units[side],
                    pad=rng.randint(0, 7),
                ),
                config=configs[side],
                connection_send_window=connection_window,
                connection_recv_window=connection_window,
                connection_replenish_on=replenish_on,
                auto_read=bool(seed % 2),
            )
        else:
            spec, mux = ssh_like_spec(
                unused_factory if side == 0 else factory,
                adapter=SshLikeAdapter(window=windows[side], max_packet=units[side]),
                config=configs[side],
                auto_read=bool(seed % 2),
            )
        specs.append(spec)
        muxes.append(mux)

    if tls:
        for side, ssl_handler in enumerate(_ssl_handlers()):
            specs[side] = dc.replace(specs[side], handlers=[ssl_handler, *specs[side].handlers])

    drivers = [PureIoPipelineDriver(spec, PureIoPipelineDriver.Config(
        read_chunk_size=rng.randint(1, 4096),
        read_batch_max_bytes=rng.randint(1, 16384),
        read_batch_max_reads=rng.randint(1, 8),
        write_high_watermark=512,
        write_low_watermark=128,
    )) for spec in specs]
    link = _ShuffledLink(*drivers, capacity=rng.choice([31, 127, 509, 4096, 65536]), seed=seed)
    apps = []
    outcomes = []
    try:
        for i in range(count):
            app = StreamApp(
                prelude=[Headers(str(i))] if protocol == 'h2' else [ChannelRequest('start')],
                send=requests[i],
                send_messages=[] if protocol == 'h2' else [ChannelExtData(1, extended[i])],
                shutdown_after_send=True,
                manual_read=bool(i % 2),
                chunk_size=rng.randint(1, 4096),
            )
            apps.append(app)
            msg = MultiplexMessages.OpenStream(
                app_spec(app, auto_read=not bool(i % 2)),
                None if protocol == 'h2' else SshOpenInfo('session', str(i).encode()),
            )
            outcomes.append(Outcome(msg))
            drivers[0].enqueue(msg)

        link.pump(max_rounds=200_000)
        tc.assertEqual([o.exc for o in outcomes], [None] * count)
        tc.assertEqual(len(factory.apps), count)
        for i, app in enumerate(apps):
            tc.assertTrue(app.final_output.is_succeeded(), (seed, protocol, tls, i, 'unfinished'))
            tc.assertEqual(bytes(app.received), responses[i])
            tc.assertEqual(app.errors, [])
            # A crossing SSH CLOSE is allowed to fail a pending shutdown fence; all accepted data must still have
            # reached the peer, and the application's final fence must complete.
            tc.assertTrue(app.shutdown_output.is_done())
            tc.assertEqual(app.messages, [Headers('done')] if protocol == 'h2' else [ChannelRequest('done')])
        for opening in factory.openings:
            i = index(opening)
            app = factory.apps[opening.key]
            tc.assertEqual(bytes(app.received), requests[i])
            tc.assertEqual(app.errors, [])
            tc.assertTrue(app.final_output.is_succeeded())
            if protocol == 'ssh':
                tc.assertEqual(b''.join(m.data for m in app.messages if isinstance(m, ChannelExtData)), extended[i])
        for mux in muxes:
            tc.assertEqual(len(mux.streams), 0)
        for driver in drivers:
            tc.assertEqual(link.unhandled_of(driver), [])
    finally:
        link.close()


def run_churn(tc, seed, *, waves=8, tls=False):
    rng = random.Random(seed)
    factory = AppFactory(lambda o: StreamApp(respond=payload((seed, 'response', o.key), 4096)))
    config = MultiplexConfig(turn_output_budget=128, yield_policy=CountingIoPipelineYieldPolicy(2))
    specs = []
    muxes = []
    roles: ta.Sequence[ta.Literal['client', 'server']] = ('client', 'server')
    for side, role in enumerate(roles):
        spec, mux = h2_like_spec(
            role,
            factory if side else AppFactory(lambda o: StreamApp()),
            adapter=H2LikeAdapter(role, initial_window=256, peer_initial_window=256, max_frame=64, pad=3),
            config=config,
            connection_send_window=2048,
            connection_recv_window=2048,
            connection_replenish_on='consume',
        )
        specs.append(spec)
        muxes.append(mux)
    if tls:
        for side, handler in enumerate(_ssl_handlers()):
            specs[side] = dc.replace(specs[side], handlers=[handler, *specs[side].handlers])
    drivers = [PureIoPipelineDriver(spec) for spec in specs]
    link = _ShuffledLink(*drivers, capacity=rng.choice([127, 509, 4096]), seed=seed)
    try:
        for wave in range(waves):
            count = rng.randint(2, 8)
            apps = []
            outcomes = []
            bodies = []
            for index in range(count):
                body = payload((seed, wave, index), 4096)
                app = StreamApp(prelude=[Headers(str(index))], send=body, shutdown_after_send=True)
                msg = MultiplexMessages.OpenStream(app_spec(app))
                outcomes.append(Outcome(msg))
                bodies.append(body)
                apps.append(app)
                drivers[0].enqueue(msg)
            link.pump(until=lambda: len(factory.apps) == count)
            cancelled = set(rng.sample(range(count), rng.randint(1, count - 1)))
            for index in cancelled:
                opened = outcomes[index].result
                tc.assertIsNotNone(opened)
                tc.assertTrue(opened.pipeline.is_ready)
                opened.pipeline.destroy()
            link.pump()
            for index, (app, outcome) in enumerate(zip(apps, outcomes)):
                key = outcome.result.key
                if index in cancelled:
                    tc.assertTrue(app.shutdown_output.is_failed())
                    tc.assertTrue(factory.apps[key].errors)
                else:
                    tc.assertTrue(app.final_output.is_succeeded())
                    tc.assertEqual(app.errors, [])
                    tc.assertEqual(bytes(app.received), payload((seed, 'response', key), 4096))
                    tc.assertEqual(bytes(factory.apps[key].received), bodies[index])
                    tc.assertEqual(factory.apps[key].errors, [])
            for side, mux in enumerate(muxes):
                tc.assertEqual(len(mux.streams), 0)
                totals = mux.credit.totals()
                tc.assertEqual(totals.send_consumed, muxes[1 - side].credit.totals().recv_received)
                tc.assertEqual(link.unhandled_of(drivers[side]), [])
                tc.assertTrue(drivers[side].is_running)
            factory.apps.clear()
            factory.openings.clear()
        drivers[0].enqueue(MultiplexMessages.Shutdown())
        link.pump()
        for driver in drivers:
            tc.assertIs(driver.state, IoPipelineDriverState.CLOSED)
    finally:
        link.close()
