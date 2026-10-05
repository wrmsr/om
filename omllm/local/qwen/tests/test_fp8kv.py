"""
The fp8 KV cache (TorchOps kv_dtype='fp8'): the static decoder holds e4m3 codes + scales, kernels and the composed
fallback agree, the whole decode / speculative / prefix-cache machinery runs on the four-array state, snapshots convert
between formats, and the quantization error is small.
"""
import os

import numpy as np

from ..model import Cache
from ..model import Decoder
from ..model import Qwen35
from ..prefixcache import PrefixCache
from .test_parity import rel_err
from .test_parity import synthetic_source


##


# These tests run the Triton kernels on CPU through Triton's interpreter, which each of them switches on for the rest of
# the process (TRITON_INTERPRET=1). Triton reads that switch every time a kernel is jitted, and it jits its own `tl`
# helpers (tl.sigmoid, ...) when it is first imported, so interpreted and compiled Triton cannot share a process:
#
#  - If Triton was already imported compiled (a kernel launched on CUDA, or torch.compile on CUDA, earlier in the
#    process), our kernels are jitted here as interpreted functions that call compiled `tl` helpers, and these tests
#    fail with "Cannot call @triton.jit'd outside of the scope of a kernel".
#  - If these tests run first on a CUDA machine, test_torch_triton.py's kernels then run interpreted on CUDA tensors,
#    which the interpreter does not support: bf16 comes out as garbage (test_qlinear_kernel) and some arguments cannot
#    be moved to the host ("'ConstTensorWrapper' object has no attribute 'untyped_storage'": test_gdn_step_kernel,
#    test_model_decode_with_kernel).
#
# So on a CUDA machine this module and test_torch_triton.py must run in separate pytest processes, and one process
# running both fails. Without CUDA both modules are interpreted throughout and the conflict does not arise.
#
# TODO: run these tests' bodies in a subprocess with TRITON_INTERPRET=1 in its environment instead of setting it in this
#  process, so that neither the order nor the grouping of tests in a pytest run matters.


def _skip() -> bool:
    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return True
    return False


def test_fp8_decode():
    if _skip():
        return
    import torch

    from ..backends.torch import TorchOps

    os.environ.setdefault('TRITON_INTERPRET', '1')
    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(3).integers(0, 256, (1, 24))

    def decode(ops):
        m = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
        cache = Cache(cfg)
        m.forward(ids[:, :12], cache)
        dec = Decoder(m, cache, capacity=64)
        lg = np.concatenate([ops.numpy(dec.step(int(t))) for t in ids[0, 12:]], 0)
        return lg, dec

    ref, _ = decode(TorchOps('cpu'))
    kern, dec = decode(TorchOps('cpu', triton=True, kv_dtype='fp8', capture_mode='static'))
    comp, _ = decode(TorchOps('cpu', triton=False, kv_dtype='fp8', capture_mode='static'))
    assert rel_err(kern, comp) < 1e-5, rel_err(kern, comp)
    assert rel_err(kern, ref) < 5e-2, rel_err(kern, ref)
    arity = [n for _, n in dec.model.state_offsets()]
    assert arity == [2, 2, 2, 4], arity
    o = dec.model.state_offsets()[3][0]
    assert [a.dtype for a in dec.flat[o:o + 4]] == [torch.float8_e4m3fn, torch.float32] * 2
    c = dec.export_cache()
    assert len(c.layers[3]) == 4 and c.layers[3][0].shape[2] == dec.seq_len
    print(f'fp8 decode: kernels == composed ({rel_err(kern, comp):.1e}); vs full precision {rel_err(kern, ref):.1e}')


def test_fp8_spec_and_snapshots():
    """
    Speculative decoding and the prefix cache on fp8 states; an fp8 snapshot resumed by an fp8 decoder equals a
    cold fp8 run, and resumed by a bf16 decoder it converts and runs.
    """

    if _skip():
        return
    from ..backends.torch import TorchOps

    os.environ.setdefault('TRITON_INTERPRET', '1')
    cfg, hf, src = synthetic_source()
    rng = np.random.default_rng(8)
    p1 = rng.integers(0, 256, 7).tolist()
    extra = rng.integers(0, 256, 5).tolist()
    ops = TorchOps('cpu', triton=True, kv_dtype='fp8', capture_mode='static')
    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
    pc = PrefixCache(ops, 1 << 30, 1 << 30)
    out1 = model.generate(p1, max_new_tokens=6, spec=3, prefix_cache=pc)
    assert len(out1) == 6 and len(pc.entries) == 2
    p2 = p1 + out1 + extra
    cold = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True).generate(p2, max_new_tokens=6, spec=3)
    warm = model.generate(p2, max_new_tokens=6, spec=3, prefix_cache=pc)
    assert model.last_prefix[0] > len(p1) and warm == cold, (warm, cold)
    # the same snapshot read by a bf16 decoder: converted on the way in, runs
    ops16 = TorchOps('cpu', triton=False, capture_mode='static')
    m16 = Qwen35.from_source(src, ops16, dtype='f32', verbose=False, mtp=True)
    pc16 = PrefixCache(ops16, 1 << 30, 1 << 30)
    snap = next(e.snap for e in pc.entries.values() if len(e.snap.tokens) == len(p1))
    pc16.put(snap)
    out16 = m16.generate(p1 + extra, max_new_tokens=6, spec=3, prefix_cache=pc16)
    assert m16.last_prefix == (len(p1), len(p1) + len(extra)) and len(out16) == 6
    snap16 = next(e.snap for e in pc16.entries.values() if len(e.snap.tokens) == len(p1) + len(extra))
    assert len(snap16.cache.layers[3]) == 2  # the bf16 decoder's own snapshot is in its format
    print('fp8 spec decode + prefix snapshots OK (fp8 -> fp8 exact, fp8 -> bf16 converts)')
