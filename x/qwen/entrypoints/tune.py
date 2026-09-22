"""
Tune the Triton int4/int8 GEMV launch configurations for a model's projection shapes on this GPU and save
them for `TorchOps(triton_tuned=...)` / `generate --triton-tuned`.

    python -m x.qwen.entrypoints.tune --model qwen3.8:27b --quant int4 --out ./.cache/qwen/gemv-int4.json
"""
import argparse

import torch

from ..backends.torch_triton import save_tuned
from ..backends.torch_triton import tune
from ..model import mtp_param_names
from ..model import required_param_names
from ..quant import QUANT_BITS
from ..weights import open_source


##


def model_shapes(model: str, with_mtp: bool = True) -> list[tuple[int, int]]:
    """Distinct (N, K) of the model's quantizable 2-D weights."""

    src = open_source(model)
    cfg = src.config
    names = required_param_names(cfg) + (mtp_param_names() if with_mtp and cfg.num_mtp_layers else [])
    if 'lm_head.weight' in set(src.names()):
        names.append('lm_head.weight')
    seen: set[tuple[int, int]] = set()
    for name in names:
        if any(s in name for s in ('norm', 'linear_attn.A', 'dt_bias', 'conv1d', 'in_proj_a', 'in_proj_b')):
            continue
        g = src._canon[name][0] if hasattr(src, '_canon') else None  # noqa
        shape = tuple(reversed([int(d) for d in src._tensors[g].shape])) if g else src.get(name).shape  # noqa
        if len(shape) == 2 and shape[1] % 64 == 0:
            seen.add((int(shape[0]), int(shape[1])))
    return sorted(seen)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--quant', choices=list(QUANT_BITS), default='int4')
    ap.add_argument('--dtype', choices=['bf16', 'f16', 'f32'], default='bf16')
    ap.add_argument('-m', type=int, default=1, help='activation rows to tune for (1 = decode; 4 = verify)')
    ap.add_argument('--out', required=True, help='JSON to write, e.g. ./.cache/qwen/gemv-int4.json')
    args = ap.parse_args()
    dtype = {'bf16': torch.bfloat16, 'f16': torch.float16, 'f32': torch.float32}[args.dtype]
    shapes = model_shapes(args.model)
    print(f'[tune] {len(shapes)} shapes: {shapes}')
    tune(shapes, QUANT_BITS[args.quant], dtype=dtype, m=args.m)
    save_tuned(args.out)
    print(f'[tune] wrote {args.out}')


if __name__ == '__main__':
    main()
