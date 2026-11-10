"""
torch.compile against the dataclasses it meets inside the compiled steps. The whole story is in the block above
`GemvConfig` in backends/torch_triton.py: torch's tracer (dynamo) cannot construct an omcore *frozen* dataclass, and
when a compiled step does, it silently runs the whole step eagerly. So anything built inside a step is a stdlib
dataclass.

Both directions are checked by real compiles, never by reading the generated `__init__`:

  - test_compiled_steps_trace_whole: the synthetic model's real compiled steps on CUDA under
    `torch._dynamo.error_on_graph_break(True)`. An omcore frozen dataclass (or anything else) that breaks a step's graph
    fails it loudly.
  - test_dynamo_still_cannot_trace_omcore_frozen_dataclasses: a canary on the dynamo behaviour itself, which fails once
    torch can trace them. That is the signal that the stdlib rule can be dropped.
"""
import dataclasses as dc
import typing as ta

import numpy as np
import pytest

from omcore import dataclasses as om_dc
from omcore import lang

from ..api import generate
from ..arch.qwen35 import load_qwen35
from ..backends.torch import TorchOps
from ..backends.torch_triton import HAVE_TRITON
from ..decode.drafts import DraftSource
from ..decode.drafts import point_drafts
from ..decode.processors import CompositeLogitProcessor
from ..decode.sampling import Sampler
from ..spec.mtp import MtpDraftSource
from ..spec.oracle import OracleDraftSource
from .test_parity import synthetic_source
from .tritonmodes import triton_modes


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import torch._dynamo as dynamo  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')
    dynamo = lang.proxy_import('torch._dynamo')


##


@triton_modes('compiled', timeout_s=900)
def test_compiled_steps_trace_whole():
    """
    Every step `TorchOps(compile=True)` compiles traces as one graph: plain decode, speculative verify, and the draft
    head's draft and refresh steps, with the real Triton kernels inside, int4 weights, both KV formats, and GEMV
    launches from `default_config` and through the `block_n` override (resolved on the first, eager run and carried
    into the traced step on each weight, so the step reads a GemvConfig and a Launch). It runs under
    `torch._dynamo.error_on_graph_break(True)`, so a graph break raises instead of dropping the step to eager.

    If this fails with dynamo's "Observed exception" and a FrozenInstanceError in the debug context, an omcore frozen
    dataclass is being constructed or replaced inside a compiled step: make it a stdlib dataclass (see the block above
    GemvConfig in backends/torch_triton.py), or build it outside the step.
    """

    if not HAVE_TRITON:
        print('triton not installed; skipping')
        return

    counters = dynamo.utils.counters

    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(11).integers(0, cfg.vocab_size, 9).tolist()

    for kv_dtype, block_n in (('bf16', None), ('fp8', 16)):
        dynamo.reset()
        counters.clear()

        ops = TorchOps(  # (no tuned table: every GEMV launch comes from default_config, or the block_n override)
            'cuda',
            compile=True,
            kv_dtype=kv_dtype,
            triton_block_n=block_n,
        )
        model = load_qwen35(
            src,
            ops,
            dtype='bf16',
            quant='int4',
            mtp=True,
            verbose=False,
        )

        def plain(p=prompt):
            generate(
                model,
                p,
                max_new_tokens=6,
                capacity=64,
            )

        def spec(p=prompt):
            generate(
                model,
                p,
                max_new_tokens=6,
                spec=3,
                capacity=64,
                draft_vocab=cfg.vocab_size // 2,
            )

        with dynamo.error_on_graph_break(True):
            # a one-token warm-up first (a server's): its prefill never runs the flash-prefill kernel
            plain(prompt[:1])
            spec(prompt[:1])  # resolves the draft head's restricted output head: a GEMV shape the plain step never saw
            # 5-token verify and head refresh steps, with drafts that are never the head's (lookup over it, k = 4)
            generate(model, prompt[:1], max_new_tokens=6, capacity=64, draft=_ForeignFirst(ops, cfg, model, rounds=99))

        # decode (T=1), verify (T=4), the draft head's draft (T=1) and refresh (T=4): at least one graph each. Guards
        # against this passing vacuously because nothing was compiled at all.
        graphs = counters['stats']['unique_graphs']
        assert graphs >= 4, f'kv={kv_dtype} block_n={block_n}: only {graphs} graphs compiled'

        # and nothing compiles again -- not the plain step after the spec one, not anything after a prompt of another
        # length: a compiled step must not guard on state that later work changes (it once guarded on the GEMV launch
        # table, which the draft head's new shape grew, and on the strides of a prefill's DeltaNet conv state, which
        # depend on the prompt's length: ~20 s on the 27B each time, mid-request) -- nor when plain and verify rounds
        # mix in one generation (as under prompt lookup with no draft head). A captured step is guarded when captured,
        # on its first use in a generation, so the case is a plain round first: the verify step is then captured with
        # the state the plain step left (once a slice of its input, with other strides than a commit's)
        plain()
        spec()
        plain()
        rounds: list[int] = []

        def every_other(ids, k):
            rounds.append(len(ids))
            return [ids[-1]] * k if len(rounds) % 2 == 0 else []  # (no drafts: a plain round)

        res = generate(
            model,
            prompt,
            max_new_tokens=12,
            capacity=64,
            draft=OracleDraftSource(ops, vocab_size=cfg.vocab_size, k=3, fn=every_other),
        )
        assert res.drafted and res.rounds > res.drafted // 3, res

        # nor when the head first drafts after a longer round it did not draft (prompt lookup over it, k = 4: a
        # follow-up turn): its draft step then takes a state refreshed over 5 positions, not 4 or its prefill's
        res = generate(model, prompt, max_new_tokens=12, capacity=64, draft=_ForeignFirst(ops, cfg, model, rounds=1))
        assert res.drafted, res
        again = counters['stats']['unique_graphs']
        assert again == graphs, f'kv={kv_dtype} block_n={block_n}: {again - graphs} steps recompiled'
        print(f'kv={kv_dtype} block_n={block_n}: {graphs} compiled graphs, no graph breaks, no recompiles')


class _ForeignFirst(DraftSource):
    """The draft head under k = 4 drafts that are not its own for the first `rounds` rounds (as prompt lookup gives)."""

    def __init__(self, ops, cfg, model, *, rounds: int) -> None:
        super().__init__()

        sampler = Sampler()
        sampler.bind(ops)
        self._ops = ops
        self._vocab_size = cfg.vocab_size
        self._head = MtpDraftSource(
            model=model,
            sampler=sampler,
            processor=CompositeLogitProcessor(ops, []),
            k=3,
            draft_vocab=cfg.vocab_size // 2,
        )
        self._rounds = rounds

    @property
    def max_drafts(self) -> int:
        return 4

    def accepts(self, resume):
        return self._head.accepts(resume)

    def start(self, gen, *, hidden, start, tokens, state):
        self._head.start(gen, hidden=hidden, start=start, tokens=tokens, state=state)

    def propose(self, gen):
        if self._rounds <= 0:
            return self._head.propose(gen)
        self._rounds -= 1
        return point_drafts(self._ops, self._vocab_size, [gen.pending] * 4)

    def on_commit(self, gen, rnd, n):
        self._head.on_commit(gen, rnd, n)

    def export(self, gen):
        return self._head.export(gen)


##


@om_dc.dataclass(frozen=True)
class OmFrozenConfig:
    """The shape of torch_triton.GemvConfig, as an omcore frozen dataclass: what the stdlib rule forbids in a step."""

    block_n: int = 32
    block_k: int = 128
    split_k: int = 1


@om_dc.dataclass()
class OmMutableConfig:
    block_n: int = 32
    block_k: int = 128
    split_k: int = 1


@dc.dataclass(frozen=True)
class StdFrozenConfig:
    block_n: int = 32
    block_k: int = 128
    split_k: int = 1


def _construct(cls: type) -> ta.Callable[..., ta.Any]:
    def fn(x, c):
        cfg = cls(64, 256, 2)  # as default_config builds one inside the step
        return x * (cfg.block_n + cfg.block_k + cfg.split_k)

    return fn


def _replace(cls: type) -> ta.Callable[..., ta.Any]:
    rep = dc.replace if cls is StdFrozenConfig else om_dc.replace

    def fn(x, c):
        cfg = rep(c, block_n=16)  # as qlinear's block_n override does inside the step
        return x * (cfg.block_n + cfg.block_k + cfg.split_k)

    return fn


def _compile_fullgraph(make: ta.Callable[[type], ta.Callable[..., ta.Any]], cls: type) -> float:
    """
    `make(cls)` compiled with fullgraph=True, so any graph break raises. The backend is 'eager' because what is under
    test is the tracer, which is the same whatever backend receives its graph, and so this runs anywhere, GPU or not.
    """

    dynamo.reset()
    out = torch.compile(make(cls), fullgraph=True, backend='eager')(torch.ones(2), cls(64, 256, 2))
    return float(out[0])


@pytest.mark.parametrize('op', ['construct', 'replace'])
def test_dynamo_still_cannot_trace_omcore_frozen_dataclasses(op):
    """
    CANARY. This test FAILS when torch gets *better*: when dynamo can construct (or `replace`) an omcore frozen
    dataclass inside a compiled function. Until then, everything built inside a compiled step must be a stdlib
    dataclass (the block above GemvConfig in backends/torch_triton.py), and test_compiled_steps_trace_whole enforces it.

    The controls first: the same function over a stdlib frozen dataclass, and over an omcore non-frozen one, compiles
    and computes, so the failure that follows is about the frozen omcore dataclass and nothing else.
    """

    if not lang.can_import('torch'):
        pytest.skip('torch not installed')

    make = {'construct': _construct, 'replace': _replace}[op]
    expect = 16 + 256 + 2 if op == 'replace' else 64 + 256 + 2

    om_dc.replace(OmMutableConfig(), block_n=1)  # its first call patches a module global, which dynamo cannot trace

    for control in (StdFrozenConfig, OmMutableConfig):
        got = _compile_fullgraph(make, control)
        assert got == expect, (control.__name__, got, expect)

    try:
        _compile_fullgraph(make, OmFrozenConfig)

    except dynamo.exc.Unsupported as e:
        if 'FrozenInstanceError' not in str(e):
            pytest.fail(
                f'dynamo still cannot {op} an omcore frozen dataclass, but no longer because of the frozen __setattr__ '
                f'(torch {torch.__version__}). Re-check the explanation above GemvConfig in '
                f'backends/torch_triton.py:\n{e}',
            )

    else:
        pytest.fail(
            f'torch {torch.__version__} can now {op} omcore frozen dataclasses inside torch.compile. The '
            f'stdlib-dataclass rule in backends/torch_triton.py (the block above GemvConfig) exists only because it '
            f'could not: it can be lifted, GemvConfig can go back to omcore, and this canary deleted.',
        )
