"""
The entrypoints' side of the injector (inject/): their command-line options as each role's configuration, and the
generate entrypoint's assembly through the bindings (`generate --inject`; serve always assembles this way).
"""
import argparse
import time

from omcore import inject as inj

from ..backends.backends import default_dtype
from ..backends.inject import BackendConfig
from ..core.model import Qwen35
from ..decode.inject import DecodeConfig
from ..decode.runners import GenerationRunner
from ..inject.inject import bind_qwen
from ..load.inject import LoadConfig
from ..load.weights import TensorSource
from ..ops.base import Ops
from ..prefix.cache import PrefixCache
from ..prefix.inject import PrefixConfig
from ..spec.inject import LookupConfig
from ..spec.inject import SpecConfig
from ..tokenizer import Tokenizer
from .common import GenerationSetup


##


def backend_config(args: argparse.Namespace) -> BackendConfig:
    return BackendConfig(
        backend=args.backend,
        device=args.device,
        kv_dtype=args.kv_dtype,
        compile=args.compile,
        compile_cache_dir=args.cache_dir,
        triton_tuned=args.triton_tuned,
    )


def load_config(args: argparse.Namespace) -> LoadConfig:
    return LoadConfig(
        model=args.model,
        dtype=args.dtype,
        quant=args.quant,
        policy=args.policy,
        quant_search=not args.no_quant_search,
        cache_dir=args.cache_dir,
        mtp=args.spec > 0,
    )


def spec_config(args: argparse.Namespace) -> SpecConfig:
    return SpecConfig(
        k=args.spec,
        draft_vocab=args.draft_vocab,
    )


def lookup_config(args: argparse.Namespace) -> LookupConfig | None:
    if not args.lookup:
        return None
    return LookupConfig(
        ngram=args.lookup,
        k=args.lookup_k,
    )


def prefix_config(args: argparse.Namespace, *, enabled: bool) -> PrefixConfig:
    return PrefixConfig(
        enabled=enabled,
        device_mib=args.cache_device_mib,
        host_mib=args.cache_host_mib,
    )


##


def assemble_generation(args: argparse.Namespace, *, prefix_cache: bool) -> GenerationSetup:
    """
    The generate entrypoint's runner from the bindings: the same roles `ManualGenerationRunner` wires by hand, each
    generation in its own scope. The model is loaded here rather than inside the first generation's timing.
    """

    injector = inj.create_injector(bind_qwen(
        backend=backend_config(args),
        load=load_config(args),
        decode=DecodeConfig(
            capacity=args.capacity or 0,
            static=not args.functional,
            prefill_checkpoints=args.prefill_checkpoints if prefix_cache else 0,
            step_prefill_max=args.step_prefill_max,
        ),
        spec=spec_config(args),
        prefix=prefix_config(args, enabled=prefix_cache),
        lookup=lookup_config(args),
    ))

    ops = injector[Ops]
    print(f'[model] {injector[TensorSource].config.summary()}')
    t0 = time.time()
    injector[Qwen35]
    print(f'[model] loaded on {ops.name} as {args.dtype or default_dtype(ops)} in {time.time() - t0:.1f}s (injected)')

    return GenerationSetup(
        ops=ops,
        tok=injector[Tokenizer],
        runner=injector[GenerationRunner],
        prefix_cache=injector[PrefixCache] if prefix_cache else None,
    )
