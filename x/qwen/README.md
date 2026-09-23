# qwen35-torch

A from-the-math implementation of the Qwen3.5 / 3.6 / 3.8 dense text models (HF `model_type: qwen3_5`, GGUF
arch `qwen35`), written once against a small backend seam (`Ops`) and run on torch, MLX core, tinygrad, or numpy, that
loads weights straight out of Ollama's blob store, plus a validation harness that uses `llama-server` as the oracle.

Dependencies: `numpy`, `gguf` (llama.cpp's Python package, MIT), `regex`, and whichever backend you run on
(`torch`, `mlx`, `tinygrad`). No `transformers`, no mlx-lm / mlx.nn, no `safetensors` package (there is a
30-line reader in `weights.py`).

```
model.py         the model, backend-free: RMSNorm, gated GQA attention w/ partial RoPE, Gated DeltaNet,
                 SwiGLU, functional cache state, activation taps
ops.py           the backend seam: `Ops` ABC (abstract primitives + composed reference implementations of
                 the fused-able ones) and `NumpyOps`, the float64 golden backend
torch_ops.py     torch backend (F.rms_norm / SDPA / conv1d, on-device quantize, TorchQWeight)
backends/torch_triton.py  Triton int4/int8 GEMV for TorchQWeight (decode / verify; prefill stays on dequant + cuBLAS)
mlx_ops.py       MLX core backend (mx.fast.rms_norm / rope / sdpa, mx.quantized_matmul, MlxQWeight)
backends/mlx_metal.py  the fused DeltaNet step as an mx.fast.metal_kernel (Metal only)
tinygrad_ops.py  tinygrad backend (Tensor.scaled_dot_product_attention, grouped conv, TinyQWeight)
backends.py      backend selection for the CLIs
quant.py         backend-agnostic weight-only int8/int4 affine quantization (numpy QWeight, MLX layout)
paramcache.py    on-disk cache of finished parameters (memory-mapped .npy per array), so a 27B loads in seconds
weights.py       Ollama manifest -> GGUF blob (gguf-py dequant) or Ollama tensor blobs (packed safetensors,
                 MLX int4/int8) -> canonical HF-layout params
tokenizer.py     byte-level BPE (qwen2 / qwen35 pre-tokenizer regexes), special tokens, streaming decode
generate.py      CLI greedy generation
validate.py      compare tokenizer / greedy tokens / per-step logprobs against llama-server
tests/test_synthetic.py  builds a tiny GGUF (and a tiny Ollama tensor-blob model) and checks the loader + model
tests/test_quant.py      quant round-trips, bit-exact MLX re-pack, quantized model vs f32
tests/test_parity.py     numpy-f64 golden vs torch vs mlx: per-layer taps, cache, quantized paths
```

On the radar, not started: a `ggml` backend (ctypes to libggml; a lazy `Ops` whose calls emit graph nodes). It
fits the same seam.

## Run

```bash
pip install numpy gguf regex torch          # and/or: pip install mlx
python -m x.qwen.tests.test_parity          # no model needed; runs every backend that imports
python -m x.qwen.generate --model qwen3.5:0.8b -p "Why is the sky blue?"
python -m x.qwen.generate --model qwen3.5:0.8b --backend mlx --raw -p "The capital of France is"
python -m x.qwen.generate --model qwen3.5:0.8b --backend torch --device cuda --dtype bf16 -p "..."
```

`--model` accepts an Ollama name (`qwen3.5:0.8b`, `qwen3.8:27b`), a `.gguf` path, or a blob path. `--backend`
defaults to mlx on macOS when it is installed, torch otherwise; `numpy` is the (slow) reference.

## The parameter cache

Loading a 27B from an Ollama GGUF costs about two minutes of gguf-py's numpy k-quant dequantization plus the
requantization, every launch. `--cache-dir DIR` (or `from_source(..., cache_dir=)`) keeps the finished
parameters under `DIR/<blob digest>-<quant>-g<group>/` as one memory-mapped `.npy` per array: f32 canonical
arrays for the dense tensors, packed `QWeight` codes + f32 scale/bias for the quantized ones (~18 GB for the
27B at int4). The first load fills it (quantizing on the device and exporting via `Ops.export_qweight`),
later loads hit and skip the GGUF entirely. The cache is backend-independent -- a cache built on torch loads
on MLX -- and per-entry, so a later `--spec` run just adds the draft head's tensors. Entries are written
atomically and a torn entry reads as a miss. Only worthwhile with `--quant` (an unquantized 27B would be 108 GB
of f32).

```bash
python -m x.qwen.entrypoints.generate --model qwen3.8:27b --quant int4 --cache-dir ./.cache/qwen ...
```

## The Ops seam

`model.py` touches the world only through an `Ops` instance: plain array algebra (reshape, slicing, `+ * @`,
broadcasting) is done directly on backend arrays -- numpy, torch and MLX spell those the same -- and everything
else goes through `Ops` methods. `Ops` is an ABC with two tiers: abstract primitives every backend must supply
(`array`/`numpy`, `cast`, `exp`, `sum`, `concat`, `linear`, ...) and concrete, overridable model primitives
(`rms_norm`, `rope`, `sdpa`, `conv1d_causal`, `gated_delta`, `quantize`) whose default implementation is composed
from the primitives. A new backend works as soon as the abstract tier exists and gets faster as it overrides the
second tier; `test_parity.py` checks every backend against the numpy float64 golden at every tap.

Rules the shared code follows (and any new shared code must): no item assignment, no in-place ops, functional
state (`mixer(x, state) -> (y, state)`), explicit `ops.f32()` where accumulation must be f32, control flow on
shapes only. Those are exactly the constraints the captured decode step relies on (below).

The gated delta rule has two composed forms behind `Ops.gated_delta`: the per-token recurrence (used for decode,
T == 1) and a chunked WY form (used for prefill) that does everything inside a 64-token chunk as batched matmuls
and carries the state across chunks, so a prompt costs O(T/64) sequential steps instead of O(T). The per-chunk
triangular inverse is a Neumann product (exact, since the matrix is nilpotent), which keeps it item-assignment
free and graph-friendly. On lazy backends (MLX, tinygrad) this is what makes prefill viable at all: the recurrence
would build a T-step graph.

## The static decode step

Prefill runs through `forward` with the functional, growing `Cache`. Decode then moves to `Decoder`
(`model.py`), whose state has shapes that never change: per attention layer a zero-padded KV buffer of `capacity`
positions (`ops.kv_write` puts the new token at `pos`, `ops.sdpa_static` attends over the whole buffer with an
additive mask from `arange > pos`, grouped-query heads folded into the matmul batch so nothing is repeated), per
DeltaNet layer the fixed-size `(conv, S)` pair, plus a 0-d device position and precomputed RoPE tables gathered by
`pos`. `Qwen35.decode_fn` builds the step as a pure function `fn(tok, pos, *flat_state) -> (logits, *flat_state)`
and `ops.capture` makes it fast:

- torch on CUDA: `CudaGraphStep` -- two warm-up runs on a side stream, capture against the argument tensors, then
  replay with `copy_` into the static inputs (skipped for the KV buffers, which `kv_write` mutates in place); a
  27B step becomes one graph launch instead of ~700 kernel launches. `capture_mode='static'` runs the same
  protocol without a graph, which is how it is tested on CPU.
- MLX: `mx.compile` (the setitem index is a runtime input; verified).
- tinygrad: `TinyJit`, with inputs and outputs cloned each call because JIT buffers are reused (correct, not yet
  fast; `__setitem__` bakes the index into recorded kernels, so `kv_write` stays the masked-blend reference there).

`Decoder.step(tok)` moves one token id in and the logits out per token (`Decoder.verify` / `commit` are the
T = k + 1 variant used by speculative decoding, below); `snapshot()` / `restore()` are the
prefix-cache primitives (restore re-pads or re-captures across a capacity change); when the sequence reaches
`capacity` the buffers double and the step is re-captured. Attention reads the full buffer every step, so cost
tracks the power-of-two capacity, not the live length -- at 32 KB/token that is ~1 GB per step at 32k, fine
against 15 GB of weights. `test_parity.py::test_static_decode_parity` checks the step against the golden forward on
every backend, through a growth and a restore. `--functional` in `generate` selects the old path for comparison.

Instrumentation: set `ops.taps = {}` and every `ops.tap(name, x)` in the model records a numpy copy (embedding,
each block's mixer output and block output, final norm, logits). Wrapping an `Ops` is the general mechanism --
a timing wrapper (force `eval` per op), a NaN-checking wrapper, a tracing wrapper that logs op/shape/dtype.

## Running the 27B models: `--quant`

Without `--quant` every weight is expanded to the compute dtype at load: ~55 GB for a 27B in bf16 (~110 GB in f32).
`--quant int8` / `--quant int4` keep the linear weights (and the embedding / lm_head) quantized on the device and
expand them per matmul, which is what makes 3.6-27B / 3.8-27B fit on ordinary hardware:

```bash
python -m x.qwen.generate --model qwen3.6:27b --quant int4 -p "..."      # ~15 GB of weights
python -m x.qwen.generate --model qwen3.6:27b --quant int8 -p "..."      # ~28 GB, essentially bf16 quality
python -m x.qwen.validate --model qwen3.5:0.8b --quant int8 -n 32        # quantized path vs llama-server
```

The scheme is asymmetric affine, one `(scale, bias)` per 64 inputs — MLX's `mx.quantize` layout — so Ollama tensor
blobs that are already MLX int4/int8 are re-packed bit-for-bit (no requantization), and on the MLX backend the
packed words go straight into `mx.quantized_matmul` (fused, no dequant traffic). GGUF k-quants are dequantized
to f32 and requantized, which adds a small error on top of the file's own quantization (int8 is lossless in
practice; int4-over-Q4_K_M is a double quantization — prefer int8 if it fits). Norms, `A`, `dt_bias`, the conv
kernel are never quantized. Projections that share an input are fused by the loader into one weight stacked
along the output dim (`model.FUSIONS`): `gate_up_proj`, attention `qkv_proj`, DeltaNet `in_proj_qkvz`, and the
two low-rank `in_proj_a` / `in_proj_b` as `in_proj_ab`, which is stored int8 whatever the model's width (Ollama
keeps them at source precision; int8 is effectively that, and cuBLAS took ~30 us per N=48 bf16 GEMM, 3 ms of
every step). 449 GEMV launches per step become 257, and the fused shapes stream better. The cache stores the fused
entries; the tuner enumerates the fused shapes.

On torch with CUDA, small-M matmuls against a `TorchQWeight` (decode and speculative verify, `triton_max_m`
tokens or fewer) go through `torch_triton.qlinear`: the packed codes are read once, dequantized in registers and
fed to `tl.dot`, so per-step traffic is the packed weight rather than a bf16 expansion of it. Prefill (large M)
is compute-bound and keeps dequant + cuBLAS. The kernel is verified against the dequant path under Triton's CPU
interpreter (`tests/test_triton.py`) and drops into CUDA graphs like any other kernel. `TorchOps(triton=False)`
turns it off. Narrow projections (o_proj, down_proj, out_proj at N=5120, k/v_proj at N=1024) are split over K
across several programs with a float32 partial-sum reduction, so they fill the GPU; the launch configuration
per (N, K) comes from a tuned table when one is loaded (`entrypoints/tune` sweeps block sizes, warps, stages and
split factor on the actual GPU and writes JSON; `--triton-tuned FILE` / `TorchOps(triton_tuned=)` loads it) and
from a fill-the-GPU heuristic otherwise. The tuner times by CUDA-graph replay and rotates through enough copies of
each weight to overflow L2, so it measures DRAM streaming -- what the decode step does -- rather than the
cache-resident bandwidth a single weight timed in a loop reports. Two formulations are swept per shape: the
tensor-core `_qlinear_kernel` (`tl.dot`, weight tile staged through shared memory) and `_qgemv_fma_kernel`
(`GemvConfig.fma`: plain FMAs reduced in registers, M <= 8, the way llama.cpp / exllama GEMVs work); the tuner
keeps whichever streams faster on the GPU at hand. Default tuning M is 4 (spec-3 verify).

The DeltaNet token step is one op on the seam, `Ops.gdn_step` (l2-norm, head broadcast, gate, recurrence, from
the raw projections in their natural layout), which the model calls for T <= 8 -- decode and speculative
verify. On torch with Triton it is a single fused kernel per layer (`torch_triton.gdn_step`): each program keeps
a `[dk, block_dv]` slice of one head's state in registers for all T tokens and writes the outputs plus the
final or per-token states. That replaces ~25 small kernels per layer (and the state's ~24 MB of round-trip
traffic) with one, which matters because the decode graph is otherwise ~2,500 nodes of a few microseconds each.
`test_triton.py::test_gdn_step_kernel` checks it against the composed reference under the interpreter.

On MLX the same step is a custom Metal kernel (`backends/mlx_metal.py`, `MlxOps.gdn_step`): one launch per layer,
a threadgroup per head and slice of 32 value columns with the `[dk, 32]` state tile in threadgroup memory for
all T tokens. `MlxOps.sdpa_static` uses `mx.fast.scaled_dot_product_attention` over the static buffer (GQA and
the boolean position mask native). Both are on when Metal is present (`MlxOps(metal=False)` forces the
references); `tests/test_mlx_metal.py` checks them against the references on Apple silicon and is skipped
elsewhere.

What remains in the graph after the two kernels is glue -- norms, casts, gates, the attention prologue -- and
`--compile` (`TorchOps(compile=True)`) hands each step function to `torch.compile` (`Ops.compile_fn`) before it
is graph-captured, so inductor fuses that glue into a few generated kernels. Step functions take everything as
arguments (tables, buffers), are built once per shape and cached on the model, so every Decoder -- warm-up, each
`generate`, the draft head's -- reuses the same compiled function instead of re-tracing 64 layers (that
re-trace was ~20 s a pop). Compiled and captured steps are specific to the buffer capacity, so `--capacity`
pins it (rounded up to a power of two) and the warm-up, every prompt and a server all share the same steps;
without it a warm-up sized for 8 tokens and a run sized for 512 compile twice. The first process pays the full
compile; with `--cache-dir`, `--warmup` then saves
`torch.compiler` artifacts to `<cache_dir>/torch-compile.bin` and later processes load them (checked on CPU:
21 s -> 4.6 s cold start on the synthetic model; compiled speculative decode reproduces plain greedy exactly).

```bash
python -m x.qwen.entrypoints.tune --model qwen3.8:27b --quant int4 --out ./.cache/qwen/gemv-int4.json
python -m x.qwen.entrypoints.generate ... --triton-tuned ./.cache/qwen/gemv-int4.json
```

## Validate against llama.cpp

```bash
python validate.py --model qwen3.5:0.8b --show-blob     # prints the GGUF blob path
llama-server -m ~/.ollama/models/blobs/sha256-... --port 8080 -c 4096
python validate.py --model qwen3.5:0.8b -p "The capital of France is" -n 32 --dtype f32
```

It checks (1) tokenizer ids vs `/tokenize`, (2) our greedy tokens vs the server's, and (3) teacher-forces
the server's tokens through our model and compares log-softmax against the server's top-K pre-sampling
logprobs (`n_probs`) at every step. A layout bug (e.g. V-head order, q/gate split, RoPE style) shows up as
garbage from step 0; a numerics-only difference shows up as agreement for tens of tokens with small
|delta logprob|.

## What the loader normalises

The canonical parameter scheme is HF's layout with *effective* values (see the docstring in
`weights.py`). Things the GGUF source undoes/handles, because llama.cpp's converter did them:

* non-gated RMSNorm weights are stored as `1 + w` in GGUF (HF uses zero-centred weights) — the model
  always does plain `w * x`;
* `ssm_a` is `-exp(A_log)`;
* linear-attention V heads are stored in *tiled* order (`[G0v0, G1v0, ..., G0v1, ...]`) across
  `attn_qkv` (V rows), `attn_gate`, `ssm_beta`, `ssm_alpha`, `ssm_a`, `ssm_dt`, the conv V-channels and
  `ssm_out` columns — the source converts back to HF grouped order so q/k broadcast with `repeat_interleave`;
* MTP (`nextn_predict_layers`) blocks at the end are skipped; a missing `output.weight` means tied embeddings.

Ollama's newer tensor-blob format needs none of that (HF names, HF layout), only the `1 + w` and
`-exp(A_log)` normalisation and MLX affine dequant.

## Speculative decoding (MTP)

The 27B checkpoints carry a one-layer multi-token-prediction head (`blk.64` / `nextn.*` in the GGUF, `mtp.*` in
HF; `nextn_predict_layers = 1`). `MtpHead` implements it: `rmsnorm(embed(x_{p+1}))` and `rmsnorm(h_p)` (the
target's final-normed hidden at p) concatenated -- embedding first -- through `fc`, one full-attention block with
the text geometry and its own KV, a final norm, the target's `lm_head`. It predicts the token at p+2 and
recurses on its own normed output.

`SpecDecoder` (`model.py`) runs one round as: draft k tokens (the first from the head's last refreshed entry,
the rest by recursion), each *sampled* from the draft head's warped distribution q; verify `[next_tok, d_1..d_k]`
in a single captured T = k + 1 target step; rejection-sample (`speculative_accept`): draft i is accepted with
probability min(1, p_i(d_i) / q_i(d_i)) where p is the target's equally-warped distribution, the first rejected
position emits a draw from the residual max(0, p - q), and if every draft survives the last row is drawn plainly.
Then commit and refresh the draft head over the committed positions with the target's true hidden states (one
captured T = k + 1 draft step). The output distribution is exactly the target's (the speculative-sampling
theorem; `test_sampler.py` checks it empirically) and the per-draft acceptance is sum(min(p, q)) = 1 - TV(p, q)
rather than p(argmax q) -- the same thing for greedy, where every distribution is one-hot, and typically 10-20
points more when sampling. All of it runs on the device; the round still has one host sync (accept flags,
corrections, drafts). Rollback costs nothing: the KV buffers are masked by position and the verify step returns
the DeltaNet state after every token, so the state after the accepted prefix is a slice.

```bash
python -m x.qwen.entrypoints.generate --model qwen3.8:27b --quant int4 --spec 3 -p "..."
python -m x.qwen.entrypoints.generate --model qwen3.8:27b --quant int4 --spec 3 --preset thinking -p "..."
```

`--draft-vocab N` drafts with the output head restricted to the first N token ids (ninfer's `--lm-head-draft`):
Qwen's BPE ids are roughly in merge-frequency order, so 32-64k of the 248k cover almost every token the target
picks, and the three draft-head launches per round each drop a 636 MB matmul to a fraction of that. Verify
always uses the full head, so drafting from a subset can only lower acceptance, never correctness.

`Sampler` does temperature / top-k / top-p / min-p / presence and frequency penalties on the device, as `Ops`
calls over the logits (top-k, then top-p/min-p among the candidates, then a Gumbel-max draw; the penalties read
a device histogram of observed tokens), so a decode step moves one token id off the device and a speculative
round moves 2k+1 of them instead of a 4 MB logits block. `--preset thinking` and `non-thinking` are Qwen's
published settings; `test_sampler.py` checks the draws against the exact distribution on every backend. `test_parity.py::test_spec_decode_parity` checks that speculative
decoding reproduces greedy decoding exactly on every backend, with the real head and with oracle drafts
corrupted at each index so every acceptance length is exercised.

## Where to go next (in order)

1. **Prefix snapshots** with a host tier (`Decoder.snapshot` + an LRU over device and pinned CPU memory, keyed
   on token prefixes) -- what turns an agent loop's turns into a few hundred tokens of prefill.
2. **Cache management** — `Cache.snapshot(ops)` is your prefix cache for the 3/4 of layers that are
   recurrent (fixed size, no growth). Only the 16 attention layers need paged/blocked KV.
3. **Kernel tuning** — sweep `triton_block_n` / `num_warps`, add split-K for the narrow projections, and put
   `sdpa_static` on a length-aware kernel so decode attention stops reading the whole KV buffer.
4. **Serving** — `Qwen35.generate` is the whole inference loop; wrap it in whatever HTTP layer you like.

MoE variants (`qwen35moe`) and the vision tower are deliberately not supported.
