# ruff: noqa: N803 N806 N812
"""
tinygrad backend for `Ops`.

tinygrad is lazy: every op appends to a graph and nothing runs until `.realize()` / `.numpy()`. `eval()` forces it. Like
MLX, the per-token `gated_delta` reference builds a T-step graph, so a chunked prefill (behind `Ops.gated_delta`) is
required for long prompts here, not just an optimisation.

Two facts about this tinygrad decide the shape of everything below. Scheduling a graph eagerly costs milliseconds of
Python per graph (and grows faster than linearly with its size), whatever the kernels do; a `TinyJit` replay costs a
couple of microseconds per kernel and ~0.15 ms per call, the whole graph being one hardware queue submission. So a
decode step must be one replay with nothing scheduled eagerly around it:

* `capture` holds the step's arrays: the first call's tables and state become buffers the jitted function closes over,
  and the state carry is done inside it -- a DeltaNet layer's new state is `assign`ed into the buffer it came from,
  `kv_write` writes into the KV buffer in place -- so the replay reads and writes fixed memory and the outputs for the
  state *are* those buffers (the object identity the torch CUDA-graph step relies on too). A step is captured once per
  process per shape and shared by every Decoder (`TinyJitStepHandle`); a Decoder that brings other state has it carried
  in.
* The position is a tinygrad `Variable` bound per call: `scalar()` makes a 0-d constant the wrapper swaps for the
  variable, so the model's arithmetic on it is symbolic, `kv_write` writes at a symbolic index, and `sdpa_static`
  attends over a symbolic-length window of the buffers (`kbuf[:, :, :pos + T]`): one captured step for the whole
  capacity whose attention cost follows the sequence (`attn_bucketed = False`). A decode step's token is a bound
  variable too (`array()` of one int), so the embedding is a slice and nothing is copied to the device per token.
* Speculative `commit` selects `stacked[m]` from the verify step's per-token states; that is recognised structurally and
  copied into the held buffers by a small JIT with `m` bound. Anything else handed back (a prefix-cache restore) is an
  eager copy, once. The decoder's commit function (`Ops.capture_carrying` with nothing but state coming out) is not
  captured for that reason: it runs as it is built, its picks at a count the graph knows (`select_at`, `kv_take`) the
  plain shrinks that are recognised.
* What the engine computes *between* steps -- the token sampled from the logits, the drafts and their probabilities, a
  round's acceptance -- is captured as well (`realized`): a graph keyed by itself, its bound variables (random pool
  offsets, token ids) the inputs, replayed whenever the same graph is built again; `numpy()` lands its result in a
  CPU-mapped buffer so the read schedules nothing. A greedy token is then two replays; a speculative round about a
  dozen.
* A step is realized per layer (`materialize`, which the model calls in its static step as in its forward), so a
  64-layer step is scheduled as 64 small graphs during capture, not one huge one, and no layer's output is left pending
  for later layers' realizations to recompute.

Weights are adopted into a few large slab buffers and held as views (`_adopt`): a step's submission takes one argument
per buffer it touches, and sixty-four layers of individually adopted tensors exceed what tinygrad can call. Quantized
codes stay packed as uint32 words (quant.QWeight's bytes as little-endian words, so a parameter cache round-trips bit
for bit), dequantized inside the matmul kernel for small token counts (decode and verify: the words are read once per
output) and into a materialised bf16 weight for prefill, where the matmul is a plain GEMM.

tinygrad's heuristics leave the GEMV an order of magnitude short of memory bandwidth; its kernel search (`beam`, the
CLIs' `--compile`) reaches it, once per kernel shape, persisted in tinygrad's cache database.

This GPU has no resizable BAR, so the memory tinygrad maps for the CPU -- a slice per eagerly compiled graph, kept as
long as its template is cached -- is a budget of a couple of hundred megabytes per process. tinygrad keys a graph's
template by its structure, so the ones that recur are one entry; symbolic offsets keep their structure stable, the
template cache is dropped past a count (`MAX_EAGER_TEMPLATES`), and steps are captured once. Two tinygrad processes
sharing the GPU share the budget.

`copy()` is eager: a lazy clone of a buffer that a later replay overwrites in place would read the overwritten data.
Except inside a step being captured. A capture runs nothing: tinygrad records what the capturing function schedules
and runs it once the capture is over, and no JIT may be captured within another. So there a copy is one more value of
the step's (what a step copies is state it hands back, which lands in a held buffer), and nothing in a step may read a
value on the host -- `Ops.expert_linear_grouped`, which reads which experts its rows chose, is for code that runs as
it is built.

A JIT's outputs are scratch its next replay overwrites, and nothing that lives on may be left pointing at them. What
a graph JIT computes therefore lands in buffers allocated for the call (`realized`): in a forward that runs as it is
built the same graph comes round again with the last one's values still live (every layer of a kind is one structure,
and Inkling 2 runs a layer three times a token and reads the block sums of the pass before). And before a captured
step runs again, whatever still pends on its last outputs is computed (`TinyJitStep._settle_readers`): the engine
reads what it wants of a step's outputs before the next, which here is no more than a graph.

Experts stored in a microscaled float format stay packed (`TinyMicroscaledExperts`) and are decoded by arithmetic on
their bytes' bits, exactly: each expert once from a slice of the stack where the rows' experts can be read, each
row's by a gather inside a captured step.
"""
import collections
import typing as ta
import weakref

from omcore import dataclasses as dc
from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.microscaled import MicroscaledWeight
from ..ops.quant import QWeight


if ta.TYPE_CHECKING:
    import numpy as np  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad as tg  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad.device as tg_device  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad.engine.realize as tg_realize  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad.runtime.support.hcq2 as tg_hcq  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad.tensor as tg_tensor  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import tinygrad.uop.ops as tg_uops  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    np = lang.proxy_import('numpy')
    tg = lang.proxy_import('tinygrad')
    tg_uops = lang.proxy_import('tinygrad.uop.ops')
    tg_hcq = lang.proxy_import('tinygrad.runtime.support.hcq2')
    tg_realize = lang.proxy_import('tinygrad.engine.realize')
    tg_tensor = lang.proxy_import('tinygrad.tensor')
    tg_device = lang.proxy_import('tinygrad.device')


##


def dtypes() -> dict[str, ta.Any]:
    """Compute dtype names -> tinygrad dtypes (a function: tinygrad is imported lazily)."""

    return {
        'f32': tg.dtypes.float32,
        'f16': tg.dtypes.float16,
        'bf16': tg.dtypes.bfloat16,
        'i32': tg.dtypes.int32,
        'i64': tg.dtypes.int64,
    }


def _tg_unwrap(t: ta.Any) -> ta.Any:
    """A one-element tensor's value node: casts and reshapes stripped, constants folded."""

    O = tg_uops.Ops
    u = t.uop.simplify()
    while u.op in (O.CAST, O.RESHAPE, O.EXPAND):
        u = u.src[0]
    return u


def _tg_sint(t: ta.Any) -> ta.Any:
    """
    A one-element int tensor as a tinygrad shape int -- a python int when it is a constant, its expression when it is
    symbolic (`pos + i` inside a captured step, a token bound to a variable) -- or None when it is a device value.
    """

    u = _tg_unwrap(t)
    if u.op is tg_uops.Ops.CONST:
        return int(u.arg)

    if u.device is None:  # an expression over variables
        return u

    return None


def _tg_value(t: ta.Any) -> int | None:
    """The python int a one-element tensor holds: a constant's, or the value its variable is bound to; else None."""

    u = _tg_unwrap(t)
    if u.op is tg_uops.Ops.CONST:
        return int(u.arg)

    if u.is_bound_var:
        return int(u.arg.val)

    return None


def _tg_run(positions: ta.Any, ar: ta.Any) -> ta.Any:
    """
    The start of `positions` when they are start + `ar`, the backend's arange of their length, for a start the graph
    knows: a python int or an expression, as `_tg_sint` gives it. None for any other positions.
    """

    u = positions.uop
    if u.op is not tg_uops.Ops.ADD:
        return None

    for start, run in (u.src, u.src[::-1]):
        if run is ar.uop:
            return _tg_sint(tg.Tensor(start))

    return None


def _tg_static(b) -> bool:
    """
    Whether a graph's base is a realized buffer, or a bitcast view of one (how a weight sees its slab: tinygrad's
    predicates call that pending, but it is a view, and never holds computation).
    """

    O = tg_uops.Ops
    if b.op is O.BITCAST:
        b = b.src[0].base
    return b.op is O.BUFFER and b.is_realized


def _tg_jit(fn: ta.Callable[..., ta.Any]) -> ta.Any:
    """
    A `TinyJit` that captures its first call. tinygrad's runs the function through once before capturing on the second,
    a warm-up for inputs that are not yet buffers; here every input and held buffer is realized before the call
    (`realized`, `TinyJitStep._hold`), and the run-through costs what the capture does: over a minute of eager
    scheduling for the 16-token prefill step of the 27B, a quarter second for each graph JIT.
    `TinygradOps.CAPTURE_FIRST` off restores the two runs.
    """

    jit = tg.TinyJit(fn)
    if TinygradOps.CAPTURE_FIRST:
        jit.cnt = 1  # the call the capture happens on (`reset()` puts it back to 0)
    return jit


def _tg_const_value(a: ta.Any) -> ta.Any:
    """The value when `a` is a constant (`TinygradOps.zeros`: no storage, one value broadcast), else None."""

    u = a.uop
    if not u.is_virtual:
        return None

    b = u.base
    if b.op is not tg_uops.Ops.CONST:
        return None

    return b.arg


def _tg_slab(a: ta.Any, shape: tuple[int, ...]) -> tuple[ta.Any, int, int] | None:
    """
    (buffer, m, n) when `a` is `stacked[m]` for a realized `stacked` of shape (n, *shape) -- the per-token state a
    speculative commit selects -- else None. Matched on the graph's structure (a slice of the first axis, reshaped),
    which is cheap; tinygrad's general view-offset query is not.
    """

    O = tg_uops.Ops

    u = a.uop
    if u.op is not O.RESHAPE or u.src[0].op is not O.SHRINK:
        return None

    sh = u.src[0]

    base = sh.src[0]
    if not base.has_buffer_identity() or not base.is_realized:
        return None
    if tuple(base.shape[1:]) != tuple(shape):
        return None

    (m, size), *rest = sh.marg
    if not isinstance(m, int) or size != 1:
        return None

    if any(lo != 0 or sz != d for (lo, sz), d in zip(rest, base.shape[1:])):
        return None

    return base.base, m, int(base.shape[0])


##


class _TgSlab:
    """A slab being filled: the placeholder its views are made over, the bytes so far, and how much is used."""

    def __init__(self, placeholder: ta.Any, extent: int) -> None:
        super().__init__()

        self.placeholder = placeholder
        self.extent = extent
        self.parts: list[tuple[int, np.ndarray]] = []
        self.used = 0


@dc.dataclass()
class TinyQWeight:
    q: tg.Tensor  # uint32 [out, in * bits // 32]: quant.QWeight's packed bytes as little-endian words
    scale: tg.Tensor  # compute dtype
    bias: tg.Tensor
    bits: int
    group: int
    shape: tuple[int, int]
    shifts: tg.Tensor  # uint32 [1, 1, 32 // bits]: the bit offset of each value in a word

    # token counts up to this go through the fused dequant-in-the-matmul kernel; beyond, the weight is materialised
    GEMV_MAX_M: ta.ClassVar[int] = 8

    def nbytes(self) -> int:
        return self.q.nbytes() + self.scale.nbytes() + self.bias.nbytes()

    def codes(self, rows: slice | tg.Tensor | None = None) -> tg.Tensor:
        """uint32 [rows, in], one value per element."""

        q = self.q if rows is None else self.q[rows]
        n, words = q.shape
        per = 32 // self.bits
        u = q.reshape(n, words, 1).expand(n, words, per) >> self.shifts
        return (u & ((1 << self.bits) - 1)).reshape(n, self.shape[1])

    def dequant(self, dtype: ta.Any, rows: slice | tg.Tensor | None = None) -> tg.Tensor:
        s = self.scale if rows is None else self.scale[rows]
        b = self.bias if rows is None else self.bias[rows]
        c = self.codes(rows)
        n = c.shape[0]
        x = c.reshape(n, -1, self.group).cast(dtype)
        x = x * s[..., None].cast(dtype) + b[..., None].cast(dtype)
        return x.reshape(n, self.shape[1])

    def linear(self, x: tg.Tensor, chunk_rows: int = 16384) -> tg.Tensor:
        out = self.shape[0]
        m = x.numel() // x.shape[-1]

        if m <= self.GEMV_MAX_M:
            # one kernel: the packed words stream once and are expanded in registers against the few rows of x. The rows
            # are materialized first: left as an expression (a norm's scaling, the gate times the up projection),
            # tinygrad folds it into the kernel and recomputes it for every output row, two to three times the time
            return x.contiguous() @ self.dequant(x.dtype).T

        # prefill: a materialised weight makes the matmul a plain GEMM (tensor cores); chunked, each chunk realized
        # before the next, so the output head's 2.5 GB expansion is never resident at once (left to one schedule, every
        # chunk's expansion stays alive until the concatenation)
        parts = []
        for i in range(0, out, chunk_rows):
            part = x @ self.dequant(x.dtype, slice(i, i + chunk_rows)).contiguous().T
            if out > chunk_rows:
                part = part.realize()
            parts.append(part)

        if len(parts) == 1:
            return parts[0]

        return tg.Tensor.cat(*parts, dim=-1)


##


def _tg_e2m1(c: ta.Any) -> ta.Any:
    """
    float32 values of 4-bit E2M1 codes (uint32, 0 .. 15: sign, two exponent bits, one mantissa bit), by arithmetic on
    the bits -- a normal code's value is a float32 whose own bits are the code's, moved into place -- where a table
    lookup would be a gather tinygrad spells as a comparison against every entry.
    """

    f32 = tg.dtypes.float32
    sign = c >> 3
    exp = (c >> 1) & 3
    man = c & 1
    normal = ((sign << 31) | ((exp + 126) << 23) | (man << 22)).bitcast(f32)  # (1 + man / 2) * 2 ** (exp - 1)
    low = man.cast(f32) * 0.5 * (1 - 2 * sign.cast(f32))  # exponent 0: man / 2
    return (exp > 0).where(normal, low)


def _tg_e4m3(b: ta.Any) -> ta.Any:
    """float32 values of 8-bit E4M3 codes (sign, four exponent bits biased by 7, three mantissa bits), likewise."""

    f32 = tg.dtypes.float32
    u = b.cast(tg.dtypes.uint32)
    sign = u >> 7
    exp = (u >> 3) & 0xF
    man = u & 7
    normal = ((sign << 31) | ((exp + 120) << 23) | (man << 20)).bitcast(f32)  # (1 + man / 8) * 2 ** (exp - 7)
    low = man.cast(f32) * (2.0 ** -9) * (1 - 2 * sign.cast(f32))  # exponent 0: man / 8 * 2 ** -6
    return (exp > 0).where(normal, low)


def _tg_pow2(b: ta.Any) -> ta.Any:
    """float32 2 ** (byte - 127): the byte is the float's exponent field (byte 0, a subnormal, is one mantissa bit)."""

    u = b.cast(tg.dtypes.uint32)
    return (u > 0).where(u << 23, 1 << 22).cast(tg.dtypes.uint32).bitcast(tg.dtypes.float32)


@dc.dataclass()
class TinyMicroscaledExperts:
    """
    E experts stored in a microscaled float format (ops/microscaled.py), as the checkpoint has them: `codes` uint8
    [E, N, K / 2] (nvfp4: two 4-bit codes a byte, low nibble first) or [E, N, K] (mxfp8), `scales` uint8
    [E, N, K / block], `outer` float32 [E] (nvfp4). The experts a matmul reads are decoded by arithmetic on the bytes,
    in float32 (the products exact), then rounded to the compute dtype.
    """

    fmt: str
    codes: tg.Tensor
    scales: tg.Tensor
    outer: tg.Tensor | None
    block: int
    shape: tuple[int, int]  # one expert's (N, K)

    def nbytes(self) -> int:
        return self.codes.nbytes() + self.scales.nbytes() + (self.outer.nbytes() if self.outer is not None else 0)

    def dequant(self, dtype: ta.Any, experts: slice | tg.Tensor) -> tg.Tensor:
        """The given experts' weights, [R, N, K] in `dtype`: a slice of the stack, or a row's expert each (a gather)."""

        n, k = self.shape
        codes = self.codes[experts]
        scales = self.scales[experts]
        r = codes.shape[0]

        if self.fmt == 'nvfp4':
            u = codes.cast(tg.dtypes.uint32)
            x = _tg_e2m1(tg.Tensor.stack(u & 0xF, u >> 4, dim=-1).reshape(r, n, k))
            s = _tg_e4m3(scales)
            if self.outer is not None:
                s = s * self.outer[experts].reshape(r, 1, 1)
        else:
            x = _tg_e4m3(codes)
            s = _tg_pow2(scales)

        w = x.reshape(r, n, k // self.block, self.block) * s.reshape(r, n, k // self.block, 1)
        return w.reshape(r, n, k).cast(dtype)


##


class TinyJitStep:
    """
    The capture of a static-shape step function `fn(toks, [hidden,] pos, ar, *tables, *state)` (see the module
    docstring): tables and state are held buffers the jitted function closes over, the position is a bound `Variable`,
    the state carry is in place, and what a caller hands back that is not the held buffer is copied in -- a `stacked[m]`
    selection by a second JIT with `m` bound, anything else eagerly.

    `state_from`: the index of the first state argument, where the caller says (`Ops.capture_carrying`). Left
    unsaid, the tables are taken to be the arguments after the position with one or two dimensions -- `ar`
    [capacity], an architecture's own [capacity, n] -- and the state everything from the first with more (a state
    array has a batch axis and at least two more).

    A draft model's functions over its memory are captured the same way (models/inkling/spec/dspark.py): the write of a
    step's rows is a step in every respect; a block's drafts take one token, have their sampler's arguments between the
    position and `ar`, and hand no state back.
    """

    DEFAULT_BEAM: ta.ClassVar[int] = 1  # depth 2 gains ~15% on the GEMV for several times the search

    def __init__(
            self,
            ops: TinygradOps,
            fn: ta.Callable[..., tuple[Array, ...]],
            state_from: int | None = None,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._fn = fn
        self._state_from = state_from
        self._statics: list[ta.Any] = []
        self._given: list[ta.Any] = []  # what stands between the position and the state, as last given: `_carry_in`
        self._n_in = 0  # args before the position: JIT inputs (tokens, the draft head's hidden rows)
        self._pos_i = 0
        self._state_i0 = 0  # the first state arg (after the position and the tables)
        self._var: ta.Any = None

        # inputs that are symbolic values rather than buffers (a token `array()` made from one int): (slot, variable,
        # shape); bound per call like the position, so nothing is scheduled to get them onto the device
        self._sym_in: list[tuple[int, ta.Any, tuple[int, ...]]] = []

        self._jit: ta.Any = None
        self._out_bufs: ta.AbstractSet[ta.Any] = frozenset()  # the buffers a run hands back: see `_settle_readers`
        self._copyins: dict[tuple[ta.Any, ...], tuple[ta.Any, ta.Any]] = {}
        self._fills: dict[tuple[tuple[int, ta.Any], ...], ta.Any] = {}

    def _hold(self, args: ta.Sequence[ta.Any]) -> list[ta.Any]:
        """
        The held buffers for the state arguments, realized in one schedule. A realized buffer is held as is (another
        step on the same state shares it); a pending value is realized into one (not copied: the pending value's own
        realization would stay alive beside the copy, and at capacity the KV buffers are gigabytes); a view of a
        realized buffer gets its own; a constant (a state started from zeros, see `TinygradOps.zeros`) has no storage of
        its own, and gets a buffer filled from it. One schedule for all of them: each costs a quarter second of Python
        on its own, and a decoder starting from nothing holds a hundred and seventy.
        """

        held = []
        pending = []
        for a in args:
            if a.uop.is_virtual:
                a = tg.Tensor.empty(*a.shape, dtype=a.dtype, device=self._ops.device).assign(a)
                pending.append(a)
            elif not a.uop.base.is_realized:
                pending.append(a)
            elif not a.uop.has_buffer_identity():
                a = a.contiguous()
                pending.append(a)
            held.append(a)
        if pending:
            tg.Tensor.realize(*pending)
        return held

    def _setup(self, args: tuple[ta.Any, ...]) -> None:
        self._ops.release_cached()  # the held buffers are large (the KV at capacity): a prefill's temporaries go first
        pos_i = next(i for i, a in enumerate(args) if a.ndim == 0)
        # the rows of a step are along its first argument's second axis (tokens, hidden rows); a function of one
        # token ([1]) is at one position
        T = args[0].shape[1] if args[0].ndim > 1 else 1
        cap = next(a.shape[0] for a in args[pos_i + 1:] if a.ndim == 1)  # ar: arange(capacity)
        self._pos_i = pos_i
        self._n_in = pos_i
        if self._state_from is not None:
            self._state_i0 = self._state_from
        else:
            self._state_i0 = next((i for i in range(pos_i + 1, len(args)) if args[i].ndim > 2), len(args))
        # the step runs T tokens at pos..pos+T-1, so pos + T <= capacity: the bound every symbolic slice is proved from
        self._var = tg.Variable('pos', 0, cap - T, dtype=tg.dtypes.int32)
        self._sym_in = [
            (i, tg.Variable(f'in{i}', 0, 2**31 - 1, dtype=tg.dtypes.int32), tuple(a.shape))
            for i, a in enumerate(args[:pos_i])
            if a.uop.is_virtual
        ]
        self._statics = [None] * (pos_i + 1) + self._hold(args[pos_i + 1:])
        self._given = [None] * (pos_i + 1) + list(args[pos_i + 1:self._state_i0])
        self._jit = _tg_jit(self._run)

    def _run(self, posv: ta.Any, *rest: ta.Any) -> tuple[ta.Any, ...]:
        statics = self._statics
        call = list(statics)
        n_sym = len(self._sym_in)
        for (i, _, shape), bv in zip(self._sym_in, rest[:n_sym]):
            call[i] = tg.Tensor(bv).reshape(shape)
        ins = iter(rest[n_sym:])
        for i in range(self._n_in):
            if call[i] is None:
                call[i] = next(ins)
        call[self._pos_i] = tg.Tensor(posv)

        outs = list(self._fn(*call))

        # the state a step hands back is its last outputs, as many as it took; a function that returns fewer hands
        # none back (a block's drafts read the draft model's memory and write nothing)
        n_state = len(statics) - self._state_i0
        if len(outs) < n_state:
            n_state = 0
        n_lead = len(outs) - n_state
        for j in range(n_state):
            s = statics[self._state_i0 + j]
            o = outs[n_lead + j]
            if o is s:  # written in place (kv_write)
                continue
            if o.shape == s.shape:  # the carry: the new state lands in the buffer it came from
                s.assign(o)
                outs[n_lead + j] = s
            # else a per-token stack (verify): a plain output the caller selects from

        tg.Tensor.realize(*outs)
        return tuple(outs)

    def _copyin(self, slots: tuple[int, ...], n: int, bases: tuple[ta.Any, ...]) -> tuple[ta.Any, ta.Any]:
        """
        The JIT that copies entry m of each stacked per-token state (`bases`: the producing step's output buffers, which
        its JIT reuses replay after replay) into the held buffers. The buffers are captured, not passed: a hundred and
        forty-four inputs cost milliseconds of checking a call. A re-captured producer has new ones, and the key misses.
        """

        key = (slots, n, bases)

        got = self._copyins.get(key)
        if got is None:
            self._copyins.clear()
            mvar = tg.Variable('m', 0, n - 1, dtype=tg.dtypes.int32)
            statics = [self._statics[i] for i in slots]
            srcs = [tg.Tensor(b).reshape(n, *s.shape) for s, b in zip(statics, bases)]

            def run(mv):
                outs = [
                    s.assign(src.shrink(((mv, mv + 1), *([None] * s.ndim))).reshape(s.shape))
                    for s, src in zip(statics, srcs)
                ]
                tg.Tensor.realize(*outs)
                return tuple(outs)

            got = self._copyins[key] = (mvar, _tg_jit(run))

        return got

    def _fill(self, consts: list[tuple[int, ta.Any]]) -> None:
        """
        The held buffers for states handed in as constants (a decoder starting from zeros) filled by a JIT per (slots,
        values): scheduled eagerly, the hundred fills of a 27B's DeltaNet states cost a couple of seconds.
        """

        key = tuple((i, v) for i, v in consts)

        jit = self._fills.get(key)
        if jit is None:
            statics = [self._statics[i] for i, _ in consts]

            def run():
                outs = [
                    s.assign(tg.Tensor.full(tuple(s.shape), v, dtype=s.dtype, device=s.device, buffer=False))
                    for s, (_, v) in zip(statics, consts)
                ]
                tg.Tensor.realize(*outs)
                return tuple(outs)

            jit = self._fills[key] = _tg_jit(run)

        jit()

    def _carry_in(self, args: tuple[ta.Any, ...]) -> None:
        slabs: list[tuple[int, ta.Any, int, int]] = []
        consts: list[tuple[int, ta.Any]] = []
        eager: list[ta.Any] = []

        # between the position and the state stand tables, the same arrays call after call, as a rule; one that is
        # not the array last given (the noise a block's drafts are drawn with) is copied into its held buffer
        for i in range(self._pos_i + 1, self._state_i0):
            a = args[i]
            if a is not self._given[i]:
                self._given[i] = a
                eager.append(self._statics[i].assign(a))

        for i in range(self._state_i0, len(args)):
            a = args[i]
            s = self._statics[i]
            if a is s:
                continue

            slab = _tg_slab(a, tuple(s.shape))
            if slab is not None:
                slabs.append((i, *slab))
                continue

            pad = self._ops.padded_prefix(a)
            if pad is not None:
                # a Decoder's zero-padded KV: only its prefix lands in the held buffer, which is gigabytes at capacity;
                # positions past the prefix are written by every later step before that step reads them (and with no
                # prefix, a decoder starting from nothing, nothing lands: the held buffer's contents are finite)
                prefix, n = pad
                if n:
                    eager.append(s.shrink((None, None, (0, n), None)).assign(prefix.cast(s.dtype)))
                continue

            v = _tg_const_value(a)

            if v is not None:
                consts.append((i, v))
            else:
                eager.append(s.assign(a))

        if consts:
            self._fill(consts)

        if slabs:
            ms = {m for _, _, m, _ in slabs}
            ns = {n for _, _, _, n in slabs}
            if len(ms) == 1 and len(ns) == 1:
                mvar, cj = self._copyin(
                    tuple(i for i, *_ in slabs),
                    next(iter(ns)),
                    tuple(b for _, b, _, _ in slabs),
                )
                cj(mvar.bind(next(iter(ms))))
            else:
                eager.extend(self._statics[i].assign(args[i]) for i, *_ in slabs)

        if eager:
            tg.Tensor.realize(*eager)

    # An input slot is one of two kinds for the life of the capture -- a bound variable (a token made from a host
    # int: `TinygradOps.array`) or a buffer -- and it is whichever the first call brought. The engine brings both to
    # one step: the token a round sampled stays on the device and is the next round's input, while a prompt's and a
    # commit's come from the host. So each kind is turned into the other when it must be.

    def _int_value(self, a: ta.Any) -> int:
        """The int a one-element input holds: its constant or bound value, else read from the device."""

        v = _tg_value(a)
        if v is None:
            v = int(np.asarray(self._ops.numpy(a)).reshape(-1)[0])
        return v

    def _buffered(self, a: ta.Any) -> ta.Any:
        """`a`, in a buffer when it is a bound value (a host token handed to a slot captured as a buffer)."""

        if not a.uop.is_virtual:
            return a

        v = _tg_value(a)
        if v is None:
            return a

        return tg.Tensor(np.full(tuple(a.shape), v, dtype=np.int32), device=self._ops.device).cast(a.dtype)

    def _settle_readers(self) -> None:
        """
        What still pends on this step's last outputs is computed now, into storage of its own. A step's outputs are
        buffers its next run overwrites, and the engine reads what it wants of them before then -- which, where
        nothing runs until it is asked for, is no more than a graph: a draft's probability under the head, read a
        few drafts later (models/qwen/spec/mtp.py), came out as the last draft's row's.
        """

        bufs = self._out_bufs
        for t in self._ops._dynamic_tensors():  # noqa
            u = t.uop
            if u.is_virtual or _tg_static(u.base):  # (a constant; or computed along with an earlier one)
                continue
            if not bufs.isdisjoint(u.toposort()):
                self._ops.realized(t)

    def __call__(self, *args: ta.Any) -> tuple[ta.Any, ...]:
        self._ops._flush_slabs()  # noqa
        if self._jit is None:
            self._setup(args)
        else:
            self._settle_readers()

        sym = {i for i, _, _ in self._sym_in}
        bound = [v.bind(self._int_value(args[i])) for i, v, _ in self._sym_in]

        # a JIT input must be a plain buffer, the same structure every call: a pending value or a view (the draft head's
        # hidden rows are a slice of a step's output) lands in one through the graph-keyed JIT
        ins = [self._ops.realized(self._buffered(a)) for i, a in enumerate(args[:self._n_in]) if i not in sym]
        posv = self._var.bind(_tg_value(args[self._pos_i]))

        self._carry_in(args)

        beam = self._ops.beam or (self.DEFAULT_BEAM if self._ops.compile else 0)
        if beam:
            with tg.Context(BEAM=beam):
                outs = self._jit(posv, *bound, *ins)
        else:
            outs = self._jit(posv, *bound, *ins)

        if not self._out_bufs:
            self._out_bufs = frozenset(o.uop.base for o in outs if not o.uop.is_virtual)

        return outs


class TinyJitStepHandle:
    """
    What `capture` returns: on each call, the one `TinyJitStep` for this step function and the shapes it is called with
    (the capacity), shared across Decoders. Every `generate` builds a Decoder and captures its steps afresh, which on
    torch is a cheap CUDA-graph capture; here a capture is a scheduling pass over the whole step and a permanent claim
    on the device's small mapped-memory budget, so it happens once per process, and a later Decoder's state is carried
    into the held buffers on its first call (the same copy a prefix-cache restore makes).
    """

    def __init__(
            self,
            ops: TinygradOps,
            fn: ta.Callable[..., tuple[Array, ...]],
            state_from: int | None = None,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._fn = fn
        self._state_from = state_from

    def __call__(self, *args: ta.Any) -> tuple[ta.Any, ...]:
        pos_i = next(i for i, a in enumerate(args) if a.ndim == 0)
        key = (self._fn, tuple(tuple(a.shape) for a in args[pos_i + 1:]))

        steps = self._ops._steps  # noqa
        step = steps.get(key)
        if step is None:
            # the same step at other shapes (a capacity it has grown past) is done with: its held buffers go
            for k in [k for k in steps if k[0] is self._fn]:
                del steps[k]
            step = steps[key] = TinyJitStep(self._ops, self._fn, self._state_from)

        return step(*args)


##


class TinygradOps(Ops):
    name = 'tinygrad'
    static_prefill = True  # an eager prefill costs ~0.25 s of scheduling per realization: see Decoder.prefill

    # the decode attention reads a symbolic-length window of the buffers, so one captured step serves the whole
    # capacity at a cost that follows the sequence
    attn_bucketed = False

    def __init__(self, device: str | None = None, beam: int = 0) -> None:
        super().__init__()

        self.device = device or tg.Device.DEFAULT
        self.name = f'tinygrad:{self.device}'

        # tinygrad's kernel search depth for the captured steps' kernels (0: its heuristics, which leave the GEMVs an
        # order of magnitude short of the memory bandwidth); the results persist in its cache database, so a later
        # process skips the search. `compile` (the CLIs' --compile) is the same thing at the default depth: a slow first
        # run, then a fast one, which is what the flag means on torch too
        self.beam = beam
        self.compile = False
        self.compile_cache: str | None = None  # accepted, unused: tinygrad keeps its own cache
        self._shifts: dict[int, ta.Any] = {}
        self._n_sym = 0
        self._pool: ta.Any = None
        self._pool_i = 0
        self._pool_jit: ta.Any = None
        self._rand_held: dict[int, list[ta.Any]] = {}  # by size, the draws handed out, weakly: see `random_uniform`
        self._steps: dict[ta.Any, TinyJitStep] = {}  # captured steps by (step function, shapes): see TinyJitStepHandle
        self._open: dict[str, _TgSlab] = {}  # see `_adopt`: the slab being filled, per group
        self._pending: list[_TgSlab] = []  # full slabs whose bytes are not yet on the device
        self._slabs: list[ta.Any] = []  # every uploaded slab: the buffers stay alive for the views
        self._graph_jits: collections.OrderedDict[ta.Any, ta.Any] = collections.OrderedDict()  # see `realized`
        self._static_refs: dict[ta.Any, ta.Any] = {}  # see `_dynamic_tensors`
        self._aranges: dict[int, ta.Any] = {}
        self._copy_jits: dict[ta.Any, ta.Any] = {}  # see `copy`
        self._pads: dict[int, tuple[ta.Any, ta.Any, int]] = {}  # see kv_pad

        # Every eagerly scheduled graph tinygrad compiles pins a CPU-mapped buffer for the life of the process, out of a
        # budget that is a few hundred megabytes on a GPU without a resizable BAR (about a thousand graphs). Keyed by
        # structure rather than by the buffers it touches, a graph that recurs with new buffers -- every layer of a
        # prefill, every round of a speculative loop -- is one entry, and its scheduling is half the cost. tinygrad keys
        # only "small" graphs that way by default; this raises the threshold for the process (a context never left,
        # which is how its settings are made)
        # tinygrad gives a wait on a device signal 30 s before calling the device hung; a first run's kernel search,
        # compiles and heuristic kernels over the full capacity hold the queues longer than that (a real hang then takes
        # this long to surface, which is the trade)
        for d in (self.device, 'CPU'):
            tg.Device[d].wait_timeout_ms = self.WAIT_TIMEOUT_MS

    def dtype(self, name):
        return dtypes()[name]

    def array(self, a, dtype=None):
        a = np.ascontiguousarray(a)

        if a.size == 1 and a.dtype.kind in 'iu' and dtype in (None, tg.dtypes.int32):
            # one int (a decode step's token): a value bound to a variable rather than a buffer, so a captured step
            # takes it like the position (no copy to schedule) and the embedding is a slice rather than a gather names
            # cycle so that graphs built on these keep a bounded set of structures (see __init__), and a few drafted in
            # one round (the test hook's oracle drafts) still get distinct variables
            self._n_sym = (self._n_sym + 1) % 16
            v = tg.Variable(f'sym{self._n_sym}', 0, 2**31 - 1, dtype=tg.dtypes.int32)
            return tg.Tensor(v.bind(int(a.reshape(-1)[0]))).reshape(a.shape)

        if not a.flags.writeable:
            a = a.copy()

        t = tg.Tensor(a, device=self.device)
        if dtype is not None and t.dtype != dtype:
            t = t.cast(dtype)

        return t

    def numpy(self, x):
        self._flush_slabs()
        if x.dtype in (tg.dtypes.bfloat16, tg.dtypes.float16):
            x = x.cast(tg.dtypes.float32)
        out = self.realized(x, host=True).numpy()
        self._guard_templates()
        return out

    # Graphs the engine builds between captured steps -- the token sampled from a step's logits, the drafts and their
    # probabilities, a speculative round's acceptance -- have the same structure every time and read buffers that stay
    # put (a captured step's outputs, the random pool), so they are captured too, keyed by the graph itself with its
    # bound variables (random pool offsets, token ids) as the inputs; past this many the captures are dropped and
    # rebuilt. A speculative round builds a few dozen distinct graphs (a view's offset is the accepted count, four
    # variants a site, host and device reads apart), and the working set is above sixty; the least recently used go when
    # there are more than this (each holds a few kilobytes of mapped memory: a thrashing cache re-captures one a round).
    MAX_GRAPH_JITS: ta.ClassVar[int] = 256
    CAPTURE_FIRST: ta.ClassVar[bool] = True  # see `_tg_jit`
    WAIT_TIMEOUT_MS: ta.ClassVar[float] = 600_000.0

    def realized(self, t, host: bool = False):
        """
        `t` as a plain, realized buffer. A pending value is computed through a JIT keyed by its graph (see above),
        into buffers allocated for this call and handed to the JIT to write, and every tensor sharing the
        computation is pointed at them, as a realization does. Scheduling eagerly instead costs milliseconds of
        Python per graph, every time. A view of a realized buffer is copied the same way, into the JIT's own output:
        scratch its next replay overwrites, for a caller that reads or copies it at once (`numpy`, `copy`, a step's
        input). With `host`, the result lands in a CPU-mapped buffer of the JIT's -- scratch too -- which `numpy()`
        then reads without a copy to schedule.

        What was computed went to the JIT's own outputs as well, once, and whatever was pointed at them had to be
        consumed before the same graph came round. A round's values are; a forward's are not: run as it is built,
        every layer of a kind is one graph, and Inkling 2 runs a layer three times a token and reads the block sums
        of the pass before -- its logits were wrong from the third pass on; and an array made on the host and read
        back on it held the next such array's values.
        """

        self._flush_slabs()
        u = t.uop
        if u.is_virtual or (u.has_buffer_identity() and u.is_realized):
            return t

        is_view = _tg_static(u.base)
        src = u if is_view else u.base

        # the key is the graph's structure: variables unbound, and the buffers it reads stood in for by placeholders,
        # which are the JIT's inputs. Keyed on the buffers themselves, a graph realized afresh (a new output buffer)
        # would change every graph downstream of it, and the misses would cascade round after round.

        O = tg_uops.Ops
        order = {x: i for i, x in enumerate(src.toposort())}
        nodes = order.keys()

        # every live tensor that is an interior node of this graph is realized along with it, as a realization does:
        # left pending, it is rebuilt inside the next graph that reads it, whose structure then carries this one's (a
        # round's inputs would encode the previous round's acceptance, and no key would ever recur)

        dyn = self._dynamic_tensors()
        held: dict[ta.Any, None] = {}
        for t2 in dyn:
            if t2 is t:
                continue
            b = t2.uop.base
            if b in nodes and b is not src and not b.is_virtual and not b.has_buffer_identity():
                held[b] = None

        roots = [src, *sorted(held, key=order.__getitem__)]
        leaves = [x for x in order if x.op is O.BUFFER]
        holders = {x: tg_uops.UOp.placeholder_like(x, slot=i) for i, x in enumerate(leaves)}
        key, vals = tg_uops.UOp.sink(*roots).substitute(holders, walk=True).unbind_all()

        # What is computed goes to storage of its own -- where its size is a number: a size that is an expression
        # (or nothing) keeps the JIT's output. The host's copy is this JIT's to make when `t` is all of what it
        # computes; a view of that is read by the pass at the end.
        own = not is_view and all(isinstance(d, int) and d > 0 for r in roots for d in r.shape)
        to_host = host and (u is src or not own)

        jkey = (key, to_host, own)
        entry = self._graph_jits.get(jkey)

        if entry is not None:
            self._graph_jits.move_to_end(jkey)

        else:
            while len(self._graph_jits) >= self.MAX_GRAPH_JITS:
                self._graph_jits.popitem(last=False)

            slots = list(holders.values())
            n_own = len(roots) if own else 0

            def rebuild(bound, ins):
                sub = {b.unbound(): b for b in bound}
                sub.update({h: x.uop for h, x in zip(slots, ins)})
                return (key.substitute(sub, walk=True) if sub else key).src

            hout: ta.Any = None
            if to_host:
                shape = tuple(int(d) for d in src.shape)
                n = 1
                for d in shape:
                    n *= d
                spec = tg_device.BufferSpec(cpu_access=True)
                buf = tg_device.Buffer(self.device, n * src.dtype.itemsize, options=spec)
                hout = tg.Tensor(tg_uops.UOp.from_buffer(buf, src.dtype, self.device)).reshape(shape)

            def run(nb, *args):
                graphs = rebuild(args[:nb], args[nb + n_own:])
                if n_own:
                    outs = [d.assign(tg.Tensor(g)) for d, g in zip(args[nb:nb + n_own], graphs)]
                    if hout is not None:
                        outs.append(hout.assign(outs[0]))
                elif hout is not None:
                    outs = [hout.assign(tg.Tensor(graphs[0])), *[tg.Tensor(g).clone() for g in graphs[1:]]]
                else:
                    outs = [tg.Tensor(g).clone() for g in graphs]
                tg.Tensor.realize(*outs)
                return tuple(outs)

            entry = self._graph_jits[jkey] = (_tg_jit(run), hout)

        jit, hout = entry
        bound = [v.bind(i) for v, i in vals.items()]
        ins = [tg.Tensor(x) for x in leaves]

        if own:
            # (written where they are: what the JIT hands back is its capturing call's)
            outs = [self._own_buffer(tuple(r.shape), r.dtype) for r in roots]
            jit(len(bound), *bound, *outs, *ins)
        else:
            outs = jit(len(bound), *bound, *ins)

        if is_view:
            return outs[0]

        # what tinygrad's own realization does to point every holder at the result, over the dynamic tensors only (a
        # scan of all of them, mostly the weights' views, costs milliseconds)
        amap = {r: o.uop for r, o in zip(roots, outs)}
        in_scope: dict[ta.Any, bool] = {}

        def visitor(node):
            return True if node in amap else any(in_scope.get(s, False) for s in node.src)

        scope = [x for x in dyn if x.uop.topovisit(visitor, in_scope)]
        new = tg_uops.UOp.sink(*[x.uop for x in scope]).substitute(amap, name='substitute graph jit', walk=True)
        for x, nu in zip(scope, new.src):
            x.uop = nu

        if own and to_host:
            return hout  # (`t` itself, read on the host: the copy the JIT made beside its own)

        return self.realized(t, host)  # a view of what was pending is now a view of a buffer: copied by the view path

    def _own_buffer(self, shape: tuple[int, ...], dtype: ta.Any) -> ta.Any:
        """A tensor over a buffer allocated here: storage for a JIT to write."""

        n = 1
        for d in shape:
            n *= d

        u = tg_uops.UOp.new_buffer(self.device, n, dtype)
        u.buffer.allocate()

        return tg.Tensor(u).reshape(shape)

    def _dynamic_tensors(self) -> list[ta.Any]:
        """
        The live tensors whose graphs hold pending computation: the only ones a realization can touch. The rest --
        realized buffers, and the weights' views of their slabs, most of what is live -- are remembered along with the
        graph they were classified by, and skipped while it is unchanged (an in-place assignment makes one pending again
        until it is realized).
        """

        static = self._static_refs
        out = []

        for tref in list(tg_tensor.all_tensors):  # noqa
            t2 = tref()
            if t2 is None:
                continue

            u = t2.uop

            wr = static.get(tref)
            if wr is not None and wr() is u:
                continue

            if _tg_static(u.base):
                static[tref] = weakref.ref(u)
            else:
                out.append(t2)

        if len(static) > 2 * len(tg_tensor.all_tensors) + 1024:  # noqa
            for tref in [r for r in static if r() is None]:
                del static[tref]

        return out

    def cast(self, x, dtype):
        return x.cast(dtype)

    def copy(self, x):
        """
        A copy in a buffer of its own (a snapshot keeps it), made by a JIT per shape into a buffer allocated here:
        scheduled eagerly, a copy costs a quarter second of Python, and a prefix snapshot takes a hundred; a graph JIT's
        output would not do, being scratch it reuses.
        """

        if tg_realize.capturing:
            # inside a step being captured, where nothing runs until the capture is over and no JIT may be captured
            # within another: the copy is one more value of the step's, in storage of its own when the step realizes
            # it (what a step copies is state it hands back, which lands in a held buffer)
            return x.contiguous()

        self._flush_slabs()

        pad = self.padded_prefix(x)
        if pad is not None:
            # a decoder's zero-padded KV, before any step wrote it: a pad of a copy of its prefix. Realized through
            # `realized`, the pad would point the decoder's state at a graph JIT's scratch, which the next replay of the
            # same graph (the layer's other buffer, the next layer's) overwrites before the step copies it in
            prefix, _ = pad
            z = self.copy(prefix) if prefix is not None else self.zeros((*x.shape[:2], 0, *x.shape[3:]), x.dtype)
            return self.kv_pad((z,), int(x.shape[2]))[0]

        src = self.realized(x)  # a pending value is computed first; a view lands in a graph JIT's scratch
        shape = tuple(int(d) for d in src.shape)

        n = 1
        for d in shape:
            n *= d
        if n == 0 or src.uop.is_virtual:
            return src.clone().realize()

        dst = self._own_buffer(shape, src.dtype)
        key = (shape, src.dtype)

        jit = self._copy_jits.get(key)
        if jit is None:
            jit = self._copy_jits[key] = _tg_jit(lambda d, s: d.assign(s).realize())

        jit(dst, src)

        self._guard_templates()  # the capturing call runs eagerly
        return dst

    def zeros(self, shape, dtype):
        # a constant, not a buffer: it folds into whatever consumes it (the engine pads with zeros, and starts states
        # from them), and a graph holding it keeps its structure. tinygrad's buffer form is an allocation with a fresh
        # identity each time, which made the round's host read a new graph every round. A step that is handed one as
        # state allocates for it (see `TinyJitStep._hold`).
        return tg.Tensor.full(tuple(shape), 0, dtype=dtype, buffer=False)

    # Eagerly scheduled graphs tinygrad keeps as templates each hold a slice of the device's mapped-memory ring (see
    # __init__); past this many, the templates are dropped and the ring is reused, at the price of recompiling the ones
    # that recur (a few tens of milliseconds each). Well under what the budget allows beside the captured steps.
    MAX_EAGER_TEMPLATES: ta.ClassVar[int] = 96

    def _guard_templates(self) -> None:
        if len(tg_hcq.hcq_compile_cache) > self.MAX_EAGER_TEMPLATES:
            tg_hcq.hcq_compile_cache.clear()

    def eval(self, *xs):
        self._flush_slabs()
        if xs:
            tg.Tensor.realize(*xs)
        self._guard_templates()

    def materialize(self, *xs):
        self._flush_slabs()
        if xs:
            tg.Tensor.realize(*xs)
        self._guard_templates()

    def nbytes(self, w):
        if isinstance(w, (TinyQWeight, TinyMicroscaledExperts)):
            return w.nbytes()
        return w.nbytes()

    def reshape(self, x, shape):
        return x.reshape(shape)

    def transpose(self, x, axes):
        return x.permute(axes)

    # tinygrad's concatenation is a pad of each part and a sum, and a pad is pushed into the computation of what it
    # pads: a part still pending a division then holds 0 / 0 outside its region -- masked, never read -- which the
    # JIT's compile fails to fold (`KeyError: Ops.FDIV` out of a compile worker, tinygrad 9f120c450). A part that
    # carries a division is therefore given storage of its own first (Inkling 2's unit-norm values on their way into
    # a KV window, an attention's merged output into a convolution's history); the rest are left to fuse.

    @staticmethod
    def _unpadded(x):
        u = x.uop
        if u.is_virtual or _tg_static(u.base):
            return x
        O = tg_uops.Ops
        if not any(n.op in (O.FDIV, O.RECIP) for n in u.toposort(gate=lambda n: n.op is not O.BUFFER)):
            return x
        return x.contiguous()

    def concat(self, xs, axis):
        xs = [self._unpadded(x) for x in xs]
        return tg.Tensor.cat(*xs, dim=axis)

    def stack(self, xs, axis):
        xs = [self._unpadded(x) for x in xs]
        return tg.Tensor.stack(*xs, dim=axis)

    def split(self, x, sizes, axis):
        return list(x.split(list(sizes), dim=axis))

    def repeat(self, x, n, axis):
        return x.repeat_interleave(n, dim=axis)

    def arange(self, n):
        # one realized buffer per size: the engine asks for the vocabulary's several times a round, and tinygrad's is a
        # cumulative sum, scheduled eagerly, every time
        n = int(n)
        t = self._aranges.get(n)
        if t is None:
            t = self._aranges[n] = tg.Tensor.arange(n, dtype=tg.dtypes.int32).to(self.device).realize()
        return t

    # tinygrad's general indexing costs half a millisecond of Python per use; the round's hot ones are plain shrinks

    def select(self, x, i):
        return x.shrink(((i, i + 1), *([None] * (x.ndim - 1)))).reshape(x.shape[1:])  # the shape `_tg_slab` matches

    def select_at(self, x, i):
        # an index the graph knows (a commit's count: a constant here, where a commit runs as it is built) is the
        # same shrink; one only the device knows is a gather
        m = _tg_sint(i)
        if m is None:
            return super().select_at(x, i)
        return self.select(x, m)

    def kv_take(self, state, positions):
        # likewise: a run of positions from a start the graph knows (a commit's window: core/kvspans.py) is a shrink
        n = int(positions.shape[0])
        ar = self._aranges.get(n)
        start = _tg_run(positions, ar) if ar is not None else None
        if start is None:
            return super().kv_take(state, positions)
        return tuple(a.shrink((None, None, (start, start + n), None)) for a in state)

    def gather_rows(self, probs, toks):
        T = probs.shape[0]
        return probs.gather(1, toks.reshape(T, 1).cast(tg.dtypes.int32)).reshape(T)

    def scalar(self, v):
        return tg.Tensor(tg.UOp.const(int(v), tg.dtypes.int32))

    def kv_pad(self, state, capacity):
        if len(self._pads) > 512:  # entries whose padded tensor is gone
            self._pads = {k: v for k, v in self._pads.items() if v[0]() is not None}

        if all(int(a.shape[2]) == 0 for a in state):
            # a decoder starting from nothing: the whole buffer is a constant (allocated and filled when first held; a
            # held buffer is left as it is, every position being written before it is read); no prefix to carry in
            out = tuple(self.zeros((*a.shape[:2], capacity, *a.shape[3:]), a.dtype) for a in state)
            for padded in out:
                self._pads[id(padded)] = (weakref.ref(padded), None, 0)
            return out

        out = super().kv_pad(state, capacity)
        for a, padded in zip(state, out):
            if padded is not a:
                # keyed by identity: a Tensor's == is elementwise, so it cannot key a dict; the weak reference tells a
                # reused id from the tensor it was made for
                self._pads[id(padded)] = (weakref.ref(padded), a, int(a.shape[2]))

        return out

    def padded_prefix(self, t) -> tuple[ta.Any, int] | None:
        """
        (prefix, n) when `t` is a `kv_pad` result still pending: the state it pads, holding n positions (None, 0 for a
        pad of nothing).
        """

        got = self._pads.get(id(t))
        if got is None or got[0]() is not t or t.uop.is_realized:
            return None
        return got[1], got[2]

    def kv_slice(self, state, n):
        # the first n positions of a decoder's KV exported before any step wrote it (a prefix snapshot resumed and
        # stored again) come from the prefix the pending pad holds; see `copy` for why the pad itself must not be
        # realized
        out = []

        for a in state:
            pad = self.padded_prefix(a)
            if pad is not None and pad[1] >= n:
                if pad[0] is None:  # nothing written yet, nothing to keep
                    out.append(self.zeros((*a.shape[:2], 0, *a.shape[3:]), a.dtype))
                    continue

                a = pad[0]

            out.append(self.copy(a if int(a.shape[2]) == n else a[:, :, :n]))

        return tuple(out)

    def kv_write(self, buf, pos, x):
        if not (buf.uop.has_buffer_identity() and buf.uop.is_realized):
            return super().kv_write(buf, pos, x)  # a pending value (the functional reference path): a masked blend

        p = _tg_sint(pos)
        self._flush_slabs()
        buf.shrink((None, None, (p, p + 1), None)).assign(x.cast(buf.dtype)).realize()
        self._guard_templates()
        return buf

    def cumsum(self, x, axis):
        return x.cumsum(axis)

    def exp(self, x):
        return x.exp()

    def rsqrt(self, x):
        return x.rsqrt()

    def sum(self, x, axis, keepdims=False):
        return x.sum(axis, keepdim=keepdims)

    def mean(self, x, axis, keepdims=False):
        return x.mean(axis, keepdim=keepdims)

    def sigmoid(self, x):
        return x.sigmoid()

    def softplus(self, x):
        return x.softplus()

    def silu(self, x):
        return x.silu()

    def softmax(self, x, axis):
        return x.softmax(axis)

    def log(self, x):
        return x.log()

    def tanh(self, x):
        # tinygrad's own is 2 sigmoid(2x) - 1, a difference of nearly equal numbers for a small x -- which is what
        # Inkling 2's softcaps and message gates take: its first visits' outputs were three times as far from the
        # float64 reference as torch's (3e-6 against 1e-6 of them). As Inkling 2's torch kernels' tanh (its ops/): the
        # series below 0.1, the quotient of exponentials above.
        ax = x.abs()
        x2 = x * x
        e = (ax * -2.0).exp()
        small = ax * (1.0 - x2 * (1.0 / 3.0 - x2 * (2.0 / 15.0 - x2 * (17.0 / 315.0))))
        t = (ax < 0.1).where(small, (1.0 - e) / (1.0 + e))
        return (x < 0.0).where(-t, t)

    def sqrt(self, x):
        return x.sqrt()

    def maximum(self, x, v):
        return x.maximum(v)

    def minimum(self, x, v):
        return x.minimum(v)

    def argmax(self, x, axis):
        return x.argmax(axis=axis).cast(tg.dtypes.int32)

    def amax(self, x, axis, keepdims=False):
        return x.max(axis=axis, keepdim=keepdims)

    def topk(self, x, k):
        v, i = x.topk(k, dim=-1, largest=True)  # sorted descending (checked)
        return v, i.cast(tg.dtypes.int32)

    def seed(self, seed):
        tg.Tensor.manual_seed(seed)
        self._pool = None
        self._pool_jit = None  # its generator's key is the seed's

    # uniforms are handed out as slices of a pool drawn in one go: `Tensor.rand` schedules its counter update eagerly (a
    # millisecond-class cost here), and a speculative round asks for random numbers five times. The pool is refilled in
    # place by a JIT (the generator's counter advances on the device, so a replay draws fresh numbers; scheduled
    # eagerly, a refill was a third of a second every dozen rounds). The slice offset is a bound variable, named by the
    # size, so the graphs built on it keep one structure call after call: tinygrad caches an eagerly scheduled graph by
    # structure and holds a mapped buffer per entry, and this device's mapping budget is small
    RAND_POOL: ta.ClassVar[int] = 1 << 24

    def random_uniform(self, shape):
        n = 1
        for d in shape:
            n *= int(d)

        pool = getattr(self, '_pool', None)
        if pool is None or n > pool.shape[0]:
            pool = tg.Tensor.empty(max(self.RAND_POOL, n), dtype=tg.dtypes.float32, device=self.device).realize()
            self._pool = pool
            self._pool_i = pool.shape[0]  # nothing drawn yet: filled below
            self._pool_jit = None

        if self._pool_i + n > pool.shape[0]:
            if self._pool_jit is None:
                size = pool.shape[0]
                self._pool_jit = _tg_jit(
                    lambda: pool.assign(tg.Tensor.rand(size, dtype=tg.dtypes.float32, device=self.device)).realize(),
                )
            self._pool_jit()
            self._guard_templates()  # the capturing call runs eagerly
            self._pool_i = 0

        i = self._pool_i
        self._pool_i = i + n

        # Named by size, so a graph drawing the same shapes keeps one structure (the graph-keyed JIT's key) -- and by
        # how many draws of the size the caller still holds, since two of one name in one graph are one draw twice,
        # silently: a run of sampled drafts takes its noise a row a draft and joins them (spec/draws.py), and every
        # draft of the run was drawn with one row.
        held = self._rand_held.setdefault(n, [])
        j = next((j for j, ref in enumerate(held) if ref() is None), len(held))
        off = tg.Variable(f'rand{n}_{j}' if j else f'rand{n}', 0, pool.shape[0] - n, dtype=tg.dtypes.int32).bind(i)

        out = pool.shrink(((off, off + n),)).reshape(shape)
        held[j:j + 1] = [weakref.ref(out)]
        return out

    # weights

    # Weights live in a few large buffers ("slabs") and the model holds views into them: the submission program of a
    # captured step takes one argument per buffer it touches, and sixty-four layers of individually adopted tensors
    # (codes, scales, biases, norms, ...) are over a thousand, past what tinygrad can call. There is one slab per layer
    # (by the parameter's name), so that every layer of a kind lays its weights out identically and the eagerly
    # scheduled graphs of a prefill are one template for all of them, not one each. A slab's size is not known until its
    # layer is loaded, so its views are made over an unallocated placeholder and re-pointed, through tinygrad's own
    # tensor map, at the exact-size buffer the bytes are uploaded into at the backend's next realization point.
    SLAB_MAX: ta.ClassVar[int] = 1 << 30  # the placeholder's extent; a group past it continues in another slab

    # A parameter larger than that is a slab by itself (Inkling 2 Mini's embedding at float32 is 1.9 GB), up to this:
    # nothing larger has been tried.
    SLAB_LIMIT: ta.ClassVar[int] = 1 << 31

    @staticmethod
    def _host_bytes(a: np.ndarray, dtype: ta.Any) -> np.ndarray:
        """`a` as the raw element bytes of `dtype` (bf16 rounded to nearest even, which numpy has no type for)."""

        if dtype == tg.dtypes.bfloat16:
            f = np.ascontiguousarray(a, dtype=np.float32).view(np.uint32)
            rounded = (f + 0x7FFF + ((f >> 16) & 1)) >> 16  # round to nearest even; inf/nan inputs do not occur
            return rounded.astype(np.uint16)
        if dtype == tg.dtypes.float16:
            return np.ascontiguousarray(a, dtype=np.float16)
        if dtype == tg.dtypes.float32:
            return np.ascontiguousarray(a, dtype=np.float32)
        if dtype == tg.dtypes.int32:
            return np.ascontiguousarray(a, dtype=np.int32)
        if dtype == tg.dtypes.uint32:
            return np.ascontiguousarray(a, dtype=np.uint32)
        if dtype == tg.dtypes.uint8:
            return np.ascontiguousarray(a, dtype=np.uint8)
        raise TypeError(dtype)

    @staticmethod
    def _slab_group(name: str | None) -> str:
        """The slab a parameter goes into: its layer, the draft head's layer or stem, or the top level."""

        if name is None:
            return 'anon'
        parts = name.split('.')
        if parts[0] == 'layers' and len(parts) > 2:
            return f'layers.{parts[1]}'
        if parts[0] == 'mtp':
            if len(parts) > 3 and parts[1] == 'layers':
                return f'mtp.layers.{parts[2]}'
            return 'mtp'
        return 'top'

    def _adopt(self, a: np.ndarray, dtype: ta.Any, name: str | None = None) -> ta.Any:
        """A device tensor holding `a` in `dtype`, as a view of its group's slab (see above)."""

        raw = self._host_bytes(a, dtype).reshape(-1).view(np.uint8)
        nbytes = raw.nbytes
        need = ((nbytes + 255) // 256) * 256  # every weight 256-byte aligned
        if need > self.SLAB_LIMIT:
            raise ValueError(f'parameter {name!r} of {nbytes} bytes exceeds a slab')

        group = self._slab_group(name)
        slab = self._open.get(group)
        if slab is None or slab.used + need > slab.extent:
            if slab is not None:
                self._pending.append(slab)
            extent = max(self.SLAB_MAX, need)
            slab = self._open[group] = _TgSlab(tg.UOp.new_buffer(self.device, extent, tg.dtypes.uint8), extent)

        off = slab.used
        slab.parts.append((off, raw))
        slab.used = off + need
        return tg.Tensor(slab.placeholder).shrink(((off, off + nbytes),)).bitcast(dtype).reshape(tuple(a.shape))

    def _flush_slabs(self) -> None:
        """
        Upload every slab that still has its bytes on the host (the open ones included): one exact-size buffer each, the
        views re-pointed at it, the host copies dropped. Called at every realization point: nothing may run against a
        slab whose bytes are still on the host.
        """

        pending = self._pending + list(self._open.values())
        if not pending:
            return

        self._pending.clear()
        self._open.clear()

        reals = []
        for slab in pending:
            host = np.zeros(slab.used, dtype=np.uint8)
            for off, raw in slab.parts:
                host[off:off + raw.nbytes] = raw
            slab.parts.clear()
            reals.append(tg.Tensor(host, device=self.device))

        tg.Tensor.realize(*reals)
        tg.Device[self.device].synchronize()

        for slab, real in zip(pending, reals):
            tg_tensor._apply_map_to_tensors({slab.placeholder: real.uop}, 'slab')  # noqa
            self._slabs.append(real)

        self.release_cached()

    def release_cached(self) -> None:
        """
        Return the device memory tinygrad's allocator keeps from freed buffers for reuse. Gigabytes of a prefill's
        temporaries (expanded weights, the head's chunks) sit there otherwise, and an allocation that no longer fits
        beside them fails rather than reclaim them.
        """

        free = getattr(tg.Device[self.device].allocator, 'free_cache', None)
        if free is not None:
            free()

    def weight(self, w, dtype, name=None):
        return self._adopt(np.asarray(w), dtype, name)

    def _shift_table(self, bits: int) -> ta.Any:
        t = self._shifts.get(bits)
        if t is None:
            per = 32 // bits
            t = self._shifts[bits] = self.array(np.arange(per, dtype=np.uint32) * bits).reshape(1, 1, per).realize()
        return t

    def qweight(self, qw: QWeight, dtype, name=None):
        return TinyQWeight(
            self._adopt(qw.words(), tg.dtypes.uint32, name),
            self._adopt(qw.scale, dtype, name),
            self._adopt(qw.bias, dtype, name),
            qw.bits,
            qw.group,
            qw.shape,
            self._shift_table(qw.bits),
        )

    def head_rows(self, w, n):
        if isinstance(w, TinyQWeight):
            return TinyQWeight(
                w.q[:n],
                w.scale[:n],
                w.bias[:n],
                w.bits,
                w.group,
                (n, w.shape[1]),
                w.shifts,
            )
        return w[:n]

    def export_qweight(self, w):
        if not isinstance(w, TinyQWeight):
            raise NotImplementedError
        self._flush_slabs()
        return QWeight(
            np.ascontiguousarray(w.q.numpy()).view(np.uint8),
            w.scale.cast(tg.dtypes.float32).numpy(),
            w.bias.cast(tg.dtypes.float32).numpy(),
            w.bits,
            w.group,
            w.shape,
        )

    def linear(self, x, w):
        if isinstance(w, TinyQWeight):
            return w.linear(x)
        return x @ w.T

    def microscaled(self, mw: MicroscaledWeight, dtype, name=None):
        return TinyMicroscaledExperts(
            fmt=mw.fmt,
            codes=self._adopt(mw.codes, tg.dtypes.uint8, name),
            scales=self._adopt(mw.scales, tg.dtypes.uint8, name),
            outer=self._adopt(mw.outer, tg.dtypes.float32, name) if mw.outer is not None else None,
            block=mw.block,
            shape=(mw.shape[1], mw.shape[2]),
        )

    def expert_dense(self, w, e, dtype):
        if isinstance(w, TinyMicroscaledExperts):
            return w.dequant(dtype, slice(e, e + 1))[0]
        return super().expert_dense(w, e, dtype)

    def expert_linear(self, x, w, eids, x_div=1):
        if not isinstance(w, TinyMicroscaledExperts):
            return super().expert_linear(x, w, eids, x_div)

        rows = x.repeat_interleave(x_div, dim=0) if x_div > 1 else x
        if not tg_realize.capturing:
            # run as it is built: which experts the rows chose is read on the host, and each is decoded once, from a
            # plain slice of the packed bytes
            return self.expert_linear_grouped(rows, w, eids)

        # inside a captured step nothing can be read: each row's expert is a gather of the packed bytes. tinygrad
        # spells one as a comparison against every expert of the stack but does not pay for 128 of them: 0.11 s for
        # a token's eight rows of Inkling 2 Mini's gate and up experts on the CPU device, the time of the rows' own
        return (w.dequant(rows.dtype, eids) @ rows.contiguous()[:, :, None])[..., 0]

    def embedding(self, ids, w, dtype):
        rows: ta.Any = ids.reshape(-1)
        if ids.numel() == 1 and (t := _tg_sint(ids)) is not None:
            # A constant or a variable (a token): the row is a view, not a one-hot gather. Not an expression over
            # variables: one-element int arrays are variables here (`array`), a forward's positions among them, and
            # what tensor arithmetic makes of two (the relative term's row for one query over one key, a first
            # chunk of one token) is not an index a shrink takes -- tinygrad's verification refuses the graph.
            if isinstance(t, int) or t.op is tg_uops.Ops.PARAM:
                rows = slice(t, t + 1)

        if isinstance(w, TinyQWeight):
            return w.dequant(dtype, rows).reshape(*ids.shape, w.shape[1])

        return w[rows].cast(dtype).reshape(*ids.shape, w.shape[1])

    # fused overrides

    def sdpa(
            self,
            q,
            k,
            v,
            scale,
            past,
    ):
        B, H, T, D = q.shape
        KV = k.shape[1]
        L = k.shape[2]

        if abs(scale * D ** 0.5 - 1.0) > 1e-6:  # tinygrad's SDPA has no scale argument
            return super().sdpa(q, k, v, scale, past)

        if KV != H:
            k = k.repeat_interleave(H // KV, dim=1)
            v = v.repeat_interleave(H // KV, dim=1)

        if T == 1:
            return q.scaled_dot_product_attention(k, v)

        mask = self.array(np.tril(np.ones((T, L), dtype=bool), k=past))

        return q.scaled_dot_product_attention(k, v, attn_mask=mask)

    def sdpa_static(
            self,
            q,
            kbuf,
            vbuf,
            pos,
            ar,
            scale,
    ):
        """The composed reference over the window of the buffers in use: positions 0 .. pos + T, a symbolic length."""

        B, H, T, D = q.shape
        KV = kbuf.shape[1]
        G = H // KV

        n = _tg_sint(pos) + T
        kw = kbuf.shrink((None, None, (0, n), None))
        vw = vbuf.shrink((None, None, (0, n), None))
        arw = ar.shrink(((0, n),))
        f32 = tg.dtypes.float32

        qg = q.reshape(B, KV, G, T, D).permute(0, 1, 3, 2, 4).reshape(B, KV, T * G, D)
        scores = (qg @ kw.permute(0, 1, 3, 2)).cast(f32) * scale  # [B, KV, T*G, n]
        qpos = pos + ar[:T]  # [T]
        mask = (arw[None, :] > qpos[:, None]).cast(f32) * -1e30  # [T, n]
        mask = mask.repeat_interleave(G, dim=0).reshape(1, 1, T * G, n)  # row t*G + g
        p = (scores + mask).softmax(-1)
        o = p.cast(vw.dtype) @ vw  # [B, KV, T*G, D]
        o = o.reshape(B, KV, T, G, D).permute(0, 1, 3, 2, 4)
        return o.reshape(B, H, T, D)

    def conv1d_causal(self, x, w):
        C, K = w.shape
        return x.conv2d(w.reshape(C, 1, K), groups=C)

    def capture(self, fn):
        return TinyJitStepHandle(self, fn)

    def capture_carrying(self, fn, outputs_from, inputs_from):
        if not outputs_from:
            # Nothing but state comes out: a decoder's commit of a step that kept a state per token
            # (decode/decoder.py). It runs as it is built -- its picks are views of that step's outputs (`select_at`,
            # `kv_take`), which the step they are handed to copies into its held buffers, the per-token ones by a
            # JIT with the count bound (`TinyJitStep._carry_in`).
            return fn

        return TinyJitStepHandle(self, fn, state_from=inputs_from)  # (the carry is the step's own: held buffers)

    def rope(
            self,
            x,
            offset,
            dims,
            theta,
    ):
        key = (offset, x.shape[2], dims, theta, x.dtype)
        tabs = self.__dict__.setdefault('_rope_cache', {})

        if key not in tabs:
            if len(tabs) > 256:
                tabs.clear()
            self._flush_slabs()
            cos_np, sin_np = self.rope_tables(offset, x.shape[2], dims, theta)
            tabs[key] = (self.array(cos_np, x.dtype).realize(), self.array(sin_np, x.dtype).realize())

        cos, sin = tabs[key]
        xr = x[..., :dims]
        xp = x[..., dims:]
        half = dims // 2
        rot = tg.Tensor.cat(-xr[..., half:], xr[..., :half], dim=-1)
        return tg.Tensor.cat(xr * cos[None, None] + rot * sin[None, None], xp, dim=-1)
