"""
The Qwen3.5 / 3.6 / 3.8 dense architecture's loading tables -- which tensors stay float32, which are never quantized,
which projections load fused -- which reach the loader pipeline as `QWEN35_LAYOUT` (Flash-Next builds its own from the
same parts).
"""
from ....load.plan import Fusion
from ....load.plan import LayoutRules
from ....load.plan import find_fusion


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


def fusion_of(name: str) -> tuple[str, list[str], int | None] | None:
    """For a canonical part name, the (fused name, all part names, bits override) it belongs to under `FUSIONS`."""

    return find_fusion(name, FUSIONS)


def is_quantizable(name: str, shape: tuple[int, ...], group: int) -> bool:
    if len(shape) != 2 or shape[1] % group:
        return False
    return not any(s in name for s in KEEP_F32 + NO_QUANT)
