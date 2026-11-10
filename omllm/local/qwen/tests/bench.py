"""
The performance arm of the safety net (UNTANGLING.md step 0): one process loads a model once and reports what a
restructuring could silently change -- prefill and decode timings, speculative rounds, prefix-hit latency, host syncs
per round, peak memory on a long prompt, the effective torch configuration (compiled graphs, graph breaks, tuned GEMV
coverage) -- plus reference greedy transcripts, so "identical output" is a diff rather than an impression.

    python -m omllm.local.qwen.tests.bench --synthetic                    # CPU: the Python-side costs
    python -m omllm.local.qwen.tests.bench --model qwen3.8:27b --quant int4 --compile \\
        --kv-dtype fp8 --cache-dir ./.cache/qwen --triton-tuned ./.cache/qwen/gemv-int4.json --long 32768 \\
        --save bench-27b.json
    python -m omllm.local.qwen.tests.bench ... --check bench-27b.json   # compare transcripts against a saved run

A test-support utility, not a test: it imports the synthetic builder from the tests.
"""
import argparse
import json
import sys
import time
import typing as ta

import numpy as np

from omcore import lang

from ..api import generate
from ..arch.qwen35 import load_qwen35
from ..core.model import Qwen35
from ..decode.generation import Generated
from ..decode.sampling import Sampler
from ..entrypoints.common import add_model_args
from ..entrypoints.common import load_model
from ..prefix.cache import PrefixCache


if ta.TYPE_CHECKING:
    import torch
else:
    torch = lang.proxy_import('torch')


##


PROMPTS = (
    'Tell me about itertools - be very detailed',
    'Write a short story about a lighthouse keeper.',
    'Explain how a hash map works, with an example in C.',
)


class SyncCounter:
    """Counts device->host reads (`ops.numpy`) by wrapping the instance's method: every host sync goes through it."""

    def __init__(self, ops: ta.Any) -> None:
        super().__init__()

        self._ops = ops
        self._orig = ops.numpy
        self.n = 0

        def numpy(x):
            self.n += 1
            return self._orig(x)

        ops.numpy = numpy

    def close(self) -> None:
        self._ops.numpy = self._orig


def _sync(ops: ta.Any) -> None:
    ops.eval()


def _timed_generate(model: Qwen35, ids: list[int], **kwargs: ta.Any) -> tuple[Generated, float, float]:
    """(what was generated, seconds to the first token, total seconds)."""

    first: list[float] = []
    t0 = time.perf_counter()

    def on_token(_):
        if not first:
            first.append(time.perf_counter() - t0)

    out = generate(model, ids, on_token=on_token, **kwargs)
    _sync(model.ops)
    return out, (first[0] if first else 0.), time.perf_counter() - t0


def _effective_torch_config(model: Qwen35) -> dict[str, ta.Any]:
    ops = model.ops
    if not ops.name.startswith('torch'):
        return {}

    from torch._dynamo.utils import counters

    from ..backends.torch import TorchQWeight
    shapes = set()
    for w in _all_weights(model):
        if isinstance(w, TorchQWeight):
            shapes.add((w.shape[0], w.shape[1], w.bits))
    return {
        'compile': bool(getattr(ops, 'compile', False)),
        'triton': bool(getattr(ops, 'triton', False)),
        'kv_dtype': getattr(ops, 'kv_dtype', None),
        'compiled_graphs': int(counters['stats'].get('unique_graphs', 0)),
        'graph_breaks': int(sum(counters['graph_break'].values())),
        'quant_shapes': len(shapes),
        'quant_shapes_tuned': sum(s in getattr(ops, 'gemv_tuned', {}) for s in shapes),
    }


def _all_weights(model: Qwen35) -> list[ta.Any]:
    out: list[ta.Any] = [model.embed, model.lm_head]
    for blk in model.blocks:
        out.extend(v for v in vars(blk.mixer).values() if v is not None)
        out.extend(v for v in vars(blk.ffn).values() if v is not None)
    return out


def _peak_gib(ops: ta.Any) -> float | None:
    if not ops.name.startswith('torch:cuda'):
        return None
    return torch.cuda.max_memory_allocated() / 2**30


def _reset_peak(ops: ta.Any) -> None:
    if ops.name.startswith('torch:cuda'):
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()


##


def run(
        model: Qwen35,
        prompts: ta.Sequence[list[int]],
        *,
        capacity: int,
        spec: int,
        draft_vocab: int,
        n_decode: int,
        n_transcript: int,
        long_ids: list[int] | None = None,
        follow_up: list[int] | None = None,
) -> dict[str, ta.Any]:
    ops = model.ops
    has_spec = spec > 0 and model.mtp is not None
    common: dict[str, ta.Any] = dict(capacity=capacity, draft_vocab=draft_vocab)
    res: dict[str, ta.Any] = {'backend': ops.name}

    # warm-up: every step shape the measurements use is captured / compiled here
    generate(model, prompts[0], max_new_tokens=8, sampler=Sampler(), **common)
    if has_spec:
        generate(model, prompts[0], max_new_tokens=8, sampler=Sampler(), spec=spec, **common)

    # plain decode, and prefill per prompt token (time to the first token over the prompt length)
    out, first, total = _timed_generate(model, prompts[0], max_new_tokens=n_decode, sampler=Sampler(), **common)
    res['prefill_ms_per_token'] = first * 1e3 / len(prompts[0])
    res['plain_tok_s'] = (len(out.tokens) - 1) / max(1e-9, total - first)

    # speculative decode
    if has_spec:
        sc = SyncCounter(ops)
        out, first, total = _timed_generate(
            model,
            prompts[0],
            max_new_tokens=n_decode,
            sampler=Sampler(),
            spec=spec,
            **common,
        )
        rounds = out.rounds
        res['spec_tok_s'] = len(out.tokens) / max(1e-9, total - first)
        res['spec_ms_per_round'] = (total - first) * 1e3 / max(1, rounds)
        res['spec_tokens_per_round'] = out.tokens_per_round
        res['spec_syncs_per_round'] = sc.n / max(1, rounds)
        sc.close()

    # prefix hit vs miss: the first-token latency of a follow-up over the same conversation
    if follow_up is not None:
        for name, use in (('miss', False), ('hit', True)):
            pc = PrefixCache(ops, 4 << 30, 0) if use else None
            base, _, _ = _timed_generate(
                model,
                prompts[0],
                max_new_tokens=16,
                sampler=Sampler(),
                prefix_cache=pc,
                **common,
            )
            _, first, _ = _timed_generate(
                model,
                prompts[0] + list(base.tokens) + follow_up,
                max_new_tokens=4,
                sampler=Sampler(),
                prefix_cache=pc,
                **common,
            )
            res[f'follow_up_first_token_ms_{name}'] = first * 1e3

    # reference transcripts: greedy ids, plain and speculative, which must agree
    transcripts: dict[str, list[int]] = {}
    for i, ids in enumerate(prompts):
        transcripts[f'{i}/plain'] = list(generate(
            model,
            ids,
            max_new_tokens=n_transcript,
            sampler=Sampler(),
            **common,
        ).tokens)
        if has_spec:
            transcripts[f'{i}/spec'] = list(generate(
                model,
                ids,
                max_new_tokens=n_transcript,
                sampler=Sampler(),
                spec=spec,
                **common,
            ).tokens)
    res['transcripts'] = transcripts
    res['spec_equals_plain'] = all(
        transcripts[f'{i}/spec'] == transcripts[f'{i}/plain']
        for i in range(len(prompts))
    ) if has_spec else None

    # long-prompt prefill: time and peak memory
    if long_ids is not None:
        _reset_peak(ops)
        _, first, _ = _timed_generate(
            model,
            long_ids,
            max_new_tokens=4,
            sampler=Sampler(),
            spec=spec if has_spec else 0,
            **common,
        )
        res['long_prompt_tokens'] = len(long_ids)
        res['long_prefill_tok_s'] = len(long_ids) / max(1e-9, first)
        res['long_peak_gib'] = _peak_gib(ops)

    res['effective'] = _effective_torch_config(model)
    return res


def _corpus() -> str:
    """Real text for the long prompt: this package's own sources (run from the repository root)."""

    import glob

    return '\n\n'.join(open(p).read() for p in sorted(glob.glob('omllm/local/qwen/**/*.py', recursive=True)))


def _check(res: dict[str, ta.Any], ref_path: str) -> list[str]:
    with open(ref_path) as f:
        ref = json.load(f)
    diffs = []
    for k, ids in ref.get('transcripts', {}).items():
        got = res['transcripts'].get(k)
        if got != ids:
            at = next((i for i, (a, b) in enumerate(zip(got or [], ids)) if a != b), min(len(got or []), len(ids)))
            diffs.append(f'transcript {k} differs from the reference at token {at}')
    return diffs


def _report(res: dict[str, ta.Any]) -> None:
    for k, v in res.items():
        if k == 'transcripts':
            continue
        if isinstance(v, float):
            v = f'{v:.3f}'
        print(f'[bench] {k}: {v}')


def _main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--synthetic', action='store_true', help='the synthetic test model on the CPU (ignores --model)')
    add_model_args(ap, model_optional=True)
    ap.add_argument('-n', type=int, default=256, help='tokens for the decode timings')
    ap.add_argument('--transcript', type=int, default=128, help='tokens per reference transcript')
    ap.add_argument('--long', type=int, default=0, help='also prefill a prompt of this many tokens')
    ap.add_argument('--save', default=None, help='write the results (with transcripts) as JSON')
    ap.add_argument('--check', default=None, help='compare transcripts against a saved run; exit 1 on a difference')
    args = ap.parse_args()

    if args.synthetic:
        from ..backends.torch import TorchOps
        from .test_parity import synthetic_source

        cfg, _, src = synthetic_source()
        ops = TorchOps('cpu', capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', mtp=True, verbose=False)
        rng = np.random.default_rng(0)
        prompts = [rng.integers(0, cfg.vocab_size, 12).tolist() for _ in range(3)]
        follow_up = rng.integers(0, cfg.vocab_size, 6).tolist()
        long_ids = rng.integers(0, cfg.vocab_size, args.long).tolist() if args.long else None
        spec = args.spec or 3
        capacity = 1024

    else:
        if args.model is None:
            ap.error('--model or --synthetic')
        if not args.spec:
            args.spec = 3
        ops, src, tok, model = load_model(args)
        prompts = [tok.encode(tok.apply_chat([{'role': 'user', 'content': p}])) for p in PROMPTS]
        follow_up = tok.encode('<|im_end|>\n' + tok.apply_chat([{'role': 'user', 'content': 'Thanks. And?'}]))
        long_ids = None
        if args.long:
            long_ids = tok.encode(_corpus())[:args.long]
        spec = args.spec
        capacity = args.capacity

    res = run(
        model,
        prompts,
        capacity=capacity,
        spec=spec,
        draft_vocab=args.draft_vocab,
        n_decode=args.n,
        n_transcript=args.transcript,
        long_ids=long_ids,
        follow_up=follow_up,
    )
    _report(res)

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(res, f, indent=1)
        print(f'[bench] saved {args.save}')

    if args.check:
        diffs = _check(res, args.check)
        for d in diffs:
            print(f'[bench] DIFF: {d}')
        if diffs:
            sys.exit(1)
        print(f'[bench] transcripts identical to {args.check}')


if __name__ == '__main__':
    _main()
