# ruff: noqa: N803 N806 N812
"""
Load a Qwen3.5-family model straight from Ollama's blob store and generate.

python generate.py --model qwen3.5:0.8b --prompt "Why is the sky blue?"
python generate.py --model ~/.ollama/models/blobs/sha256-... --raw --prompt "The capital of France is"

Everything is assembled by hand (api.ManualGenerationRunner over api.generate) unless `--inject`, which assembles the
same roles through the injector (entrypoints/inject.py, inject/): either way the rest of this file drives a
GenerationRunner, so the two paths differ only in how it was put together.
"""
import argparse
import sys
import time

from omcore.logs import all as logs

from ..api import ManualGenerationRunner
from ..backends import BACKENDS
from ..decode.runners import GenerationParams
from ..decode.terminators import BudgetTerminator
from ..load.weights import OllamaModel
from ..load.weights import describe_gguf
from ..load.weights import open_source
from ..load.weights import resolve_weights
from ..prefix.cache import PrefixCache
from ..tokenizer import Tokenizer
from .common import GenerationSetup
from .common import load_model
from .inject import assemble_generation


##


DTYPES = (
    'bf16',
    'f16',
    'f32',
)


def main() -> None:
    logs.configure_standard_logging('INFO')

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
    ap.add_argument(
        '--draft-vocab',
        type=int,
        default=0,
        metavar='N',
        help=(
            'draft with an output head restricted to the first N token ids (0 = full vocabulary); 32768-65536 makes '
            'the draft steps several times cheaper and costs little acceptance'
        ),
    )
    ap.add_argument(
        '--lookup',
        type=int,
        default=0,
        metavar='N',
        help=(
            'prompt-lookup drafting first: when the last N tokens occurred earlier in the context, draft what followed '
            'them there (else the MTP head, with --spec); 0 = off'
        ),
    )
    ap.add_argument(
        '--lookup-k',
        type=int,
        default=3,
        metavar='K',
        help=(
            'prompt-lookup draft length (at least --spec\'s); more than the head\'s pays on copies (15 is 2.8x the '
            'head alone on a file rewrite with the 27B), and compiles a verify step of its own; keep K + 1 <= 16'
        ),
    )
    ap.add_argument(
        '--temperature',
        type=float,
        default=0.0,
        help='0 = greedy (default)',
    )
    ap.add_argument(
        '--top-k',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--top-p',
        type=float,
        default=1.0,
    )
    ap.add_argument(
        '--min-p',
        type=float,
        default=0.0,
    )
    ap.add_argument(
        '--presence-penalty',
        type=float,
        default=0.0,
    )
    ap.add_argument(
        '--seed',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--cache-dir',
        default=None,
        help='directory for the finished-parameter cache (paramcache.py); e.g. ./.cache/qwen. First load fills it',
    )
    ap.add_argument(
        '--policy',
        choices=['uniform', 'km'],
        default='uniform',
        help='per-tensor precision policy',
    )
    ap.add_argument(
        '--kv-dtype',
        choices=['bf16', 'fp8'],
        default='bf16',
        help='KV cache format (torch): see serve',
    )
    ap.add_argument(
        '--no-quant-search',
        action='store_true',
        help='plain min/max quantization',
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
        '--capacity',
        type=int,
        default=None,
        help=(
            'pin the decode buffers (KV positions) to this length, rounded up to a power of two; the captured and '
            'compiled steps are specific to it, so pin it to your working context (e.g. 8192) and every prompt reuses '
            'them. Default: prompt + new tokens'
        ),
    )
    ap.add_argument(
        '--prefix-cache',
        action='store_true',
        help=(
            'snapshot the state after the prompt and after the generation and resume later requests from the longest '
            'matching snapshot (prefixcache.py); with --follow-up, demonstrates the second turn'
        ),
    )
    ap.add_argument(
        '--cache-device-mib',
        type=int,
        default=4096,
        help='prefix cache budget on the device',
    )
    ap.add_argument(
        '--cache-host-mib',
        type=int,
        default=8192,
        help='prefix cache budget in (pinned) host memory',
    )
    ap.add_argument(
        '--follow-up',
        default=None,
        metavar='TEXT',
        help=(
            'after the answer, send a second user turn with this text over the same conversation (the ids of the first '
            'turn, verbatim) and report how much of it the prefix cache reused'
        ),
    )
    ap.add_argument(
        '--warmup',
        action='store_true',
        help='run a short throwaway generation first so graph capture / kernel compile stay out of the timing',
    )
    ap.add_argument(
        '--inject',
        action='store_true',
        help='assemble through the injector (inject/) instead of by hand (api.ManualGenerationRunner)',
    )
    ap.add_argument(
        '--preset',
        choices=['thinking', 'non-thinking'],
        default=None,
        help=(
            "Qwen's published sampling presets: "
            "thinking t=1.0/top-p .95/top-k 20; non-thinking t=0.7/top-p .8/top-k 20/presence 1.5"
        ),
    )
    args = ap.parse_args()
    if args.preset == 'thinking':
        args.temperature, args.top_p, args.top_k, args.presence_penalty = 1.0, 0.95, 20, 0.0
    elif args.preset == 'non-thinking':
        args.temperature, args.top_p, args.top_k, args.presence_penalty = 0.7, 0.8, 20, 1.5

    if args.info:
        r = resolve_weights(args.model)
        if not isinstance(r, OllamaModel):
            print(describe_gguf(r))  # type: ignore[arg-type]
        src = open_source(args.model)  # raises with a diagnostic if the mapping fails
        print(f'[model] {src.config.summary()}')
        for sn in src.names():
            print(sn)
        return

    use_prefix = bool(args.prefix_cache or args.follow_up)
    setup = (
        assemble_generation(args, prefix_cache=use_prefix)
        if args.inject else
        _assemble_by_hand(args, prefix_cache=use_prefix)
    )
    tok, runner, prefix_cache = setup.tok, setup.runner, setup.prefix_cache

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
    eos = frozenset(
        i
        for i in (
            tok.eos_id,
            tok.special.get('<|im_end|>'),
            tok.special.get('<|endoftext|>'),
        )
        if i is not None
    )

    if args.warmup:
        t0 = time.time()
        # throwaway generations with the real run's prompt + max_new_tokens, so their decode buffers (and the steps
        # captured / compiled for them) are the real run's, each ended early by a budget of its own: the real prompt,
        # then with prompt lookup one counting in a cycle, which a model goes on with, so lookup drafts and its steps
        # are compiled too (a real prompt rarely repeats itself in a few tokens)
        total = len(ids) + args.max_new_tokens
        budget = max(8, 2 * max(args.spec, args.lookup_k if args.lookup else 0) + 2)
        prompts = [ids]
        if args.lookup:
            prompts.append(tok.encode(' '.join(['1 2 3 4 5 6 7 8'] * 6))[:max(1, total - budget)])
        for prompt in prompts:
            runner.run(GenerationParams(
                prompt=prompt,
                max_new_tokens=total - len(prompt),
                eos_ids=eos,
                terminators=[BudgetTerminator(budget)],
            ))
        if prefix_cache is not None:
            prefix_cache.clear()  # (or the real run would resume from the warm-up's snapshot of its own prompt)
        print(f'[gen] warm-up (capture + compile) {time.time() - t0:.1f}s')
        if args.compile and getattr(setup.ops, 'compile_cache', None):
            from ..backends.torch import save_compile_cache

            if save_compile_cache(setup.ops.compile_cache):  # type: ignore[attr-defined]
                print(f'[gen] saved compile cache to {setup.ops.compile_cache}')  # type: ignore[attr-defined]

    def run(ids: list[int]) -> list[int]:
        streamer = Tokenizer.Streamer(tok)
        t0 = time.time()
        n = [0]
        first = [0.0]

        def on_token(i):
            if not n[0]:
                first[0] = time.time() - t0
            n[0] += 1
            sys.stdout.write(streamer.push(i))
            sys.stdout.flush()

        res = runner.run(GenerationParams(
            prompt=ids,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            min_p=args.min_p,
            seed=args.seed,
            presence_penalty=args.presence_penalty,
            eos_ids=eos,
            on_token=on_token,
        ))
        sys.stdout.write(streamer.flush())
        dt = time.time() - t0
        print(
            f'\n[gen] {n[0]} tokens in {dt:.1f}s ({n[0] / dt:.1f} tok/s incl. prefill; '
            f'first token {first[0] * 1000:.0f} ms)',
        )
        if prefix_cache is not None:
            print(f'[prefix] reused {res.reused} of {res.prompt_tokens} prompt tokens; {prefix_cache.stats()}')
        if args.spec or args.lookup:
            print(
                f'[spec] {res.rounds} rounds, {res.accepted} of {res.drafted} drafts accepted '
                f'({res.accepted / max(1, res.drafted):.0%}; {res.tokens_per_round:.2f} tokens/round)',
            )
        return list(res.tokens)

    out = run(ids)
    if args.follow_up:
        # the second turn continues the exact ids of the first (a harness must keep ids, not re-tokenise text)
        im_end = tok.special.get('<|im_end|>')
        tail = list(out)
        if tail and tail[-1] == im_end:
            tail = tail[:-1]
        cont = tok.apply_chat([{'role': 'user', 'content': args.follow_up}], think=args.think)
        ids2 = ids + tail + tok.encode('<|im_end|>\n' + cont)
        print(f'\n[gen] follow-up: {len(ids2)} prompt tokens')
        run(ids2)


def _assemble_by_hand(args: argparse.Namespace, *, prefix_cache: bool) -> GenerationSetup:
    """The runner wired by hand: the model loaded here, the rest per generation by api.generate."""

    ops, _, tok, model = load_model(args, policy=args.policy, quant_search=not args.no_quant_search)
    pc = PrefixCache(ops, args.cache_device_mib << 20, args.cache_host_mib << 20) if prefix_cache else None
    return GenerationSetup(
        ops=ops,
        tok=tok,
        runner=ManualGenerationRunner(
            model,
            spec=args.spec,
            draft_vocab=args.draft_vocab,
            lookup_ngram=args.lookup,
            lookup_k=args.lookup_k,
            capacity=args.capacity,
            prefix_cache=pc,
            static=not args.functional,
        ),
        prefix_cache=pc,
    )


if __name__ == '__main__':
    main()
