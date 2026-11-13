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
    output_gate: str = 'silu'  # the Gated DeltaNet's gated-norm activation: 'silu' | 'sigmoid'
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


@dc.dataclass()
class Qwen4ExpConfig(Qwen35Config):
    """
    Qwen3.8-Flash-Next (`qwen4_exp`, FLASHNEXT.md): Qwen3.5's mixer geometry plus a mixture-of-experts feed-forward in
    every layer, the four-branch gated residual, QSA on the attention layers and the n-gram layer. `layer_types` are
    "linear" | "indexed"; `intermediate_size` is unused (no dense feed-forward). Defaults are the reference config's.
    """

    num_experts: int = 512
    num_experts_per_tok: int = 10
    moe_intermediate_size: int = 512
    shared_expert_intermediate_size: int = 512
    norm_topk_prob: bool = True

    hc_count: int = 4  # residual branches
    hc_lowrank: int = 320  # the read gate's bottleneck

    indexer_heads: int = 0  # QSA's indexer query heads (one key head)
    indexer_head_dim: int = 0
    indexer_budget: int = 0  # tokens selected from complete blocks per query
    indexer_compress_ratio: int = 0  # tokens per block

    ple_layers: list[int] = dc.field(default_factory=list)  # 0-indexed layers carrying the n-gram layer
    ple_embed_dim: int = 0
    ple_conv_kernel: int = 4
    ngram_size: int = 3
    heads_per_ngram: int = 8
    ngram_vocab_size_base: int = 20_000_000
    ngram_vocab_divisor: int = 128
    ngram_seed: int = 1234
    eos_id: int = 0  # what the n-gram hash shifts in at segment starts

    @property
    def block_topk(self) -> int:
        return self.indexer_budget // self.indexer_compress_ratio

    def summary(self) -> str:
        n_lin = sum(t == 'linear' for t in self.layer_types)

        return (
            f'hidden={self.hidden_size} x {self.hc_count} branches '
            f'layers={self.num_layers} ({n_lin} linear / {self.num_layers - n_lin} indexed) '
            f'vocab={self.vocab_size}'
            f'\n'

            f'  '
            f'moe : {self.num_experts} experts, top {self.num_experts_per_tok} x {self.moe_intermediate_size} '
            f'+ shared {self.shared_expert_intermediate_size}'
            f'\n'

            f'  '
            f'attn: {self.num_heads}q/{self.num_kv_heads}kv x {self.head_dim}, rope_dim={self.rope_dim}; '
            f'qsa {self.indexer_heads} x {self.indexer_head_dim}, budget {self.indexer_budget} '
            f'in blocks of {self.indexer_compress_ratio}'
            f'\n'

            f'  '
            f'gdn : {self.num_k_heads}k/{self.num_v_heads}v x {self.head_k_dim}, conv={self.conv_kernel}, '
            f'gate={self.output_gate}'
            f'\n'

            f'  '
            f'ple : layers {self.ple_layers}, {(self.ngram_size - 1) * self.heads_per_ngram} heads x '
            f'{self.ple_embed_dim} dims'
        )
