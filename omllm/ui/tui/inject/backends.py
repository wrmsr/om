import typing as ta

from omcore import inject as inj
from omdev.home.secrets import load_secrets

from .... import agent as agn
from .... import llm
from ....core import registry as reg
from ..config import Config


##


DEFAULT_MODEL: ta.Final = 'openai'

MODELS: ta.Final[ta.Mapping[str, tuple[llm.ModelKey, str | None]]] = {
    'openai': (llm.ModelKey('openai', 'gpt-5.6-luna'), 'openai_api_key'),
    'openrouter': (llm.ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731'), 'openrouter_api_key'),
    'groq': (llm.ModelKey('groq', 'openai/gpt-oss-120b'), 'groq_api_key'),
    'cerebras': (llm.ModelKey('cerebras', 'gpt-oss-120b'), 'cerebras_api_key'),
    'ollama': (llm.ModelKey('ollama', 'qwen3.8:27b'), None),
}


##


def bind_backends(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    backend_cls: ta.Any
    backend: ta.Any
    if (config.model or DEFAULT_MODEL) == 'scripted':
        # Offline development / testing: the scripted backend's built-in canned responses, no keys or network.
        if config.immediate:
            backend_cls = llm.ScriptedImmediateBackend
        else:
            backend_cls = llm.ScriptedStreamBackend

        backend = backend_cls(
            llm.Model(key=llm.ModelKey('scripted', 'scripted'), backend='scripted'),
        )

    else:
        model_key, api_key_name = MODELS[config.model or DEFAULT_MODEL]
        model = llm.default_model_catalog()[model_key]  # noqa

        if config.immediate:
            backend_cls = llm.ImmediateBackend
        else:
            backend_cls = llm.StreamBackend

        backend_impl_cls = reg.get_registry_cls(backend_cls, model.backend)

        backend = backend_impl_cls(
            model,
            **(dict(api_key=load_secrets().get(api_key_name)) if api_key_name is not None else {}),
        )

    lst.append(inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        }),
    ))

    return inj.as_elements(*lst)
