"""
torch.compile miscompiles an indexed in-place write made through a dtype view of an argument (inductor, Triton backend).

Standalone repro, needing only torch with CUDA:

    python dtypeviewrepro.py

It exits 1 if the bug reproduces and 0 if it does not, so it doubles as a check for when the bug is fixed.


The bug
-------

`Tensor.view(dtype)` reinterprets a buffer's bytes as another dtype of the same width. Writing through such a view
stores bit patterns: no value conversion is involved. Under torch.compile on CUDA, an indexed write (`index_copy_`, or
`view[index_tensor] = ...`, which is `index_put_`) through a dtype view of one of the compiled function's arguments
stores the values converted *by value* to the buffer's dtype instead:

    def f(buf, idx, src):
        buf.view(torch.int32).index_copy_(0, idx, src)
        return buf

    idx = torch.tensor([2, 3], device='cuda')
    src = torch.tensor([1.0, -2.5], device='cuda').view(torch.int32)  # the bit patterns of 1.0 and -2.5
    f(torch.zeros(8, device='cuda'), idx, src)                 # [0, 0, 1.0, -2.5, 0, 0, 0, 0]
    torch.compile(f)(torch.zeros(8, device='cuda'), idx, src)  # [0, 0, 1065353216.0, -1071644672.0, 0, 0, 0, 0]

The result is silently wrong whenever Triton can convert between the two dtypes by value (int32 <-> float32 above, in
both directions), and a compilation error when it cannot. A uint8 view of a float8_e4m3fn buffer is such a pair, and is
how this was found (an fp8 KV cache whose codes were written through a byte view because eager `index_copy_` has no
float8 kernel):

    torch._inductor.exc.InductorError: CompilationError: at <line>:<col>:
        ...
    cannot cast uint8[constexpr[2]] to <['2'], fp8e4nv>

Not affected, as the control cases below show: the CPU (C++) backend; the same write when the buffer is created inside
the compiled function; a slice write through the view (`view[2:4] = src`). Reads through a dtype view are handled (see
the cause, below).


The cause
---------

Traced in torch 2.14.1 and triton 3.8.0:

 1. `aten.view.dtype` is lowered by `torch/_inductor/lowering.py:to_dtype_bitcast` to `DtypeView.create(x, dtype)`.
    When `x` is already storage, which a graph input is, `torch/_inductor/ir.py:DtypeView.create` returns a
    `ReinterpretView` of the same buffer whose layout carries the new dtype.

 2. Reading through that view is handled: `ReinterpretView.make_loader` wraps the load in `ops.to_dtype_bitcast`
    whenever `layout.dtype != data.dtype`.

 3. Writing through it is not. `lowering.py:index_put_impl_` emits an `ir.Scatter` with the view's dtype inside a
    `ComputedBuffer` whose layout is `MutationLayoutSHOULDREMOVE(self)`, which resolves to the underlying buffer. The
    generated kernel therefore receives the output pointer typed as the *buffer* and stores a value typed as the *view*
    straight into it, with no bitcast in between. For the example above (from `TORCH_LOGS=output_code`; `in_ptr1` is
    `src`, `out_ptr0` is the argument `buf`):

        triton_meta={'signature': {'in_ptr0': '*i64', 'in_ptr1': '*i32', 'out_ptr0': '*fp32', ...
        def triton_poi_fused_index_copy_view_0(in_ptr0, in_ptr1, out_ptr0, xnumel, XBLOCK : tl.constexpr):
            ...
            tmp6 = tl.load(in_ptr1 + (x0), xmask)
            ...
            tl.store(out_ptr0 + (tl.broadcast_to(tmp4, [XBLOCK])), tmp6, xmask)

 4. Triton's `tl.store` converts a value to the pointer's element type by value (`triton/language/semantic.py`: `store`
    calls `cast`). int32 -> fp32 is a legal value cast, hence the silent corruption. uint8 -> fp8e4nv has no value cast
    (only a bitcast), so the same store trips the `cannot cast` assertion at the end of `cast`.

The expected behaviour is the mirror image of the loader: bitcast the value to the buffer's dtype before the store (or
cast the pointer), when the scatter's target is a view whose dtype differs from its buffer's.


The workaround
--------------

Do not make a dtype view the target of an indexed write inside a compiled function: write with the buffer's own dtype.
For float8, where eager `index_copy_` is not implemented, `buf[:, :, idx] = codes` (`index_put_`) is, and it compiles to
an in-place scatter of the right type. See `TorchOps.kv_write_state` in omllm/local/qwen/backends/torch.py and the test
that pins it, omllm/local/qwen/tests/test_torch_triton.py::test_fp8_compiled_write.


Output
------

On the machine this was found on:

    torch 2.14.1+cu130, triton 3.8.0, python 3.14.8
    NVIDIA GeForce RTX 5090, compute capability 12.0

    float32 buffer, int32 view, index_copy_ (cuda)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: [0, 0, 1.06535e+09, -1.07164e+09, 0, 0, 0, 0]
      -> WRONG
    float32 buffer, int32 view, view[idx] = src (cuda)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: [0, 0, 1.06535e+09, -1.07164e+09, 0, 0, 0, 0]
      -> WRONG
    int32 buffer, float32 view, index_copy_ (cuda)
      eager:    [0, 0, 1.06535e+09, -1.07164e+09, 0, 0, 0, 0]
      compiled: [0, 0, 1, -2, 0, 0, 0, 0]
      -> WRONG
    float8_e4m3fn buffer, uint8 view, index_copy_ (cuda)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: InductorError: cannot cast uint8[constexpr[2]] to <['2'], fp8e4nv>
      -> WRONG
    control: buffer created inside the function (cuda)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: [0, 0, 1, -2.5, 0, 0, 0, 0]
      -> ok
    control: slice write, view[2:4] = src (cuda)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: [0, 0, 1, -2.5, 0, 0, 0, 0]
      -> ok
    control: cpu (cpu)
      eager:    [0, 0, 1, -2.5, 0, 0, 0, 0]
      compiled: [0, 0, 1, -2.5, 0, 0, 0, 0]
      -> ok

    bug reproduced: 4 of 4 dtype-view writes compiled wrongly
"""
import dataclasses as dc
import importlib.metadata
import sys
import typing as ta

import torch


##


@dc.dataclass(frozen=True)
class Case:
    name: str
    device: str
    buf_dtype: torch.dtype
    view_dtype: torch.dtype

    op: str = 'index_copy_'  # 'index_copy_' | 'setitem' (index_put_ with a tensor index) | 'slice'
    local: bool = False  # the buffer is created inside the compiled function rather than passed to it
    control: bool = False  # expected to be compiled correctly


CASES: ta.Sequence[Case] = (
    Case('float32 buffer, int32 view, index_copy_', 'cuda', torch.float32, torch.int32),
    Case('float32 buffer, int32 view, view[idx] = src', 'cuda', torch.float32, torch.int32, op='setitem'),
    Case('int32 buffer, float32 view, index_copy_', 'cuda', torch.int32, torch.float32),
    Case('float8_e4m3fn buffer, uint8 view, index_copy_', 'cuda', torch.float8_e4m3fn, torch.uint8),

    Case('control: buffer created inside the function', 'cuda', torch.float32, torch.int32, local=True, control=True),
    Case('control: slice write, view[2:4] = src', 'cuda', torch.float32, torch.int32, op='slice', control=True),
    Case('control: cpu', 'cpu', torch.float32, torch.int32, control=True),
)


def make_fn(case: Case) -> ta.Callable[..., torch.Tensor]:
    def write(buf: torch.Tensor, idx: torch.Tensor, src: torch.Tensor) -> torch.Tensor:
        view = buf.view(case.view_dtype)
        if case.op == 'index_copy_':
            view.index_copy_(0, idx, src)
        elif case.op == 'setitem':
            view[idx] = src
        elif case.op == 'slice':
            view[2:4] = src
        else:
            raise ValueError(case.op)
        return buf

    def write_local(idx: torch.Tensor, src: torch.Tensor) -> torch.Tensor:
        return write(torch.zeros(8, dtype=case.buf_dtype, device=src.device), idx, src)

    return write_local if case.local else write


def make_args(case: Case) -> tuple[torch.Tensor, ...]:
    """Fresh arguments: a zeroed 8-element buffer (unless local), the indices 2 and 3, and the two values to store."""

    idx = torch.tensor([2, 3], device=case.device)
    vals = torch.tensor([1.0, -2.5], device=case.device)
    if case.buf_dtype.is_floating_point:
        src = vals.to(case.buf_dtype).view(case.view_dtype)  # the bit patterns of 1.0 and -2.5 in the buffer's dtype
    else:
        src = vals.to(case.view_dtype)
    if case.local:
        return (idx, src)
    return (torch.zeros(8, dtype=case.buf_dtype, device=case.device), idx, src)


def raw_bytes(t: torch.Tensor) -> list[int]:
    return t.detach().cpu().contiguous().view(torch.uint8).tolist()


def values(t: torch.Tensor) -> str:
    return '[' + ', '.join(f'{x:g}' for x in t.detach().cpu().float().tolist()) + ']'


def run_case(case: Case) -> bool:
    """Runs one case eagerly and compiled, prints both, and returns whether the compiled result is right."""

    fn = make_fn(case)
    want = fn(*make_args(case))
    print(f'{case.name} ({case.device})')
    print(f'  eager:    {values(want)}')

    torch._dynamo.reset()  # noqa
    try:
        got = torch.compile(fn, dynamic=False)(*make_args(case))
    except Exception as e:  # noqa
        lines = [ln.strip() for ln in str(e).splitlines() if ln.strip()]
        why = next((ln for ln in lines if 'cannot cast' in ln), lines[0] if lines else '')
        print(f'  compiled: {type(e).__name__}: {why}')
        ok = False
    else:
        print(f'  compiled: {values(got)}')
        ok = raw_bytes(got) == raw_bytes(want)

    if ok:
        note = '' if case.control else '  (the bug did not reproduce here)'
    else:
        note = '  (unexpected: this is a control)' if case.control else ''
    print(f'  -> {"ok" if ok else "WRONG"}{note}')
    return ok


def _main() -> None:
    try:
        triton_version = importlib.metadata.version('triton')
    except importlib.metadata.PackageNotFoundError:
        triton_version = 'not installed'
    print(f'torch {torch.__version__}, triton {triton_version}, python {sys.version.split()[0]}')

    if not torch.cuda.is_available():
        print('CUDA is not available: the bug is in the Triton backend, so there is nothing to reproduce here')
        return
    cc = torch.cuda.get_device_capability(0)
    print(f'{torch.cuda.get_device_name(0)}, compute capability {cc[0]}.{cc[1]}')
    print()

    n_bad = 0
    for case in CASES:
        ok = run_case(case)
        if not ok and not case.control:
            n_bad += 1
    print()

    if n_bad:
        print(f'bug reproduced: {n_bad} of {sum(not c.control for c in CASES)} dtype-view writes compiled wrongly')
        sys.exit(1)
    print('bug not reproduced: every dtype-view write compiled correctly')


if __name__ == '__main__':
    _main()
