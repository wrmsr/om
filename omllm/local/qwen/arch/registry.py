"""Which architecture builds a source's model, by its config."""
from ..core.config import Qwen4ExpConfig
from ..core.config import Qwen35Config
from .qwen4exp import Qwen4ExpArchitecture
from .qwen35 import Qwen35Architecture


##


def architecture_for(cfg: Qwen35Config) -> Qwen35Architecture:
    if isinstance(cfg, Qwen4ExpConfig):
        return Qwen4ExpArchitecture()
    return Qwen35Architecture()
