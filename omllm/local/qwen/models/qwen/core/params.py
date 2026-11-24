# ruff: noqa: N803 N806 N812
from .config import Qwen35Config


##


def required_param_names(cfg: Qwen35Config) -> list[str]:
    names = ['embed_tokens.weight', 'norm.weight']
    for i, kind in enumerate(cfg.layer_types):
        q = f'layers.{i}.'
        names += [
            q + 'input_layernorm.weight',
            q + 'post_attention_layernorm.weight',
            q + 'mlp.gate_proj.weight',
            q + 'mlp.up_proj.weight',
            q + 'mlp.down_proj.weight',
        ]
        if kind == 'full':
            names += [
                q + f'self_attn.{n}.weight'
                for n in (
                    'q_proj',
                    'k_proj',
                    'v_proj',
                    'o_proj',
                    'q_norm',
                    'k_norm',
                )
            ]
        else:
            names += [
                q + f'linear_attn.{n}.weight'
                for n in (
                    'in_proj_qkv',
                    'in_proj_z',
                    'in_proj_a',
                    'in_proj_b',
                    'conv1d',
                    'norm',
                    'out_proj',
                )
            ]
            names += [q + 'linear_attn.A', q + 'linear_attn.dt_bias']
    return names


def mtp_param_names() -> list[str]:
    """The one-layer draft head: stem, a full-attention block (text geometry, private weights), final norm."""

    q = 'mtp.layers.0.'
    names = [
        'mtp.fc.weight',
        'mtp.pre_fc_norm_embedding.weight',
        'mtp.pre_fc_norm_hidden.weight',
        'mtp.norm.weight',
        q + 'input_layernorm.weight',
        q + 'post_attention_layernorm.weight',
        q + 'mlp.gate_proj.weight',
        q + 'mlp.up_proj.weight',
        q + 'mlp.down_proj.weight',
    ]
    names += [
        q + f'self_attn.{n}.weight'
        for n in (
            'q_proj',
            'k_proj',
            'v_proj',
            'o_proj',
            'q_norm',
            'k_norm',
        )
    ]
    return names
