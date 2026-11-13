"""
Qwen3.8-Flash-Next at its real dimensions, without its weights: a few layers built directly on the GPU with random
int4 weights, compiled and graph-captured, decoding past QSA's budget -- every kernel at its real shape, and a decode
step's time to extrapolate from. Shapes come from transformers' reference model on the meta device.

    python -m omllm.local.qwen.tests.flashnext_smoke --layers 4 --experts 32 --prompt 3000

A token's cost depends on the experts it routes to (10), not on how many there are, so a few dozen experts stand in for
512 (and a small n-gram vocabulary for the 51B-parameter table).
"""
import argparse
import time
import typing as ta

import numpy as np

from ..api import generate
from ..arch.qwen4exp import Qwen4ExpArchitecture
from ..backends.torch import TorchOps
from ..core.config import Qwen4ExpConfig
from ..load.weights import HFSource


if ta.TYPE_CHECKING:
    import torch
else:
    from omcore import lang

    torch = lang.proxy_import('torch')


##


def flashnext_config(layers: int, experts: int) -> tuple[ta.Any, Qwen4ExpConfig]:
    """The reference config at Flash-Next's dimensions (FLASHNEXT.md §2), and ours from it."""

    import transformers

    every = [i + 1 for i in range(layers) if (i + 1) % 4]
    hf = transformers.Qwen4ExpTextConfig(
        vocab_size=248320,
        hidden_size=2560,
        num_hidden_layers=layers,
        num_attention_heads=24,
        num_key_value_heads=2,
        head_dim=256,
        linear_num_key_heads=16,
        linear_num_value_heads=48,
        linear_key_head_dim=128,
        linear_value_head_dim=128,
        num_experts=experts,
        num_experts_per_tok=10,
        moe_intermediate_size=640,
        shared_expert_intermediate_size=640,
        hc_count=4,
        hc_lowrank=320,
        ple_layer_ids=every[1:2] or every[:1],
        ple_embed_dim=2560,
        ngram_vocab_size_base=1000,
        indexer_n_heads=4,
        indexer_kv_heads=1,
        indexer_head_dim=128,
        indexer_budget=2048,
        indexer_compress_ratio=4,
        rope_parameters={'rope_type': 'default', 'rope_theta': 1e7, 'partial_rotary_factor': 0.25},
        eos_token_id=248046,
        max_position_embeddings=262144,
        tie_word_embeddings=False,
    )
    cfg = HFSource.config_from_hf(hf.to_dict())
    if not isinstance(cfg, Qwen4ExpConfig):
        raise TypeError(type(cfg))
    return hf, cfg


def param_shapes(hf: ta.Any) -> dict[str, tuple[int, ...]]:
    """Our canonical names' shapes, from the reference model on the meta device (experts unstacked, as on disk)."""

    import transformers

    with torch.device('meta'):
        meta = transformers.Qwen4ExpForCausalLM(hf)
    shapes: dict[str, tuple[int, ...]] = {}
    for n, p in meta.named_parameters():
        n = n.replace('model.', '', 1)
        if n.endswith('mlp.experts.gate_up_proj'):
            for e in range(p.shape[0]):
                shapes[n.replace('gate_up_proj', f'{e}.gate_proj.weight')] = (p.shape[1] // 2, p.shape[2])
                shapes[n.replace('gate_up_proj', f'{e}.up_proj.weight')] = (p.shape[1] // 2, p.shape[2])
        elif n.endswith('mlp.experts.down_proj'):
            for e in range(p.shape[0]):
                shapes[n.replace('down_proj', f'{e}.down_proj.weight')] = tuple(p.shape[1:])
        elif n.endswith('linear_attn.A_log'):
            shapes[n[:-len('A_log')] + 'A'] = tuple(p.shape)
        elif n.endswith('conv1d.weight'):
            shapes[n] = (p.shape[0], p.shape[2])
        else:
            shapes[n] = tuple(p.shape)
    return shapes


def random_params(ops: TorchOps, cfg: Qwen4ExpConfig, shapes: ta.Mapping[str, tuple[int, ...]]) -> dict[str, ta.Any]:
    """Random weights for every name the architecture plans, int4 where the loader would quantize."""

    arch = Qwen4ExpArchitecture()
    g = torch.Generator(device=ops.device).manual_seed(0)
    keep_f32 = arch.layout.keep_f32
    no_quant = arch.layout.no_quant
    params: dict[str, ta.Any] = {}
    for n in arch.param_names(cfg):
        shape = shapes[n]
        if 'norm' in n:
            w = 1 + torch.randn(shape, device=ops.device, generator=g) * 0.05
        elif n.endswith('linear_attn.A'):
            w = -torch.rand(shape, device=ops.device, generator=g) * 4
        else:
            w = torch.randn(shape, device=ops.device, generator=g) * shape[-1] ** -0.5
        f32 = any(k in n for k in keep_f32)
        quantized = len(shape) == 2 and shape[-1] % 64 == 0 and not f32 and 'embed' not in n
        if quantized and not any(k in n for k in no_quant):
            params[n] = ops.quantize(w.float().cpu().numpy(), 4, 64, torch.bfloat16, search=False)
        else:
            params[n] = w.to(torch.float32 if f32 else torch.bfloat16)
    return params


def main() -> None:
    from omcore.logs import all as logs

    logs.configure_standard_logging('INFO')

    ap = argparse.ArgumentParser()
    ap.add_argument('--layers', type=int, default=4, help='a multiple of 4 keeps the 3:1 linear / QSA mix')
    ap.add_argument('--experts', type=int, default=32)
    ap.add_argument('--prompt', type=int, default=3000, help='prompt tokens (QSA selects past 2048 + 4)')
    ap.add_argument('--tokens', type=int, default=128)
    ap.add_argument('--capacity', type=int, default=8192)
    ap.add_argument('--kv-dtype', choices=['bf16', 'fp8'], default='fp8')
    args = ap.parse_args()

    import torch._dynamo as dynamo

    hf, cfg = flashnext_config(args.layers, args.experts)
    print(cfg.summary())

    ops = TorchOps('cuda', compile=True, kv_dtype=args.kv_dtype)
    ops.quant_native = True
    t0 = time.time()
    params = random_params(ops, cfg, param_shapes(hf))
    model = Qwen4ExpArchitecture().build(cfg, params, ops, torch.bfloat16)
    del params
    print(f'[smoke] built in {time.time() - t0:.0f}s; {torch.cuda.memory_allocated() / 2**30:.1f} GiB on the device')

    prompt = np.random.default_rng(0).integers(0, cfg.vocab_size - 1000, args.prompt).tolist()
    kw: dict[str, ta.Any] = dict(capacity=args.capacity)
    with dynamo.error_on_graph_break(True):
        t0 = time.time()
        generate(model, prompt, max_new_tokens=8, **kw)
        print(f'[smoke] warm-up (compile + capture) {time.time() - t0:.0f}s')

        torch.cuda.synchronize()
        stamps: list[float] = []
        res = generate(
            model,
            prompt,
            max_new_tokens=args.tokens,
            on_token=lambda t: stamps.append(time.perf_counter()),
            **kw,
        )
        torch.cuda.synchronize()

    step = (stamps[-1] - stamps[0]) / max(1, res.rounds - 1)
    print(
        f'[smoke] {res.rounds} decode steps: {step * 1e3:.2f} ms each for {args.layers} layers '
        f'(~{step * 48 / args.layers * 1e3:.1f} ms at 48); peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB',
    )


if __name__ == '__main__':
    main()
