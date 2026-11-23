"""
Inkling 2 (`inkling2_loop`; INKLING.md): attention with a learned relative term and a sink, and a mixture of experts,
both behind short convolutions over time and both reading a residual stream of block sums -- with a stretch of the
layers run several times a token. Built from its own parts (core/inkling2/) through the engine's shared ones: the
stateful-sublayer block (core/sublayers.py), the short convolutions (core/shortconv.py), the KV state and its
formats and the spans attention keeps it over (core/kvspans.py), the stacked-expert seam.

The model's execution order is the config's visits (`Inkling2Config.visits`): one entry per (layer, pass), the
looped layers' entries built over the same sublayers -- one set of weights -- each with its own slot of decode state,
and the loop's two markers between the passes (core/inkling2/loop.py).

With `mtp` the checkpoint's draft model is built beside it (core/dspark/, from its own names under `mtp.`:
dspark.py), and the model then hands out, as its hidden output, the states inside the stack that the drafter reads
(core/inkling2/readouts.py). Not built: the vision tower.
"""
import typing as ta

from ..core.draftheads import DraftHead
from ..core.heads import SoftcappedOutputHead
from ..core.inkling2.attention import Inkling2Attention
from ..core.inkling2.attention import LogScaling
from ..core.inkling2.config import Inkling2Config
from ..core.inkling2.connections import DepthAttentionConnection
from ..core.inkling2.connections import DepthFeedForwardConnection
from ..core.inkling2.depth import DepthResidualStream
from ..core.inkling2.loop import LoopEntry
from ..core.inkling2.loop import LoopRestart
from ..core.inkling2.messages import MessageGate
from ..core.inkling2.messages import MessageReader
from ..core.inkling2.moe import Inkling2MoE
from ..core.inkling2.readouts import BlockSumReadout
from ..core.kvspans import FullKvSpan
from ..core.kvspans import KvSpan
from ..core.kvspans import RunningKvSpan
from ..core.kvspans import SlidingKvSpan
from ..core.mixing import Connection
from ..core.mixing import Layer
from ..core.mixing import Mixer
from ..core.model import Qwen35
from ..core.positions import PlainStepPositions
from ..core.readouts import Readout
from ..core.shortconv import ConvolvedMixer
from ..core.shortconv import DynamicShortConv
from ..core.shortconv import FeedForwardMixer
from ..core.shortconv import ShortConv
from ..core.shortconv import StaticShortConv
from ..core.sublayers import SublayerBlock
from ..load.pipeline import LoadReport
from ..load.pipeline import ParamLoader
from ..load.pipeline import open_param_cache
from ..load.plan import LayoutRules
from ..load.recipe import LoadRecipe
from ..load.weights import TensorSource
from ..ops.base import Ops
from ..ops.base import Weight
from .base import Architecture
from .dspark import DSPARK_LAYOUT
from .dspark import build_dspark
from .dspark import dspark_param_names


##


INKLING2_LAYOUT = LayoutRules(
    # no fusions: a layer's query, key and value projections do not share an input (connections.py)
    fusions=(),
    # the norms' weights, the convolutions' taps, every depth query, the router and its bias, and the message gates'
    # two float32 projections: all computed with in float32 whatever the compute dtype
    keep_f32=(
        'norm',
        'sconv.weight',
        'sconv.static_w',
        'quer',
        'mlp.gate.',
        'forget_weight',
        'gain_weight',
    ),
    # small projections and tables that a quantized model keeps at the compute dtype
    no_quant=(
        'l2_clip',
        'rel_logits_proj',
        'wr_du',
        'attn_sink_proj',
        'sconv',
        'controllers',
    ),
)

INKLING2_DRAFT_PREFIX = 'mtp.'

# the model's rules and the drafter's: its names are planned through the same loader (no name of either matches a
# pattern of the other's)
INKLING2_DRAFT_LAYOUT = LayoutRules(
    fusions=INKLING2_LAYOUT.fusions,
    keep_f32=(*INKLING2_LAYOUT.keep_f32, *DSPARK_LAYOUT.keep_f32),
    no_quant=(*INKLING2_LAYOUT.no_quant, *DSPARK_LAYOUT.no_quant),
)


def inkling2_param_names(cfg: Inkling2Config) -> list[str]:
    names = ['embed.weight', 'embed_norm.weight', 'norm.weight', 'unembed.weight', 'output_query']

    for i in range(cfg.num_layers):
        q = f'layers.{i}.'
        local = cfg.is_local(i)

        names += [
            q + f'attn.{n}.weight'
            for n in ('wq_du', 'wk_dv', 'wv_dv', 'wr_du', 'wo_ud', 'attn_sink_proj', 'gate_attn', 'rel_logits_proj')
        ]
        names += [q + 'attn.q_l2_clip.scale', q + 'attn.rel_l2_clip.scale']

        for n in ('k_sconv', 'v_sconv'):
            if local:
                names += [q + f'attn.{n}.weight']
            else:
                names += [q + f'attn.{n}.static_w', q + f'attn.{n}.proj.weight']
        names += [q + 'attn_sconv.weight', q + 'mlp_sconv.weight']

        if local:
            names += [q + 'attn_norm.weight']
        else:
            names += [q + f'{n}_input_norm.weight' for n in ('q', 'k', 'v')]
        names += [q + 'mlp_norm.weight']

        if i:
            names += [q + 'attn_queries']
        names += [q + 'mlp_query']

        names += [q + 'mlp.gate.weight', q + 'mlp.gate.bias', q + 'mlp.experts.gate_up', q + 'mlp.experts.down']

        if cfg.loop_passes > 1 and cfg.loop_start <= i < cfg.loop_end:
            names += [
                q + f'controllers.{n}.{w}'
                for n in ('attn', 'k', 'v', 'mlp')
                for w in ('down_weight', 'forget_weight', 'gain_weight')
            ]
            names += [q + 'message_queries']

    return names


class Inkling2Architecture(Architecture):
    @property
    def layout(self) -> LayoutRules:
        return INKLING2_DRAFT_LAYOUT

    def param_names(self, cfg: Inkling2Config) -> list[str]:
        return inkling2_param_names(cfg)

    def draft_param_names(self, cfg: Inkling2Config) -> list[str]:
        """The draft model's names (empty for a checkpoint that describes none)."""

        if cfg.draft is None:
            return []
        return [INKLING2_DRAFT_PREFIX + n for n in dspark_param_names(cfg.draft)]

    # construction

    def _short_conv(self, cfg: Inkling2Config, p: ta.Mapping[str, Weight], prefix: str) -> ShortConv:
        if prefix + '.weight' in p:
            return StaticShortConv(p[prefix + '.weight'])
        return DynamicShortConv(
            weight=p[prefix + '.static_w'],
            proj=p[prefix + '.proj.weight'],
            heads=cfg.num_kv_heads,
        )

    # The slots a local layer's window has to run in before it is moved back (core/kvspans.py, RunningKvSpan): as
    # many again as the window, so once in a window's worth of tokens -- and enough for any step.
    WINDOW_ROOM_MIN: ta.ClassVar[int] = 16

    def _span(self, cfg: Inkling2Config, i: int, in_place: bool) -> KvSpan:
        """What layer i's attention sees and how it is kept: by the layer's kind, and by how the backend writes."""

        if not cfg.is_local(i):
            return FullKvSpan(num_kv_heads=cfg.num_kv_heads, head_dim=cfg.head_dim)

        if in_place:
            return RunningKvSpan(
                num_kv_heads=cfg.num_kv_heads,
                head_dim=cfg.head_dim,
                window=cfg.window,
                room=max(cfg.window - 1, self.WINDOW_ROOM_MIN),
            )

        return SlidingKvSpan(num_kv_heads=cfg.num_kv_heads, head_dim=cfg.head_dim, window=cfg.window)

    def _attention(
            self,
            cfg: Inkling2Config,
            p: ta.Mapping[str, Weight],
            i: int,
            in_place: bool,
    ) -> Mixer:
        q = f'layers.{i}.'
        local = cfg.is_local(i)

        attention = Inkling2Attention(
            num_heads=cfg.num_heads,
            num_kv_heads=cfg.num_kv_heads,
            head_dim=cfg.head_dim,
            wq=p[q + 'attn.wq_du.weight'],
            wk=p[q + 'attn.wk_dv.weight'],
            wv=p[q + 'attn.wv_dv.weight'],
            wr=p[q + 'attn.wr_du.weight'],
            wo=p[q + 'attn.wo_ud.weight'],
            sink=p[q + 'attn.attn_sink_proj.weight'],
            gate=p[q + 'attn.gate_attn.weight'],
            q_scale=p[q + 'attn.q_l2_clip.scale'],
            rel_scale=p[q + 'attn.rel_l2_clip.scale'],
            rel_proj=p[q + 'attn.rel_logits_proj.weight'],
            k_conv=self._short_conv(cfg, p, q + 'attn.k_sconv'),
            v_conv=self._short_conv(cfg, p, q + 'attn.v_sconv'),
            span=self._span(cfg, i, in_place),
            qk_clip=cfg.qk_clip,
            rel_clip=cfg.rel_clip,
            log_scaling=None if local else LogScaling(cfg.log_scale_floor, cfg.log_scale_alpha),
            eps=cfg.rms_eps,
        )

        return ConvolvedMixer(attention, StaticShortConv(p[q + 'attn_sconv.weight']))

    def _moe(self, cfg: Inkling2Config, p: ta.Mapping[str, Weight], i: int) -> Mixer:
        q = f'layers.{i}.'

        moe = Inkling2MoE(
            router=p[q + 'mlp.gate.weight'],
            bias=p[q + 'mlp.gate.bias'],
            gate_up=p[q + 'mlp.experts.gate_up'],
            down=p[q + 'mlp.experts.down'],
            intermediate=cfg.moe_intermediate_size,
            top_k=cfg.num_experts_per_tok,
            route_scale=cfg.route_scale,
            gate_softcap=cfg.gate_softcap,
            up_softcap=cfg.up_softcap,
        )

        return ConvolvedMixer(FeedForwardMixer(moe), StaticShortConv(p[q + 'mlp_sconv.weight']))

    def _messages(
            self,
            cfg: Inkling2Config,
            p: ta.Mapping[str, Weight],
            i: int,
            dtype: ta.Any,
    ) -> tuple[MessageReader, MessageReader] | tuple[None, None]:
        """A looped layer's message readers: its attention inputs' (query, key, value) and its feed-forward's."""

        q = f'layers.{i}.'
        if q + 'message_queries' not in p:
            return None, None

        def gate(n: str) -> MessageGate:
            return MessageGate(
                down=p[q + f'controllers.{n}.down_weight'],
                forget=p[q + f'controllers.{n}.forget_weight'],
                gain=p[q + f'controllers.{n}.gain_weight'],
                eps=cfg.rms_eps,
                dtype=dtype,
            )

        queries = p[q + 'message_queries']  # [4, hidden]: query, key, value, mlp
        return (
            MessageReader(queries=queries[:3], gates=[gate('attn'), gate('k'), gate('v')]),
            MessageReader(queries=queries[3:], gates=[gate('mlp')]),
        )

    def _sublayers(
            self,
            cfg: Inkling2Config,
            p: ta.Mapping[str, Weight],
            i: int,
            dtype: ta.Any,
            in_place: bool,
    ) -> list[tuple[Mixer, Connection]]:
        """Physical layer i's two sublayers and their connections: one set, however many visits run it."""

        q = f'layers.{i}.'
        attn_messages, mlp_messages = self._messages(cfg, p, i, dtype)

        if cfg.is_local(i):
            norms = [p[q + 'attn_norm.weight']]
        else:
            norms = [p[q + f'{n}_input_norm.weight'] for n in ('q', 'k', 'v')]

        return [
            (
                self._attention(cfg, p, i, in_place),
                DepthAttentionConnection(
                    queries=p.get(q + 'attn_queries'),
                    norms=norms,
                    eps=cfg.rms_eps,
                    dtype=dtype,
                    boundary=(i % cfg.block_layers == 0),
                    messages=attn_messages,
                ),
            ),
            (
                self._moe(cfg, p, i),
                DepthFeedForwardConnection(
                    query=p[q + 'mlp_query'],
                    norm=p[q + 'mlp_norm.weight'],
                    eps=cfg.rms_eps,
                    dtype=dtype,
                    messages=mlp_messages,
                ),
            ),
        ]

    def build(
            self,
            cfg: Inkling2Config,
            params: ta.Mapping[str, Weight],
            ops: Ops,
            dtype: ta.Any,
    ) -> Qwen35:
        """A model from finished parameters (canonical names: load/inkling2.py)."""

        sublayers = [self._sublayers(cfg, params, i, dtype, ops.kv_in_place) for i in range(cfg.num_layers)]

        layers: list[Layer] = []
        places: list[int] = []  # each visit's place among the layers
        for visit, (layer, loop_pass) in enumerate(cfg.visits()):
            if layer == cfg.loop_start and cfg.loop_passes > 1:
                layers.append(LoopRestart(eps=cfg.rms_eps) if loop_pass else LoopEntry())
            places.append(len(layers))
            layers.append(SublayerBlock(index=visit, sublayers=sublayers[layer]))

        embed = params['embed.weight']
        unembed = params['unembed.weight']

        draft: DraftHead | None = None
        readout: Readout | None = None
        dp = INKLING2_DRAFT_PREFIX
        if cfg.draft is not None and dp + 'mask_embed' in params:
            *taps, last = cfg.draft.taps
            if last != len(places) or cfg.draft.hidden_size != cfg.hidden_size:
                raise ValueError(f'a drafter of width {cfg.draft.hidden_size} reading {cfg.draft.taps}: not this model')
            readout = BlockSumReadout([places[t] for t in taps])
            draft = build_dspark(
                cfg.draft,
                {n[len(dp):]: w for n, w in params.items() if n.startswith(dp)},
                ops,
                dtype,
                embed=embed,
                embed_norm=params['embed_norm.weight'],
                unembed=unembed,
                logit_cap=cfg.logit_softcap,
            )

        return Qwen35(
            cfg=cfg,
            ops=ops,
            dtype=dtype,
            embed=embed,
            lm_head=unembed,
            blocks=layers,
            residual=DepthResidualStream(
                embed_norm=params['embed_norm.weight'],
                query=params['output_query'],
                norm=params['norm.weight'],
                eps=cfg.rms_eps,
                dtype=dtype,
            ),
            positions=PlainStepPositions(),
            head=SoftcappedOutputHead(unembed, cfg.logit_softcap),
            readout=readout,
            mtp=draft,
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
        cfg = src.config
        if not isinstance(cfg, Inkling2Config):
            raise TypeError(cfg)

        loader = ParamLoader(
            src,
            ops,
            recipe=recipe,
            layout=self.layout,
            dtype=dtype,
            cache=open_param_cache(cache_dir, src, recipe) if cache_dir is not None else None,
        )

        specs = loader.plan(self.param_names(cfg))
        if mtp:
            names = self.draft_param_names(cfg)
            if not names or not all(src.has(n) for n in names):
                raise ValueError('no draft model in this checkpoint (its config\'s mtp_config and mtp.safetensors)')
            specs += loader.plan(names)
        params = loader.materialize(specs, on_progress=on_progress)

        return self.build(cfg, params, ops, ops.dtype(dtype)), loader.report()
