# ruff: noqa: N803 N806 N812
"""
No-model-needed test. Builds a tiny random Qwen3.5 in HF layout, writes it to a GGUF the way llama.cpp's converter does
(name mapping, +1 norms, -exp(A_log), V-head tiling, conv squeeze), then checks that:

  * GGUFSource undoes every transform (loaded params == HF effective params)
  * the same weights written as Ollama tensor blobs (packed safetensors, MLX int8 affine) load to the same values
    through OllamaTensorSource
  * the per-token gated delta rule matches an independent chunked implementation
  * cached incremental decode == one-shot forward
  * tokenizer round-trips
"""
import json
import pathlib
import struct
import tempfile

import gguf
import numpy as np

from ..tokenizer import PRE_REGEX
from ..tokenizer import Tokenizer
from ..tokenizer import bytes_to_unicode
from ..weights import MT_JSON
from ..weights import MT_TENSOR
from ..weights import GGUFSource
from ..weights import OllamaModel
from ..weights import OllamaTensorSource
from ..weights import Qwen35Config


##


CFG = dict(
    vocab_size=320,
    hidden_size=64,
    num_layers=4,
    intermediate_size=128,
    rms_eps=1e-6,
    num_heads=4,
    num_kv_heads=2,
    head_dim=32,
    rope_theta=10000.0,
    rope_dim=8,
    num_k_heads=2,
    num_v_heads=4,
    head_k_dim=16,
    head_v_dim=16,
    conv_kernel=4,
    layer_types=[
        'linear',
        'linear',
        'linear',
        'full',
    ],
    num_mtp_layers=1,
)


def make_hf_params(cfg: Qwen35Config, seed=0):
    """HF checkpoint semantics: zero-centred norm weights, A_log, grouped V order, conv [C,1,K]."""

    rng = np.random.default_rng(seed)
    h, ff = cfg.hidden_size, cfg.intermediate_size
    n = lambda *s: (rng.standard_normal(s) * 0.05).astype(np.float32)  # type: ignore
    p = {
        'embed_tokens.weight': n(cfg.vocab_size, h),
        'norm.weight': n(h),
        'lm_head.weight': n(cfg.vocab_size, h),
    }
    for i, lt in enumerate(cfg.layer_types):
        q = f'layers.{i}.'
        p[q + 'input_layernorm.weight'] = n(h)
        p[q + 'post_attention_layernorm.weight'] = n(h)
        p[q + 'mlp.gate_proj.weight'] = n(ff, h)
        p[q + 'mlp.up_proj.weight'] = n(ff, h)
        p[q + 'mlp.down_proj.weight'] = n(h, ff)
        if lt == 'full':
            p[q + 'self_attn.q_proj.weight'] = n(cfg.num_heads * cfg.head_dim * 2, h)
            p[q + 'self_attn.k_proj.weight'] = n(cfg.num_kv_heads * cfg.head_dim, h)
            p[q + 'self_attn.v_proj.weight'] = n(cfg.num_kv_heads * cfg.head_dim, h)
            p[q + 'self_attn.o_proj.weight'] = n(h, cfg.num_heads * cfg.head_dim)
            p[q + 'self_attn.q_norm.weight'] = n(cfg.head_dim)
            p[q + 'self_attn.k_norm.weight'] = n(cfg.head_dim)
        else:
            p[q + 'linear_attn.in_proj_qkv.weight'] = n(cfg.conv_dim, h)
            p[q + 'linear_attn.in_proj_z.weight'] = n(cfg.value_dim, h)
            p[q + 'linear_attn.in_proj_b.weight'] = n(cfg.num_v_heads, h)
            p[q + 'linear_attn.in_proj_a.weight'] = n(cfg.num_v_heads, h)
            p[q + 'linear_attn.conv1d.weight'] = n(cfg.conv_dim, 1, cfg.conv_kernel)
            p[q + 'linear_attn.A_log'] = np.log(rng.uniform(1, 16, cfg.num_v_heads)).astype(np.float32)
            p[q + 'linear_attn.dt_bias'] = n(cfg.num_v_heads) + 1.0
            p[q + 'linear_attn.norm.weight'] = n(cfg.head_v_dim) + 1.0
            p[q + 'linear_attn.out_proj.weight'] = n(h, cfg.value_dim)
    if cfg.num_mtp_layers:
        # the draft head: stem + one full-attention block with the text geometry + final norm
        q = 'mtp.layers.0.'
        p['mtp.fc.weight'] = n(h, 2 * h)
        p['mtp.pre_fc_norm_embedding.weight'] = n(h)
        p['mtp.pre_fc_norm_hidden.weight'] = n(h)
        p['mtp.norm.weight'] = n(h)
        p[q + 'input_layernorm.weight'] = n(h)
        p[q + 'post_attention_layernorm.weight'] = n(h)
        p[q + 'mlp.gate_proj.weight'] = n(ff, h)
        p[q + 'mlp.up_proj.weight'] = n(ff, h)
        p[q + 'mlp.down_proj.weight'] = n(h, ff)
        p[q + 'self_attn.q_proj.weight'] = n(cfg.num_heads * cfg.head_dim * 2, h)
        p[q + 'self_attn.k_proj.weight'] = n(cfg.num_kv_heads * cfg.head_dim, h)
        p[q + 'self_attn.v_proj.weight'] = n(cfg.num_kv_heads * cfg.head_dim, h)
        p[q + 'self_attn.o_proj.weight'] = n(h, cfg.num_heads * cfg.head_dim)
        p[q + 'self_attn.q_norm.weight'] = n(cfg.head_dim)
        p[q + 'self_attn.k_norm.weight'] = n(cfg.head_dim)
    return p


def effective(hf: dict) -> dict:
    """What the model should see (canonical scheme)."""

    out = {}
    for k, v in hf.items():
        if k.endswith('A_log'):
            out[k[: -len('A_log')] + 'A'] = -np.exp(v)
        elif (k.endswith('norm.weight') and not k.endswith('linear_attn.norm.weight')) or 'pre_fc_norm' in k:
            out[k] = v + 1.0
        elif k.endswith('conv1d.weight'):
            out[k] = v[:, 0, :]
        else:
            out[k] = v
    return out


def tile_v_heads(
        x,
        axis,
        num_k,
        r,
        d,
):  # llama.cpp `_reorder_v_heads` (grouped -> tiled)
    if r == 1:
        return x
    shape = list(x.shape)
    axis %= x.ndim
    x = x.reshape([*shape[:axis], num_k, r, d, *shape[axis + 1:]])
    perm = list(range(x.ndim))
    perm[axis], perm[axis + 1] = perm[axis + 1], perm[axis]
    return np.ascontiguousarray(x.transpose(perm)).reshape(shape)


def tiny_tokenizer_fields():
    b2u = bytes_to_unicode()
    tokens = [b2u[b] for b in range(256)]
    tokens += ['<|endoftext|>', '<|im_start|>', '<|im_end|>']
    types = [gguf.TokenType.NORMAL] * 256 + [gguf.TokenType.CONTROL] * 3
    merges = []
    # a few merges: "he" "ll" "hell" "o " etc.
    for a, b in [
        ('h', 'e'),
        ('l', 'l'),
        ('he', 'll'),
        ('hell', 'o'),
        ('Ġ', 't'),
        ('Ġt', 'he'),
    ]:
        merges.append(f'{a} {b}')
        tokens.append(a + b)
        types.append(gguf.TokenType.NORMAL)
    return tokens, types, merges


def write_gguf(path, cfg: Qwen35Config, hf: dict, quantize=True, flavor='llamacpp'):
    """
    flavor: 'llamacpp' (conversion/qwen.py) or 'ollama' (convert_qwen3next.go) -- same layout transforms, but Ollama
    names the dt bias bare `ssm_dt`, writes a per-layer head_count_kv with zeros for recurrent blocks instead of
    `attention.recurrent_layers`, and records `ssm.v_head_reordered`.
    """

    w = gguf.GGUFWriter(str(path), 'qwen35')
    n_blocks = cfg.num_layers + cfg.num_mtp_layers
    w.add_block_count(n_blocks)
    if cfg.num_mtp_layers:
        w.add_uint32('qwen35.nextn_predict_layers', cfg.num_mtp_layers)
    w.add_embedding_length(cfg.hidden_size)
    w.add_feed_forward_length(cfg.intermediate_size)
    w.add_context_length(4096)
    w.add_head_count(cfg.num_heads)
    if flavor == 'ollama':
        w.add_head_count_kv(
            [cfg.num_kv_heads if t == 'full' else 0 for t in cfg.layer_types] + [cfg.num_kv_heads] * cfg.num_mtp_layers,
        )
    else:
        w.add_head_count_kv(cfg.num_kv_heads)
    w.add_key_length(cfg.head_dim)
    w.add_value_length(cfg.head_dim)
    w.add_layer_norm_rms_eps(cfg.rms_eps)
    w.add_rope_dimension_count(cfg.rope_dim)
    w.add_rope_freq_base(cfg.rope_theta)
    w.add_array('qwen35.rope.dimension_sections', [11, 11, 10, 0])
    w.add_ssm_conv_kernel(cfg.conv_kernel)
    w.add_ssm_state_size(cfg.head_k_dim)
    w.add_ssm_group_count(cfg.num_k_heads)
    w.add_ssm_time_step_rank(cfg.num_v_heads)
    w.add_ssm_inner_size(cfg.value_dim)
    if flavor == 'ollama':
        w.add_bool('qwen35.ssm.v_head_reordered', True)
    else:
        w.add_array(
            'qwen35.attention.recurrent_layers',
            [t == 'linear' for t in cfg.layer_types] + [False] * cfg.num_mtp_layers,
        )
    w.add_uint32('qwen35.full_attention_interval', 4)
    w.add_vocab_size(cfg.vocab_size)
    tokens, types, merges = tiny_tokenizer_fields()
    assert len(tokens) <= cfg.vocab_size
    tokens += [f'[PAD{i}]' for i in range(cfg.vocab_size - len(tokens))]
    types += [gguf.TokenType.UNUSED] * (cfg.vocab_size - len(types))
    w.add_tokenizer_model('gpt2')
    w.add_tokenizer_pre('qwen35')
    w.add_token_list(tokens)
    w.add_token_types(types)
    w.add_token_merges(merges)
    w.add_eos_token_id(256)
    w.add_add_bos_token(False)

    r = cfg.num_v_heads // cfg.num_k_heads
    nk = cfg.num_k_heads
    dv = cfg.head_v_dim
    qk = 2 * cfg.key_dim

    def name(k):  # HF canonical -> GGUF
        if k == 'embed_tokens.weight':
            return 'token_embd.weight'
        if k == 'norm.weight':
            return 'output_norm.weight'
        if k == 'lm_head.weight':
            return 'output.weight'
        if k.startswith('mtp.'):  # conversion/qwen.py: mtp.* -> layer n_layer, stem under nextn.*
            i = str(cfg.num_layers)
            stem = {
                'mtp.fc.weight': 'nextn.eh_proj.weight',
                'mtp.pre_fc_norm_embedding.weight': 'nextn.enorm.weight',
                'mtp.pre_fc_norm_hidden.weight': 'nextn.hnorm.weight',
                'mtp.norm.weight': 'nextn.shared_head_norm.weight',
            }
            if k in stem:
                return f'blk.{i}.{stem[k]}'
            rest = k.split('.', 3)[3]
        else:
            i, rest = k.split('.', 2)[1:]
        m = {
            'input_layernorm.weight': 'attn_norm.weight',
            'post_attention_layernorm.weight': 'post_attention_norm.weight',
            'mlp.gate_proj.weight': 'ffn_gate.weight',
            'mlp.up_proj.weight': 'ffn_up.weight',
            'mlp.down_proj.weight': 'ffn_down.weight',
            'self_attn.q_proj.weight': 'attn_q.weight',
            'self_attn.k_proj.weight': 'attn_k.weight',
            'self_attn.v_proj.weight': 'attn_v.weight',
            'self_attn.o_proj.weight': 'attn_output.weight',
            'self_attn.q_norm.weight': 'attn_q_norm.weight',
            'self_attn.k_norm.weight': 'attn_k_norm.weight',
            'linear_attn.in_proj_qkv.weight': 'attn_qkv.weight',
            'linear_attn.in_proj_z.weight': 'attn_gate.weight',
            'linear_attn.in_proj_b.weight': 'ssm_beta.weight',
            'linear_attn.in_proj_a.weight': 'ssm_alpha.weight',
            'linear_attn.conv1d.weight': 'ssm_conv1d.weight',
            'linear_attn.A_log': 'ssm_a',
            'linear_attn.dt_bias': 'ssm_dt' if flavor == 'ollama' else 'ssm_dt.bias',
            'linear_attn.norm.weight': 'ssm_norm.weight',
            'linear_attn.out_proj.weight': 'ssm_out.weight',
        }
        return f'blk.{i}.{m[rest]}'

    for k, v in hf.items():
        d = v.astype(np.float32)
        # replicate conversion/qwen.py transforms
        if k.endswith('A_log'):
            d = -np.exp(d)
        elif (k.endswith('norm.weight') and not k.endswith('linear_attn.norm.weight')) or 'pre_fc_norm' in k:
            d = d + 1  # (the converter renames pre_fc_norm_* to enorm/hnorm before its *norm.weight rule)
        elif 'conv1d' in k:
            d = d.squeeze()
        if 'linear_attn.' in k and r > 1:
            if 'in_proj_qkv' in k:
                d = np.concatenate([d[:qk], tile_v_heads(d[qk:], 0, nk, r, dv)], 0)
            elif 'in_proj_z' in k:
                d = tile_v_heads(d, 0, nk, r, dv)
            elif 'in_proj_b' in k or 'in_proj_a' in k:
                d = tile_v_heads(d, 0, nk, r, 1)
            elif 'A_log' in k or 'dt_bias' in k:
                d = tile_v_heads(d.reshape(-1, 1), 0, nk, r, 1).reshape(d.shape)
            elif 'conv1d' in k:
                d = np.concatenate([d[:qk], tile_v_heads(d[qk:], 0, nk, r, dv)], 0)
            elif 'out_proj' in k:
                d = tile_v_heads(d, 1, nk, r, dv)
        gname = name(k)
        d = np.ascontiguousarray(d)
        if quantize and d.ndim == 2 and d.shape[1] % 32 == 0 and 'norm' not in gname:
            qt = (
                gguf.GGMLQuantizationType.Q8_0
                if d.shape[0] % 2 else
                gguf.GGMLQuantizationType.Q4_K
            )
            if qt == gguf.GGMLQuantizationType.Q4_K and d.shape[1] % 256 != 0:
                qt = gguf.GGMLQuantizationType.Q8_0
            w.add_tensor(gname, gguf.quants.quantize(d, qt), raw_dtype=qt)
        else:
            w.add_tensor(gname, d)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()


##
# Ollama tensor-blob writer


def mlx_affine_quant(w: np.ndarray, bits=8, group=64):
    per_word = 32 // bits
    rows, cols = w.shape
    g = w.reshape(rows, cols // group, group)
    lo = g.min(-1, keepdims=True)
    hi = g.max(-1, keepdims=True)
    scale = (hi - lo) / (2**bits - 1)
    scale = np.where(scale == 0, 1e-8, scale)
    q = (
        np.clip(np.round((g - lo) / scale), 0, 2**bits - 1)
        .astype(np.uint32)
        .reshape(rows, cols)
    )
    packed = np.zeros((rows, cols // per_word), dtype=np.uint32)
    for j in range(per_word):
        packed |= q[:, j::per_word] << (bits * j)
    return packed, scale[..., 0].astype(np.float32), lo[..., 0].astype(np.float32)


def write_safetensors(path, tensors: dict, metadata: dict | None = None):
    header, blobs, off = {}, [], 0
    for n, a in tensors.items():
        a = np.ascontiguousarray(a)
        dt = {np.dtype('float32'): 'F32', np.dtype('uint32'): 'U32'}[a.dtype]
        header[n] = {
            'dtype': dt,
            'shape': list(a.shape),
            'data_offsets': [off, off + a.nbytes],
        }
        blobs.append(a.tobytes())
        off += a.nbytes
    if metadata:
        header['__metadata__'] = metadata
    hb = json.dumps(header).encode()
    with open(path, 'wb') as f:
        f.write(struct.pack('<Q', len(hb)))
        f.write(hb)
        for b in blobs:
            f.write(b)


def write_ollama_tensor_model(root: pathlib.Path, cfg: Qwen35Config, hf: dict):
    (root / 'blobs').mkdir(parents=True)
    layers = []
    n = 0
    for k, v in hf.items():
        hf_name = 'model.language_model.' + k if k != 'lm_head.weight' and not k.startswith('mtp.') else k
        digest = f'sha256:{n:064x}'
        n += 1
        p = root / 'blobs' / digest.replace(':', '-')
        if (
                v.ndim == 2 and
                v.shape[1] % 64 == 0 and
                'norm' not in k and
                'embed' not in k
        ):
            packed, s, b = mlx_affine_quant(v, 8, 64)
            write_safetensors(
                p,
                {
                    hf_name: packed,
                    hf_name + '.scale': s,
                    hf_name + '.bias': b,
                },
                {
                    'quant_type': 'int8',
                    'group_size': '64',
                },
            )
        else:
            write_safetensors(p, {hf_name: v})
        layers.append({
            'mediaType': MT_TENSOR,
            'digest': digest,
            'size': p.stat().st_size,
            'name': hf_name,
        })
    hfcfg = {
        'architectures': ['Qwen3_5ForConditionalGeneration'],
        'model_type': 'qwen3_5',
        'text_config': {
            'vocab_size': cfg.vocab_size,
            'hidden_size': cfg.hidden_size,
            'num_hidden_layers': cfg.num_layers,
            'intermediate_size': cfg.intermediate_size,
            'rms_norm_eps': cfg.rms_eps,
            'num_attention_heads': cfg.num_heads,
            'num_key_value_heads': cfg.num_kv_heads,
            'head_dim': cfg.head_dim,
            'rope_parameters': {
                'rope_theta': cfg.rope_theta,
                'partial_rotary_factor': 0.25,
                'mrope_section': [11, 11, 10],
                'rope_type': 'default',
            },
            'linear_num_key_heads': cfg.num_k_heads,
            'linear_num_value_heads': cfg.num_v_heads,
            'linear_key_head_dim': cfg.head_k_dim,
            'linear_value_head_dim': cfg.head_v_dim,
            'linear_conv_kernel_dim': cfg.conv_kernel,
            'full_attention_interval': 4,
            'layer_types': [
                'linear_attention' if t == 'linear' else 'full_attention'
                for t in cfg.layer_types
            ],
            'tie_word_embeddings': False,
            'mtp_num_hidden_layers': cfg.num_mtp_layers,
        },
    }
    tokens, types, merges = tiny_tokenizer_fields()
    tj = {
        'model': {
            'type': 'BPE',
            'vocab': {
                t: i for i, t in enumerate(tokens) if types[i] != gguf.TokenType.CONTROL
            },
            'merges': merges,
        },
        'added_tokens': [
            {'id': i, 'content': t, 'special': True}
            for i, t in enumerate(tokens)
            if types[i] == gguf.TokenType.CONTROL
        ],
        'pre_tokenizer': {
            'pretokenizers': [
                {
                    'type': 'Split',
                    'pattern': {
                        'Regex': PRE_REGEX[
                            'qwen35'
                        ],
                    },
                },
            ],
        },
    }
    for fname, obj in [('config.json', hfcfg), ('tokenizer.json', tj)]:
        digest = f'sha256:{n:064x}'
        n += 1
        p = root / 'blobs' / digest.replace(':', '-')
        p.write_text(json.dumps(obj))
        layers.append({
            'mediaType': MT_JSON,
            'digest': digest,
            'size': p.stat().st_size,
            'name': fname,
        })
    manifest = {'schemaVersion': 2, 'layers': layers}
    mp = root / 'manifests' / 'registry.ollama.ai' / 'library' / 'tiny' / 'latest'
    mp.parent.mkdir(parents=True)
    mp.write_text(json.dumps(manifest))
    return OllamaModel(mp, manifest, root / 'blobs')


##
# independent chunked GDN


def chunk_gated_delta_rule_ref(q, k, v, g, beta, chunk_size=4):
    """
    Chunkwise (WY-representation) gated delta rule, written independently of the recurrent loop in model.py, following
    Yang et al. 2024 (as in FLA / HF `torch_chunk_gated_delta_rule`). q,k: [B,H,T,dk] (l2-normed, q scaled), v:
    [B,H,T,dv], g,beta: [B,H,T]. Returns [B,H,T,dv].
    """

    import torch

    B, H, T, dk = q.shape
    dv = v.shape[-1]
    C = chunk_size
    pad = (C - T % C) % C
    if pad:
        q, k, v = [torch.nn.functional.pad(x, (0, 0, 0, pad)) for x in (q, k, v)]
        g, beta = [torch.nn.functional.pad(x, (0, pad)) for x in (g, beta)]
    L = T + pad
    n = L // C
    q, k, v = [x.reshape(B, H, n, C, -1) for x in (q, k, v)]
    g, beta = [x.reshape(B, H, n, C) for x in (g, beta)]
    gcum = g.cumsum(-1)  # [B,H,n,C]
    kb = k * beta[..., None]
    vb = v * beta[..., None]
    # A = tril(kb k^T * exp(gcum_i - gcum_j)), strictly lower
    decay = (gcum[..., :, None] - gcum[..., None, :]).exp()  # [B,H,n,C,C]
    mask = torch.tril(torch.ones(C, C, dtype=torch.bool, device=q.device), -1)
    A = (kb @ k.transpose(-1, -2)) * decay
    A = A.masked_fill(~mask, 0)
    # T = (I + A)^-1 (lower unitriangular), solve via forward substitution
    I = torch.eye(C, device=q.device, dtype=q.dtype).expand_as(A)
    Tm = torch.linalg.solve_triangular(I + A, I, upper=False)
    W = Tm @ (kb * gcum.exp()[..., None])  # [B,H,n,C,dk]
    U = Tm @ vb  # [B,H,n,C,dv]
    S = torch.zeros(B, H, dk, dv, dtype=q.dtype, device=q.device)
    out = torch.zeros(B, H, n, C, dv, dtype=q.dtype, device=q.device)
    for i in range(n):
        qi, ki = q[:, :, i], k[:, :, i]
        gi = gcum[:, :, i]  # [B,H,C]
        u = U[:, :, i] - W[:, :, i] @ S  # [B,H,C,dv]  v - k S (decayed)
        intra = (qi @ ki.transpose(-1, -2)) * (
            gi[..., :, None] - gi[..., None, :]
        ).exp()
        intra = intra.masked_fill(
            ~torch.tril(torch.ones(C, C, dtype=torch.bool, device=q.device)), 0,
        )
        out[:, :, i] = (qi * gi.exp()[..., None]) @ S + intra @ u
        S = (
            S * gi[..., -1, None, None].exp()
            + (ki * (gi[..., -1, None] - gi).exp()[..., None]).transpose(-1, -2) @ u
        )
    return out.reshape(B, H, L, dv)[:, :, :T]


##
# tests


def test_gguf_roundtrip(tmp_path):
    _test_gguf_roundtrip(tmp_path)


def _test_gguf_roundtrip(tmp_path=None):
    tmp_path = pathlib.Path(tmp_path or tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    eff = effective(hf)
    write_gguf(tmp_path / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp_path / 'tiny.gguf')
    assert src.config.layer_types == cfg.layer_types
    assert (
        src.config.num_v_heads == 4
        and src.config.num_k_heads == 2
        and src.config.rope_dim == 8
    )
    assert set(src.names()) == set(eff.keys()), set(src.names()) ^ set(eff.keys())
    for k in eff:
        got = src.get(k)
        assert got.shape == eff[k].shape, (k, got.shape, eff[k].shape)
        np.testing.assert_allclose(got, eff[k], rtol=1e-6, atol=1e-6, err_msg=k)
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    ids = tok.encode('hello the<|im_end|>')
    assert tok.decode(ids) == 'hello the<|im_end|>'
    assert ids[-1] == 258  # <|im_end|>
    # quantized variant loads too
    write_gguf(tmp_path / 'tiny_q.gguf', cfg, hf, quantize=True)
    srcq = GGUFSource(tmp_path / 'tiny_q.gguf')
    for k in eff:
        got = srcq.get(k)
        err = np.abs(got - eff[k]).max()
        assert err < 0.02, (k, err)
    # Ollama's converter flavour (bare ssm_dt, per-layer head_count_kv, v_head_reordered flag) loads identically
    write_gguf(tmp_path / 'tiny_ollama.gguf', cfg, hf, quantize=False, flavor='ollama')
    srco = GGUFSource(tmp_path / 'tiny_ollama.gguf')
    assert srco.config.layer_types == cfg.layer_types and srco.v_heads_tiled
    assert set(srco.names()) == set(eff.keys())
    for k in eff:
        np.testing.assert_allclose(srco.get(k), eff[k], rtol=1e-6, atol=1e-6, err_msg=k)
    print('gguf roundtrip OK')
    return cfg, hf, eff, src


def test_ollama_tensor_blobs(tmp_path):
    _test_ollama_tensor_blobs(tmp_path)


def _test_ollama_tensor_blobs(tmp_path=None):
    tmp_path = pathlib.Path(tmp_path or tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    eff = effective(hf)
    om = write_ollama_tensor_model(tmp_path / 'ollama', cfg, hf)
    src = OllamaTensorSource(om)
    assert src.config.layer_types == cfg.layer_types
    assert src.config.rope_dim == 8
    assert set(src.names()) == set(eff.keys()), set(src.names()) ^ set(eff.keys())
    for k in eff:
        got = src.get(k)
        assert got.shape == eff[k].shape, (k, got.shape, eff[k].shape)
        err = np.abs(got - eff[k]).max()
        assert err < 2e-3, (k, err)
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    assert tok.encode('hello<|im_end|>')[-1] == 258
    print('ollama tensor blobs OK')


def test_model():
    try:
        import torch
    except ImportError:
        print('torch not installed; skipping model tests')
        return

    from ..backends.torch import TorchOps
    from ..model import Cache
    from ..model import Qwen35

    cfg, hf, eff, src = _test_gguf_roundtrip()
    ops = TorchOps('cpu')
    torch.manual_seed(0)
    # recurrent vs independent chunked implementation
    B = 2
    H = 4
    T = 11
    d = 16
    q = torch.nn.functional.normalize(torch.randn(B, H, T, d), dim=-1) / d**0.5
    k = torch.nn.functional.normalize(torch.randn(B, H, T, d), dim=-1)
    v = torch.randn(B, H, T, d)
    g = -torch.rand(B, H, T) * 2
    beta = torch.rand(B, H, T)
    o_rec, _ = ops.gated_delta(q, k, v, g, beta, torch.zeros(B, H, d, d))
    o_chk = chunk_gated_delta_rule_ref(q.double(), k.double(), v.double(), g.double(), beta.double())
    err = (o_rec.double() - o_chk).abs().max().item()
    assert err < 1e-4, err
    print(f'recurrent vs chunked GDN OK (max err {err:.2e})')

    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
    ids = np.random.default_rng(0).integers(0, 256, (1, 9))
    full = ops.numpy(model.forward(ids))
    assert full.shape == (1, 9, cfg.vocab_size) and np.isfinite(full).all()
    # incremental with cache must match the one-shot forward
    cache = Cache(cfg)
    step = [ops.numpy(model.forward(ids[:, :3], cache))]
    for t in range(3, 9):
        step.append(ops.numpy(model.forward(ids[:, t:t + 1], cache)))
    inc = np.concatenate(step, axis=1)
    err = np.abs(inc - full).max()
    assert err < 1e-4, err
    # snapshot / prefix reuse
    cache2 = Cache(cfg)
    model.forward(ids[:, :5], cache2)
    snap = cache2.snapshot(ops)
    a = ops.numpy(model.forward(ids[:, 5:], cache2))
    b = ops.numpy(model.forward(ids[:, 5:], snap))
    assert np.abs(a - b).max() < 1e-6
    gen = model.generate(ids[0].tolist(), max_new_tokens=5)
    assert len(gen) == 5
    print(f'model forward / cache / generate OK (incremental vs full max err {err:.2e})')
