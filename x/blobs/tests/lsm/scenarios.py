"""
A seeded, model-based scenario runner checking LsmDb and LsmReader against a plain dict, for any AsyncBlobStore. Shared
by the core LSM tests and the S3 ones.
"""
import random
import typing as ta

from omcore import dataclasses as dc

from ...asyncs import AsyncBlobStore
from .dbs import LsmDb
from .options import LsmOptions
from .readers import LsmReader


##


SMALL_OPTIONS = LsmOptions(
    memtable_max_bytes=512,
    block_size=64,
    sst_target_size=768,
    l0_compaction_trigger=3,
    prefetch_bytes=128,
)


@dc.dataclass(frozen=True, kw_only=True)
class ScenarioStats:
    ops: int
    flushes: int
    compactions: int
    reopens: int
    crashes: int
    reader_checks: int
    final_manifest_id: int


async def collect(it: ta.AsyncIterator[tuple[bytes, bytes]]) -> list[tuple[bytes, bytes]]:
    return [kv async for kv in it]


def model_scan(model: ta.Mapping[bytes, bytes], start: bytes | None, end: bytes | None) -> list[tuple[bytes, bytes]]:
    return [
        (k, model[k])
        for k in sorted(model)
        if (start is None or k >= start) and (end is None or k < end)
    ]


async def run_model_scenario(
        store: AsyncBlobStore,
        *,
        seed: int,
        ops: int,
        prefix: str = 'db',
        options: LsmOptions = SMALL_OPTIONS,
        num_keys: int = 60,
        max_readers: int = 3,
) -> ScenarioStats:
    rng = random.Random(seed)
    keys = [f'k{i:03d}'.encode() for i in range(num_keys)]

    model: dict[bytes, bytes] = {}  # what the live writer should show
    durable: dict[bytes, bytes] = {}  # what survives a crash: the last flush
    readers: list[tuple[LsmReader, dict[bytes, bytes]]] = []

    flushes = compactions = reopens = crashes = reader_checks = 0

    db = await LsmDb.open(store, prefix, options=options)

    def rand_range() -> tuple[bytes | None, bytes | None]:
        a = rng.choice([None, *keys])
        b = rng.choice([None, *keys])
        if a is not None and b is not None and b < a:
            a, b = b, a
        return a, b

    weights = {
        'put': 40,
        'delete': 12,
        'get': 15,
        'scan': 6,
        'flush': 4,
        'compact': 2,
        'reopen': 2,
        'crash': 1,
        'open_reader': 2,
        'check_reader': 3,
    }
    names = list(weights)
    for _ in range(ops):
        op = rng.choices(names, weights=[weights[n] for n in names])[0]

        if op == 'put':
            k = rng.choice(keys)
            v = rng.randbytes(rng.randint(0, 40))
            await db.put(k, v)
            model[k] = v

        elif op == 'delete':
            k = rng.choice(keys)
            await db.delete(k)
            model.pop(k, None)

        elif op == 'get':
            k = rng.choice(keys)
            assert await db.get(k) == model.get(k), k

        elif op == 'scan':
            a, b = rand_range()
            assert await collect(db.scan(a, b)) == model_scan(model, a, b), (a, b)

        elif op == 'flush':
            await db.flush()
            durable = dict(model)
            flushes += 1

        elif op == 'compact':
            await db.flush()
            durable = dict(model)
            await db.compact()
            compactions += 1

        elif op == 'reopen':
            await db.close()
            durable = dict(model)
            db = await LsmDb.open(store, prefix, options=options)
            reopens += 1

        elif op == 'crash':
            # Abandon the writer without flushing: only the last flush survives.
            model = dict(durable)
            db = await LsmDb.open(store, prefix, options=options)
            crashes += 1

        elif op == 'open_reader':
            if len(readers) >= max_readers:
                readers.pop(0)
            readers.append((await LsmReader.open(store, prefix, options=options), dict(durable)))

        elif op == 'check_reader':
            if readers:
                r, snap = rng.choice(readers)
                a, b = rand_range()
                assert await collect(r.scan(a, b)) == model_scan(snap, a, b), (a, b)
                k = rng.choice(keys)
                assert await r.get(k) == snap.get(k), k
                reader_checks += 1

        else:
            raise RuntimeError(op)

        # Auto-flushes make more durable than the model knows - catch up whenever the memtable has emptied.
        if not db.unflushed_bytes:
            durable = dict(model)

    await db.close()
    db = await LsmDb.open(store, prefix, options=options)
    assert await collect(db.scan()) == model_scan(model, None, None)
    for k in keys:
        assert await db.get(k) == model.get(k)
    final_id = db.manifest_id
    await db.close()

    return ScenarioStats(
        ops=ops,
        flushes=flushes,
        compactions=compactions,
        reopens=reopens,
        crashes=crashes,
        reader_checks=reader_checks,
        final_manifest_id=final_id,
    )
