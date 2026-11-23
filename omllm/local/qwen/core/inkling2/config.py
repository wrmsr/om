import typing as ta

from omcore import dataclasses as dc

from ..config import ModelConfig


##


@dc.dataclass()
class Inkling2Config(ModelConfig):
    """
    Inkling 2 (`inkling2_loop`; INKLING.md): `num_layers` physical layers, each attention and a mixture of experts
    reading a residual stream of block summaries, of which the layers `loop_start` .. `loop_end - 1` are run
    `loop_passes` times a token. `vocab_size` is the logits' width; the embedding table (and the tokenizer) has
    `embed_size` ids, the rest of which the model never produces.
    """

    embed_size: int
    num_layers: int  # physical layers: sets of weights
    rms_eps: float

    # attention: the same geometry in every layer; `local_layers` attend a sliding window, the others everything
    num_heads: int
    num_kv_heads: int
    head_dim: int
    window: int  # a local layer's keys per query, itself included
    local_layers: list[int]
    rel_dim: int  # the relative-position features per query head
    rel_extent: int  # backward distances the relative term covers; zero (not masked) past them
    qk_clip: float  # l2 clip of each head's query and key
    rel_clip: float
    log_scale_floor: int  # a global layer's queries grow by 1 + alpha log(max((pos + 1) / floor, 1))
    log_scale_alpha: float
    conv_kernel: int

    # mixture of experts
    num_experts: int
    num_experts_per_tok: int
    moe_intermediate_size: int
    route_scale: float  # what a token's expert weights sum to
    gate_softcap: float
    up_softcap: float

    # the residual stream
    block_layers: int  # layers per block: every block's first layer archives the sum so far

    # the loop
    loop_start: int
    loop_end: int
    loop_passes: int
    loop_gate_rank: int

    logit_softcap: float
    context_length: int = 1 << 20
    eos_id: int | None = None
    extra: dict = dc.field(default_factory=dict)

    def __post_init__(self) -> None:
        b = self.block_layers
        if self.num_layers % b or self.loop_start % b or self.loop_end % b:
            raise ValueError(
                f'the layers ({self.num_layers}) and the loop ({self.loop_start}..{self.loop_end}) must be whole '
                f'blocks of {b}',
            )
        if not (0 <= self.loop_start < self.loop_end <= self.num_layers) or self.loop_passes < 1:
            raise ValueError(f'bad loop: {self.loop_start}..{self.loop_end} x {self.loop_passes}')

    @property
    def num_visits(self) -> int:
        """Layers run per token: the loop's counted once per pass."""

        return self.num_layers + (self.loop_passes - 1) * (self.loop_end - self.loop_start)

    def visits(self) -> list[tuple[int, int]]:
        """The execution order: (physical layer, pass) per visit -- pass 0 outside the loop."""

        out = [(i, 0) for i in range(self.loop_start)]
        for p in range(self.loop_passes):
            out += [(i, p) for i in range(self.loop_start, self.loop_end)]
        out += [(i, 0) for i in range(self.loop_end, self.num_layers)]
        return out

    def is_local(self, layer: int) -> bool:
        return layer in self.local_layers

    def summary(self) -> str:
        n_local = len(self.local_layers)

        return (
            f'hidden={self.hidden_size} '
            f'layers={self.num_layers} ({n_local} local / {self.num_layers - n_local} global), '
            f'{self.loop_start}..{self.loop_end - 1} x {self.loop_passes}: {self.num_visits} visits '
            f'vocab={self.vocab_size} of {self.embed_size}'
            f'\n'

            f'  '
            f'attn: {self.num_heads}q/{self.num_kv_heads}kv x {self.head_dim}, window {self.window}, '
            f'rel {self.rel_dim} x {self.rel_extent}, conv={self.conv_kernel}'
            f'\n'

            f'  '
            f'moe : {self.num_experts} experts, top {self.num_experts_per_tok} x {self.moe_intermediate_size}'
            f'\n'

            f'  '
            f'residual: blocks of {self.block_layers}, message rank {self.loop_gate_rank}'
        )


def inkling2_config_from_hf(cfg: ta.Mapping[str, ta.Any]) -> Inkling2Config:
    """
    Our config from a checkpoint's config.json: the released form (a `text_config` with `local_layer_ids`, a nested
    `loop_config`, `intermediate_size` for the experts' width) or the one the reference library writes for a text
    model (`layer_types`, `loop_*`, `moe_intermediate_size`). A key the two forms spell differently is read from
    whichever is present; one that neither has is an error rather than a guess.
    """

    t = cfg.get('text_config', cfg)
    loop = t.get('loop_config') or {}

    def first(*keys: str, of: ta.Mapping[str, ta.Any] = t) -> ta.Any:
        for k in keys:
            if of.get(k) is not None:
                return of[k]
        raise KeyError(f'inkling2 config has none of {keys}')

    n_layers = int(t['num_hidden_layers'])
    if 'local_layer_ids' in t:
        local = sorted(int(i) for i in t['local_layer_ids'])
    else:
        kinds = {'hybrid_sliding': True, 'hybrid': False}
        local = [i for i, k in enumerate(t['layer_types']) if kinds[k]]

    heads = (int(t['num_attention_heads']), int(t['num_key_value_heads']), int(t['head_dim']))
    swa = (
        int(t.get('swa_num_attention_heads', heads[0])),
        int(t.get('swa_num_key_value_heads', heads[1])),
        int(t.get('swa_head_dim', heads[2])),
    )
    if swa != heads:
        raise ValueError(f'local and global attention of different geometries are not supported: {swa} / {heads}')
    if int(t.get('n_shared_experts') or 0):
        raise ValueError('shared experts are not supported')
    if loop.get('is_varloop'):
        raise ValueError('a variable-pass loop is not supported')
    if t.get('scoring_func', 'sigmoid') != 'sigmoid':
        raise ValueError(f'unsupported router scoring {t["scoring_func"]!r}')

    eos = t.get('eos_token_id', cfg.get('eos_token_id'))

    return Inkling2Config(
        vocab_size=int(first('unpadded_vocab_size', 'vocab_size')),
        hidden_size=int(t['hidden_size']),
        embed_size=int(t['vocab_size']),
        num_layers=n_layers,
        rms_eps=float(t.get('rms_norm_eps', 1e-6)),
        num_heads=heads[0],
        num_kv_heads=heads[1],
        head_dim=heads[2],
        window=int(t['sliding_window_size']),
        local_layers=local,
        rel_dim=int(t['d_rel']),
        rel_extent=int(t['rel_extent']),
        qk_clip=float(t['qk_l2_clip_threshold']),
        rel_clip=float(t['rel_l2_clip_threshold']),
        log_scale_floor=int(t['log_scaling_n_floor']),
        log_scale_alpha=float(t['log_scaling_alpha']),
        conv_kernel=int(first('sconv_kernel_size', 'conv_kernel_size')),
        num_experts=int(t['n_routed_experts']),
        num_experts_per_tok=int(t['num_experts_per_tok']),
        moe_intermediate_size=int(first('moe_intermediate_size', 'intermediate_size')),
        route_scale=float(t['route_scale']),
        gate_softcap=float(t['mlp_gate_softcap']),
        up_softcap=float(t['mlp_up_softcap']),
        block_layers=int(t['n_layers_per_attn_res_block']),
        loop_start=int(first('loop_layer_index_start') if 'loop_layer_index_start' in t else first('core_start', of=loop)),  # noqa
        loop_end=int(first('loop_layer_index_end') if 'loop_layer_index_end' in t else first('core_end', of=loop)),
        loop_passes=int(first('loop_num_passes') if 'loop_num_passes' in t else first('num_passes', of=loop)),
        loop_gate_rank=int(first('loop_gate_rank') if 'loop_gate_rank' in t else first('gate_rank', of=loop)),
        logit_softcap=float(t['final_logit_softcapping']),
        context_length=int(first('model_max_length', 'max_position_embeddings')),
        eos_id=(eos[0] if isinstance(eos, list) else eos),
    )
