"""
Two sources of one model, compared -- a GGUF against the checkpoint it was converted from, say: their configs, every
parameter the model takes (a tensor both hold packed by its bytes, the rest as float32), the tokenizers' ids over
text, and with --logits a forward of each on the CPU over the text's first tokens.

    python -m omllm.local.qwen.load.tests.comparesources --model M.gguf --against CHECKPOINT --text FILE... --logits 8

The exit status says whether they are the same model: the parameters and the token ids equal, the configs equal but
for floats one source keeps as float32, the logits within --logits-tolerance. Needs the real files, and for the
logits memory for a float32 model at a time.

A file that stores some tensors with loss is not the same model, and the report then says how far each kind of
parameter is from the checkpoint's: its relative RMS error, which should be what its storage type costs (half a
percent for Q8_0, three and a half for Q5_K) and nothing like it where a type is decoded wrongly.
"""
import argparse
import collections
import math
import re
import sys
import time
import typing as ta

import numpy as np

from omcore import dataclasses as dc

from ...arch.loading import load_qwen35
from ...arch.registry import architecture_for
from ...tokenizer import Tokenizer
from ..weights import TensorSource
from ..weights import open_source


##


@dc.dataclass(frozen=True)
class TensorComparison:
    name: str
    how: str  # 'packed nvfp4', 'float32', ...
    equal: bool
    max_abs: float  # the largest difference of two float32 readings; nan for packed bytes that differ
    rel_rms: float = 0.  # |a - b| over |b| for two float32 readings that differ: what a lossy storage type cost


def compare_configs(a: ta.Any, b: ta.Any) -> list[str]:
    """
    The fields that differ, each as a line; one that differs only as a float does from its float32 is marked so. A
    source's own notes (`extra`) and the draft model it may describe (`draft`) are not the model's.
    """

    out = []
    for f in dc.fields(a):
        if f.name in ('extra', 'draft'):
            continue

        x, y = getattr(a, f.name), getattr(b, f.name)
        if x == y:
            continue

        rounded = isinstance(x, float) and isinstance(y, float) and np.float32(x) == np.float32(y)
        out.append(f'{f.name}: {x!r} / {y!r}{" (the same float32)" if rounded else " DIFFERENT"}')

    return out


def compare_tensor(a: TensorSource, b: TensorSource, name: str) -> TensorComparison:
    pa, pb = a.get_microscaled(name), b.get_microscaled(name)

    if pa is not None and pb is not None:
        equal = (
            (pa.fmt, pa.shape) == (pb.fmt, pb.shape) and
            np.array_equal(pa.codes, pb.codes) and
            np.array_equal(pa.scales, pb.scales) and
            (pa.outer is None or pb.outer is None or np.array_equal(pa.outer, pb.outer))  # (both, by the format)
        )
        return TensorComparison(name, f'packed {pa.fmt}', equal, 0. if equal else math.nan)

    how = 'float32'
    if pa is not None or pb is not None:
        how += f' ({pa.fmt if pa is not None else "dense"} / {pb.fmt if pb is not None else "dense"})'

    x = pa.dequantize() if pa is not None else a.get(name)
    y = pb.dequantize() if pb is not None else b.get(name)
    if x.shape != y.shape:
        return TensorComparison(name, how, False, math.inf, math.inf)

    if np.array_equal(x, y):
        return TensorComparison(name, how, True, 0.)

    return TensorComparison(name, how, False, float(np.abs(x - y).max()), relative_rms(x, y))


def relative_rms(x: np.ndarray, y: np.ndarray) -> float:
    """|x - y| / |y| over all their elements, summed in float64 a slice of the first axis at a time."""

    x, y = np.atleast_1d(x), np.atleast_1d(y)
    step = max(1, len(x) // 16)
    d = n = 0.
    for i in range(0, len(x), step):
        xs, ys = x[i:i + step].astype(np.float64), y[i:i + step].astype(np.float64)
        d += float(((xs - ys) ** 2).sum())
        n += float((ys ** 2).sum())
    return math.sqrt(d / n) if n else math.inf


def compare_tokenizers(a: Tokenizer, b: Tokenizer, texts: ta.Sequence[str]) -> tuple[bool, int]:
    """Whether the two are the same vocabulary and give the same ids over `texts`, and how many ids that was."""

    def settings(t: Tokenizer) -> tuple:
        return (t.pre, t.ignore_merges, t.eos_id, t.bos_id, t.add_bos)

    same = a.tokens == b.tokens and a.special == b.special and settings(a) == settings(b)

    n = 0
    for text in texts:
        ids = a.encode(text)
        same = same and ids == b.encode(text)
        n += len(ids)

    return same, n


def cpu_logits(src: TensorSource, ids: np.ndarray, *, threads: int) -> np.ndarray:
    """float32 logits [T, vocab] of a float32 model on the CPU, loaded for this and dropped."""

    import torch

    from ...backends.torch import TorchOps

    torch.set_num_threads(threads)
    ops = TorchOps('cpu')
    model = load_qwen35(src, ops, dtype='f32', verbose=False)
    with torch.no_grad():
        return np.asarray(ops.numpy(model.forward(ids[None])))[0].astype(np.float32)


def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--against', required=True)
    ap.add_argument('--text', nargs='*', default=[], help='files whose text both tokenizers encode')
    ap.add_argument('--logits', type=int, default=0, help='compare logits over this many of the text\'s first tokens')
    ap.add_argument('--logits-tolerance', type=float, default=1e-3)
    ap.add_argument('--threads', type=int, default=2)
    args = ap.parse_args()

    a, b = open_source(args.model), open_source(args.against)
    print(f'{type(a).__name__} {args.model}\n{type(b).__name__} {args.against}')
    ok = True

    lines = compare_configs(a.config, b.config)
    ok = ok and not any(line.endswith('DIFFERENT') for line in lines)
    print(f'config: {len(lines)} fields differ' + ''.join(f'\n  {line}' for line in lines))

    names = architecture_for(a.config).param_names(a.config)  # type: ignore[attr-defined]
    missing = [n for n in names if not (a.has(n) and b.has(n))]
    ok = ok and not missing
    print(f'parameters: {len(names)}, {len(missing)} not in both{f": {missing[:5]}" if missing else ""}')

    t0 = time.time()
    kinds: dict[tuple[str, str], list[TensorComparison]] = collections.defaultdict(list)
    for name in names:
        if name in missing:
            continue
        c = compare_tensor(a, b, name)
        kinds[(re.sub(r'\.\d+\.', '.*.', name), c.how)].append(c)
        if not c.equal:
            print(f'  {name}: {c.how}, max |difference| {c.max_abs:.3g}, relative RMS error {c.rel_rms:.3g}')
    for (kind, how), cs in kinds.items():
        ok = ok and all(c.equal for c in cs)
        worst = max(c.max_abs for c in cs)
        far = max(c.rel_rms for c in cs)
        print(
            f'  {kind:44s} {len(cs):3d}  {how:28s} {sum(c.equal for c in cs):3d} equal, '
            f'max |difference| {worst:.3g}' + (f', relative RMS error up to {far:.3g}' if far else ''),
        )
    print(f'  ({time.time() - t0:.0f} s)')

    texts = []
    for fn in args.text:
        with open(fn) as f:
            texts.append(f.read())
    tokenizer = Tokenizer.from_spec(a.tokenizer_spec)
    same, n = compare_tokenizers(tokenizer, Tokenizer.from_spec(b.tokenizer_spec), texts)
    ok = ok and same
    print(f'tokenizer: {"the same" if same else "DIFFERENT"} over {n} tokens of {len(texts)} texts')

    if args.logits:
        ids = np.asarray([i for text in texts for i in tokenizer.encode(text)][:args.logits], dtype=np.int32)
        if not len(ids):
            ap.error('--logits needs --text')

        x = cpu_logits(a, ids, threads=args.threads)
        y = cpu_logits(b, ids, threads=args.threads)
        worst = float(np.abs(x - y).max())
        agree = float((x.argmax(-1) == y.argmax(-1)).mean())
        ok = ok and worst <= args.logits_tolerance
        print(
            f'logits: {x.shape[0]} positions x {x.shape[1]}, float32 on the CPU: '
            f'{"equal" if np.array_equal(x, y) else "not equal"}, max |difference| {worst:.3g} '
            f'(largest logit {float(np.abs(y).max()):.3g}), top-1 the same at {agree:.0%}',
        )

    print('the same model' if ok else 'NOT the same model')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    _main()
