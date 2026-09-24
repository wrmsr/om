# ruff: noqa: N803 N806 N812
"""
Measure what a quantization recipe costs: KL divergence of a model's next-token distributions from a reference model's,
over real text, plus top-1 agreement and each model's perplexity.

Two 27B models do not fit on one 32 GB GPU together, so it runs in two passes: the reference (int8 is close enough to
lossless to stand in for bf16, and fits) saves its log-probabilities; the candidate loads them and compares.

    python -m omllm.local.qwen.entrypoints.kl --model qwen3.8:27b --quant int8 --text some.txt --save ref-int8.npz
    python -m omllm.local.qwen.entrypoints.kl --model qwen3.8:27b --quant int4 --text some.txt --ref ref-int8.npz python
    -m omllm.local.qwen.entrypoints.kl --model /path/to/hf/Qwen3.8-27B --quant int4 --policy km \\
        --text some.txt --ref ref-int8.npz

`--text` is any file (a few of your own source files concatenated make a fair test for a coding agent); `--n-tokens`
(default 2048) of it are scored, teacher-forced. Numbers: mean KL in nats (0.01 is barely noticeable, 0.05 is the
neighbourhood of a good 4-bit, 0.2+ is degraded), top-1 agreement, perplexities.
"""
import argparse
import time

import numpy as np

from ..model import Cache
from ..model import Qwen35
from .common import add_model_args
from .common import load_model


##


def logprobs(model: Qwen35, ids: list[int], chunk: int = 512) -> np.ndarray:
    """Log-softmax of the model's logits at every position of `ids`, teacher-forced: [T, V] float16."""

    ops = model.ops
    cache = Cache(model.cfg)
    out: list[np.ndarray] = []
    for s in range(0, len(ids), chunk):
        logits = model.forward(np.asarray([ids[s:s + chunk]], dtype=np.int32), cache)
        lp = ops.numpy(logits[0]).astype(np.float32)
        lp = lp - lp.max(-1, keepdims=True)
        lp = lp - np.log(np.exp(lp).sum(-1, keepdims=True))
        out.append(lp.astype(np.float16))
    return np.concatenate(out, 0)


def compare(ref: np.ndarray, cur: np.ndarray, ids: list[int]) -> dict:
    """KL(ref || cur) per predicted token and the summary numbers."""

    T = min(len(ref), len(cur), len(ids) - 1)
    kl = np.zeros(T, dtype=np.float64)
    agree = 0
    nll_ref = 0.0
    nll_cur = 0.0
    for t in range(T):
        r = ref[t].astype(np.float64)
        c = cur[t].astype(np.float64)
        p = np.exp(r)
        kl[t] = float((p * (r - c)).sum())
        agree += int(np.argmax(r) == np.argmax(c))
        nll_ref -= r[ids[t + 1]]
        nll_cur -= c[ids[t + 1]]
    return {
        'tokens': T,
        'kl_mean': float(kl.mean()),
        'kl_median': float(np.median(kl)),
        'kl_p99': float(np.percentile(kl, 99)),
        'kl_max': float(kl.max()),
        'top1_agreement': agree / T,
        'ppl_ref': float(np.exp(nll_ref / T)),
        'ppl_cur': float(np.exp(nll_cur / T)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--text',
        required=True,
        help='text file to score',
    )
    ap.add_argument(
        '--n-tokens',
        type=int,
        default=2048,
    )
    ap.add_argument(
        '--chunk',
        type=int,
        default=512,
    )
    ap.add_argument(
        '--save',
        default=None,
        help='write this model\'s log-probs (the reference) to an .npz',
    )
    ap.add_argument(
        '--ref',
        default=None,
        help='compare against log-probs saved by --save',
    )
    ap.add_argument(
        '--policy',
        choices=[
            'uniform',
            'km',
        ],
        default='uniform',
    )
    ap.add_argument(
        '--no-quant-search',
        action='store_true',
        help='plain min/max quantization',
    )
    add_model_args(ap)
    args = ap.parse_args()
    if not args.save and not args.ref:
        ap.error('one of --save / --ref')

    ops, src, tok, model = load_model(
        args,
        policy=args.policy,
        quant_search=not args.no_quant_search,
    )
    with open(args.text, encoding='utf-8', errors='replace') as f:
        text = f.read()
    ids = tok.encode(text)[:args.n_tokens + 1]
    print(f'[kl] {len(ids)} tokens of {args.text}')
    t0 = time.time()
    lp = logprobs(model, ids, args.chunk)
    print(f'[kl] scored in {time.time() - t0:.1f}s')
    if args.save:
        np.savez(args.save, logprobs=lp, ids=np.asarray(ids, dtype=np.int32))
        nll = -sum(float(lp[t, ids[t + 1]]) for t in range(len(ids) - 1)) / (len(ids) - 1)
        print(f'[kl] saved reference log-probs to {args.save}; ppl {np.exp(nll):.3f}')
    if args.ref:
        ref = np.load(args.ref)
        rids = ref['ids'].tolist()
        n = min(len(rids), len(ids))
        if rids[:n] != ids[:n]:
            ap.error('the reference was scored on different tokens (different text or tokenizer)')
        stats = compare(ref['logprobs'], lp, ids)
        print(
            f"[kl] {stats['tokens']} tokens: KL mean {stats['kl_mean']:.4f} nats (median {stats['kl_median']:.4f}, "
            f"p99 {stats['kl_p99']:.3f}, max {stats['kl_max']:.3f}); top-1 agreement {stats['top1_agreement']:.1%}; "
            f"ppl ref {stats['ppl_ref']:.3f} vs this {stats['ppl_cur']:.3f}",
        )


if __name__ == '__main__':
    main()
