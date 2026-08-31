import typing as ta

from omcore import inject as inj
from omdev.home.secrets import load_secrets

from .... import agent as agn
from .... import llm
from ....core import registry as reg
from ..config import Config
from ..models import DEFAULT_MODEL_NAME
from ..models import MODELS_BY_NAME


##


def bind_backends(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    backend_cls: ta.Any
    backend: ta.Any
    if (config.model or DEFAULT_MODEL_NAME) == 'scripted':
        # Offline development / testing: the scripted backend's built-in canned responses, no keys or network.
        if config.immediate:
            backend_cls = llm.ScriptedImmediateBackend
        else:
            backend_cls = llm.ScriptedStreamBackend

        backend = backend_cls(
            llm.Model(key=llm.ModelKey('scripted', 'scripted'), backend='scripted'),
        )

    else:
        model = MODELS_BY_NAME[config.model or DEFAULT_MODEL_NAME]
        llm_model = llm.default_model_catalog()[model.key]
        api_key_name = model.api_key_name

        if config.immediate:
            backend_cls = llm.ImmediateBackend
        else:
            backend_cls = llm.StreamBackend

        backend_impl_cls = reg.get_registry_cls(backend_cls, llm_model.backend)

        backend = backend_impl_cls(
            llm_model,
            **(dict(api_key=load_secrets().get(api_key_name)) if api_key_name is not None else {}),
        )

    lst.append(inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        }),
    ))

    return inj.as_elements(*lst)
