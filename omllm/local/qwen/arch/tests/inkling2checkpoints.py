# ruff: noqa: N803 N806
"""
Synthetic Inkling 2 checkpoints for the tests: random weights in the layout of the released one -- its tensor names,
its experts packed as NVFP4 (and MXFP8 in the last layers) with their scales beside them -- at toy widths, written
with numpy alone. The config is the flat form the reference library writes for a text model; the released nested
form is `RELEASED_CONFIG` (test_inkling2.py parses it).

The same seed writes the same bytes, which is what lets reference logits be kept beside the tests (see
test_inkling2.py: `REFERENCE`).
"""
import json
import os.path
import struct
import typing as ta

import numpy as np

from ...tokenizer import PRE_REGEX
from ...tokenizer import bytes_to_unicode


##


def inkling2_test_config(**overrides: ta.Any) -> dict[str, ta.Any]:
    """
    A small text config: 8 layers in blocks of 2 (the second of each global), layers 2..5 looped 3 times -- 16 visits
    -- over a window of 6 and a relative extent of 5, with the log scaling starting at position 12.
    """

    cfg: dict[str, ta.Any] = dict(
        model_type='inkling2_loop_text',
        vocab_size=320,
        unpadded_vocab_size=300,
        hidden_size=64,
        num_hidden_layers=8,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=16,
        swa_num_attention_heads=4,
        swa_num_key_value_heads=2,
        swa_head_dim=16,
        sliding_window_size=6,
        d_rel=4,
        rel_extent=5,
        log_scaling_n_floor=12,
        log_scaling_alpha=0.1,
        layer_types=['hybrid_sliding', 'hybrid'] * 4,
        max_position_embeddings=4096,
        rms_norm_eps=1e-6,
        conv_kernel_size=4,
        moe_intermediate_size=32,
        n_routed_experts=8,
        num_experts_per_tok=2,
        route_scale=8.0,
        qk_l2_clip_threshold=22.627416997969522,
        rel_l2_clip_threshold=8.0,
        n_layers_per_attn_res_block=2,
        mlp_gate_softcap=4.0,
        mlp_up_softcap=25.0,
        final_logit_softcapping=30.0,
        scoring_func='sigmoid',
        loop_layer_index_start=2,
        loop_layer_index_end=6,
        loop_num_passes=3,
        loop_gate_rank=8,
        eos_token_id=266,  # (the test tokenizer's <|content_model_end_sampling|>)
    )
    cfg.update(overrides)
    return cfg


# the released checkpoint's config.json, text part (public metadata), for the parser's other spelling of the keys
RELEASED_CONFIG: ta.Mapping[str, ta.Any] = {
    'model_type': 'inkling2_loop',
    'eos_token_id': 200006,
    'text_config': {
        'model_type': 'inkling2_loop_text',
        'model_max_length': 1048576,
        'hidden_size': 2304,
        'num_hidden_layers': 24,
        'vocab_size': 201024,
        'num_attention_heads': 24,
        'num_key_value_heads': 8,
        'head_dim': 128,
        'd_rel': 16,
        'rel_extent': 1024,
        'log_scaling_n_floor': 8192,
        'log_scaling_alpha': 0.1,
        'rms_norm_eps': 1e-06,
        'qk_l2_clip_threshold': 22.627416997969522,
        'rel_l2_clip_threshold': 8.0,
        'local_layer_ids': [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22],
        'sconv_kernel_size': 4,
        'unpadded_vocab_size': 200058,
        'final_logit_softcapping': 30.0,
        'swa_head_dim': 128,
        'swa_num_attention_heads': 24,
        'swa_num_key_value_heads': 8,
        'sliding_window_size': 1024,
        'n_layers_per_attn_res_block': 6,
        'n_routed_experts': 128,
        'num_experts_per_tok': 8,
        'n_shared_experts': 0,
        'intermediate_size': 1152,
        'mlp_gate_softcap': 4.0,
        'mlp_up_softcap': 25.0,
        'route_scale': 8.0,
        'loop_config': {'core_start': 6, 'core_end': 18, 'num_passes': 3, 'gate_rank': 64, 'is_varloop': False},
    },
}


# the protocol's special tokens (serve/inkling2.py), in the order the test tokenizer gives them ids after the bytes
TEST_SPECIAL_TOKENS = (
    '<|endoftext|>',
    '<|message_user|>',
    '<|message_model|>',
    '<|message_system|>',
    '<|message_tool|>',
    '<|content_text|>',
    '<|content_model_end_sampling|>',
    '<|content_thinking|>',
    '<|end_message|>',
    '<|content_xml|>',
    '<|content_invoke_tool_json|>',
)


def inkling2_tokenizer_json(vocab_size: int = 300) -> dict[str, ta.Any]:
    """
    A tokenizer.json for the synthetic checkpoints: the 256 bytes, a few merges, and the chat protocol's special
    tokens after them, padded with unused ones to `vocab_size` ids -- the released tokenizer's shape (its split
    pattern, `ignore_merges`) at toy size.
    """

    b2u = bytes_to_unicode()
    vocab = {b2u[i]: i for i in range(256)}
    merges = [('t', 'h'), ('th', 'e'), ('i', 'n'), (b2u[ord(' ')], 'the')]
    for a, b in merges:
        vocab[a + b] = len(vocab)

    specials = [*TEST_SPECIAL_TOKENS]
    specials += [f'<|unused_{i}|>' for i in range(len(vocab) + len(specials), vocab_size)]

    return {
        'model': {
            'type': 'BPE',
            'vocab': vocab,
            'merges': [f'{a} {b}' for a, b in merges],
            'ignore_merges': True,
        },
        'added_tokens': [
            {'id': len(vocab) + i, 'content': t, 'special': True}
            for i, t in enumerate(specials)
        ],
        'pre_tokenizer': {
            'type': 'Sequence',
            'pretokenizers': [
                {'type': 'Split', 'pattern': {'Regex': PRE_REGEX['inkling2']}, 'behavior': 'Isolated', 'invert': False},
                {'type': 'ByteLevel', 'add_prefix_space': False, 'trim_offsets': True, 'use_regex': False},
            ],
        },
    }


def write_safetensors(path: str, tensors: ta.Mapping[str, tuple[str, np.ndarray]]) -> None:
    """name -> (safetensors dtype, array): 'F32' float32, 'BF16' uint16 bit patterns, 'U8' / 'F8_E4M3' uint8 bytes."""

    header: dict[str, ta.Any] = {}
    blobs = []
    off = 0
    for name, (dtype, arr) in tensors.items():
        arr = np.ascontiguousarray(arr)
        header[name] = {'dtype': dtype, 'shape': list(arr.shape), 'data_offsets': [off, off + arr.nbytes]}
        blobs.append(arr.tobytes())
        off += arr.nbytes

    hb = json.dumps(header).encode()
    with open(path, 'wb') as f:
        f.write(struct.pack('<Q', len(hb)))
        f.write(hb)
        for b in blobs:
            f.write(b)


def _nvfp4_tensors(rng: np.random.Generator, E: int, N: int, K: int) -> dict[str, tuple[str, np.ndarray]]:
    """Random NVFP4 experts [E, N, K]: every code, scales between 1/4 and 4, an outer factor near 1/40 per expert."""

    exp = rng.integers(5, 9, (E, N, K // 16), dtype=np.uint8)
    man = rng.integers(0, 8, (E, N, K // 16), dtype=np.uint8)
    return {
        '': ('U8', rng.integers(0, 256, (E, N, K // 2), dtype=np.uint8)),
        '_scale': ('F8_E4M3', (exp << 3) | man),
        '_amax': ('F32', rng.uniform(0.5, 1.5, E).astype(np.float32)),
        '_outer_scale_denominator': ('F32', np.asarray([40.0], dtype=np.float32)),
    }


def _mxfp8_tensors(rng: np.random.Generator, E: int, N: int, K: int) -> dict[str, tuple[str, np.ndarray]]:
    """Random MXFP8 experts [E, N, K]: codes of either sign between 1/16 and 4, block scales 2 ** -5 .. 2 ** -3."""

    sign = rng.integers(0, 2, (E, N, K), dtype=np.uint8)
    exp = rng.integers(3, 9, (E, N, K), dtype=np.uint8)
    man = rng.integers(0, 8, (E, N, K), dtype=np.uint8)
    return {
        '': ('F8_E4M3', (sign << 7) | (exp << 3) | man),
        '_scale': ('U8', rng.integers(122, 125, (E, N, K // 32), dtype=np.uint8)),
    }


def write_inkling2_checkpoint(
        path: str,
        cfg: ta.Mapping[str, ta.Any] | None = None,
        *,
        seed: int = 0,
        mxfp8_layers: int = 2,
        dense_experts: bool = False,
) -> dict[str, ta.Any]:
    """
    A checkpoint directory at `path` for `cfg` (`inkling2_test_config()` by default): config.json, tokenizer.json and
    model.safetensors. The last `mxfp8_layers` layers' experts are MXFP8, the others' NVFP4 -- or, with
    `dense_experts`, all float32 as the reference library writes them. Returns the config.
    """

    cfg = dict(cfg if cfg is not None else inkling2_test_config())
    rng = np.random.default_rng(seed)

    D = cfg['hidden_size']
    L = cfg['num_hidden_layers']
    H, KV, HD = cfg['num_attention_heads'], cfg['num_key_value_heads'], cfg['head_dim']
    R, X, W = cfg['d_rel'], cfg['rel_extent'], cfg['sliding_window_size']
    K = cfg['conv_kernel_size']
    E, I = cfg['n_routed_experts'], cfg['moe_intermediate_size']  # noqa: E741
    G = cfg['loop_gate_rank']
    loop = range(cfg['loop_layer_index_start'], cfg['loop_layer_index_end'])

    def n(*shape: int, scale: float = 0.1) -> tuple[str, np.ndarray]:
        return 'F32', (rng.standard_normal(shape) * scale).astype(np.float32)

    def gamma(*shape: int) -> tuple[str, np.ndarray]:
        return 'F32', (1 + rng.standard_normal(shape) * 0.1).astype(np.float32)

    t: dict[str, tuple[str, np.ndarray]] = {}
    P = 'model.llm.'

    t[P + 'embed.weight'] = n(cfg['vocab_size'], D, scale=1.0)
    t[P + 'embed_norm.weight'] = gamma(D)
    t[P + 'norm.weight'] = gamma(D)
    t[P + 'unembed.weight'] = n(cfg['vocab_size'], D, scale=0.5)
    t[P + 'attn_res.output_query'] = n(D, scale=1.0)
    t[P + 'middle_cycle_cross_pass_queries'] = n(2 * len(loop), D, scale=1.0)
    t[P + 'middle_cycle_cross_pass_kv_queries'] = n(2 * len(loop), D, scale=1.0)

    for i in range(L):
        q = P + f'layers.{i}.'
        local = cfg['layer_types'][i] == 'hybrid_sliding'

        t[q + 'attn.wq_du.weight'] = n(H * HD, D)
        t[q + 'attn.wk_dv.weight'] = n(KV * HD, D)
        t[q + 'attn.wv_dv.weight'] = n(KV * HD, D)
        t[q + 'attn.wr_du.weight'] = n(H * R, D)
        t[q + 'attn.wo_ud.weight'] = n(D, H * HD)
        t[q + 'attn.attn_sink_proj.weight'] = n(H, D)
        t[q + 'attn.gate_attn.weight'] = n(H * HD, D)
        t[q + 'attn.q_l2_clip.scale'] = ('F32', (3 + rng.standard_normal((H, HD))).astype(np.float32))
        t[q + 'attn.rel_l2_clip.scale'] = ('F32', (3 + rng.standard_normal((H, R))).astype(np.float32))
        # (a local layer's relative table spans its window; a global layer's, the config's extent)
        t[q + 'attn.rel_logits_proj.proj'] = n(R, W if local else X, scale=1.0)

        for c in ('k_sconv', 'v_sconv'):
            if local:
                t[q + f'attn.{c}.weight'] = n(KV * HD, 1, K, scale=0.5)
            else:
                t[q + f'attn.{c}.static_w'] = n(K, KV * HD, scale=0.5)
                t[q + f'attn.{c}.weight_proj'] = n(KV * K, D)
        t[q + 'attn_sconv.weight'] = n(D, 1, K, scale=0.5)
        t[q + 'mlp_sconv.weight'] = n(D, 1, K, scale=0.5)

        if local:
            t[q + 'attn_norm.weight'] = gamma(D)
        else:
            for c in ('q', 'k', 'v'):
                t[q + f'{c}_input_norm.weight'] = gamma(D)
        t[q + 'mlp_norm.weight'] = gamma(D)

        if i:
            t[P + f'attn_res.attn_queries.{i - 1}'] = n(D, scale=1.0) if local else n(3, D, scale=1.0)
        t[P + f'attn_res.mlp_queries.{i}'] = n(D, scale=1.0)

        t[q + 'mlp.gate.weight'] = n(E, D, scale=0.3)
        t[q + 'mlp.gate.bias'] = n(E, scale=0.2)
        for name, (N_, K_) in (('w13_weight', (2 * I, D)), ('w2_weight', (D, I))):
            if dense_experts:
                parts = {'': n(E, N_, K_)}
            elif i >= L - mxfp8_layers:
                parts = _mxfp8_tensors(rng, E, N_, K_)
            else:
                parts = _nvfp4_tensors(rng, E, N_, K_)
            for suffix, v in parts.items():
                t[q + 'mlp.experts.' + name + suffix] = v

        if i in loop:
            for c in ('attn', 'k', 'v', 'mlp'):
                t[q + f'controllers.{c}.down_weight'] = n(G, 2 * D)
                t[q + f'controllers.{c}.forget_weight'] = n(D, G, scale=0.5)
                t[q + f'controllers.{c}.gain_weight'] = n(D, G, scale=0.5)

    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, 'config.json'), 'w') as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(path, 'tokenizer.json'), 'w') as f:
        json.dump(inkling2_tokenizer_json(cfg['unpadded_vocab_size']), f)
    write_safetensors(os.path.join(path, 'model.safetensors'), t)

    return cfg
