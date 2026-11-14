from omcore import dataclasses as dc
from omcore import inject as inj

from ..decode.runners import GenerationRunner
from ..prefix.cache import PrefixCache
from ..tokenizer import Tokenizer
from .serving import Engine
from .serving import SamplingDefaults


##


@dc.dataclass(frozen=True)
class ServeConfig:
    defaults: SamplingDefaults = dc.field(default_factory=SamplingDefaults)
    enable_thinking: bool = True
    preserve_thinking: bool = True
    reasoning_effort: str | None = None  # None: the chat template's default, where it takes one
    open_think: bool = False  # the generation prompt opens the reasoning block, as the checkpoints' templates do
    max_queue: int = 4
    model_name: str = 'qwen'


def _engine(
        runner: GenerationRunner,
        tok: Tokenizer,
        config: ServeConfig,
        prefix_cache: PrefixCache | None = None,  # bound when prefix caching is on (prefix/inject.py): for its stats
) -> Engine:
    return Engine(
        runner,
        tok,
        prefix_cache=prefix_cache,
        defaults=config.defaults,
        enable_thinking=config.enable_thinking,
        preserve_thinking=config.preserve_thinking,
        reasoning_effort=config.reasoning_effort,
        open_think=config.open_think,
        max_queue=config.max_queue,
        model_name=config.model_name,
    )


def bind_serve(config: ServeConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(ServeConfig, to_const=config),
        inj.bind(Engine, to_fn=_engine, singleton=True),
    )
