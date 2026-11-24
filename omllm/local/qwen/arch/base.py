"""
An architecture: what a checkpoint's parameters are and how they become a model -- which blocks, from which parts.
What the rest of the engine asks of one is to load a model from a source; an implementation -- a family's, in its
models/*/arch/ -- says how, with its own parameter names and loader layout through the shared pipeline
(load/pipeline.py).
Which architecture a source's model is, is its config's type (registry.py).
"""
import abc
import typing as ta

from omcore import lang

from ..core.model import Qwen35
from ..load.pipeline import LoadReport
from ..load.recipe import LoadRecipe
from ..load.weights import TensorSource
from ..ops.base import Ops


##


class Architecture(lang.Abstract):
    @abc.abstractmethod
    def load(
            self,
            src: TensorSource,
            ops: Ops,
            *,
            recipe: LoadRecipe,
            dtype: str = 'bf16',
            mtp: bool = False,
            cache_dir: str | None = None,
            on_progress: ta.Callable[[int, int], None] | None = None,
    ) -> tuple[Qwen35, LoadReport]:
        """
        The model from a source, and what the load did. `dtype` is the compute dtype's name; `mtp` also loads the
        architecture's draft head, where it has one; `cache_dir` keeps the finished parameters (load/paramcache.py).
        """

        raise NotImplementedError
