import typing as ta

from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True)
class DsparkConfig:
    """
    A DSpark block drafter (drafter.py): `num_layers` pre-norm layers of grouped-query attention and a SwiGLU, the
    layers in `local_layers` seeing the last `window` positions of the past and the others all of it; `block` slots a
    call, the first the last token and the rest drafts; a recurrent head of `markov_rank` over the drafts.

    `taps` are the target's states a past position is read from, as the checkpoint counts them: for each but the
    last, the layer -- by place in the target's execution order -- whose incoming stream is read; the last, one past
    the target's last layer, is its final normed state.
    """

    hidden_size: int
    num_layers: int
    num_heads: int
    num_kv_heads: int
    head_dim: int
    intermediate_size: int
    rms_eps: float
    rope_theta: float
    window: int
    local_layers: tuple[int, ...]
    block: int
    markov_rank: int
    taps: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.num_heads % self.num_kv_heads:
            raise ValueError(f'{self.num_heads} query heads over {self.num_kv_heads} key heads')
        if self.head_dim % 2:
            raise ValueError(f'a rotary head of odd width {self.head_dim}')
        if self.block < 2:
            raise ValueError(f'a block of {self.block} slots drafts nothing')
        if len(self.taps) < 1 or list(self.taps) != sorted(set(self.taps)):
            raise ValueError(f'taps must ascend: {self.taps}')

    @property
    def drafts(self) -> int:
        """The tokens a block drafts."""

        return self.block - 1

    def is_local(self, i: int) -> bool:
        return i in self.local_layers


def dspark_config_from_hf(m: ta.Mapping[str, ta.Any]) -> DsparkConfig:
    """From a checkpoint's `mtp_config`."""

    kind = m.get('markov_head_type')
    if kind != 'rnn_hidden':
        raise ValueError(f'unsupported draft head {kind!r}')
    if m.get('q_bias') or m.get('o_bias'):
        raise ValueError('a drafter with attention biases is not supported')

    return DsparkConfig(
        hidden_size=int(m['hidden_size']),
        num_layers=int(m['num_hidden_layers']),
        num_heads=int(m['num_attention_heads']),
        num_kv_heads=int(m['num_key_value_heads']),
        head_dim=int(m['head_dim']),
        intermediate_size=int(m['intermediate_size']),
        rms_eps=float(m.get('rms_norm_eps', 1e-6)),
        rope_theta=float(m['rope_theta']),
        window=int(m['sliding_window_size']),
        local_layers=tuple(sorted(int(i) for i in m.get('local_layer_ids', ()))),
        block=int(m['block_size']),
        markov_rank=int(m['markov_rank']),
        taps=tuple(int(i) for i in m['target_layer_ids']),
    )
