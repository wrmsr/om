"""
The composition root: every role's bindings, and the one place the draft-source chain's order is spelled out. A
second architecture, a prompt-lookup draft source, a logit bias, a request log -- each is one more binder called here.
"""
from omcore import inject as inj

from ..arch.inject import bind_arch
from ..backends.inject import BackendConfig
from ..backends.inject import bind_backend
from ..constrain.inject import bind_constrain
from ..decode.drafts import DraftSource
from ..decode.inject import DecodeConfig
from ..decode.inject import bind_decode
from ..load.inject import LoadConfig
from ..load.inject import bind_load
from ..prefix.inject import PrefixConfig
from ..prefix.inject import bind_prefix
from ..serve.inject import ServeConfig
from ..serve.inject import bind_serve
from ..serve.serving import Engine
from ..spec.inject import LookupConfig
from ..spec.inject import SpecConfig
from ..spec.inject import bind_lookup
from ..spec.inject import bind_spec


##


def bind_qwen(
        *,
        backend: BackendConfig,
        load: LoadConfig,
        decode: DecodeConfig,
        spec: SpecConfig,
        prefix: PrefixConfig,
        lookup: LookupConfig | None = None,
        serve: ServeConfig | None = None,
) -> inj.Elements:
    drafts = inj.wrapper_binder_helper(DraftSource)

    lst: list[inj.Elemental] = [
        bind_backend(backend),
        bind_load(load),
        bind_arch(),
        bind_decode(decode),
        bind_constrain(),
        bind_prefix(prefix),

        # the draft-source chain, innermost first: the MTP head (or none), then what falls back to it
        bind_spec(spec, drafts),
        *([bind_lookup(lookup, drafts)] if lookup is not None else []),
        inj.bind(DraftSource, to_key=drafts.top),
    ]

    if serve is not None:
        lst.append(bind_serve(serve))

    return inj.as_elements(*lst)


def create_engine(
        *,
        backend: BackendConfig,
        load: LoadConfig,
        decode: DecodeConfig,
        spec: SpecConfig,
        prefix: PrefixConfig,
        serve: ServeConfig,
        lookup: LookupConfig | None = None,
) -> Engine:
    """A serving engine assembled by the injector (not started)."""

    injector = inj.create_injector(bind_qwen(
        backend=backend,
        load=load,
        decode=decode,
        spec=spec,
        prefix=prefix,
        lookup=lookup,
        serve=serve,
    ))
    return injector[Engine]
