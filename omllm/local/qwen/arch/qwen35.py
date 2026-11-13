"""
The Qwen3.5 / 3.6 / 3.8 dense architecture (HF `qwen3_5`, GGUF `qwen35`): which parameters it has, how the loader lays
them out, and how its blocks are composed from them. A second architecture -- Flash-Next's `qwen4_exp`, with its QSA
mixers, MoE feed-forwards and Gated Residual stream -- is a sibling of this module, composing the same `Block` from
different parts; nothing below the architecture learns about either.
"""
import os
import typing as ta

from ..core.attention import Attention
from ..core.block import Block
from ..core.block import block_params
from ..core.config import Qwen35Config
from ..core.deltanet import GatedDeltaNet
from ..core.mixing import Connection
from ..core.mixing import Mixer
from ..core.mixing import PlainConnection
from ..core.mixing import PlainResidual
from ..core.mixing import ResidualStream
from ..core.mlp import MLP
from ..core.model import Qwen35
from ..core.mtp import MtpHead
from ..core.params import mtp_param_names
from ..core.params import required_param_names
from ..load.pipeline import LoadReport
from ..load.pipeline import ParamLoader
from ..load.pipeline import open_param_cache
from ..load.plan import LayoutRules
from ..load.policies import QWEN35_LAYOUT
from ..load.recipe import LoadRecipe
from ..load.weights import TensorSource
from ..ops.base import Ops
from ..ops.base import Weight


##


class Qwen35Architecture:
    """
    Qwen3.5's hybrid stack: three Gated DeltaNet layers to every gated-attention layer (the config's `layer_types`), a
    dense SwiGLU after every mixer, one plain residual stream, and an optional one-layer MTP draft head with a
    full-attention block of the same geometry. The older and smaller Qwen3.5 checkpoints are this architecture with no
    draft head (and tied embeddings).
    """

    @property
    def layout(self) -> LayoutRules:
        """How the loader stores this architecture's parameters: fusions, float32 placement, never-quantized names."""

        return QWEN35_LAYOUT

    def param_names(self, cfg: Qwen35Config) -> list[str]:
        return required_param_names(cfg)

    def draft_param_names(self, cfg: Qwen35Config) -> list[str]:
        if not cfg.num_mtp_layers:
            raise ValueError('this source has no MTP head')
        return mtp_param_names()

    # construction

    def _residual(self, cfg: Qwen35Config, norm: Weight) -> ResidualStream:
        """The stream's two ends; `norm` is the final norm before the output head."""

        return PlainResidual(norm, cfg.rms_eps)

    def _connection(self, cfg: Qwen35Config, norm: Weight) -> Connection:
        """A sublayer's connection to the stream; `norm` is its pre-norm."""

        return PlainConnection(norm, cfg.rms_eps)

    def _mixer(self, cfg: Qwen35Config, kind: str, p: ta.Mapping[str, Weight]) -> Mixer:
        if kind == 'full':
            return Attention(cfg, dict(p))
        if kind == 'linear':
            return GatedDeltaNet(cfg, dict(p))
        raise ValueError(f'unknown layer type {kind!r}')

    def _block(
            self,
            cfg: Qwen35Config,
            index: int,
            kind: str,
            p: ta.Mapping[str, Weight],
    ) -> Block:
        return Block(
            index=index,
            mixer=self._mixer(cfg, kind, p),
            ffn=MLP(dict(p)),
            mixer_conn=self._connection(cfg, p['input_layernorm']),
            ffn_conn=self._connection(cfg, p['post_attention_layernorm']),
        )

    def build(
            self,
            cfg: Qwen35Config,
            params: ta.Mapping[str, Weight],
            ops: Ops,
            dtype: ta.Any,
    ) -> Qwen35:
        """A model from finished parameters (canonical names, fused as `layout` says)."""

        blocks = [
            self._block(cfg, i, kind, block_params(params, f'layers.{i}.'))
            for i, kind in enumerate(cfg.layer_types)
        ]

        embed = params['embed_tokens.weight']
        lm_head = params.get('lm_head.weight', embed)

        mtp: MtpHead | None = None
        if 'mtp.fc.weight' in params:
            mtp = MtpHead(
                cfg=cfg,
                ops=ops,
                dtype=dtype,
                embed=embed,
                lm_head=lm_head,
                fc=params['mtp.fc.weight'],
                enorm=params['mtp.pre_fc_norm_embedding.weight'],
                hnorm=params['mtp.pre_fc_norm_hidden.weight'],
                residual=self._residual(cfg, params['mtp.norm.weight']),
                block=self._block(cfg, cfg.num_layers, 'full', block_params(params, 'mtp.layers.0.')),
            )

        return Qwen35(
            cfg=cfg,
            ops=ops,
            dtype=dtype,
            embed=embed,
            lm_head=lm_head,
            blocks=blocks,
            residual=self._residual(cfg, params['norm.weight']),
            mtp=mtp,
            nbytes=sum(ops.nbytes(p) for p in params.values()),
        )

    # loading

    def load(
            self,
            src: TensorSource,
            ops: Ops,
            *,
            recipe: LoadRecipe,
            dtype: str = 'bf16',
            mtp: bool = False,
            cache_dir: str | None = None,
            on_progress: ta.Callable[[int, int], None] | None = None,
    ) -> tuple[Qwen35, LoadReport]:
        """
        The model from a source through the loader pipeline (load/pipeline.py) with this architecture's names and
        layout -- the draft head (`mtp`) from its own names through the same pipeline -- and what the load did.
        """

        cfg = src.config

        loader = ParamLoader(
            src,
            ops,
            recipe=recipe,
            layout=self.layout,
            dtype=dtype,
            cache=open_param_cache(cache_dir, src, recipe) if cache_dir is not None else None,
        )

        specs = loader.plan(
            self.param_names(cfg),
            optional=() if cfg.tied_embeddings else ('lm_head.weight',),
        )
        if mtp:
            specs += loader.plan(self.draft_param_names(cfg))

        params = loader.materialize(specs, on_progress=on_progress)

        return self.build(cfg, params, ops, ops.dtype(dtype)), loader.report()


def load_qwen35(
        src: TensorSource,
        ops: Ops,
        *,
        dtype: str = 'bf16',
        quant: str | None = None,
        group: int = 64,
        verbose: bool = True,
        mtp: bool = False,
        cache_dir: str | os.PathLike | None = None,
        policy: str | ta.Callable[[str, ta.Any], int | None] = 'uniform',
        quant_search: bool = True,
) -> Qwen35:
    """
    A Qwen3.5-family model from a source -- whichever architecture its config is (arch/registry.py), Qwen3.8-Flash-Next
    included -- for scripts, tests and the CLIs (the injector bindings use the architecture directly).

    dtype: 'bf16' | 'f16' | 'f32' (compute dtype; norms, A, dt_bias, conv stay f32).
    quant: None, 'int8' or 'int4' (weight-only affine, see ops/quant.py). If the source already holds MLX-quantized
           tensors at the requested width they are re-packed as-is; otherwise weights are quantized.
    policy: per-tensor precision, a name in load.policies.POLICIES ('uniform', 'km') or a callable
           (name, cfg) -> bits | None; a fused group whose parts would differ in width is loaded unfused.
    quant_search: error-minimising scale search when quantizing; off = plain min/max. Both are part of the parameter
           cache's key.
    mtp:   also load the multi-token-prediction draft head (needs `num_mtp_layers >= 1` in the source).
    cache_dir: keep the finished parameters on disk there (see load/paramcache.py); the first load fills it, later ones
           memory-map it and skip the GGUF dequantization entirely.
    verbose: print load progress and a summary.
    """

    cfg = src.config
    if verbose and cfg.rope_scaling:
        print(
            f'[model] WARNING: rope_scaling={cfg.rope_scaling} present; only plain RoPE is implemented '
            f'(fine for prompts within the original context length)',
        )

    def progress(done: int, total: int) -> None:
        if done % 50 == 1 or done == total:
            print(f'\r[model] loading tensors {done}/{total}', end='', flush=True)

    from .registry import architecture_for  # (a function-local import: the other architectures build on this module)

    model, report = architecture_for(cfg).load(
        src,
        ops,
        recipe=LoadRecipe(
            quant=quant,
            group=group,
            search=quant_search,
            policy=policy,
        ),
        dtype=dtype,
        mtp=mtp,
        cache_dir=os.fspath(cache_dir) if cache_dir is not None else None,
        on_progress=progress if verbose else None,
    )

    if verbose:
        print(f'\n[model] {report.summary()}')

    return model
