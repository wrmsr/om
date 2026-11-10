import os

from omcore import dataclasses as dc
from omcore import inject as inj

from ..ops.base import Ops
from .backends import make_ops


##


@dc.dataclass(frozen=True)
class BackendConfig:
    """
    The backend and its options. kv_dtype, compile and triton_tuned are torch options (ignored elsewhere, with a
    note); compile_cache_dir keeps torch.compile's artifacts between processes.
    """

    backend: str | None = None
    device: str | None = None
    kv_dtype: str = 'bf16'
    compile: bool = False
    compile_cache_dir: str | None = None
    triton_tuned: str | None = None


def _ops(config: BackendConfig) -> Ops:
    ops = make_ops(config.backend, config.device)

    if config.compile:
        if not hasattr(ops, 'compile'):
            raise ValueError('compile is a torch backend option')
        ops.compile = True
        if config.compile_cache_dir:
            cache = os.path.join(config.compile_cache_dir, 'torch-compile.bin')
            ops.compile_cache = cache  # type: ignore[attr-defined]

    if config.kv_dtype != 'bf16':
        if hasattr(ops, 'kv_dtype'):
            ops.kv_dtype = config.kv_dtype
        else:
            print(f'[model] kv_dtype {config.kv_dtype} is a torch backend option; the KV cache stays in the compute dtype')  # noqa

    if config.triton_tuned and hasattr(ops, 'gemv_tuned'):
        from .torch_triton import load_tuned

        ops.gemv_tuned = load_tuned(config.triton_tuned)
        print(f'[model] {len(ops.gemv_tuned)} tuned GEMV configs from {config.triton_tuned}')

    return ops


def bind_backend(config: BackendConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(BackendConfig, to_const=config),
        inj.bind(Ops, to_fn=_ops, singleton=True),
    )
