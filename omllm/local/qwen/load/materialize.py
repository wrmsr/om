"""
The second stage of the loader pipeline: a planned `ParamSpec` to a parameter adopted by the backend. In order of
preference: the parameter cache; a re-pack of tensors the source already holds quantized at the planned width (no
requantization, so no second rounding); the source's tensors read as float32 and quantized or adopted dense. Whatever
was computed goes back into the cache.
"""
import typing as ta

from omcore import lang

from ..ops.base import Ops
from ..ops.base import Weight
from ..ops.quant import QWeight
from ..ops.quant import from_native
from ..ops.quant import quantize as quantize_np
from .paramcache import ParamCache
from .plan import ParamSpec


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


Acquired: ta.TypeAlias = ta.Literal['cache', 'repack', 'quantize', 'dense']


##


class ParamMaterializer:
    def __init__(
            self,
            src: ta.Any,
            ops: Ops,
            *,
            dtype: ta.Any,
            group: int,
            search: bool,
            cache: ParamCache | None = None,
    ) -> None:
        """`dtype` is the backend's compute dtype (`ops.dtype(...)`); `src` a `load.weights.TensorSource`."""

        super().__init__()

        self._src = src
        self._ops = ops
        self._dtype = dtype
        self._f32 = ops.dtype('f32')
        self._group = group
        self._search = search
        self._cache = cache

    def _cached(self, spec: ParamSpec) -> tuple[Weight, bool] | None:
        if self._cache is None:
            return None

        got = self._cache.get(spec.name)
        if got is None:
            return None

        if isinstance(got, QWeight):
            return self._ops.qweight(got, self._dtype, name=spec.name), True

        return self._ops.weight(got, self._f32 if spec.keep_f32 else self._dtype, name=spec.name), False

    def _repacked(self, spec: ParamSpec, bits: int) -> Weight | None:
        """Every part natively quantized at the planned width and group: stacked as-is (their codes are rows)."""

        natives = [self._src.get_quant(p) for p in spec.parts]
        if not all(nq is not None and nq.bits == bits and nq.group == self._group for nq in natives):
            return None

        qw = from_native(
            np.concatenate([nq.values for nq in natives], 0),
            np.concatenate([nq.scale for nq in natives], 0),
            np.concatenate([nq.bias for nq in natives], 0),
            bits,
            self._group,
        )
        if self._cache is not None:
            self._cache.put(spec.name, qw)

        return self._ops.qweight(qw, self._dtype, name=spec.name)

    def _read(self, spec: ParamSpec) -> np.ndarray:
        if len(spec.parts) == 1:
            return np.array(self._src.get(spec.parts[0]), dtype=np.float32, copy=True)

        return np.concatenate([np.asarray(self._src.get(p), dtype=np.float32) for p in spec.parts], 0)

    def _quantized(self, spec: ParamSpec, arr: np.ndarray, bits: int) -> Weight:
        ops = self._ops

        if self._cache is None:
            return ops.quantize(arr, bits, self._group, self._dtype, self._search, name=spec.name)

        try:  # quantize on the device (fast) and export it for the cache; else the canonical numpy quantizer
            p = ops.quantize(arr, bits, self._group, self._dtype, self._search, name=spec.name)
            qw = ops.export_qweight(p)
        except NotImplementedError:
            qw = quantize_np(arr, bits, self._group, self._search)
            p = ops.qweight(qw, self._dtype, name=spec.name)

        self._cache.put(spec.name, qw)
        return p

    def materialize(self, spec: ParamSpec) -> tuple[Weight, Acquired, bool]:
        """The adopted parameter, how it was obtained, and whether it is held quantized."""

        if (got := self._cached(spec)) is not None:
            return got[0], 'cache', got[1]

        bits = spec.bits

        if bits is not None and (p := self._repacked(spec, bits)) is not None:
            return p, 'repack', True

        arr = self._read(spec)

        if bits is not None and arr.ndim == 2 and arr.shape[1] % self._group == 0:
            return self._quantized(spec, arr, bits), 'quantize', True

        if self._cache is not None:
            self._cache.put(spec.name, arr)

        return self._ops.weight(arr, self._f32 if spec.keep_f32 else self._dtype, name=spec.name), 'dense', False
