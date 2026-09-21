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
tinygrad_ops.py  tinygrad backend (Tensor.scaled_dot_product_attention, grouped conv, TinyQWeight)
backends.py      backend selection for the CLIs
quant.py         backend-agnostic weight-only int8/int4 affine quantization (numpy QWeight, MLX layout)
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

`Decoder.step(tok)` moves one token id in and the logits out per token; `snapshot()` / `restore()` are the
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
kernel and the two low-rank DeltaNet projections (`in_proj_a` / `in_proj_b`, which Ollama also keeps at source
precision) are never quantized.

On torch with CUDA, small-M matmuls against a `TorchQWeight` (decode and speculative verify, `triton_max_m`
tokens or fewer) go through `torch_triton.qlinear`: the packed codes are read once, dequantized in registers and
fed to `tl.dot`, so per-step traffic is the packed weight rather than a bf16 expansion of it. Prefill (large M)
is compute-bound and keeps dequant + cuBLAS. The kernel is verified against the dequant path under Triton's CPU
interpreter (`tests/test_triton.py`) and drops into CUDA graphs like any other kernel. `TorchOps(triton=False)`
turns it off; `triton_block_n` / `num_warps` are the untuned knobs, and a split-K variant for the narrow (N=5120)
projections is the obvious next optimisation.

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

## Where to go next (in order)

1. **MTP speculative decoding** — the 27B checkpoints carry a one-layer draft head; verify is a captured T=4 step
   and rollback is `Decoder.restore` of a pre-verify snapshot.
2. **Cache management** — `Cache.snapshot(ops)` is your prefix cache for the 3/4 of layers that are
   recurrent (fixed size, no growth). Only the 16 attention layers need paged/blocked KV.
3. **Kernel tuning** — sweep `triton_block_n` / `num_warps`, add split-K for the narrow projections, and put
   `sdpa_static` on a length-aware kernel so decode attention stops reading the whole KV buffer.
4. **Serving** — `Qwen35.generate` is the whole inference loop; wrap it in whatever HTTP layer you like.

MoE variants (`qwen35moe`) and the vision tower are deliberately not supported.
