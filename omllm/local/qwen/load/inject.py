from omcore import dataclasses as dc
from omcore import inject as inj

from ..tokenizer import Tokenizer
from .recipe import LoadRecipe
from .weights import TensorSource
from .weights import open_source


##


@dc.dataclass(frozen=True)
class LoadConfig:
    """
    What to load and how: `model` is an Ollama name, a .gguf / blob path or a Hugging Face checkpoint directory; quant,
    group, policy and quant_search make the recipe (load/recipe.py); cache_dir keeps the finished parameters.
    """

    model: str
    dtype: str | None = None  # default: the backend's (bf16 on accelerators, f32 on cpu)
    quant: str | None = None
    group: int = 64
    policy: str = 'uniform'
    quant_search: bool = True
    cache_dir: str | None = None
    mtp: bool = False


def _source(config: LoadConfig) -> TensorSource:
    return open_source(config.model)


def _recipe(config: LoadConfig) -> LoadRecipe:
    return LoadRecipe(
        quant=config.quant,
        group=config.group,
        search=config.quant_search,
        policy=config.policy,
    )


def _tokenizer(src: TensorSource) -> Tokenizer:
    return Tokenizer.from_spec(src.tokenizer_spec)


def bind_load(config: LoadConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(LoadConfig, to_const=config),
        inj.bind(TensorSource, to_fn=_source, singleton=True),
        inj.bind(LoadRecipe, to_fn=_recipe, singleton=True),
        inj.bind(Tokenizer, to_fn=_tokenizer, singleton=True),
    )
