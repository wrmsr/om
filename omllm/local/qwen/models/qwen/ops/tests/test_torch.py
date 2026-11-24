# ruff: noqa: N803 N806 N812
"""
The Triton kernel for the DeltaNet step (torchkernels.py) against its composed definition (base.py), in both Triton
modes: through Triton's interpreter on the CPU, and compiled on CUDA where there is a GPU.
"""
try:
    import torch
except ImportError:
    torch = None  # type: ignore[assignment]

from .....tests.tritonmodes import triton_modes
from ..backends import qwen_ops


##


@triton_modes('interpret', 'compiled')
def test_gdn_step_kernel():
    """
    The fused DeltaNet step against the composed `QwenOps.gdn_step` reference: T in (1, 4), 3 value heads per key
    head, final state and all-states variants. And as a prefill: runs of 9 and 70 tokens (past the composed path's
    chunk of 64, and not a multiple of it), and 300 where compiled (the interpreter takes a minute over it), against
    the per-token recurrence in float64 -- the definition; the kernel is that recurrence in float32.
    """

    from .....backends.torch import TorchOps
    from ..torchkernels import gdn_step

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    ops = TorchOps(device, triton=False)  # reference path
    torch.manual_seed(0)
    B, Hk, Hv, dk, dv = 2, 2, 6, 16, 32
    A = -torch.rand(Hv, device=device) * 4 - 0.1
    dt = torch.randn(Hv, device=device)
    for T in (1, 4):
        q = torch.randn(B, T, Hk, dk, device=device)
        k = torch.randn(B, T, Hk, dk, device=device)
        v = torch.randn(B, T, Hv, dv, device=device)
        a = torch.randn(B, T, Hv, device=device)
        b = torch.randn(B, T, Hv, device=device)
        S0 = torch.randn(B, Hv, dk, dv, device=device) * 0.3
        for all_states in (False, True):
            ro, rs = qwen_ops(ops).gdn_step(q, k, v, a, b, A, dt, S0, all_states)
            for block_dv in (16, 32):
                fo, fs = gdn_step(q, k, v, a, b, A, dt, S0, all_states, block_dv=block_dv, num_warps=4)
                eo = ((fo - ro).abs().max() / ro.abs().max()).item()
                es = ((fs - rs).abs().max() / rs.abs().max()).item()
                assert eo < 1e-4 and es < 1e-4, (T, all_states, block_dv, eo, es)
                assert fs.shape == rs.shape
        # non-contiguous inputs (as produced by split + reshape in the model)
        big = torch.randn(B, T, 2 * Hk * dk + Hv * dv, device=device)
        qq, kk, vv = torch.split(big, [Hk * dk, Hk * dk, Hv * dv], -1)
        ro, rs = qwen_ops(ops).gdn_step(qq.reshape(B, T, Hk, dk), kk.reshape(B, T, Hk, dk), vv.reshape(B, T, Hv, dv), a, b, A, dt, S0, False)  # noqa
        fo, fs = gdn_step(qq.reshape(B, T, Hk, dk), kk.reshape(B, T, Hk, dk), vv.reshape(B, T, Hv, dv), a, b, A, dt, S0, False)  # noqa
        assert ((fo - ro).abs().max() / ro.abs().max()).item() < 1e-4
    print('fused DeltaNet step matches the reference (T=1, 4; final and all states)')

    ops64 = TorchOps(device, triton=False)
    runs = (9, 70, 300) if device == 'cuda' else (9, 70)
    Bl = B if device == 'cuda' else 1  # (the interpreter runs every program in numpy: keep its share small)
    for T in runs:
        q = torch.randn(Bl, T, Hk, dk, device=device)
        k = torch.randn(Bl, T, Hk, dk, device=device)
        v = torch.randn(Bl, T, Hv, dv, device=device)
        a = torch.randn(Bl, T, Hv, device=device)
        b = torch.randn(Bl, T, Hv, device=device)
        S0 = torch.randn(Bl, Hv, dk, dv, device=device) * 0.3
        q64, k64, v64, a64, b64, A64, dt64, S64 = (t.double() for t in (q, k, v, a, b, A, dt, S0))
        # the recurrence, every state: [T, B, Hv, dk, dv]
        ro, rs = qwen_ops(ops64).gdn_step(q64, k64, v64, a64, b64, A64, dt64, S64, True)

        fo, fs = gdn_step(q, k, v, a, b, A, dt, S0, False)
        eo = ((fo - ro).abs().max() / ro.abs().max()).item()
        es = ((fs - rs[-1]).abs().max() / rs[-1].abs().max()).item()
        assert eo < 1e-5 and es < 1e-5, (T, eo, es)

        if T <= 70:  # the state after every token, past the 8 tokens a verify step asks for
            fo, fs = gdn_step(q, k, v, a, b, A, dt, S0, True)
            assert fs.shape == rs.shape
            es = ((fs - rs).abs().max() / rs.abs().max()).item()
            assert ((fo - ro).abs().max() / ro.abs().max()).item() < 1e-5 and es < 1e-5, (T, 'all states', es)

        # a run split in two equals the run: the state carries exactly what a prefill chunk boundary needs
        h = T // 2
        o1, s1 = gdn_step(q[:, :h], k[:, :h], v[:, :h], a[:, :h], b[:, :h], A, dt, S0, False)
        o2, s2 = gdn_step(q[:, h:], k[:, h:], v[:, h:], a[:, h:], b[:, h:], A, dt, s1, False)
        full_o, full_s = gdn_step(q, k, v, a, b, A, dt, S0, False)
        assert torch.equal(torch.cat([o1, o2], 1), full_o) and torch.equal(s2, full_s), T
    print(f'fused DeltaNet recurrence matches float64 over {runs} tokens; split runs are bitwise the whole')
