# qwen35-torch

A from-the-math PyTorch implementation of the Qwen3.5 / 3.6 / 3.8 dense text models
(HF `model_type: qwen3_5`, GGUF arch `qwen35`) that loads weights straight out of Ollama's
blob store, plus a validation harness that uses `llama-server` as the oracle.

Dependencies: `torch`, `numpy`, `gguf` (llama.cpp's Python package, MIT), `regex`.
No `transformers`, no `safetensors` package (there is a 30-line reader in `weights.py`).

```
qwen35/weights.py    Ollama manifest -> GGUF blob (gguf-py dequant) or Ollama tensor blobs
                     (packed safetensors, MLX int4/int8 affine dequant) -> canonical HF-layout params
qwen35/tokenizer.py  byte-level BPE (qwen2 / qwen35 pre-tokenizer regexes), special tokens, streaming decode
qwen35/model.py      the model: RMSNorm, gated GQA attention w/ partial RoPE, Gated DeltaNet, SwiGLU, cache
generate.py          CLI greedy generation
validate.py          compare tokenizer / greedy tokens / per-step logprobs against llama-server
tests/test_synthetic.py  builds a tiny GGUF (and a tiny Ollama tensor-blob model) and checks everything
```

## Run

```bash
pip install torch numpy gguf regex
python tests/test_synthetic.py                       # no model needed
python generate.py --model qwen3.5:0.8b -p "Why is the sky blue?"
python generate.py --model qwen3.5:0.8b --raw -p "The capital of France is" --dtype f32
```

`--model` accepts an Ollama name (`qwen3.5:0.8b`, `qwen3.8:27b`), a `.gguf` path, or a blob path.

## Validate against llama.cpp

```bash
python validate.py --model qwen3.5:0.8b --show-blob     # prints the GGUF blob path
llama-server -m ~/.ollama/models/blobs/sha256-... --port 8080 -c 4096
python validate.py --model qwen3.5:0.8b -p "The capital of France is" -n 32 --dtype f32
```

It checks (1) tokenizer ids vs `/tokenize`, (2) our greedy tokens vs the server's, and (3) teacher-forces
the server's tokens through our model and compares log-softmax against the server's top-K pre-sampling
logprobs (`n_probs`) at every step.  A layout bug (e.g. V-head order, q/gate split, RoPE style) shows up as
garbage from step 0; a numerics-only difference shows up as agreement for tens of tokens with small
|delta logprob|.

## What the loader normalises

The canonical parameter scheme is HF's layout with *effective* values (see the docstring in
`weights.py`).  Things the GGUF source undoes/handles, because llama.cpp's converter did them:

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

1. **Chunked prefill** for the DeltaNet layers — `tests/test_synthetic.py::chunk_gated_delta_rule_ref`
   is a small WY-form chunked implementation that already agrees with the recurrence; move it into
   `model.py` and use it when `T > 1`.  Prefill goes from O(T) sequential steps to O(T/64).
2. **Cache management** — `Cache.snapshot()` is your prefix cache for the 3/4 of layers that are
   recurrent (fixed size, no growth).  Only the 16 attention layers need paged/blocked KV.
3. **Quantised matmuls** — right now everything is dequantised to bf16/f32 at load.  27B in bf16 is
   ~55 GB; keeping the GGUF blocks and writing your own Q4_K/Q8_0 dot kernels (or int4 for the MLX
   blobs) is where the real memory win is.
4. **Serving** — `Qwen35.generate` is the whole inference loop; wrap it in whatever HTTP layer you like.

MoE variants (`qwen35moe`) and the vision tower are deliberately not supported.
