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
from ..model import Sampler
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
    ap.add_argument(
        '--functional',
        action='store_true',
        help='decode with the growing functional cache instead of the captured static step (reference path)',
    )
    ap.add_argument(
        '--spec',
        type=int,
        default=0,
        metavar='K',
        help='MTP speculative decoding with K draft tokens per round (loads the draft head); 0 = off',
    )
    ap.add_argument('--temperature', type=float, default=0.0, help='0 = greedy (default)')
    ap.add_argument('--top-k', type=int, default=0)
    ap.add_argument('--top-p', type=float, default=1.0)
    ap.add_argument('--min-p', type=float, default=0.0)
    ap.add_argument('--presence-penalty', type=float, default=0.0)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument(
        '--cache-dir',
        default=None,
        help='directory for the finished-parameter cache (paramcache.py); e.g. ./.cache/qwen. First load fills it',
    )
    ap.add_argument(
        '--warmup',
        action='store_true',
        help='run a short throwaway generation first so graph capture / kernel compile stay out of the timing',
    )
    ap.add_argument(
        '--preset',
        choices=['thinking', 'non-thinking'],
        default=None,
        help="Qwen's published sampling presets: thinking t=1.0/top-p .95/top-k 20; non-thinking t=0.7/top-p .8/top-k 20/presence 1.5",  # noqa
    )
    args = ap.parse_args()
    if args.preset == 'thinking':
        args.temperature, args.top_p, args.top_k, args.presence_penalty = 1.0, 0.95, 20, 0.0
    elif args.preset == 'non-thinking':
        args.temperature, args.top_p, args.top_k, args.presence_penalty = 0.7, 0.8, 20, 1.5

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
    model = Qwen35.from_source(
        src,
        ops,
        dtype=dtype,
        quant=args.quant,
        mtp=args.spec > 0,
        cache_dir=args.cache_dir,
    )
    print(f'[model] loaded on {ops.name} as {dtype} in {time.time() - t0:.1f}s')
    sampler = Sampler(
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        min_p=args.min_p,
        presence_penalty=args.presence_penalty,
        seed=args.seed,
    )

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

    if args.warmup:
        t0 = time.time()
        model.generate(ids, max_new_tokens=max(8, 2 * args.spec + 2), sampler=Sampler(), spec=args.spec)
        print(f'[gen] warm-up (capture + compile) {time.time() - t0:.1f}s')

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
        static=not args.functional,
        sampler=sampler,
        spec=args.spec,
    )
    sys.stdout.write(streamer.flush())
    dt = time.time() - t0
    print(f'\n[gen] {n[0]} tokens in {dt:.1f}s ({n[0] / dt:.1f} tok/s incl. prefill)')
    if args.spec and model.last_spec is not None:
        sd = model.last_spec
        print(
            f'[spec] {sd.rounds} rounds, {sd.accepted} drafts accepted '
            f'({sd.accepted / max(1, sd.rounds * args.spec):.0%} of {args.spec}/round; '
            f'{(sd.accepted + sd.rounds) / max(1, sd.rounds):.2f} tokens/round)',
        )


if __name__ == '__main__':
    main()
