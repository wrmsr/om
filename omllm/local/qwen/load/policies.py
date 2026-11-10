# ruff: noqa: N803 N806 N812
"""
The Qwen3.5 / 3.6 / 3.8 dense architecture's loading tables -- which tensors stay float32, which are never quantized,
which projections load fused -- and the per-tensor precision policies. The tables reach the loader pipeline as
`QWEN35_LAYOUT`; an architecture with other layers supplies its own.
"""
import typing as ta

from .plan import Fusion
from .plan import LayoutRules
from .plan import find_fusion


##


# tensors that stay in float32 whatever the compute dtype
KEEP_F32 = (
    'norm',
    'linear_attn.A',
    'dt_bias',
    'conv1d',
)

# 2-D weights that are never quantized: the low-rank DeltaNet projections are quantization-sensitive (Ollama's own
# converter also keeps them at source precision)
NO_QUANT = (
    'in_proj_a',
    'in_proj_b',
)


# Projections that share an input are loaded as one weight stacked along the output dim: one GEMV launch instead of two
# or three, and a wider N streams better. (fused suffix, part suffixes, bits override). The a/b pair is kept separate
# from qkv/z because it is stored at int8 whatever the model's width.
FUSIONS: tuple[Fusion, ...] = (
    (
        'mlp.gate_up_proj.weight',
        ('mlp.gate_proj.weight', 'mlp.up_proj.weight'),
        None,
    ),
    (
        'self_attn.qkv_proj.weight',
        ('self_attn.q_proj.weight', 'self_attn.k_proj.weight', 'self_attn.v_proj.weight'),
        None,
    ),
    (
        'linear_attn.in_proj_qkvz.weight',
        ('linear_attn.in_proj_qkv.weight', 'linear_attn.in_proj_z.weight'),
        None,
    ),
    (
        'linear_attn.in_proj_ab.weight',
        ('linear_attn.in_proj_a.weight', 'linear_attn.in_proj_b.weight'),
        8,
    ),
)


QWEN35_LAYOUT = LayoutRules(
    fusions=FUSIONS,
    keep_f32=KEEP_F32,
    no_quant=NO_QUANT,
)


# Per-tensor precision policies: name -> bits override (None = the model's width). 'km' is llama.cpp's Q4_K_M recipe
# with int8 where it uses Q6_K: attention value projections everywhere, the down projections of the first and last
# eighth of the layers, and the output head. (The a/b projections are int8 under every policy, via FUSIONS.)
def _policy_uniform(name: str, cfg: ta.Any) -> int | None:
    return None


def _policy_km(name: str, cfg: ta.Any) -> int | None:
    if name.endswith('self_attn.v_proj.weight') or name == 'lm_head.weight':
        return 8
    if name.endswith('mlp.down_proj.weight') and name.startswith('layers.'):
        i = int(name.split('.')[1])
        n = cfg.num_layers
        if i < (n + 7) // 8 or i >= n - (n + 7) // 8:
            return 8
    return None


POLICIES: dict[str, ta.Callable[[str, ta.Any], int | None]] = {
    'uniform': _policy_uniform,
    'km': _policy_km,
}


def fusion_of(name: str) -> tuple[str, list[str], int | None] | None:
    """For a canonical part name, the (fused name, all part names, bits override) it belongs to under `FUSIONS`."""

    return find_fusion(name, FUSIONS)


def is_quantizable(name: str, shape: tuple[int, ...], group: int) -> bool:
    if len(shape) != 2 or shape[1] % group:
        return False
    return not any(s in name for s in KEEP_F32 + NO_QUANT)
