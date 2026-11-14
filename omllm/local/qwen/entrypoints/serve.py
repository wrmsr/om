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
import os
import sys
import time

from omcore.logs import all as logs

from ..decode.inject import DecodeConfig
from ..inject.inject import create_engine
from ..serve.chat import CHAT_FORMATS
from ..serve.inject import ServeConfig
from ..serve.serving import SamplingDefaults
from ..serve.serving import client
from ..serve.serving import serve
from ..tokenizer import DEFAULT_REASONING_EFFORT
from ..tokenizer import REASONING_EFFORT_INSTRUCTIONS
from .common import add_model_args
from .inject import backend_config
from .inject import load_config
from .inject import lookup_config
from .inject import prefix_config
from .inject import spec_config


##


def main() -> None:
    logs.configure_standard_logging('INFO')

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
        '--reasoning-effort',
        choices=list(REASONING_EFFORT_INSTRUCTIONS),
        default=None,
        help='the reasoning effort of a request that names none (`reasoning_effort`), for a checkpoint whose chat '
             f"template takes one (qwen3.8); default: the template's own, {DEFAULT_REASONING_EFFORT}",
    )
    ap.add_argument(
        '--chat-format',
        choices=sorted(CHAT_FORMATS),
        default=None,
        help="the chat format: how tools are described and called, where reasoning blocks go (serve/chat.py); "
             "default: the checkpoint's own, by its chat template ('legacy', the JSON tool-call format, without one)",
    )
    ap.add_argument(
        '--open-think',
        action=argparse.BooleanOptionalAction,
        default=None,
        help='with thinking on, end the generation prompt with the opened <think> block (the model then reasons '
             'rather than deciding whether to); default: as the chat format has it',
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
        '--step-prefill-max',
        type=int,
        default=0,
        metavar='N',
        help='prefill up to N new tokens through the captured 16-token decode step instead of the eager forward '
             '(a short follow-up to a cached conversation: 20 ms where the eager forward takes 68 on the 27B); 48 is '
             'about where the two cross. One more step shape to compile, the same one --lookup-k 15 uses; 0: off',
    )
    ap.add_argument(
        '--prefill-checkpoints',
        type=int,
        default=0,
        metavar='N',
        help='keep up to N states from inside each prefill in the prefix cache (after its 1st, 2nd, 4th ... chunk), '
             'so a request that shares only the start of an earlier prompt -- another session with the same system '
             'prompt and tools, a rewritten history -- resumes there instead of starting cold; each is a full state '
             '(on the 27B ~150 MB plus 32 KB a token), so mind the cache budgets',
    )
    ap.add_argument(
        '--warmup',
        action='store_true',
        help='capture / compile the decode steps before listening',
    )
    ap.add_argument('--policy', choices=['uniform', 'km'], default='uniform', help='per-tensor precision policy')
    ap.add_argument('--no-quant-search', action='store_true', help='plain min/max quantization')
    add_model_args(ap)
    args = ap.parse_args()

    if args.client is not None:
        res = client(args.url, [{'role': 'user', 'content': args.client}], stream=True)
        sys.stdout.write('\n')
        print(json.dumps({k: v for k, v in res.items() if k != 'message'}, indent=1))
        return

    defaults = SamplingDefaults(max_tokens=args.max_tokens)
    if args.preset == 'non-thinking':
        defaults = SamplingDefaults(0.7, 20, 0.8, 0.0, 1.5, 0.0, args.max_tokens)
    elif args.preset == 'greedy':
        defaults = SamplingDefaults(0.0, 0, 1.0, 0.0, 0.0, 0.0, args.max_tokens)

    # assembled by the injector (inject/): each role's configuration, nothing else
    engine = create_engine(
        backend=backend_config(args),
        load=load_config(args),
        decode=DecodeConfig(
            capacity=args.capacity,
            prefill_chunk=args.prefill_chunk,
            prefill_checkpoints=0 if args.no_prefix_cache else args.prefill_checkpoints,
            step_prefill_max=args.step_prefill_max,
        ),
        spec=spec_config(args),
        lookup=lookup_config(args),
        prefix=prefix_config(args, enabled=not args.no_prefix_cache),
        serve=ServeConfig(
            defaults=defaults,
            enable_thinking=not args.no_think,
            preserve_thinking=not args.strip_thinking,
            reasoning_effort=args.reasoning_effort,
            open_think=args.open_think,
            chat_format=args.chat_format,
            max_queue=args.max_queue,
            model_name=args.model,
        ),
    )

    fmt = engine.describe_format()
    print(
        f"[serve] chat format {fmt['chat_format']} (the checkpoint's own unless --chat-format said otherwise); "
        f"thinking {'on' if fmt['thinking'] else 'off'} by default"
        + (f", reasoning effort {fmt['reasoning_effort']}" if fmt['reasoning_effort'] else '')
        + (', generation prompt opens the reasoning block' if fmt['open_think'] else ''),
        flush=True,
    )

    if args.warmup:
        t0 = time.time()
        engine.warmup(max_new_tokens=max(8, 2 * args.spec + 2))
        print(f'[serve] warm-up (capture + compile) {time.time() - t0:.1f}s')
        if args.compile and args.cache_dir:
            from ..backends.torch import save_compile_cache

            path = os.path.join(args.cache_dir, 'torch-compile.bin')
            if save_compile_cache(path):
                print(f'[serve] saved compile cache to {path}')

    engine.start()
    srv = serve(engine, args.host, args.port)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == '__main__':
    main()
