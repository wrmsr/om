"""
Qwen3.8-Flash-Next (`qwen4_exp`; FLASHNEXT.md): every layer a mixer (Gated DeltaNet, or gated attention with QSA)
and a mixture of experts, both meeting a four-branch gated residual stream, and the n-gram layer on its layers. Built
from the same parts as Qwen3.5 where they are the same (core/deltanet.py, core/attention.py, core/mlp.py) and its own
where not (core/gated_residual.py, core/moe.py, core/qsa.py, core/ple.py). The MTP head is not in the reference
implementation and is not built.
"""
import typing as ta

from ..core.block import Block
from ..core.block import block_params
from ..core.config import Qwen4ExpConfig
from ..core.config import Qwen35Config
from ..core.deltanet import GatedDeltaNet
from ..core.gated_residual import GatedResidualConnection
from ..core.gated_residual import GatedResidualStream
from ..core.mixing import Mixer
from ..core.mlp import MLP
from ..core.model import Qwen35
from ..core.moe import MoE
from ..core.ple import NGramLayerEmbedding
from ..core.qsa import IndexedAttention
from ..load.plan import LayoutRules
from ..load.policies import FUSIONS
from ..load.policies import KEEP_F32
from ..load.policies import NO_QUANT
from ..ops.base import Ops
from ..ops.base import Weight
from .qwen35 import Qwen35Architecture


##


QWEN4EXP_LAYOUT = LayoutRules(
    fusions=(
        *FUSIONS,  # the attention and DeltaNet fusions apply as they are; no expert name matches the dense MLP's
        (
            'mlp.shared_expert.gate_up_proj.weight',
            ('mlp.shared_expert.gate_proj.weight', 'mlp.shared_expert.up_proj.weight'),
            None,
        ),
    ),
    keep_f32=KEEP_F32,
    # the n-gram table is gathered by row (FLASHNEXT.md phase 5); the router stays at compute precision. (Experts are
    # quantized one by one and stacked by Ops.expert_weights: the loader stacking them per layer is still to come.)
    no_quant=(*NO_QUANT, 'ngram_embedding', 'mlp.gate.weight', 'shared_expert_gate'),
)


def qwen4exp_param_names(cfg: Qwen4ExpConfig) -> list[str]:
    def connection(prefix: str, inject: bool = True) -> list[str]:
        names = [prefix + n + '.weight' for n in ('hc_norm', 'input_mix_weight_down', 'input_mix_weight_up')]
        return [*names, prefix + 'block_inject_weight.weight'] if inject else names

    names = ['embed_tokens.weight', *connection('hyper_connection_mixer.', inject=False)]
    for i, kind in enumerate(cfg.layer_types):
        q = f'layers.{i}.'
        names += connection(q + 'attn_hyper_connection.') + connection(q + 'mlp_hyper_connection.')
        if kind == 'linear':
            names += [
                q + f'linear_attn.{n}.weight'
                for n in ('in_proj_qkv', 'in_proj_z', 'in_proj_a', 'in_proj_b', 'conv1d', 'norm', 'out_proj')
            ]
            names += [q + 'linear_attn.A', q + 'linear_attn.dt_bias']
        else:
            names += [
                q + f'self_attn.{n}.weight'
                for n in ('q_proj', 'k_proj', 'v_proj', 'o_proj', 'q_norm', 'k_norm')
            ]
            names += [
                q + f'self_attn.indexer.{n}.weight'
                for n in ('index_qk_proj', 'q_layernorm', 'k_layernorm')
            ]
        names += [
            q + 'mlp.gate.weight',
            q + 'mlp.shared_expert_gate.weight',
            *(q + f'mlp.shared_expert.{n}.weight' for n in ('gate_proj', 'up_proj', 'down_proj')),
            *(
                q + f'mlp.experts.{e}.{n}.weight'
                for e in range(cfg.num_experts)
                for n in ('gate_proj', 'up_proj', 'down_proj')
            ),
        ]
        if i in cfg.ple_layers:
            names += [
                q + f'ple.{n}.weight'
                for n in ('conv1d', 'key_proj', 'value_proj', 'norm_conv', 'norm_key', 'norm_query')
            ]
            names += [q + 'ple.ple_embedding.ngram_embedding.weight']
    return names


class Qwen4ExpArchitecture(Qwen35Architecture):
    @property
    def layout(self) -> LayoutRules:
        return QWEN4EXP_LAYOUT

    def param_names(self, cfg: Qwen35Config) -> list[str]:
        return qwen4exp_param_names(ta.cast(Qwen4ExpConfig, cfg))

    def draft_param_names(self, cfg: Qwen35Config) -> list[str]:
        raise ValueError('the qwen4_exp draft head is not in the reference implementation; no MTP for this model yet')

    # construction

    def _gated_connection(
            self,
            cfg: Qwen4ExpConfig,
            params: ta.Mapping[str, Weight],
            ops: Ops,
            prefix: str,
            inject: bool = True,
    ) -> GatedResidualConnection:
        return GatedResidualConnection(
            hc=cfg.hc_count,
            hidden=cfg.hidden_size,
            norm=ops.reshape(params[prefix + 'hc_norm.weight'], (cfg.hc_count, cfg.hidden_size)),
            down=params[prefix + 'input_mix_weight_down.weight'],
            up=params[prefix + 'input_mix_weight_up.weight'],
            inject=params[prefix + 'block_inject_weight.weight'] if inject else None,
            eps=cfg.rms_eps,
        )

    def _moe(self, cfg: Qwen4ExpConfig, params: ta.Mapping[str, Weight], ops: Ops, prefix: str) -> MoE:
        def expert(e: int, n: str) -> ta.Any:
            return params[f'{prefix}experts.{e}.{n}.weight']

        experts = range(cfg.num_experts)
        return MoE(
            router=params[prefix + 'gate.weight'],
            gate_up=ops.expert_weights([[expert(e, 'gate_proj'), expert(e, 'up_proj')] for e in experts]),
            down=ops.expert_weights([[expert(e, 'down_proj')] for e in experts]),
            intermediate=cfg.moe_intermediate_size,
            shared=MLP(block_params(params, prefix + 'shared_expert.')),
            shared_gate=params[prefix + 'shared_expert_gate.weight'],
            top_k=cfg.num_experts_per_tok,
            norm_topk=cfg.norm_topk_prob,
        )

    def _mixer_of(self, cfg: Qwen4ExpConfig, kind: str, params: ta.Mapping[str, Weight], q: str) -> Mixer:
        if kind == 'linear':
            return GatedDeltaNet(cfg, block_params(params, q + 'linear_attn.'))
        if kind == 'indexed':
            return IndexedAttention(
                cfg,
                block_params(params, q + 'self_attn.'),
                block_params(params, q + 'self_attn.indexer.'),
            )
        raise ValueError(f'unknown layer type {kind!r}')

    def build(
            self,
            cfg: Qwen35Config,
            params: ta.Mapping[str, Weight],
            ops: Ops,
            dtype: ta.Any,
    ) -> Qwen35:
        c = ta.cast(Qwen4ExpConfig, cfg)

        blocks = []
        for i, kind in enumerate(c.layer_types):
            q = f'layers.{i}.'
            ple = None
            if i in c.ple_layers:
                p = dict(block_params(params, q + 'ple.'))
                for n in ('norm_key', 'norm_query', 'norm_conv'):
                    p[n] = ops.reshape(p[n], (c.hc_count, c.hidden_size))
                ple = NGramLayerEmbedding(c, c.ple_layers.index(i), p)
            blocks.append(Block(
                index=i,
                mixer=self._mixer_of(c, kind, params, q),
                ffn=self._moe(c, params, ops, q + 'mlp.'),
                mixer_conn=self._gated_connection(c, params, ops, q + 'attn_hyper_connection.'),
                ffn_conn=self._gated_connection(c, params, ops, q + 'mlp_hyper_connection.'),
                embedding=ple,
            ))

        embed = params['embed_tokens.weight']
        return Qwen35(
            cfg=c,
            ops=ops,
            dtype=dtype,
            embed=embed,
            lm_head=params.get('lm_head.weight', embed),
            blocks=blocks,
            residual=GatedResidualStream(
                self._gated_connection(c, params, ops, 'hyper_connection_mixer.', inject=False),
            ),
            nbytes=sum(ops.nbytes(p) for p in params.values()),
        )
