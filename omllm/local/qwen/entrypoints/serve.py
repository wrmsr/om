"""
Serve a model as an OpenAI chat-completions endpoint (serving.py).

    python -m omllm.local.qwen.entrypoints.serve --model qwen3.8:27b --quant int4 --spec 3 --draft-vocab 65536 \\
        --compile --cache-dir ./.cache/qwen --triton-tuned ./.cache/qwen/gemv-int4.json --port 8000

    curl -N http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{
        "messages": [{"role": "user", "content": "Why is the sky blue?"}], "stream": true}'

`--client "text"` instead sends one streaming request to a running server (--url) and prints the reply.
"""
import argparse
import json
import sys
import time

from ..model import Sampler
from ..prefixcache import PrefixCache
from ..serving import Engine
from ..serving import SamplingDefaults
from ..serving import client
from ..serving import serve
from .common import add_model_args
from .common import load_model


##


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--client',
        default=None,
        metavar='TEXT',
        help='send TEXT to a running server and exit',
    )
    ap.add_argument(
        '--url',
        default='http://127.0.0.1:8000',
        help='server for --client',
    )
    ap.add_argument(
        '--host',
        default='127.0.0.1',
    )
    ap.add_argument(
        '--port',
        type=int,
        default=8000,
    )
    ap.add_argument(
        '--max-queue',
        type=int,
        default=4,
        help='requests waiting behind the running one before 503',
    )
    ap.add_argument(
        '--max-tokens',
        type=int,
        default=4096,
        help='default completion budget',
    )
    ap.add_argument(
        '--preset',
        choices=['thinking', 'non-thinking', 'greedy'],
        default='thinking',
        help="default sampling: Qwen's thinking (t=1.0/top-p .95/top-k 20) or non-thinking (t=0.7/top-p .8/top-k 20/"
             'presence 1.5) presets, or greedy; requests override per field',
    )
    ap.add_argument(
        '--no-think',
        action='store_true',
        help='reasoning off unless a request turns it on (chat_template_kwargs.enable_thinking)',
    )
    ap.add_argument(
        '--strip-thinking',
        action='store_true',
        help="render history the stock template's way (reasoning dropped from turns before the last user query); "
             'costs the prefix cache on every thinking-mode turn',
    )
    ap.add_argument(
        '--prefill-chunk',
        type=int,
        default=4096,
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
        '--no-prefix-cache',
        action='store_true',
    )
    ap.add_argument(
        '--warmup',
        action='store_true',
        help='capture / compile the decode steps before listening',
    )
    add_model_args(ap)
    args = ap.parse_args()

    if args.client is not None:
        res = client(args.url, [{'role': 'user', 'content': args.client}], stream=True)
        sys.stdout.write('\n')
        print(json.dumps({k: v for k, v in res.items() if k != 'message'}, indent=1))
        return

    ops, src, tok, model = load_model(args)
    defaults = SamplingDefaults(max_tokens=args.max_tokens)
    if args.preset == 'non-thinking':
        defaults = SamplingDefaults(0.7, 20, 0.8, 0.0, 1.5, 0.0, args.max_tokens)
    elif args.preset == 'greedy':
        defaults = SamplingDefaults(0.0, 0, 1.0, 0.0, 0.0, 0.0, args.max_tokens)
    prefix_cache = None
    if not args.no_prefix_cache:
        prefix_cache = PrefixCache(ops, args.cache_device_mib << 20, args.cache_host_mib << 20)

    if args.warmup:
        t0 = time.time()
        model.generate(
            tok.encode('hello'),
            max_new_tokens=max(8, 2 * args.spec + 2),
            sampler=Sampler(),
            spec=args.spec,
            capacity=args.capacity,
            draft_vocab=args.draft_vocab,
        )
        print(f'[serve] warm-up (capture + compile) {time.time() - t0:.1f}s')
        if args.compile and getattr(ops, 'compile_cache', None):
            from ..backends.torch import save_compile_cache

            if save_compile_cache(ops.compile_cache):
                print(f'[serve] saved compile cache to {ops.compile_cache}')

    engine = Engine(
        model,
        tok,
        spec=args.spec,
        draft_vocab=args.draft_vocab,
        capacity=args.capacity,
        prefix_cache=prefix_cache,
        defaults=defaults,
        enable_thinking=not args.no_think,
        preserve_thinking=not args.strip_thinking,
        max_queue=args.max_queue,
        prefill_chunk=args.prefill_chunk,
        model_name=args.model,
    )
    srv = serve(engine, args.host, args.port)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == '__main__':
    main()
