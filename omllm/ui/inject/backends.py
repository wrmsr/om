import os
import types
import typing as ta

from omcore import inject as inj
from omcore import lang
from omdev.home.secrets import load_secrets

from ... import agent as agn
from ... import llm
from ...core import registry as reg
from ..config import UiConfig
from ..types import InitialLlmOptions


##


def bind_backends(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    backend_cls: ta.Any
    backend: ta.Any
    if (config.model or llm.DEFAULT_MODEL_NAME) == 'scripted':
        # Offline development / testing: the scripted backend's built-in canned responses, no keys or network.
        if config.immediate:
            backend_cls = llm.ScriptedImmediateBackend
        else:
            backend_cls = llm.ScriptedStreamBackend

        backend = backend_cls(
            llm.Model(
                key=llm.ModelKey('scripted', 'scripted'),
                backend='scripted',
                reasoning_efforts=frozenset(llm.ReasoningEffort),
            ),
        )

        lst.append(inj.bind(
            agn.BackendManager,
            to_const=agn.DictBackendManager.of(backend),
        ))

    else:
        model = llm.default_models_by_name()[config.model or llm.DEFAULT_MODEL_NAME]
        llm_model = llm.provider_model_catalog()[model.key]

        if config.immediate:
            backend_cls = llm.ImmediateBackend
        else:
            backend_cls = llm.StreamBackend

        backend_impl_cls = reg.get_registry_cls(backend_cls, llm_model.backend_)

        async def provide_backend() -> agn.BackendManager:
            akr = llm.ApiKeyResolverImpl(
                secrets=load_secrets(),
                environ=types.MappingProxyType(os.environ),  # noqa
            )
            api_key = akr.resolve_first_api_key(model.api_keys or [])

            backend = backend_impl_cls(
                llm_model,
                **lang.opt_kw(
                    api_key=api_key,
                    base_url=config.url,
                    model_id=config.backend_model_id,
                ),
            )

            return agn.DictBackendManager.of(backend)

        lst.append(inj.bind(
            agn.BackendManager,
            to_async_fn=provide_backend,
            singleton=True,
        ))

    #

    lst.append(inj.bind(InitialLlmOptions, to_const=InitialLlmOptions(llm.Options(
        reasoning_effort=config.effort,
        thinking=config.thinking,
    ))))

    #

    return inj.as_elements(*lst)
