"""
A DSpark drafter (models/inkling/core/dspark/) from its parameters: not an architecture -- a drafter is no model of its
own -- but what the architecture whose checkpoint ships one builds beside its model, handing over the target's parts the
drafter borrows. Canonical names are the checkpoint's (models/inkling/load/checkpoints.py), without the prefix the
checkpoint's source gives them.
"""
import typing as ta

from ....load.plan import LayoutRules
from ....ops.base import Array
from ....ops.base import Ops
from ....ops.base import Weight
from ..core.dspark.config import DsparkConfig
from ..core.dspark.drafter import DsparkDrafter
from ..core.dspark.layers import DsparkLayer
from ..core.dspark.markov import DsparkMarkovHead
from ..core.dspark.memory import DsparkContext
from ..core.dspark.memory import DsparkTapMix


##


# What a layout that plans a drafter's names adds to its own (substrings of the names below).
DSPARK_LAYOUT = LayoutRules(
    # the norms' weights, the tap mix, the mask vector and the head's biases
    keep_f32=(
        'norm',
        'tap_mix',
        'mask_embed',
        'markov_head.rnn_proj.bias',
        'markov_head.out.bias',
    ),
    # never quantized: 0.6 GB that decides how many of a round's rows the target keeps
    no_quant=(
        'self_attn.',
        'mlp.gate_proj',
        'mlp.up_proj',
        'mlp.down_proj',
        'markov_head.',
    ),
)


def dspark_param_names(cfg: DsparkConfig) -> list[str]:
    names = ['tap_mix', 'mask_embed', 'norm.weight']

    for i in range(cfg.num_layers):
        q = f'layers.{i}.'
        names += [q + 'dflare_norm.weight', q + 'input_layernorm.weight', q + 'post_attention_layernorm.weight']
        names += [
            q + f'self_attn.{n}.weight'
            for n in (
                'k_proj_ctx',
                'v_proj_ctx',
                'k_norm_ctx',
                'q_proj',
                'k_proj',
                'v_proj',
                'q_norm',
                'k_norm',
                'o_proj',
            )
        ]
        names += [q + f'mlp.{n}.weight' for n in ('gate_proj', 'up_proj', 'down_proj')]

    names += [
        'markov_head.' + n
        for n in (
            'dflare_norm.weight',
            'markov_w1.weight',
            'state_proj.weight',
            'input_proj.weight',
            'rnn_proj.bias',
            'out.weight',
            'out.bias',
        )
    ]

    return names


def build_dspark(
        cfg: DsparkConfig,
        params: ta.Mapping[str, Weight],
        ops: Ops,
        dtype: ta.Any,
        *,
        embed: Weight,
        embed_norm: Array,
        unembed: Weight,
        logit_cap: float,
) -> DsparkDrafter:
    """
    The drafter from its parameters and the target's it borrows: the embedding and its norm, the output projection,
    and the cap on the logits. The tap mix's rows are the layers' in order, then the head's.
    """

    p = params
    eps = cfg.rms_eps

    def mix(row: int, norm: Array) -> DsparkTapMix:
        return DsparkTapMix(
            weights=ops.select(p['tap_mix'], row),
            norm=norm,
            eps=eps,
            dtype=dtype,
        )

    layers: list[DsparkLayer] = []
    for i in range(cfg.num_layers):
        q = f'layers.{i}.'
        a = q + 'self_attn.'

        layers.append(DsparkLayer(
            cfg=cfg,
            context=DsparkContext(
                mix=mix(i, p[q + 'dflare_norm.weight']),
                k=p[a + 'k_proj_ctx.weight'],
                v=p[a + 'v_proj_ctx.weight'],
                k_norm=p[a + 'k_norm_ctx.weight'],
                num_kv_heads=cfg.num_kv_heads,
                head_dim=cfg.head_dim,
                eps=eps,
                dtype=dtype,
            ),
            window=cfg.window if cfg.is_local(i) else None,
            attn_norm=p[q + 'input_layernorm.weight'],
            q=p[a + 'q_proj.weight'],
            k=p[a + 'k_proj.weight'],
            v=p[a + 'v_proj.weight'],
            q_norm=p[a + 'q_norm.weight'],
            k_norm=p[a + 'k_norm.weight'],
            o=p[a + 'o_proj.weight'],
            mlp_norm=p[q + 'post_attention_layernorm.weight'],
            gate=p[q + 'mlp.gate_proj.weight'],
            up=p[q + 'mlp.up_proj.weight'],
            down=p[q + 'mlp.down_proj.weight'],
            dtype=dtype,
        ))

    m = 'markov_head.'
    head = DsparkMarkovHead(
        mix=mix(cfg.num_layers, p[m + 'dflare_norm.weight']),
        tokens=p[m + 'markov_w1.weight'],
        state_proj=p[m + 'state_proj.weight'],
        input_proj=p[m + 'input_proj.weight'],
        bias=p[m + 'rnn_proj.bias'],
        out=p[m + 'out.weight'],
        out_bias=p[m + 'out.bias'],
        rank=cfg.markov_rank,
        cap=logit_cap,
        dtype=dtype,
    )

    return DsparkDrafter(
        cfg=cfg,
        ops=ops,
        dtype=dtype,
        embed=embed,
        embed_norm=embed_norm,
        unembed=unembed,
        mask=p['mask_embed'],
        layers=layers,
        norm=p['norm.weight'],
        head=head,
    )
