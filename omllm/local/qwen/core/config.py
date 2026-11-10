from omcore import dataclasses as dc


##


@dc.dataclass()
class Qwen35Config:
    vocab_size: int
    hidden_size: int
    num_layers: int
    intermediate_size: int
    rms_eps: float
    # full attention
    num_heads: int
    num_kv_heads: int
    head_dim: int
    rope_theta: float
    rope_dim: int  # partial rotary: number of dims rotated (64 for head_dim 256)
    # gated delta net
    num_k_heads: int
    num_v_heads: int
    head_k_dim: int
    head_v_dim: int
    conv_kernel: int
    layer_types: list[str]  # "linear" | "full", len == num_layers
    context_length: int = 262144
    rope_scaling: dict | None = None
    tied_embeddings: bool = False
    num_mtp_layers: int = 0  # multi-token-prediction draft blocks after the text stack (1 for the 27B checkpoints)
    extra: dict = dc.field(default_factory=dict)

    @property
    def key_dim(self) -> int:
        return self.num_k_heads * self.head_k_dim

    @property
    def value_dim(self) -> int:
        return self.num_v_heads * self.head_v_dim

    @property
    def conv_dim(self) -> int:
        return 2 * self.key_dim + self.value_dim

    def summary(self) -> str:
        n_lin = sum(t == 'linear' for t in self.layer_types)

        return (
            f'hidden={self.hidden_size} '
            f'layers={self.num_layers} ({n_lin} linear / {self.num_layers - n_lin} full) '
            f'ffn={self.intermediate_size} '
            f'vocab={self.vocab_size}'
            f'\n'

            f'  '
            f'attn: {self.num_heads}q/{self.num_kv_heads}kv x {self.head_dim}, '
            f'rope_dim={self.rope_dim} '
            f'theta={self.rope_theta:g}'
            f'\n'

            f'  '
            f'gdn : {self.num_k_heads}k/{self.num_v_heads}v x {self.head_k_dim}, '
            f'conv={self.conv_kernel}'
            f'\n'

            f'  '
            f'tied_embeddings={self.tied_embeddings} '
            f'rope_scaling={self.rope_scaling}'
        )
