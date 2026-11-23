# ruff: noqa: N803 N806
"""
The DSpark drafter (core/dspark/, spec/dspark.py) on a synthetic draft model beside the synthetic Inkling 2 checkpoint
(arch/tests/inkling2checkpoints.py): its drafts against a plain evaluation of what the drafter is -- written here from
its description, a loop per head and key, over the checkpoint's own tensors and the target's states from a
teacher-forced pass -- and the generation it drafts for against the one without it.
"""
import tempfile
import typing as ta

import numpy as np

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...arch.tests.inkling2checkpoints import write_inkling2_checkpoint
from ...arch.tests.inkling2checkpoints import write_inkling2_draft
from ...core.dspark.drafter import DsparkDrafter
from ...core.model import Qwen35
from ...decode.drafts import DraftSource
from ...decode.generation import Generation
from ...decode.observers import Observer
from ...decode.rounds import Round
from ...decode.sampling import Sampler
from ...load.weights import open_source
from ...ops.base import Ops
from ...ops.reference import NumpyOps
from ...prefix.cache import PrefixCache
from ...tests.test_parity import leading_backends
from ..dspark import DsparkDraftSource
from ..lookup import LookupDraftSource


##


PROMPT = [258, 261, 5, 9, 31, 7, 5, 9, 31, 7, 44, 12, 5, 9, 31, 7, 44, 12, 263, 259, 262]


def _static(ops: Ops) -> Ops:
    if getattr(ops, 'capture_mode', None) == 'auto':
        ops.capture_mode = 'static'  # type: ignore[attr-defined]
    return ops


def _load(path: str, ops: Ops, mtp: bool = True) -> Qwen35:
    return load_qwen35(open_source(path), ops, dtype='f32', verbose=False, mtp=mtp)


class _Rounds(Observer):
    """Each round's committed length before it, its pending token and its drafts."""

    def __init__(self, ops: Ops) -> None:
        super().__init__()

        self._ops = ops
        self.rounds: list[tuple[int, int, list[int]]] = []

    def on_prefill(self, gen: Generation) -> None:
        pass

    def on_round(self, gen: Generation, rnd: Round, kept: ta.Sequence[int]) -> None:
        before = len(gen.prompt) + len(gen.tokens) - len(kept)
        drafts = [] if rnd.drafts is None else [int(t) for t in self._ops.numpy(rnd.drafts.tokens)]
        self.rounds.append((before, rnd.tokens[0], drafts))


def _plain_drafts(
        t: ta.Mapping[str, np.ndarray],
        target: ta.Mapping[str, np.ndarray],
        m: ta.Mapping[str, ta.Any],
        taps: np.ndarray,
        anchor: int,
        vocab: int,
        cap: float,
) -> list[int]:
    """
    A block's drafts by the book: `taps` [L, n, H] the target's states at the L committed positions, `anchor` the
    token at position L. float64, a loop per slot, head and layer.
    """

    eps = m['rms_norm_eps']
    NQ, NKV, D = m['num_attention_heads'], m['num_key_value_heads'], m['head_dim']
    B, R, W = m['block_size'], m['markov_rank'], m['sliding_window_size']
    N = m['num_hidden_layers']
    L = taps.shape[0]
    taps = taps.astype(np.float64)

    def rms(x: np.ndarray, w: np.ndarray) -> np.ndarray:
        return x / np.sqrt((x * x).mean(-1, keepdims=True) + eps) * w

    def rope(z: np.ndarray, pos: int) -> np.ndarray:
        half = D // 2
        ang = pos * m['rope_theta'] ** (-np.arange(half) / half)
        a, b = z[..., :half], z[..., half:]
        return np.concatenate([a * np.cos(ang) - b * np.sin(ang), b * np.cos(ang) + a * np.sin(ang)], -1)

    def softmax(x: np.ndarray) -> np.ndarray:
        e = np.exp(x - x.max())
        return e / e.sum()

    # the mix as the reference uses it: softmaxed in float32, held as bfloat16 (what the loader hands over)
    fw = t['fuse_weight'].astype(np.float32)
    e = np.exp(fw - fw.max(-1, keepdims=True))
    alpha = (e / e.sum(-1, keepdims=True)).astype(np.float32)
    u32 = alpha.view(np.uint32)
    alpha = ((u32 + 0x7fff + ((u32 >> 16) & 1)) & 0xffff0000).view(np.float32).astype(np.float64)

    x = np.zeros((B, m['hidden_size']))
    x[0] = rms(target['embed'][anchor].astype(np.float64), target['embed_norm'])
    x[1:] = t['mask_embed']

    for i in range(N):
        p = f'layers.{i}.'
        a = p + 'self_attn.'

        c = rms((alpha[i][None, :, None] * taps).sum(1), t[p + 'dflare_norm.weight'])
        kc = rms((c @ t[a + 'k_proj_ctx.weight'].T).reshape(L, NKV, D), t[a + 'k_norm_ctx.weight'])
        kc = np.stack([rope(kc[q], q) for q in range(L)]) if L else kc
        vc = (c @ t[a + 'v_proj_ctx.weight'].T).reshape(L, NKV, D)
        lo = max(0, L - W) if i in m['local_layer_ids'] else 0

        u = rms(x, t[p + 'input_layernorm.weight'])
        q = rms((u @ t[a + 'q_proj.weight'].T).reshape(B, NQ, D), t[a + 'q_norm.weight'])
        k = rms((u @ t[a + 'k_proj.weight'].T).reshape(B, NKV, D), t[a + 'k_norm.weight'])
        q = np.stack([rope(q[j], L + j) for j in range(B)])
        k = np.stack([rope(k[j], L + j) for j in range(B)])
        v = (u @ t[a + 'v_proj.weight'].T).reshape(B, NKV, D)

        out = np.zeros((B, NQ, D))
        for j in range(B):
            for h in range(NQ):
                g = h // (NQ // NKV)
                keys = np.concatenate([kc[lo:L, g], k[:, g]])
                vals = np.concatenate([vc[lo:L, g], v[:, g]])
                out[j, h] = softmax(keys @ q[j, h] / np.sqrt(D)) @ vals
        x = x + out.reshape(B, NQ * D) @ t[a + 'o_proj.weight'].T

        mm = rms(x, t[p + 'post_attention_layernorm.weight'])
        gate = mm @ t[p + 'mlp.gate_proj.weight'].T
        x = x + (gate / (1 + np.exp(-gate)) * (mm @ t[p + 'mlp.up_proj.weight'].T)) @ t[p + 'mlp.down_proj.weight'].T

    y = rms(x, t['norm.weight'])[1:]
    g = rms((alpha[N][:, None] * taps[L - 1]).sum(0), t['markov_head.dflare_norm.weight'])

    s = np.zeros(R)
    prev = anchor
    drafts: list[int] = []
    for j in range(B - 1):
        z = np.concatenate([s, t['markov_head.markov_w1.weight'][prev], y[j], g])
        r = t['markov_head.rnn_proj.weight'] @ z + t['markov_head.rnn_proj.bias']
        gate = 1 / (1 + np.exp(-r[:R]))
        s = gate * s + (1 - gate) * np.tanh(r[R:2 * R])
        d = t['markov_head.hidden_out.weight'] @ np.tanh(r[2 * R:]) + t['markov_head.hidden_out.bias']
        logits = cap * np.tanh(target['unembed'][:vocab] @ (y[j] + d) / cap)
        prev = int(np.argmax(logits))
        drafts.append(prev)
    return drafts


def _always(model: Qwen35, sampler: Sampler) -> DsparkDraftSource:
    """A source that hands the target every draft of every block (a row costs nothing), for a generation's sampler."""

    return DsparkDraftSource(model=model, sampler=sampler, k=(model.mtp.cfg.drafts,), row_cost=0.)  # type: ignore


def test_drafts_are_the_drafters():
    """
    Every round's drafts are what the description gives for that round's block, from the checkpoint's own tensors and
    the states of a teacher-forced pass over the tokens committed so far: the readout's taps, each layer's memory
    as it is written over the prompt and then a round's rows at a time -- rejected rows and lookup rounds' many kept
    ones among them -- the block, the head's fold and its walk. And the drafts change nothing: the tokens are the
    plain ones.
    """

    with tempfile.TemporaryDirectory() as tmp:
        cfg = write_inkling2_checkpoint(tmp)
        t = write_inkling2_draft(tmp)
        src = open_source(tmp)
        m = src.hf_config['mtp_config']  # type: ignore[attr-defined]
        target = {
            'embed': src.get('embed.weight'),
            'embed_norm': src.get('embed_norm.weight'),
            'unembed': src._f32('model.llm.unembed.weight'),  # type: ignore[attr-defined]  # noqa: SLF001
        }
        vocab = cfg['unpadded_vocab_size']
        H = cfg['hidden_size']

        for ops in [NumpyOps(), *leading_backends()]:
            model = _load(tmp, _static(ops))
            assert isinstance(model.mtp, DsparkDrafter)
            plain = list(generate(_load(tmp, _static(ops), mtp=False), PROMPT, max_new_tokens=20).tokens)

            def check(
                    wrap: ta.Callable[[DraftSource], DraftSource],
                    want_rounds: int,
                    ops: Ops = ops,
                    model: Qwen35 = model,
            ) -> None:
                seen = _Rounds(ops)
                sampler = Sampler()
                res = generate(
                    model,
                    PROMPT,
                    max_new_tokens=20,
                    sampler=sampler,
                    draft=wrap(_always(model, sampler)),
                    observers=[seen],
                    capacity=32,
                )
                assert list(res.tokens) == plain, (ops.name, res.tokens, plain)

                full = [*PROMPT, *plain]
                _, hidden = model.forward(np.asarray([full], dtype=np.int64), return_hidden=True)
                taps = ops.numpy(hidden)[0].reshape(len(full), len(m['target_layer_ids']), H)

                drafted = 0
                for before, anchor, drafts in seen.rounds:
                    assert anchor == full[before]
                    if len(drafts) != m['block_size'] - 1:
                        continue  # (a lookup round's)
                    want = _plain_drafts(t, target, m, taps[:before], anchor, vocab, cfg['final_logit_softcapping'])
                    assert drafts == want, (ops.name, before, drafts, want)
                    drafted += 1
                assert drafted >= want_rounds, (ops.name, drafted)

            check(lambda d: d, 12)

            # under prompt lookup: its rounds keep several tokens at a time, and the drafter remembers their rows
            # all the same (k = 5: rounds of another shape than the drafter's own)
            def lookup(d: DraftSource, ops: Ops = ops, model: Qwen35 = model) -> DraftSource:
                return LookupDraftSource(ops, vocab_size=model.cfg.vocab_size, wrapped=d, ngram=2, k=5)

            check(lookup, 3)


def test_sampled_and_resumed():
    """
    A follow-up resumed from a stored state -- the drafter's memory exported with the target's -- drafts as a cold
    run does, as does one resumed from a checkpoint inside the prefill, and one whose decoder starts in the buffers
    the last left; and sampled decoding runs through the head's sampled drafts.
    """

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        write_inkling2_draft(tmp)

        for ops in [NumpyOps(), *leading_backends()]:
            model = _load(tmp, _static(ops))

            def run(prompt: ta.Sequence[int], ops: Ops = ops, model: Qwen35 = model, **kw: ta.Any) -> tuple:
                seen = _Rounds(ops)
                sampler = Sampler()
                res = generate(
                    model,
                    prompt,
                    max_new_tokens=8,
                    sampler=sampler,
                    draft=_always(model, sampler),
                    observers=[seen],
                    **kw,
                )
                return res, [r for r in seen.rounds if r[2]]

            pc = PrefixCache(ops, 1 << 30, 0)
            r1, _ = run(PROMPT[:15], prefix_cache=pc)
            p2 = [*PROMPT[:15], *r1.tokens, 1, 7, 8, 9]
            r2, d2 = run(p2, prefix_cache=pc)
            cold, dc = run(p2)
            assert r2.reused == 15 + len(r1.tokens), (ops.name, r2.reused)
            assert list(r2.tokens) == list(cold.tokens) and d2 == dc, (ops.name, d2, dc)

            if not ops.static_prefill:  # (a prefill through the captured step keeps no checkpoints yet)
                pc = PrefixCache(ops, 1 << 30, 0)
                run(p2, prefix_cache=pc, prefill_chunk=4, prefill_checkpoints=3)
                other = [*p2[:9], 250, 251, 252]  # shares 9 tokens: resumes from the checkpoint after 8
                r3, d3 = run(other, prefix_cache=pc)
                cold3, dc3 = run(other)
                assert r3.reused == 8, (ops.name, r3.reused)
                assert list(r3.tokens) == list(cold3.tokens) and d3 == dc3, (ops.name, d3, dc3)

            # a decoder that grows: the memory follows the target's capacity
            grown, dg = run(p2, capacity=len(p2) + 2)
            assert list(grown.tokens) == list(cold.tokens) and dg == dc, (ops.name, dg, dc)

            # sampled: the drafts come with the distributions they were drawn from -- the head's at the sampler's
            # temperature, whole (the truncations are the target's) -- which is what the rejection step needs of them
            class Drawn(Observer):
                def __init__(self) -> None:
                    super().__init__()

                    self.rows = 0

                def on_prefill(self, gen: Generation) -> None:
                    pass

                def on_round(self, gen: Generation, rnd: Round, kept: ta.Sequence[int], ops: Ops = ops) -> None:
                    d = rnd.drafts
                    if d is None:
                        return
                    q = ops.numpy(d.q)
                    toks = ops.numpy(d.tokens)
                    assert np.allclose(q.sum(-1), 1, atol=1e-4) and (q > 0).all(), ops.name
                    assert np.allclose(ops.numpy(d.q_d), q[np.arange(len(toks)), toks], rtol=1e-5), ops.name
                    self.rows += len(toks)

            drawn = Drawn()
            sampler = Sampler(temperature=0.8, top_p=0.95, seed=3)
            res = generate(
                model,
                PROMPT,
                max_new_tokens=12,
                sampler=sampler,
                draft=_always(model, sampler),
                observers=[drawn],
            )
            assert len(res.tokens) == 12 and res.drafted >= 12 and drawn.rows == res.drafted, (ops.name, res.drafted)


def test_cuda_graphs():
    """
    On CUDA the block, the memory's writes and the commit are graphs, bound to the buffers a generation leaves the
    next: the drafts of three generations in a row -- the second in the first's buffers and steps, the third resumed
    from a stored state -- are the ones the CPU's steps draft, and none of them changes the tokens.
    """

    try:
        import torch
    except ImportError:
        return
    if not torch.cuda.is_available():
        print('no CUDA device; skipping')
        return

    from ...backends.torch import TorchOps

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        write_inkling2_draft(tmp)

        outs = {}
        for device in ('cpu', 'cuda'):
            ops = TorchOps(device) if device == 'cuda' else _static(TorchOps(device))
            model = _load(tmp, ops)
            pc = PrefixCache(ops, 1 << 30, 0)
            got = []
            runs: list[tuple[list[int], dict[str, ta.Any]]] = [
                (PROMPT, dict()),
                (PROMPT[:16], dict()),
                (PROMPT, dict(prefix_cache=pc)),
                ([*PROMPT, 40, 41, 42, 7, 8], dict(prefix_cache=pc)),
            ]
            for prompt, kw in runs:
                seen = _Rounds(ops)
                sampler = Sampler()
                res = generate(
                    model,
                    prompt,
                    max_new_tokens=14,
                    sampler=sampler,
                    draft=_always(model, sampler),
                    observers=[seen],
                    capacity=64,
                    **kw,
                )
                got.append((list(res.tokens), seen.rounds, res.reused))
            outs[device] = got

        assert outs['cuda'] == outs['cpu']
        assert outs['cuda'][3][2] > 0  # (the last one did resume)
        assert sum(len(r[2]) for _, rounds, _ in outs['cuda'] for r in rounds) >= 60


def test_the_count_follows_the_heads_word():
    """Sure drafts are all handed over, a guess is not, and a fall in the head's confidence cuts the round there."""

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        write_inkling2_draft(tmp)
        model = _load(tmp, NumpyOps())

        src = DsparkDraftSource(model=model, sampler=Sampler())
        assert src.max_drafts == 3
        assert src._count(np.asarray([.999, .999, .999])) == 3  # noqa: SLF001
        assert src._count(np.asarray([.05, .999, .999])) == 0  # noqa: SLF001
        assert src._count(np.asarray([.999, .999, .01])) == 2  # noqa: SLF001

        only = DsparkDraftSource(model=model, sampler=Sampler(), k=(2,))
        assert only._count(np.asarray([.999, .999, .999])) == 2  # noqa: SLF001
