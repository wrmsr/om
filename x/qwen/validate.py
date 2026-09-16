"""
Validate the torch implementation against llama.cpp, using llama-server as the oracle.

Start the oracle on the *same* GGUF blob Ollama uses:

    llama-server -m ~/.ollama/models/blobs/sha256-<digest> --port 8080 -c 4096
    # (find the digest with: python validate.py --model qwen3.5:0.8b --show-blob)

Then:

    python validate.py --model qwen3.5:0.8b --prompt "The capital of France is" -n 32

Three checks, no extra deps (urllib only):
  1. tokenizer:   our ids == /tokenize ids
  2. greedy:      our argmax tokens == the server's greedy tokens, step by step
  3. logprobs:    teacher-force the server's tokens through our model and compare
                  log-softmax(ours) with the server's top-K pre-sampling logprobs (n_probs) at every position.  Reports
                  max |delta| and top-1 agreement.

Run with --dtype f32 for a like-for-like comparison (llama.cpp does activations in f32). Expected on a Q4_K_M/Q8_0 blob
with matching dequant: top-1 agreement ~100% for the first few dozen tokens and max |delta logprob| in the 1e-2..1e-1
range (different matmul orders / KV precision).  Anything wildly off means a layout/ordering bug.
"""
import argparse
import json
import math
import sys
import time
import urllib.request

import torch

from .model import Cache
from .model import Qwen35
from .tokenizer import Tokenizer
from .weights import MT_GGUF
from .weights import open_source
from .weights import resolve_ollama


##


def post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--server', default='http://127.0.0.1:8080')
    ap.add_argument('--prompt', '-p', default='The capital of France is')
    ap.add_argument(
        '--chat', action='store_true', help='wrap prompt in the chat template first',
    )
    ap.add_argument('-n', type=int, default=32)
    ap.add_argument('--top-k', type=int, default=10)
    ap.add_argument('--device', default=None)
    ap.add_argument('--dtype', choices=['bf16', 'f16', 'f32'], default='f32')
    ap.add_argument(
        '--show-blob', action='store_true', help='print the GGUF blob path and exit',
    )
    args = ap.parse_args()

    if args.show_blob:
        om = resolve_ollama(args.model)
        for l in om.layers(MT_GGUF):
            print(om.blob(l['digest']), l.get('size'))
        return

    from generate import DTYPES
    from generate import pick_device

    device = pick_device(args.device)
    dtype = DTYPES[args.dtype]

    src = open_source(args.model)
    print(f'[model] {src.config.summary()}')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    text = (
        tok.apply_chat([{'role': 'user', 'content': args.prompt}], think=False)
        if args.chat
        else args.prompt
    )

    # 1. tokenizer

    ours = tok.encode(text, parse_special=True)
    ref = post(
        f'{args.server}/tokenize',
        {'content': text, 'add_special': False, 'parse_special': True},
    )['tokens']
    if ours == ref:
        print(f'[tokenizer] OK ({len(ours)} tokens)')
    else:
        print(f'[tokenizer] MISMATCH\n  ours: {ours}\n  ref : {ref}')
        for i, (a, b) in enumerate(zip(ours, ref)):
            if a != b:
                print(
                    f'  first diff at {i}: ours={a} ({tok.decode([a])!r}) ref={b} ({tok.decode([b])!r})',
                )
                break
    prompt_ids = ref  # use the oracle's ids from here on so model checks are independent of tokenizer

    # 2. oracle greedy generation with per-step top-K logprobs

    t0 = time.time()
    resp = post(
        f'{args.server}/completion',
        {
            'prompt': prompt_ids,
            'n_predict': args.n,
            'temperature': 0.0,
            'samplers': [],
            'n_probs': args.top_k,
            'return_tokens': True,
            'cache_prompt': False,
            'seed': 0,
        },
    )
    ref_tokens = resp.get('tokens') or []
    probs = resp.get('completion_probabilities') or resp.get('probs') or []
    if not ref_tokens and probs:
        ref_tokens = [p['id'] for p in probs]
    print(
        f'[oracle] {len(ref_tokens)} tokens in {time.time() - t0:.1f}s: {tok.decode(ref_tokens)!r}',
    )
    if not probs:
        print(
            '[oracle] server returned no completion_probabilities; is n_probs supported? continuing with tokens only',
        )

    # 3. our model, teacher-forced on the oracle's tokens

    model = Qwen35.from_source(src, device=device, dtype=dtype)
    seq = prompt_ids + ref_tokens[:-1]
    cache = Cache(src.config)
    t0 = time.time()
    logits = model.forward(torch.tensor([seq], device=device), cache)  # [1, L, V]
    print(f'[ours] forward over {len(seq)} tokens in {time.time() - t0:.1f}s')
    logp = torch.log_softmax(
        logits[0, len(prompt_ids) - 1 :].float(), dim=-1,
    )  # position i predicts ref_tokens[i]

    top1_ok = 0
    greedy_prefix_ok = True
    first_div = None
    max_abs = 0.0
    for i, rt in enumerate(ref_tokens):
        ours_top = int(logp[i].argmax())
        if ours_top == rt:
            top1_ok += 1
        elif first_div is None:
            first_div = i
        if probs and i < len(probs):
            entry = probs[i]
            tops = entry.get('top_logprobs') or entry.get('top_probs') or []
            for tp in tops:
                ref_lp = tp.get('logprob')
                if ref_lp is None and 'prob' in tp:
                    ref_lp = math.log(max(tp['prob'], 1e-30))
                d = abs(float(logp[i, tp['id']]) - ref_lp)
                max_abs = max(max_abs, d)
    n = len(ref_tokens)
    print(
        f'[compare] top-1 agreement: {top1_ok}/{n}  (first divergence at step {first_div})',
    )
    if probs:
        print(
            f'[compare] max |delta logprob| over oracle top-{args.top_k} at every step: {max_abs:.4f}',
        )

    # step-by-step table for the first few positions
    print('\nstep  ref_tok  ours_tok  ref_lp   ours_lp   ref_piece / ours_piece')
    for i in range(min(n, 12)):
        rt = ref_tokens[i]
        ot = int(logp[i].argmax())
        ref_lp = None
        if probs and i < len(probs):
            ref_lp = probs[i].get('logprob')
            if ref_lp is None and 'prob' in probs[i]:
                ref_lp = math.log(max(probs[i]['prob'], 1e-30))
        mark = '' if rt == ot else '  <-- diff'
        print(
            f"{i:4d}  {rt:7d}  {ot:8d}  {ref_lp if ref_lp is not None else float('nan'):7.3f}  {float(logp[i, rt]):7.3f}   "
            f"{tok.decode([rt])!r} / {tok.decode([ot])!r}{mark}",
        )

    # also run our own greedy decode from the same prompt for a sanity string
    ours_gen = model.generate(prompt_ids, max_new_tokens=n)
    print(f'\n[ours greedy] {tok.decode(ours_gen)!r}')
    match = sum(a == b for a, b in zip(ours_gen, ref_tokens))
    print(f'[ours greedy] {match}/{n} tokens identical to oracle')
    sys.exit(0 if top1_ok >= 0.9 * n else 1)


if __name__ == '__main__':
    main()
