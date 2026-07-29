"""
Benchmarks the streaming parser across input feeding modes, against the stdlib C and pure-python decoders as baselines.
"""
import json
import json.decoder
import json.scanner
import random
import typing as ta

from ...... import lang
from ...utils import stream_parse_one_value


##


def _make_doc(n: int, *, seed: int = 42) -> ta.Any:
    rnd = random.Random(seed)
    return [
        {
            'id': i,
            'name': f'item-{i}-' + 'x' * rnd.randint(0, 20),
            'value': rnd.random() * 1000,
            'count': rnd.randint(0, 10 ** 6),
            'active': rnd.random() < 0.5,
            'tags': [f'tag{j}' for j in range(rnd.randint(0, 5))],
            'meta': {'a': None, 'b': 'some "quoted" \u00e9scaped\ntext', 'c': [1.5, -2, 3e8]},
        }
        for i in range(n)
    ]


def _py_json_loads(s: str) -> ta.Any:
    # Forces the stdlib pure-python scanner - the fairest 'well-optimized zero-dep python' baseline. These are stdlib
    # internals absent from typeshed.
    d = json.decoder.JSONDecoder()
    d.parse_string = json.decoder.py_scanstring  # type: ignore[attr-defined]
    d.scan_once = json.scanner.py_make_scanner(d)  # type: ignore[attr-defined]
    return d.decode(s)


def _bench(name: str, fn: ta.Callable[[], ta.Any], *, num_runs: int = 5) -> ta.Any:
    best: float | None = None
    v: ta.Any = None
    for _ in range(num_runs):
        with lang.Timer() as tmr:
            v = fn()
        if best is None or tmr.elapsed < best:
            best = tmr.elapsed
    print(f'{name:24} {best * 1_000.:10.1f} ms')  # type: ignore[operator]
    return v


def _main() -> None:
    doc = _make_doc(2_000)
    s = json.dumps(doc)
    print(f'doc: {len(s) / 1024.:.0f} KiB')

    _bench('json.loads (C)', lambda: json.loads(s))
    _bench('json.loads (python)', lambda: _py_json_loads(s))

    for name, fn in [
        ('stream str', lambda: stream_parse_one_value(s)),
        ('stream single chunk', lambda: stream_parse_one_value([s])),
        ('stream 8KiB chunks', lambda: stream_parse_one_value([s[i:i + 8192] for i in range(0, len(s), 8192)])),
        ('stream per-char iter', lambda: stream_parse_one_value(iter(s))),
    ]:
        v = _bench(name, fn)
        if v != doc:
            raise ValueError(name)

    #

    es = '"' + ('a\\"' * 256_000) + '"'
    print(f'\nescaped-quotes doc: {len(es) / 1024.:.0f} KiB')

    for name, fn in [
        ('stream single chunk', lambda: stream_parse_one_value([es])),
        ('stream 8KiB chunks', lambda: stream_parse_one_value([es[i:i + 8192] for i in range(0, len(es), 8192)])),
    ]:
        v = _bench(name, fn, num_runs=3)
        if v != json.loads(es):
            raise ValueError(name)


if __name__ == '__main__':
    _main()
