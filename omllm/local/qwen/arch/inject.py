from omcore import inject as inj
from omcore.logs import all as logs

from ..backends.backends import default_dtype
from ..core.model import Qwen35
from ..load.inject import LoadConfig
from ..load.recipe import LoadRecipe
from ..load.weights import TensorSource
from ..ops.base import Ops
from .qwen35 import Qwen35Architecture
from .registry import architecture_for


##


log = logs.get_module_logger(globals())


def _architecture(src: TensorSource) -> Qwen35Architecture:
    return architecture_for(src.config)


def _model(
        arch: Qwen35Architecture,
        src: TensorSource,
        ops: Ops,
        recipe: LoadRecipe,
        config: LoadConfig,
) -> Qwen35:
    model, report = arch.load(
        src,
        ops,
        recipe=recipe,
        dtype=config.dtype or default_dtype(ops),
        mtp=config.mtp,
        cache_dir=config.cache_dir,
    )
    log.info('%s', report.summary())
    return model


def bind_arch() -> inj.Elements:
    return inj.as_elements(
        inj.bind(Qwen35Architecture, to_fn=_architecture, singleton=True),
        inj.bind(Qwen35, to_fn=_model, singleton=True),
    )
