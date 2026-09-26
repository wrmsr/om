"""Model-loading options shared by the entrypoints (serve uses them; generate still carries its own copy)."""
import argparse
import pathlib
import time
import typing as ta

from ..backends.backends import BACKENDS
from ..backends.backends import default_dtype
from ..backends.backends import make_ops
from ..model import Qwen35
from ..ops import DTYPE_NAMES as DTYPES
from ..tokenizer import Tokenizer
from ..weights import open_source


##


def add_model_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument(
        '--model',
        required=True,
        help='Ollama model name (qwen3.8:27b), a path to a .gguf / blob, or a Hugging Face checkpoint directory',
    )
    ap.add_argument(
        '--backend',
        choices=BACKENDS,
        default=None,
        help='default: mlx on macOS if installed, else torch',
    )
    ap.add_argument(
        '--device',
        default=None,
        help='torch device (cuda / mps / cpu); default: best available',
    )
    ap.add_argument(
        '--dtype',
        choices=DTYPES,
        default=None,
        help='default: bf16 on accelerators, f32 on cpu',
    )
    ap.add_argument(
        '--quant',
        choices=['int8', 'int4'],
        default=None,
        help='keep linear weights quantized on device (weight-only affine, group 64); default: none',
    )
    ap.add_argument(
        '--spec',
        type=int,
        default=0,
        metavar='K',
        help='MTP speculative decoding with K draft tokens per round (loads the draft head); 0 = off',
    )
    ap.add_argument(
        '--draft-vocab',
        type=int,
        default=0,
        metavar='N',
        help='draft with an output head restricted to the first N token ids (0 = full vocabulary)',
    )
    ap.add_argument(
        '--cache-dir',
        default=None,
        help='directory for the finished-parameter cache (paramcache.py) and compile artifacts, e.g. ./.cache/qwen',
    )
    ap.add_argument(
        '--triton-tuned',
        default=None,
        help='JSON from entrypoints/tune with per-shape GEMV launch configs, e.g. ./.cache/qwen/gemv-int4.json',
    )
    ap.add_argument(
        '--compile',
        action='store_true',
        help='torch.compile the captured steps (fuses the small ops between the big kernels); slow first run',
    )
    ap.add_argument(
        '--kv-dtype',
        choices=['bf16', 'fp8'],
        default='bf16',
        help='KV cache format (torch): bf16 (32 KB per position on the 27B) or fp8 e4m3 codes with per-position '
             'scales (16 KB) -- half the memory for the live buffers and for prefix snapshots, measured by kl',
    )
    ap.add_argument(
        '--capacity',
        type=int,
        default=32768,
        help='decode buffer length (KV positions), rounded up to a power of two; the captured / compiled steps are '
             'specific to it, so pin it to the longest context you will run (the model supports 262144: 8.6 GB of KV '
             'for the 27B, plus the same again per prefix-cache snapshot of a full context). Attention only reads '
             'the positions in use, so a large capacity costs memory, not time',
    )


def load_model(
        args: argparse.Namespace,
        policy: str = 'uniform',
        quant_search: bool = True,
) -> tuple[ta.Any, ta.Any, Tokenizer, Qwen35]:
    """(ops, source, tokenizer, model) from the options above (and the quantization recipe, see Qwen35.from_source)."""

    ops = make_ops(args.backend, args.device)
    dtype = args.dtype or default_dtype(ops)
    if args.compile:
        if not hasattr(ops, 'compile'):
            raise SystemExit('--compile is a torch backend option')
        ops.compile = True
        if args.cache_dir:
            ops.compile_cache = str(pathlib.Path(args.cache_dir) / 'torch-compile.bin')  # type: ignore[attr-defined]
    if getattr(args, 'kv_dtype', 'bf16') != 'bf16':
        if not hasattr(ops, 'kv_dtype'):
            print(f'[model] --kv-dtype {args.kv_dtype} is a torch backend option; the KV cache stays in the compute dtype')  # noqa
        else:
            ops.kv_dtype = args.kv_dtype
    if args.triton_tuned and hasattr(ops, 'triton'):
        from ..backends.torch_triton import load_tuned

        print(f'[model] {load_tuned(args.triton_tuned)} tuned GEMV configs from {args.triton_tuned}')
    src = open_source(args.model)
    print(f'[model] {src.config.summary()}')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    t0 = time.time()
    model = Qwen35.from_source(
        src,
        ops,
        dtype=dtype,
        quant=args.quant,
        mtp=args.spec > 0,
        cache_dir=args.cache_dir,
        policy=policy,
        quant_search=quant_search,
    )
    print(f'[model] loaded on {ops.name} as {dtype} in {time.time() - t0:.1f}s')
    return ops, src, tok, model
