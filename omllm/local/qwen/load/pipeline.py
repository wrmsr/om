"""
The loader pipeline: canonical names -> planned specs (placement, precision, fusion; plan.py) -> adopted parameters
(the cache, native re-pack, or read + quantize; materialize.py), with a report of what came from where. The names and
the layout rules are inputs, so an architecture supplies them; the draft head is planned from its own names through the
same loader. Building the model from the parameters is the caller's (`Qwen35.from_source`).

    loader = ParamLoader(src, ops, recipe=LoadRecipe(quant='int4'), layout=QWEN35_LAYOUT, dtype='bf16', cache=cache)
    specs = loader.plan(required_param_names(cfg), optional=['lm_head.weight'])
    specs += loader.plan(mtp_param_names())
    params = loader.materialize(specs)
    loader.report()
"""
import collections
import typing as ta

from omcore import dataclasses as dc

from ..ops.base import Ops
from ..ops.base import Weight
from .materialize import Acquired
from .materialize import ParamMaterializer
from .paramcache import ParamCache
from .plan import LayoutRules
from .plan import ParamSpec
from .plan import plan_params
from .recipe import LoadRecipe


##


def open_param_cache(cache_dir: str, src: ta.Any, recipe: LoadRecipe) -> ParamCache:
    """The cache entry for this source and recipe: `<cache_dir>/<source identity>-<quant>-g<group>[-<variant>]`."""

    return ParamCache.open(
        cache_dir,
        src,
        recipe.quant,
        recipe.group,
        recipe.cache_variant(),
    )


@dc.dataclass(frozen=True)
class LoadReport:
    params: int
    acquired: ta.Mapping[str, int]  # 'cache' / 'repack' / 'quantize' / 'dense' -> parameters obtained that way
    quantized: int  # parameters held quantized
    nbytes: int
    backend: str
    recipe: LoadRecipe
    cache_root: str | None = None
    cache_hits: int = 0
    cache_misses: int = 0

    def summary(self) -> str:
        out = f'{self.nbytes / 2**30:.2f} GiB of weights on {self.backend}'

        if self.recipe.quant is not None:
            n = self.acquired
            out += (
                f', {self.quantized} of {self.params} held at {self.recipe.quant} ({self.recipe.describe()}): '
                f'{n.get("repack", 0)} re-packed, {n.get("quantize", 0)} quantized, {n.get("cache", 0)} cached'
            )

        if self.cache_root is not None:
            out += f'; cache {self.cache_root}: {self.cache_hits} hit / {self.cache_misses} miss'

        return out


class ParamLoader:
    def __init__(
            self,
            src: ta.Any,
            ops: Ops,
            *,
            recipe: LoadRecipe,
            layout: LayoutRules,
            dtype: str = 'bf16',
            cache: ParamCache | None = None,
    ) -> None:
        """
        `src` is a `load.weights.TensorSource`; `dtype` the compute dtype's name ('bf16', 'f16', 'f32'), with what
        `layout.keep_f32` matches staying float32; `cache` an opened parameter cache (`open_param_cache`) or None.
        """

        super().__init__()

        self._src = src
        self._ops = ops
        self._recipe = recipe
        self._layout = layout
        self._cache = cache
        self._cfg = src.config

        self._materializer = ParamMaterializer(
            src,
            ops,
            dtype=ops.dtype(dtype),
            group=recipe.group,
            search=recipe.search,
            cache=cache,
        )

        self._acquired: collections.Counter[str] = collections.Counter()
        self._quantized = 0
        self._params = 0
        self._nbytes = 0

    def plan(
            self,
            names: ta.Sequence[str],
            *,
            optional: ta.Sequence[str] = (),
    ) -> list[ParamSpec]:
        """Specs for `names` (all required) plus those of `optional` the source has."""

        available = set(self._src.names())

        missing = [n for n in names if n not in available]
        if missing:
            raise KeyError(f'source is missing {len(missing)} tensors, e.g. {missing[:5]}')

        return plan_params(
            [*names, *(n for n in optional if n in available)],
            layout=self._layout,
            width=lambda n: self._recipe.width(n, self._cfg),
            available=available,
        )

    def materialize(
            self,
            specs: ta.Sequence[ParamSpec],
            *,
            on_progress: ta.Callable[[int, int], None] | None = None,
    ) -> dict[str, Weight]:
        """The adopted parameters by name, in spec order. `on_progress(done, total)` is called after each one."""

        out: dict[str, Weight] = {}

        for i, spec in enumerate(specs):
            p, how, quantized = self._materializer.materialize(spec)
            out[spec.name] = p

            self._account(p, how, quantized)

            if on_progress is not None:
                on_progress(i + 1, len(specs))

        return out

    def _account(self, p: Weight, how: Acquired, quantized: bool) -> None:
        self._params += 1
        self._acquired[how] += 1
        self._quantized += int(quantized)
        self._nbytes += self._ops.nbytes(p)

    def report(self) -> LoadReport:
        cache = self._cache
        return LoadReport(
            params=self._params,
            acquired=dict(self._acquired),
            quantized=self._quantized,
            nbytes=self._nbytes,
            backend=self._ops.name,
            recipe=self._recipe,
            cache_root=str(cache.root) if cache is not None else None,
            cache_hits=cache.hits if cache is not None else 0,
            cache_misses=cache.misses if cache is not None else 0,
        )
