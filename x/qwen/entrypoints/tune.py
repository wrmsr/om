"""
Tune the Triton int4/int8 GEMV launch configurations for a model's projection shapes on this GPU and save
them for `TorchOps(triton_tuned=...)` / `generate --triton-tuned`.

    python -m x.qwen.entrypoints.tune --model qwen3.8:27b --quant int4 --out ./.cache/qwen/gemv-int4.json
"""
import argparse

import torch

from ..backends.triton import save_tuned
from ..backends.triton import tune
from ..model import fusion_of
from ..model import mtp_param_names
from ..model import required_param_names
from ..quant import QUANT_BITS
from ..weights import open_source


##


def model_shapes(model: str, bits: int, with_mtp: bool = True) -> dict[int, set[tuple[int, int]]]:
    """
    Distinct (N, K) of the model's quantized 2-D weights as the model actually runs them -- fused projections
    (gate_up, qkv, qkvz, ab; see model.FUSIONS) count once with their stacked N -- grouped by bit width (the
    a/b pair is int8 whatever the model's width).
    """

    src = open_source(model)
    cfg = src.config
    names = required_param_names(cfg) + (mtp_param_names() if with_mtp and cfg.num_mtp_layers else [])
    if 'lm_head.weight' in set(src.names()):
        names.append('lm_head.weight')

    def shape_of(name: str) -> tuple[int, int]:
        g = src._canon[name][0] if hasattr(src, '_canon') else None  # noqa
        sh = tuple(reversed([int(d) for d in src._tensors[g].shape])) if g else src.get(name).shape  # noqa
        return int(sh[0]), int(sh[1])

    out: dict[int, set[tuple[int, int]]] = {}
    seen_fused: set[str] = set()
    for name in names:
        if any(s in name for s in ('norm', 'linear_attn.A', 'dt_bias', 'conv1d')):
            continue
        f = fusion_of(name)
        if f is not None:
            fused, parts, fbits = f
            if fused in seen_fused:
                continue
            seen_fused.add(fused)
            shapes = [shape_of(pn) for pn in parts]
            n, k = sum(sh[0] for sh in shapes), shapes[0][1]
            b = fbits or bits
        else:
            n, k = shape_of(name)
            b = bits
        if k % 64 == 0:
            out.setdefault(b, set()).add((n, k))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--quant', choices=list(QUANT_BITS), default='int4')
    ap.add_argument('--dtype', choices=['bf16', 'f16', 'f32'], default='bf16')
    ap.add_argument('-m', type=int, default=4, help='activation rows to tune for (1 = plain decode; 4 = spec-3 verify, the default)')
    ap.add_argument('--out', required=True, help='JSON to write, e.g. ./.cache/qwen/gemv-int4.json')
    args = ap.parse_args()
    dtype = {'bf16': torch.bfloat16, 'f16': torch.float16, 'f32': torch.float32}[args.dtype]
    by_bits = model_shapes(args.model, QUANT_BITS[args.quant])
    for b, shapes in sorted(by_bits.items()):
        shapes = sorted(shapes)
        print(f'[tune] int{b}: {len(shapes)} shapes: {shapes}')
        tune(shapes, b, dtype=dtype, m=args.m)
    save_tuned(args.out)
    print(f'[tune] wrote {args.out}')


if __name__ == '__main__':
    main()
