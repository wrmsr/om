"""
Per-tensor precision policies: which width a parameter is quantized at, by its name, where a model's width is not
wanted for all of them. (Which tensors stay float32, are never quantized or load fused is an architecture's layout:
`LayoutRules`, plan.py, which each family supplies for its own layers.)
"""
import typing as ta


##


# name -> bits override (None = the model's width). 'km' is llama.cpp's Q4_K_M recipe with int8 where it uses Q6_K:
# attention value projections everywhere, the down projections of the first and last eighth of the layers, and the
# output head -- by the names the Hugging Face text layout gives them, which are Qwen's canonical ones; a parameter
# named otherwise keeps the model's width. (The Qwen layouts' a/b projections are int8 under every policy, by their
# fusion.)
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
