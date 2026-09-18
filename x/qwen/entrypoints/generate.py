"""
Load a Qwen3.5-family model straight from Ollama's blob store and generate.

python generate.py --model qwen3.5:0.8b --prompt "Why is the sky blue?"
python generate.py --model ~/.ollama/models/blobs/sha256-... --raw --prompt "The capital of France is"
"""
import argparse
import sys
import time

from ..backends import BACKENDS
from ..backends import default_dtype
from ..backends import make_ops
from ..model import Qwen35
from ..tokenizer import Tokenizer
from ..weights import OllamaModel
from ..weights import describe_gguf
from ..weights import open_source
from ..weights import resolve_weights


##


DTYPES = (
    'bf16',
    'f16',
    'f32',
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--model',
        required=True,
        help='Ollama model name (qwen3.5:0.8b) or path to a .gguf / blob',
    )
    ap.add_argument(
        '--prompt',
        '-p',
        default='Why is the sky blue?',
    )
    ap.add_argument(
        '--raw',
        action='store_true',
        help='no chat template; feed the prompt as-is',
    )
    ap.add_argument(
        '--think',
        action='store_true',
        help='leave reasoning enabled in the chat template',
    )
    ap.add_argument(
        '-n',
        '--max-new-tokens',
        type=int,
        default=128,
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
        '--info',
        action='store_true',
        help='dump the raw GGUF metadata + tensors, then the mapped config and names, and exit',
    )
    ap.add_argument(
        '--quant',
        choices=[
            'int8',
            'int4',
        ],
        default=None,
        help='keep linear weights quantized on device (weight-only affine, group 64); default: none',
    )
    args = ap.parse_args()

    ops = make_ops(args.backend, args.device)
    dtype = args.dtype or default_dtype(ops)

    if args.info:
        r = resolve_weights(args.model)
        if not isinstance(r, OllamaModel):
            print(describe_gguf(r))
        src = open_source(args.model)  # raises with a diagnostic if the mapping fails
        print(f'[model] {src.config.summary()}')
        for sn in src.names():
            print(sn)
        return
    src = open_source(args.model)
    print(f'[model] {src.config.summary()}')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    t0 = time.time()
    model = Qwen35.from_source(src, ops, dtype=dtype, quant=args.quant)
    print(f'[model] loaded on {ops.name} as {dtype} in {time.time() - t0:.1f}s')

    text = (
        args.prompt
        if args.raw
        else tok.apply_chat(
            [{'role': 'user', 'content': args.prompt}],
            think=args.think,
        )
    )
    ids = tok.encode(text)
    print(f'[gen] {len(ids)} prompt tokens')
    eos = {
        i
        for i in (
            tok.eos_id,
            tok.special.get('<|im_end|>'),
            tok.special.get('<|endoftext|>'),
        )
        if i is not None
    }

    streamer = Tokenizer.Streamer(tok)
    t0 = time.time()
    n = [0]

    def on_token(i):
        n[0] += 1
        sys.stdout.write(streamer.push(i))
        sys.stdout.flush()

    model.generate(
        ids,
        max_new_tokens=args.max_new_tokens,
        eos_ids=eos,
        on_token=on_token,
    )
    sys.stdout.write(streamer.flush())
    dt = time.time() - t0
    print(f'\n[gen] {n[0]} tokens in {dt:.1f}s ({n[0] / dt:.1f} tok/s incl. prefill)')


if __name__ == '__main__':
    main()
