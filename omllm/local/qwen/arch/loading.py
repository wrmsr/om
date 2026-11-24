"""Loading a model from a source by hand, whichever architecture its config is."""
import os
import typing as ta

from ..core.model import Qwen35
from ..load.recipe import LoadRecipe
from ..load.weights import TensorSource
from ..ops.base import Ops
from .registry import architecture_for


##


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
    A model from a source -- whichever architecture its config is (registry.py): the Qwen3.5 family,
    Qwen3.8-Flash-Next, Inkling 2 -- for scripts, tests and the CLIs (the injector bindings use the architecture
    directly). The name is this package's first model's.

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

    def progress(done: int, total: int) -> None:
        if done % 50 == 1 or done == total:
            print(f'\r[model] loading tensors {done}/{total}', end='', flush=True)

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
