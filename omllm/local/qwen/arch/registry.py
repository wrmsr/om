"""Which architecture builds a source's model: by the type of its config."""
import typing as ta

from ..core.config import ModelConfig
from ..models.inkling.arch.inkling2 import Inkling2Architecture
from ..models.inkling.core.config import Inkling2Config
from ..models.qwen.arch.qwen4exp import Qwen4ExpArchitecture
from ..models.qwen.arch.qwen35 import Qwen35Architecture
from ..models.qwen.core.config import Qwen4ExpConfig
from ..models.qwen.core.config import Qwen35Config
from .base import Architecture


##


ARCHITECTURES: ta.Mapping[type[ModelConfig], ta.Callable[[], Architecture]] = {
    Qwen35Config: Qwen35Architecture,
    Qwen4ExpConfig: Qwen4ExpArchitecture,
    Inkling2Config: Inkling2Architecture,
}


def architecture_for(cfg: ModelConfig) -> Architecture:
    try:
        factory = ARCHITECTURES[type(cfg)]
    except KeyError:
        raise TypeError(f'no architecture for a {type(cfg).__name__}') from None
    return factory()
