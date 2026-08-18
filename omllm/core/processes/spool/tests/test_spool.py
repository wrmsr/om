import asyncio
import os
import tempfile

import pytest

from ...asyncio.notifier import AsyncioSpoolNotifier
from ...asyncio.notifier import ImmediateSpoolNotifier
from ..frames import FRAME_HEADER_SIZE
from ..frames import decode_frames
from ..frames import encode_frame
from ..render import ArrivalMergedRenderer
from ..render import RawRenderer
from ..render import TaggedLinesRenderer
from ..spool import OutputSpool
from ..storage import SpoolStorage


def _mono():
    n = [0]

    def f():
        n[0] += 1_000_000
        return n[0]

    return f


def _spool(*, memory_cap=None, spill_dir=None, spill=True, notifier=None, mono=None):
    st = SpoolStorage(memory_cap=memory_cap, spill_dir=spill_dir if spill else None)
    return OutputSpool(
        st,
        notifier or ImmediateSpoolNotifier(),
        mono_ns=mono or _mono(),
        wall_ns=lambda: 1_700_000_000_000_000_000,
    )


def test_frames_roundtrip():
    f1 = encode_frame(1, b'hello', t_mono_ns=1, t_wall_ns=2, seq=0)
    f2 = encode_frame(2, b'', t_mono_ns=3, t_wall_ns=4, seq=1)
    f3 = encode_frame(1, b'x' * 100, t_mono_ns=5, t_wall_ns=6, seq=2)
    buf = f1 + f2 + f3
    recs, consumed = decode_frames(buf, 1000)
    assert consumed == len(buf)
    assert [(r.fd, r.data, r.seq, r.offset) for r in recs] == [
        (1, b'hello', 0, 1000),
        (2, b'', 1, 1000 + len(f1)),
        (1, b'x' * 100, 2, 1000 + len(f1) + len(f2)),
    ]
    assert recs[0].end == 1000 + len(f1)

    # Trailing partial frame is left unconsumed.
    recs, consumed = decode_frames(buf[:-1], 0)
    assert len(recs) == 2
    assert consumed == len(f1) + len(f2)

    # max_payload returns at least one record.
    recs, consumed = decode_frames(buf, 0, max_payload=1)
    assert len(recs) == 1
    recs, consumed = decode_frames(buf, 0, max_payload=5)
    assert len(recs) == 2  # 5 + 0


def test_spool_basic_reads():
    sp = _spool()
    sp.append(1, b'hello ')
    sp.append(2, b'err\n')
    sp.append(1, b'world\n')

    r = sp.read_available(0)
    assert [x.data for x in r.records] == [b'hello ', b'err\n', b'world\n']
    assert r.start == 0
    assert r.end == r.total == sp.total
    assert not r.more
    assert not r.ended
    assert r.data(1) == b'hello world\n'
    assert r.data(2) == b'err\n'

    r2 = sp.read_available(r.end)
    assert r2.empty
    assert r2.start == r2.end == sp.total

    r3 = sp.read_available(0, max_bytes=7)
    assert [x.data for x in r3.records] == [b'hello ', b'err\n']
    assert r3.more
    r4 = sp.read_available(r3.end)
    assert [x.data for x in r4.records] == [b'world\n']

    sp.mark_ended()
    assert sp.read_available(0).ended


def test_spool_memory_cap_drops_without_spill():
    sp = _spool(memory_cap=100, spill=False)
    frames = []
    for i in range(10):
        frames.append(sp.append(1, bytes([65 + i]) * 30))
    st = sp.storage
    assert st.total == 10 * (FRAME_HEADER_SIZE + 30)
    assert st.spilled_end == 0
    assert st.mem_start > 0

    r = sp.read_available(0)
    assert r.dropped_before == st.mem_start
    assert r.start == st.mem_start
    assert len(r.records) == 1  # cap 100 holds only one 62-byte frame
    assert r.records[0].data == b'J' * 30
    assert r.end == st.total


def test_spool_memory_cap_spills():
    with tempfile.TemporaryDirectory() as td:
        sp = _spool(memory_cap=200, spill_dir=td)
        for i in range(20):
            sp.append(1 + (i % 2), bytes([65 + i]) * 50)
        st = sp.storage
        assert st.spill_path is not None
        assert os.path.exists(st.spill_path)
        assert st.spilled_end == st.mem_start > 0
        assert st.spilled_end + 200 >= st.total - 200

        # Full read from 0 crosses from file to memory transparently.
        r = sp.read_available(0)
        assert r.dropped_before == 0
        assert [x.data[0:1] for x in r.records] == [bytes([65 + i]) for i in range(20)]
        assert r.end == st.total

        # Bounded reads with cursors walk the whole stream.
        cur = 0
        seen: list = []
        while True:
            r = sp.read_available(cur, max_bytes=120)
            if not r.records:
                break
            seen.extend(x.data[0:1] for x in r.records)
            cur = r.end
        assert seen == [bytes([65 + i]) for i in range(20)]

        # Frame larger than the read chunk is fetched whole.
        sp.append(1, b'Z' * (300 * 1024))
        r = sp.read_available(cur)
        assert len(r.records) == 1
        assert len(r.records[0].data) == 300 * 1024

        path = st.spill_path
        sp.close()
        assert not os.path.exists(path)

        sp2 = _spool(memory_cap=10, spill_dir=td)
        sp2.append(1, b'abc')
        sp2.append(1, b'def')
        p2 = sp2.storage.spill_path
        sp2.close(keep_spill=True)
        assert os.path.exists(p2)
        os.unlink(p2)


@pytest.mark.asyncs('asyncio')
async def test_spool_wait_and_subscribe():
    notifier = AsyncioSpoolNotifier()
    sp = _spool(notifier=notifier)

    async def producer():
        for i in range(3):
            await asyncio.sleep(0.01)
            sp.append(1, f'line {i}\n'.encode())
        await asyncio.sleep(0.01)
        sp.mark_ended()

    t = asyncio.create_task(producer())

    # wait: collects for the window (or until ended).
    r = await sp.read(0, wait=5.)
    assert r.ended
    assert r.data() == b'line 0\nline 1\nline 2\n'
    await t

    # subscribe replays from cursor 0 then ends.
    got: list = []
    async for rr in sp.subscribe(0):
        got.extend(x.data for x in rr.records)
    assert b''.join(got) == b'line 0\nline 1\nline 2\n'

    # wait on an ended empty tail returns immediately.
    r = await sp.read(r.end, wait=5.)
    assert r.empty and r.ended

    # max_bytes bounds a waiting read.
    sp2 = _spool(notifier=AsyncioSpoolNotifier())

    async def producer2():
        for _i in range(5):
            await asyncio.sleep(0.005)
            sp2.append(1, b'x' * 10)

    t2 = asyncio.create_task(producer2())
    r = await sp2.read(0, wait=5., max_bytes=25)
    assert len(r.data()) >= 25
    assert r.more or len(r.records) == 3
    await t2

    # timeout returns what is there.
    r = await sp2.read(sp2.total, wait=0.02)
    assert r.empty and not r.ended


def test_renderers():
    mono = _mono()
    sp = _spool(mono=mono)
    sp.append(1, 'héllo '.encode()[:2])  # split a multibyte char across chunks
    sp.append(1, 'héllo '.encode()[2:])
    sp.append(2, b'oops\n')
    sp.append(1, b'world\n')
    sp.append(1, b'unterminated')
    recs = sp.read_available(0).records

    assert RawRenderer({1}).render(recs) == 'héllo world\nunterminated'
    assert RawRenderer({2}).render(recs) == 'oops\n'
    assert ArrivalMergedRenderer().render(recs) == 'héllo oops\nworld\nunterminated'

    t = TaggedLinesRenderer(timestamps=False)
    out = t.render(recs)
    assert out == 'fd=1| héllo \nfd=2| oops\nfd=1| world\nfd=1| unterminated'

    t = TaggedLinesRenderer(fd_tags=False)
    out = t.render(recs)
    lines = out.split('\n')
    assert all(len(l.split('| ')[0]) == 12 for l in lines)  # HH:MM:SS.mmm

    # Renderer is stateful across successive reads.
    t = TaggedLinesRenderer(timestamps=False)
    assert t.render(recs[:1]) == 'fd=1| h'
    assert t.render(recs[1:2]) == 'éllo '
    assert t.render(recs[2:]) == '\nfd=2| oops\nfd=1| world\nfd=1| unterminated'


def test_tagged_resume_gap():
    n = [0]

    def mono():
        return n[0]

    sp = _spool(mono=mono)
    n[0] = 0
    sp.append(1, b'progress: 10%')
    n[0] = 5_000_000_000
    sp.append(1, b' 20%')
    n[0] = 5_100_000_000
    sp.append(1, b' 30%\n')
    recs = sp.read_available(0).records

    t = TaggedLinesRenderer(timestamps=False, resume_gap_s=2., break_marker=' ...')
    assert t.render(recs) == 'fd=1| progress: 10% ...\nfd=1 +|  20% 30%\n'
