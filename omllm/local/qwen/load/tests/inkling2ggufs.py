# ruff: noqa: N803 N806
"""
Synthetic Inkling 2 GGUFs for the tests: a synthetic checkpoint (arch/tests/inkling2checkpoints.py) converted the way
llama.cpp's converter converts the released one -- its metadata keys, its tensor names, the layouts it changes --
and written with the `gguf` package's writer. The conversion starts from the checkpoint's raw tensors, not from a
source's canonical ones, so what the GGUF source undoes is not what wrote the file.

The experts are written as the released GGUFs have them: a checkpoint's NVFP4 tensors as GGML NVFP4, their bytes
regrouped and each expert's factor in a `.scale` tensor beside them; its MXFP8 tensors, for which a GGUF has no type,
decoded and stored as `expert_type` (BF16 holds them exactly).
"""
import json
import os.path
import typing as ta

import gguf
import numpy as np

from ...ops.microscaled import MicroscaledWeight
from ..gguf.constants import GGMLQuantizationType
from ..gguf.quants import quantize
from ..weights import SafetensorsFile


##


ARCHITECTURE = 'inkling2_loop'

# the tensors a smaller file quantizes (`dense_type`): the tables and the attention's projections
QUANTIZED = (
    'token_embd.weight',
    'output.weight',
    'attn_q.weight',
    'attn_k.weight',
    'attn_v.weight',
    'attn_output.weight',
    'attn_gate.weight',
    'attn_rel.weight',
)

# the released GGUFs' metadata below `inkling2_loop.` (public), as a reader gives it: floats as float32 holds them
RELEASED_GGUF_METADATA: ta.Mapping[str, ta.Any] = {
    'block_count': 24,
    'context_length': 1048576,
    'embedding_length': 2304,
    'feed_forward_length': 1152,
    'attention.head_count': [24] * 24,
    'attention.head_count_kv': [8] * 24,
    'attention.layer_norm_rms_epsilon': 9.999999974752427e-07,
    'expert_count': 128,
    'expert_used_count': 8,
    'attention.key_length': 128,
    'attention.value_length': 128,
    'loop.count': 3,
    'loop.start': 6,
    'loop.end': 18,
    'loop.gate_rank': 64,
    'vocab_size': 201024,
    'vocab_size_unpadded': 200058,
    'expert_feed_forward_length': 1152,
    'attention.key_length_swa': 128,
    'attention.value_length_swa': 128,
    'rope.dimension_count': 0,
    'attention.sliding_window': 1024,
    'attention.sliding_window_pattern': [i % 6 != 5 for i in range(24)],
    'shortconv.l_cache': 4,
    'expert_weights_scale': 8.0,
    'activation.situ_beta': 4.0,
    'activation.situ_linear_beta': 25.0,
    'attn_res.block_size': 6,
    'final_logit_softcapping': 30.0,
    'attention.relative_length': 16,
    'attention.relative_extent': 1024,
    'attention.qk_clip': 22.627416610717773,
    'attention.relative_clip': 8.0,
    'attention.log_scale_floor': 8192,
    'attention.log_scale_alpha': 0.10000000149011612,
    'loop.varying': False,
}


def inkling2_gguf_metadata(cfg: ta.Mapping[str, ta.Any]) -> dict[str, tuple[str, ta.Any]]:
    """
    The architecture's keys (below `inkling2_loop.`) for a flat text config, each with the GGUF type the released
    files keep it as: 'u32', 'f32', 'bool', or 'array'.
    """

    L = cfg['num_hidden_layers']

    return {
        'block_count': ('u32', L),
        'context_length': ('u32', cfg['max_position_embeddings']),
        'embedding_length': ('u32', cfg['hidden_size']),
        'feed_forward_length': ('u32', cfg['moe_intermediate_size']),
        'attention.head_count': ('array', [cfg['num_attention_heads']] * L),
        'attention.head_count_kv': ('array', [cfg['num_key_value_heads']] * L),
        'attention.layer_norm_rms_epsilon': ('f32', cfg['rms_norm_eps']),
        'expert_count': ('u32', cfg['n_routed_experts']),
        'expert_used_count': ('u32', cfg['num_experts_per_tok']),
        'attention.key_length': ('u32', cfg['head_dim']),
        'attention.value_length': ('u32', cfg['head_dim']),
        'loop.count': ('u32', cfg['loop_num_passes']),
        'loop.start': ('u32', cfg['loop_layer_index_start']),
        'loop.end': ('u32', cfg['loop_layer_index_end']),
        'loop.gate_rank': ('u32', cfg['loop_gate_rank']),
        'vocab_size': ('u32', cfg['vocab_size']),
        'vocab_size_unpadded': ('u32', cfg['unpadded_vocab_size']),
        'expert_feed_forward_length': ('u32', cfg['moe_intermediate_size']),
        'attention.key_length_swa': ('u32', cfg['swa_head_dim']),
        'attention.value_length_swa': ('u32', cfg['swa_head_dim']),
        'rope.dimension_count': ('u32', 0),
        'attention.sliding_window': ('u32', cfg['sliding_window_size']),
        'attention.sliding_window_pattern': ('array', [k == 'hybrid_sliding' for k in cfg['layer_types']]),
        'shortconv.l_cache': ('u32', cfg['conv_kernel_size']),
        'expert_weights_scale': ('f32', cfg['route_scale']),
        'activation.situ_beta': ('f32', cfg['mlp_gate_softcap']),
        'activation.situ_linear_beta': ('f32', cfg['mlp_up_softcap']),
        'attn_res.block_size': ('u32', cfg['n_layers_per_attn_res_block']),
        'final_logit_softcapping': ('f32', cfg['final_logit_softcapping']),
        'attention.relative_length': ('u32', cfg['d_rel']),
        'attention.relative_extent': ('u32', cfg['rel_extent']),
        'attention.qk_clip': ('f32', cfg['qk_l2_clip_threshold']),
        'attention.relative_clip': ('f32', cfg['rel_l2_clip_threshold']),
        'attention.log_scale_floor': ('u32', cfg['log_scaling_n_floor']),
        'attention.log_scale_alpha': ('f32', cfg['log_scaling_alpha']),
        'loop.varying': ('bool', False),
    }


def ggml_nvfp4_blocks(codes: np.ndarray, scales: np.ndarray) -> np.ndarray:
    """
    A checkpoint's NVFP4 rows -- `codes` [..., K / 2], two 4-bit codes a byte in order, the low nibble first, and
    `scales` [..., K / 16] -- as GGML stores them, [..., K / 64 * 36]: super-blocks of 64 weights, each its four scale
    bytes and then, per 16 weights, eight bytes holding weights 0..7 in their low nibbles and 8..15 in their high.
    """

    lead = codes.shape[:-1]
    K = codes.shape[-1] * 2
    assert K % 64 == 0, K

    each = np.stack([codes & 0x0F, codes >> 4], -1).reshape(*lead, K // 16, 16)  # a weight's code, in order
    packed = each[..., :8] | (each[..., 8:] << 4)

    return np.concatenate(
        [
            scales.reshape(*lead, K // 64, 4),
            packed.reshape(*lead, K // 64, 32),
        ],
        -1,
    ).reshape(*lead, K // 64 * 36)


def inkling2_gguf_tensors(
        checkpoint: str,
        *,
        dense_type: GGMLQuantizationType = GGMLQuantizationType.F32,
        expert_type: GGMLQuantizationType = GGMLQuantizationType.BF16,
) -> dict[str, tuple[GGMLQuantizationType, np.ndarray]]:
    """
    The checkpoint's tensors as the converter names and lays them out: name -> (type, float32 values, or the stored
    bytes of an NVFP4 tensor). `dense_type` is what the tensors in `QUANTIZED` are to be stored as, `expert_type`
    what the experts the checkpoint has as MXFP8 are.
    """

    with open(os.path.join(checkpoint, 'config.json')) as f:
        cfg = json.load(f)
    st = SafetensorsFile(os.path.join(checkpoint, 'model.safetensors'))  # type: ignore[arg-type]

    P = 'model.llm.'
    L = cfg['num_hidden_layers']
    I = cfg['moe_intermediate_size']  # noqa: E741
    start, end = cfg['loop_layer_index_start'], cfg['loop_layer_index_end']

    t: dict[str, tuple[GGMLQuantizationType, np.ndarray]] = {}

    def f32(raw: str) -> np.ndarray:
        return np.ascontiguousarray(st.get(P + raw), dtype=np.float32)

    def add(name: str, x: np.ndarray) -> None:
        t[name] = (dense_type if name.endswith(QUANTIZED) else GGMLQuantizationType.F32, x)

    def add_experts(name: str, raw: str, order: np.ndarray | None) -> None:
        """A stack of experts, its rows in `order`: packed if the checkpoint packs it as NVFP4, else decoded."""

        kinds = (st.dtype(P + raw), st.dtype(P + raw + '_scale'))
        codes = st.raw(P + raw)
        scales = st.raw(P + raw + '_scale')
        if order is not None:
            codes, scales = codes[:, order], scales[:, order]

        if kinds == ('U8', 'F8_E4M3'):
            t[name + '.weight'] = (GGMLQuantizationType.NVFP4, ggml_nvfp4_blocks(codes, scales))
            add(name + '.scale', f32(raw + '_amax') / f32(raw + '_outer_scale_denominator').reshape(-1)[0])

        else:
            assert kinds == ('F8_E4M3', 'U8'), kinds
            E, N, K = codes.shape
            t[name + '.weight'] = (expert_type, MicroscaledWeight('mxfp8', codes, scales, None, (E, N, K)).dequantize())

    add('token_embd.weight', f32('embed.weight'))
    add('token_embd_norm.weight', f32('embed_norm.weight'))
    add('output.weight', f32('unembed.weight'))
    add('output_norm.weight', f32('norm.weight'))
    add('output_res_query.weight', f32('attn_res.output_query'))

    messages = f32('middle_cycle_cross_pass_queries')
    kv_messages = f32('middle_cycle_cross_pass_kv_queries')

    for i in range(L):
        q = f'layers.{i}.'
        p = f'blk.{i}.'
        local = cfg['layer_types'][i] == 'hybrid_sliding'

        for n, g in (
                ('wq_du', 'attn_q'),
                ('wk_dv', 'attn_k'),
                ('wv_dv', 'attn_v'),
                ('wr_du', 'attn_rel'),
                ('wo_ud', 'attn_output'),
                ('attn_sink_proj', 'attn_sink_proj'),
                ('gate_attn', 'attn_gate'),
        ):
            add(p + f'{g}.weight', f32(q + f'attn.{n}.weight'))
        add(p + 'attn_q_clip.weight', f32(q + 'attn.q_l2_clip.scale'))
        add(p + 'attn_rel_clip.weight', f32(q + 'attn.rel_l2_clip.scale'))
        add(p + 'attn_rel_bias.weight', f32(q + 'attn.rel_logits_proj.proj').T)

        for n in ('k', 'v'):
            if local:
                add(p + f'attn_{n}_conv.weight', f32(q + f'attn.{n}_sconv.weight')[:, 0, :])
            else:
                # (the taps by lag become a plain convolution's: the lags reversed, a row per channel)
                add(p + f'attn_{n}_conv.weight', np.flip(f32(q + f'attn.{n}_sconv.static_w'), 0).T)
                add(p + f'attn_{n}_conv_proj.weight', f32(q + f'attn.{n}_sconv.weight_proj'))
        add(p + 'attn_post_conv.weight', f32(q + 'attn_sconv.weight')[:, 0, :])
        add(p + 'ffn_post_conv.weight', f32(q + 'mlp_sconv.weight')[:, 0, :])

        if local:
            add(p + 'attn_norm.weight', f32(q + 'attn_norm.weight'))
        else:
            for n in ('q', 'k', 'v'):
                add(p + f'attn_{n}_inp_norm.weight', f32(q + f'{n}_input_norm.weight'))
        add(p + 'ffn_norm.weight', f32(q + 'mlp_norm.weight'))

        if i:
            add(p + 'attn_res_query.weight', f32(f'attn_res.attn_queries.{i - 1}'))
        add(p + 'ffn_res_query.weight', f32(f'attn_res.mlp_queries.{i}'))

        add(p + 'ffn_gate_inp.weight', f32(q + 'mlp.gate.weight'))
        add(p + 'exp_probs_b.bias', f32(q + 'mlp.gate.bias'))
        # (the checkpoint alternates an expert's gate and up rows; the converter puts the gate rows first)
        add_experts(
            p + 'ffn_gate_up_exps',
            q + 'mlp.experts.w13_weight',
            np.concatenate([np.arange(0, 2 * I, 2), np.arange(1, 2 * I, 2)]),
        )
        add_experts(p + 'ffn_down_exps', q + 'mlp.experts.w2_weight', None)

        if start <= i < end:
            for n, g in (('attn', 'q'), ('k', 'k'), ('v', 'v'), ('mlp', 'ffn')):
                for part in ('down', 'forget', 'gain'):
                    add(p + f'loop_{g}_ctrl_{part}.weight', f32(q + f'controllers.{n}.{part}_weight'))

            j = i - start
            add(
                p + 'loop_msg_query.weight',
                np.stack([messages[2 * j], kv_messages[2 * j], kv_messages[2 * j + 1], messages[2 * j + 1]]),
            )

    return t


def _add_metadata(w: gguf.GGUFWriter, prefix: str, metadata: ta.Mapping[str, tuple[str, ta.Any]]) -> None:
    add: dict[str, ta.Callable[[str, ta.Any], None]] = {
        'u32': w.add_uint32,
        'f32': w.add_float32,
        'bool': w.add_bool,
        'array': w.add_array,
    }
    for key, (kind, value) in metadata.items():
        add[kind](f'{prefix}.{key}', value)


def _add_tokenizer(w: gguf.GGUFWriter, tj: ta.Mapping[str, ta.Any], *, pre: str, eos_id: int) -> None:
    """The tokenizer's fields from a tokenizer.json: the added tokens are control tokens, and nothing else is."""

    vocab = tj['model']['vocab']
    added = {at['id']: at['content'] for at in tj['added_tokens']}
    tokens = [''] * (max([*vocab.values(), *added]) + 1)
    for t, i in vocab.items():
        tokens[i] = t
    for i, t in added.items():
        tokens[i] = t

    w.add_tokenizer_model('gpt2')
    w.add_tokenizer_pre(pre)
    w.add_token_list(tokens)
    w.add_token_types([gguf.TokenType.CONTROL if i in added else gguf.TokenType.NORMAL for i in range(len(tokens))])
    w.add_token_merges(list(tj['model']['merges']))
    w.add_eos_token_id(eos_id)
    w.add_add_bos_token(False)


def write_inkling2_gguf(
        path: str,
        checkpoint: str,
        *,
        architecture: str = ARCHITECTURE,
        metadata: ta.Mapping[str, tuple[str, ta.Any]] | None = None,
        pre: str = 'inkling2',
        dense_type: GGMLQuantizationType = GGMLQuantizationType.F32,
        expert_type: GGMLQuantizationType = GGMLQuantizationType.BF16,
        tensors: ta.Mapping[str, np.ndarray | None] | None = None,
) -> None:
    """
    The synthetic checkpoint directory `checkpoint` as a GGUF at `path`. `metadata` replaces or adds architecture
    keys (in `inkling2_gguf_metadata`'s form) and `pre` is the pre-tokenizer the file names; `dense_type` and
    `expert_type` are `inkling2_gguf_tensors`'; `tensors` adds float32 tensors by name, or with None leaves one out.
    """

    with open(os.path.join(checkpoint, 'config.json')) as f:
        cfg = json.load(f)
    with open(os.path.join(checkpoint, 'tokenizer.json')) as f:
        tj = json.load(f)

    w = gguf.GGUFWriter(path, architecture)
    _add_metadata(w, architecture, {**inkling2_gguf_metadata(cfg), **(metadata or {})})
    _add_tokenizer(w, tj, pre=pre, eos_id=cfg['eos_token_id'])

    t = inkling2_gguf_tensors(checkpoint, dense_type=dense_type, expert_type=expert_type)
    for name, x in (tensors or {}).items():
        if x is None:
            del t[name]
        else:
            t[name] = (GGMLQuantizationType.F32, x)

    for name, (qtype, x) in t.items():
        if qtype == GGMLQuantizationType.F32:
            w.add_tensor(name, np.ascontiguousarray(x, dtype=np.float32))
        else:
            stored = x if qtype == GGMLQuantizationType.NVFP4 else quantize(x, qtype)
            w.add_tensor(name, stored, raw_dtype=getattr(gguf.GGMLQuantizationType, qtype.name))

    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()
