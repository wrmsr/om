import os
import types
import typing as ta

from omcore import inject as inj
from omcore.asyncs.asynclite import all as asl
from omdev.home.secrets import load_secrets

from ... import agent as agn
from ... import llm
from ...agent.inject.backends import BackendBinder
from ...agent.inject.backends import BackendModelOverrides
from ...agent.inject.backends import DispatchingBackendBinder
from ...agent.inject.backends import InjectorBackendOpener
from ...agent.inject.backends import RegistryBackendBinder
from ...agent.inject.backends import ScriptedBackendBinder
from ...agent.inject.backends import bind_backend_binder
from ...core.apikeys import ApiKeyResolver
from ...core.apikeys import ApiKeyResolverImpl
from ..types import InitialLlmOptions
from .config import BackendsConfig


##


# Offline development / testing: the scripted backend's built-in canned responses, no keys or network.
SCRIPTED_MODEL: ta.Final[llm.Model] = llm.Model(
    key=llm.ModelKey('scripted', 'scripted'),
    name='Scripted offline model',
    backend='scripted',
    short_ids=llm.ModelShortIds(short_id='scripted'),
    reasoning_efforts=frozenset(llm.ReasoningEffort),
)


def _resolve_default_model(config: BackendsConfig, catalog: llm.ModelCatalog) -> llm.Model:
    model_id = config.model or llm.DEFAULT_MODEL_SHORT_ID
    if model_id == 'scripted':
        return SCRIPTED_MODEL
    return catalog[model_id].model()


def _provide_api_key_resolver() -> ApiKeyResolver:
    return ApiKeyResolverImpl(
        secrets=load_secrets(),
        environ=types.MappingProxyType(os.environ),  # noqa
    )


def _provide_registry_backend_binder(
        config: BackendsConfig,
        catalog: llm.ModelCatalog,
        api_key_resolver: ApiKeyResolver,
) -> RegistryBackendBinder:
    overrides_by_model_key: dict[llm.ModelKey, BackendModelOverrides] = {}
    if config.url is not None or config.backend_model_id is not None:
        default_model = _resolve_default_model(config, catalog)
        if default_model.key is not None:
            overrides_by_model_key[default_model.key] = BackendModelOverrides(
                base_url=config.url,
                model_id=config.backend_model_id,
            )

    return RegistryBackendBinder(
        api_key_resolver=api_key_resolver,
        overrides_by_model_key=overrides_by_model_key,
    )


def _provide_dispatching_backend_binder(
        by_name: ta.Mapping[str, BackendBinder],
        default: RegistryBackendBinder,
) -> DispatchingBackendBinder:
    return DispatchingBackendBinder(
        by_name=by_name,
        default=default,
    )


def _provide_managed_backend_manager(
        config: BackendsConfig,
        catalog: llm.ModelCatalog,
        opener: agn.BackendOpener,
        events: asl.Events,
) -> agn.ManagedBackendManager:
    return agn.ManagedBackendManager(
        opener=opener,
        events=events,
        default_model=_resolve_default_model(config, catalog),
        no_prefer_stream=bool(config.immediate),
    )


def bind_backends(config: BackendsConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        inj.bind(BackendsConfig, to_const=config),

        inj.bind(llm.ModelCatalog, to_fn=llm.manifest_model_catalog, singleton=True),

        inj.bind(ApiKeyResolver, to_fn=_provide_api_key_resolver, singleton=True),

        inj.bind(ScriptedBackendBinder, singleton=True),
        bind_backend_binder('scripted', ScriptedBackendBinder),

        inj.bind(RegistryBackendBinder, to_fn=_provide_registry_backend_binder, singleton=True),
        inj.bind(DispatchingBackendBinder, to_fn=_provide_dispatching_backend_binder, singleton=True),
        inj.bind(BackendBinder, to_key=DispatchingBackendBinder),

        inj.bind(InjectorBackendOpener, singleton=True),
        inj.bind(agn.BackendOpener, to_key=InjectorBackendOpener),

        inj.bind(
            agn.ManagedBackendManager,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(_provide_managed_backend_manager),
        ),
        inj.bind(agn.BackendManager, to_key=agn.ManagedBackendManager),
    ])

    #

    lst.append(inj.bind(InitialLlmOptions, to_const=InitialLlmOptions(llm.Options(
        reasoning_effort=config.effort,
        thinking=config.thinking,
    ))))

    #

    return inj.as_elements(*lst)
