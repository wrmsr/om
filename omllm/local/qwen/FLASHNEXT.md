# FLASHNEXT

Running Qwen3.8-Flash-Next on this engine: what the model is, what differs from the Qwen3.8-27B the engine was
built around, what has to be added and how, and a strategy for actually running it on the hardware in the house.
Written October 2026, six weeks after the model's release, from the Qwen team's technical report
(arXiv 2608.30320), the model card, the vLLM / SGLang / ms-swift recipes and the community quantizations. Where
a detail below is marked *verify*, it is something the reference implementation (`transformers >= 5.16`, model
type `qwen4_exp`) settles and the sources available did not.

Read NEXT.md and UNTANGLING.md first. This document assumes the engine as it stands there, and several of the
items below are the same items with a model attached (MoE, expert offload, device profiles, the FP4 path).


## 1. What it is, and why it matters to us

Qwen3.8-Flash-Next (released 2026-08-26) is Alibaba's open-weight preview of the architecture that will underpin
Qwen4 — the role Qwen3-Next-80B-A3B played for Qwen3.5. It is a multimodal, ultra-sparse mixture-of-experts
model: a 125B-parameter backbone with ~6B activated per token, plus a 51B n-gram embedding table designed to live
in host memory, plus a 4B single-layer multi-token-prediction head; ~180B on disk in bf16 (~360 GB). Native
context 262,144, extensible to 1M with YaRN. On the agentic-coding benchmarks that matter to an agent harness it
edges the 27B we run (SWE-bench Pro 62.5 vs 61.7, LiveCodeBench v6 91.9 vs 90.3, vendor numbers) at a fraction of
the active compute, and the Qwen team reports attention-kernel speedups of 7.6x prefill / 4.9x decode over dense
attention at 1M context.

Why it fits this engine unusually well: it is a direct descendant of the architecture we implemented. The Gated
DeltaNet layers are *exactly* ours — 16 QK heads and 48 V heads at dimension 128, the short convolution, the
sigmoid output gate, zero-centred RMSNorm, three of every four layers — and the engine's whole lower half
(quantizer, parameter cache, Ops seam and backends, static decode step, speculative decoding with an MTP head,
prefix snapshots, grammar, serving) carries over untouched. Four components are new: an MoE feed-forward in every
layer, Qwen Sparse Attention (QSA) in the 1-in-4 attention layers, a four-branch Gated Residual stream, and the
n-gram embedding layer. Building them is also building Qwen4's shape ahead of time.


## 2. Side by side with the 27B

| | Qwen3.8-27B (what we run) | Qwen3.8-Flash-Next |
| --- | --- | --- |
| Parameters | 27B dense | 125B backbone, 6B active; + 51B n-gram table; + 4B MTP |
| Layers | 64: 48 GDN + 16 full attention (3:1) | 48: 36 GDN + 12 QSA (3:1), MoE after every mixer |
| Hidden size | 5120 | 2560 (residual carried as 4 branches of 2560) |
| GDN | 16 QK / 48 V heads, dim 128, conv 4 | same |
| Attention | gated GQA, 24 Q / 4 KV heads, dim 256, RoPE 64 | QSA: 24 Q / 2 KV heads, dim 256, RoPE 64; top-512 micro-blocks of 4 tokens (2048-token budget) + tail, chosen by a 4-head MQA indexer at dim 128 |
| Feed-forward | dense SwiGLU, intermediate 17408 | 512 experts, 10 routed + 1 shared active, expert intermediate 640 |
| Residual stream | one vector | Gated Residual: 4 branches, element-wise data-dependent read gate, per-branch scalar write gate, rank-320 bottleneck |
| Extra capacity | — | n-gram embedding at layer 2: 20M bigram/trigram entries (51B params), hashed lookup, host-resident |
| MTP head | 1 layer (attention + dense FFN) | 1 layer (QSA + MoE), reuses the target's QSA indices across draft steps |
| Vocabulary | 248,320 | 248,320 (same tokenizer family; template adds `reasoning_effort`) |
| Modality | text | text + vision tower (ignored here) |
| Context | 262,144 | 262,144 native, 1M with YaRN |
| KV per token | 64 KB (16 layers x 2 x 4 x 256 x bf16) | 24 KB (12 x 2 x 2 x 256) + ~0.8 KB of indexer block keys |
| DeltaNet state | 48 x 3.1 MB = 150 MB | 36 x 3.1 MB = 113 MB |
| Weights at int4 | 14.3 GB | ~70 GB backbone + ~2 GB MTP; n-gram ~26 GB (int4) / 51 (int8) / 95 (bf16) |
| Reference impl | transformers Qwen3.5 | transformers `qwen4_exp`; llama.cpp; dedicated vLLM image |


## 3. What carries over unchanged

Worth listing, because it is most of the engine.

- **GDN layers**, including the fused Triton and Metal step kernels and the chunked prefill (forward-substitution
  WY form) — identical head geometry to the 27B, so even the tuned kernel configurations apply.
- **Quantizer, precision policies, parameter cache.** Per-expert int4 is the same affine group-64 format; the cache
  gets more entries, not a new kind.
- **The Ops seam and all three GPU backends**, the lazy-import discipline, the static step and its capture, the
  compile path.
- **Speculative decoding.** The MTP head is one layer with the same contract (conditions on the target's final
  hidden and the next token; `nextn=1`), so `SpecDecoder`, rejection sampling, the draft-vocabulary restriction and
  the refresh protocol apply. The report's own four-step speculative numbers (mean accepted length ~4.1 of 4 on
  code) say the head is strong.
- **Prefix snapshots, grammar-constrained tool calls, JSON mode, the chat format and server.** None of these look
  inside a layer. The n-gram lookup is a pure function of token ids, so snapshots stay valid.
- **The length-aware decode attention and flash prefill** remain the fast path for QSA layers *below the budget*
  (see §4.3): under ~2k tokens of context, selection covers everything and sparse attention equals dense.


## 4. What is new, component by component

Each subsection: the math as the report gives it, the shapes, what the engine needs (seam ops with a composed
reference, kernels, loader), how it interacts with the features we already have, and how to test it.

### 4.1 Mixture of experts

**What.** Every layer's feed-forward is a router over 512 experts selecting 10, plus one shared expert that is
always on. Each expert is a SwiGLU with intermediate size 640 (gate, up, down: 3 x 2560 x 640 = 4.9M parameters;
the 73,728 expert tensors in the checkpoint are 48 layers x 512 x 3 projections). Per token the routed experts
are 10 x 4.9M x 48 = 2.4B of the 6B active parameters. The router is a 2560 -> 512 linear; the selection and
weighting formula (softmax then top-k with renormalisation, as Qwen3-Next, or sigmoid with a bias term) is
*verify* in the reference. The shared expert's size and gate (Qwen3-Next had a sigmoid `shared_expert_gate`) are
*verify*.

**Seam ops.** Two:
- `moe_route(h) -> (expert_ids [T, 10], weights [T, 10])` — the router matmul, activation, top-k, renorm. Plain
  composed ops everywhere; a few small launches.
- `moe_experts(h, expert_ids, weights, W_gate, W_up, W_down) -> [T, H]` — the grouped expert computation. The
  composed reference loops over the distinct experts present (for each: gather its tokens, run the SwiGLU, scatter
  the weighted result). Slow and obviously right; it is what the parity tests pin.

**Kernels.** At decode (M = 1, or 5 rows under speculation) the work per layer is 10 experts x 3 projections of
int4 weights — ~1,400 tiny GEMVs per step if launched separately, which would cost more in launches than in
bytes. The GEMV kernel we have takes an expert axis: weights stored stacked as `[E, N, K/2]` with stacked scales,
the launch grid covers (expert slot, N-block), each program reads its expert id from a small index tensor and
offsets into the stack. One launch per projection per layer; the gate/up pair fuses into one as the dense
`gate_up` does. Shared expert is an ordinary dense SwiGLU. Prefill (M in the thousands) wants a grouped GEMM —
tokens sorted by expert, one launch computing all experts' tiles — which is a few hundred lines of Triton
(the `tl.dot` tiling of our flash kernel with an expert-offset table); until it exists, the composed loop with
dequantised bf16 cuBLAS matmuls is acceptable for prefill, since prefill is compute-bound and the experts are
small. On MLX, `mx.gather_qmm` is exactly the grouped quantized matmul this needs, for both prefill and decode.

**Loader.** Stack the per-expert tensors into `[E, ...]` per layer and projection, quantize per expert (the
quantizer is per-row anyway; a stacked tensor is just more rows), cache per layer-projection (~150 entries per
layer instead of 1,536). The router and the shared expert's gate stay bf16; the shared expert follows the policy.
Expert quantization is where precision matters least per byte and most in total — the community NVFP4 checkpoint
quantizes *only* the experts and leaves everything else bf16; a `km`-style policy here is "experts int4,
everything else int8 or bf16", and the KL harness decides.

**Interactions.** The static step is indifferent (fixed shapes: 10 ids per row). Speculative decoding: the verify
step's T rows may pick different experts; the grouped kernel handles rows independently, so nothing changes except
the union of experts touched per step, which matters for offload (§7). The parameter cache's identity scheme is
unchanged.

**Tests.** Synthetic model with tiny experts (E = 8, k = 2): grouped kernel vs the composed loop vs the numpy
golden; a parity test that the dense FFN path is the E = 1 special case.

### 4.2 Gated Residual

**What.** The residual stream is widened to four branches, `R` of shape `[T, 4, H]`. Each sublayer (every GDN /
QSA mixer and every MoE block: 96 sublayers) reads its input as a weighted mix of the branches passed through an
element-wise, data-dependent gate, and writes its output back to the branches with a per-branch scalar write gate.
The read weights, gate and write weights are each a static learned term plus a data-dependent term predicted from
a normalised view of the residual state through a rank-320 bottleneck. The cross-branch mixing operator of
Hyper-Connections (`H_res`) was dropped for inference efficiency. Exact wiring — whether the bottleneck reads the
flattened `4 x H` state or each branch, where the norm sits, how the gate is activated — is *verify*.

**What the engine needs.** No kernel: elementwise ops, norms over `[4, H]`, and small matmuls (`[1, 10240] x
[10240, 320]` and `[320, ~H]` per sublayer). Two things to watch. First, the GR parameters are ~4M per sublayer,
~0.4B in total: at bf16 that is 0.8 GB of weight traffic per token, which is not nothing on a memory-bound step;
int8 for the bottleneck projections is a precision-policy entry. Second, the structural change: `Block` takes and
returns `R`, not `x`; the n-gram layer adds into `R`; the final norm reads a mix of the branches. In the untangled
layout this is a *residual-stream strategy* (plain vs gated) the layers call through, and it is the one place
where the new model forces a change to the layer contract rather than adding a sibling implementation.

**Interactions.** Decode-step memory traffic is 4x the activations (20 KB per token instead of 5 — nothing).
Snapshots and the functional `Cache` do not hold the residual, so nothing changes there. The report notes the
residual state "supports FP8 storage" — a training detail we can ignore.

**Tests.** Parity against the reference implementation on the synthetic config; a unit test that a GR with the
static weights set to "read branch 0, write branch 0, gate 1" reproduces the plain residual.

### 4.3 Qwen Sparse Attention

**What.** Core attention is GQA with 24 query heads and 2 KV heads at dimension 256, partial RoPE over 64
dimensions — our `Attention` with a 12:1 group ratio and far less KV. What is new is that each query attends only
to a selected subset of positions: the top `K_B = 512` micro-blocks of `r = 4` tokens (a 2048-token budget) plus
the tokens of the final incomplete block, which are always included. Selection comes from a compressed lightweight
indexer, per layer:

- `q̂_i^h = RMSNorm(W_Q^h x_i)` for H = 4 indexer query heads at dim 128; `k_i = W_K x_i`, one shared key head.
- Keys are average-pooled over each block of 4 tokens, then normed: `k̂_b = RMSNorm(AvgPool(k_{4b..4b+3}))`.
  Compression happens *before* positional encoding so tokens at different rotary phases are not averaged.
- Partial RoPE (64 of 128 dims) on `q̂_i` at position i and on `k̂_b` at the block's start position `4b`.
- Score `I_ib = Σ_h ReLU(⟨q_i^h, k̄_b⟩)` for blocks fully observed (`4b + 3 <= i`), `-inf` otherwise.
- `B_i = TopK_512(I_i)`, expanded to token indices, union the tail block.

Below `512 x 4 + 4` tokens of context every block is selected and QSA is dense attention: our existing kernels are
the reference and the fast path, and the indexer can be skipped entirely. The sparse machinery matters from ~2k
tokens and pays off from ~64k (the report's crossover versus a paged dense kernel).

**What the engine needs.**
1. *Indexer weights and a block-key cache.* Per QSA layer, `W_Q` (4 x 128 x 2560), `W_K` (128 x 2560), two
   norms. The compressed, normed, RoPE'd block keys are a per-layer cache of `[n/4, 128]` — 64 bytes per token per
   layer, ~0.8 KB per token across the 12 layers. It is appended every fourth token: during prefill in bulk, during
   decode when a block completes (positions `4b..4b+3` all present). Under speculation the verify step's T rows may
   complete a block mid-step; the row-local tail handling covers it, and the block key is written at commit.
2. *Scoring and selection.* `[T, 4, 128] x [n/4, 128]^T`, ReLU, sum over heads, `topk` over up to 65,536 blocks at
   full context — small matmul plus a `torch.topk` / `mx.argpartition`; fine as composed ops, including inside the
   captured step (fixed shapes: top-512 over a capacity-sized block table with `-inf` padding beyond `pos`).
3. *Sparse decode attention.* Our length-aware decode kernel with one change: instead of walking contiguous key
   blocks `0..pos`, each program walks the 512 selected blocks through an index table `[T, 512]` (plus the tail).
   Blocks of 4 adjacent tokens keep the loads reasonably coalesced; the per-row causal mask becomes "selected and
   <= pos + t". Splits parallelise over the 512 blocks instead of the sequence. Partials merge as now.
4. *Sparse prefill attention.* Flash-attention where every query row has its own block list — the DeepSeek-V3.2
   "DSA" kernel shape, which FlashInfer and vLLM grew for that model. Our flash prefill kernel plus a per-row
   gather of K/V blocks by index; the cost is `O(T x 2048)` per layer regardless of context, which is the point.
   The composed reference is a gather plus masked SDPA.
5. *Partial RoPE at block granularity* — a variant of our rope op taking a position per row.

On MLX, the indexer and selection are plain ops; sparse attention needs either a Metal gather-attention kernel or,
at first, a gather of the selected K/V into a dense `[T, 2048, 256]` tensor followed by `mx.fast.sdpa` with a mask —
correct, simple, and only 2048 wide, so quite possibly fast enough to keep.

**Interactions.** The length-aware kernel and the bucketing both become the sub-budget fast path; the Decoder's
window logic is untouched. Capacity still sizes the KV buffers (now 24 KB per token). fp8 KV applies to the
selected keys the same way. The prefix cache's KV slices are unaffected; the block-key cache is one more array in
the attention layer's state tuple (`kv_arity` grows by one — the KV-format seam was built for exactly this).
**MTP:** the head's attention is QSA too, and the report follows GLM in *reusing the target's top-k indices across
the draft steps* rather than re-indexing — our `SpecDecoder` can hand the verify step's indices to the draft
head's step, which fits the round's structure and saves the indexer in the hot loop.

**Tests.** Synthetic config with `r = 2`, `K_B = 3`, so a 16-token sequence exercises selection, the tail, and the
dense-equivalence below budget; sparse kernels vs the gather-plus-masked-SDPA reference under the Triton
interpreter; a parity test that at `n <= budget` the sparse path equals the dense path bit-for-bit (same kernel).

### 4.4 N-gram embedding (the "PLE" layer)

**What.** 20 million bigram and trigram entries, 51B parameters (the row size therefore totals 2560 across the
hash heads), looked up by hashing the current token with its predecessors ("multi-head hashing": several hash
functions per n-gram order, each indexing the table; *verify* the head count, table split and row dimension),
gated and added to the residual at layer 2. Deterministic addressing is the design point: the ids for a token are
known before its forward pass, so the rows can be prefetched from host memory while the GPU is busy, and the table
can live on the host entirely (the vLLM recipe requires that on 80 GB cards; Unsloth memory-maps it from SSD).

**What the engine needs.**
- A hash function matching the reference (*verify*; it must be bit-exact), run on the host over token ids.
- A host-resident table: bf16 95 GB, or quantized with our quantizer per row — int8 51 GB, int4 ~26 GB — with
  dequantisation of the gathered rows only, on the device.
- A gather-and-copy: `index_select` on a pinned host tensor, `to(device, non_blocking=True)`, overlapped with the
  layers before layer 2. Per token it is a handful of rows totalling ~5 KB — trivial on PCIe, and small enough
  that memory-mapping the table from NVMe (a few random 1-2 KB reads per token, prefetchable) is a real option when
  host RAM is short.
- The gate and add into the residual (into `R`; which branch or via the write gate is *verify*).

**Interactions.** Prefill gathers `T x heads` rows per chunk (a 4096-token chunk is ~20 MB) — fine. Speculative
decoding: the drafts are known before the verify step, so all `k + 1` rows' n-grams prefetch in one copy; the
draft head's own layer-2 lookup, if the head includes the n-gram layer (*verify*), is the same. The lookup is a
function of token ids only, so prefix snapshots are unaffected and the prefix cache needs no new state. Inside a
CUDA-graph-captured step the host gather cannot run, so the rows are an *input* to the step (a `[T, 2560]` tensor
copied into a static buffer before replay), which the static-input protocol already supports.

**Tests.** Hash equality against the reference on a few thousand token pairs; a parity test that the device path
with the table "on host" equals the table on device.

### 4.5 MTP head

One layer, 4B parameters, with QSA and an MoE block — i.e. a full new-architecture `Block`, which our `MtpHead`
already is for the old architecture. Trained with a multi-step objective; the engine's recursion through the
head already produces chained drafts. Changes: the head's attention takes indices from the target (§4.3); the
head's MoE experts are quantized and cached like the backbone's. At ~2 GB at int4 it is cheap to keep resident
even when the backbone's experts are not (§7).

### 4.6 Tokenizer, template, vision, YaRN, checkpoints

- **Tokenizer:** the 248,320-entry family; confirm `tokenizer.json` is byte-identical to the 27B's or load it
  from the checkpoint as the HF source already does.
- **Template:** ChatML with tools and thinking as now, plus `reasoning_effort` — a rendering detail for
  `chat.py`, worth one look at the template in `tokenizer_config.json`.
- **Vision:** the checkpoint includes a vision tower and the embedding table includes image tokens. The text path
  is a plain causal LM; the loader skips `visual.*` tensors. Vision stays "maybe later" per NEXT.md.
- **YaRN** for >262k: a rope-scaling variant in the rope tables — small, and only if 1M is ever wanted.
- **Checkpoints to load from:** bf16 safetensors (our HF source, with the n-gram table's shards handled lazily);
  the official FP8 (block-128 fine-grained scales) which needs an fp8-with-block-scales dequant in the loader —
  worth adding, since it halves the download and is "nearly identical" per the model card; community GGUFs
  (Unsloth's dynamic quants, including the n-gram table at no lower than 4-bit) through the GGUF reader; the
  experts-only NVFP4 checkpoints, relevant to NEXT.md's FP4 item.


## 5. Memory and speed, at int4

Per token of decode, the bytes that move (int4 unless noted; the engine is memory-bound):

- Routed experts: 10 x 4.9M = 49M parameters per layer, x 48 layers = 2.4B parameters ≈ **1.25 GB** at int4.
  The dominant term.
- Dense part (GDN projections, QSA projections, indexers, shared experts, routers, GR bottlenecks): the non-expert
  active parameters are ~3.5B ≈ **1.9 GB** at int4 (less with GR and routers at int8 — these are small).
- KV read at 32k context: 12 layers x 2 KV heads x 2048 selected tokens x 256 x 2 (K + V) x 2 bytes ≈ **50 MB** —
  QSA's whole point; the dense 27B reads 1 GB at 32k.
- DeltaNet state: 113 MB read and written.
- n-gram rows: ~5 KB, over PCIe.

So ~3.3 GB per token: at the 5090's ~1.8 TB/s that is a ~2 ms floor against the 27B's ~8 ms (14.3 GB), i.e. the
model is potentially ~3-4x faster per token than the 27B *if everything is resident*, and speculative decoding
multiplies both the same way. On the M4 Max's ~500 GB/s unified memory it is a ~7 ms floor — the community reports
~60 tok/s on an M5 Max with MLX, consistent with that plus overheads.

Resident memory at int4: backbone ~70 GB (experts ~63, dense ~7), MTP ~2 GB, KV at the full window ~6.3 GB bf16
(3.2 at fp8), block keys ~0.2 GB, DeltaNet state and activations under 1 GB, n-gram table host-side (26 GB int4 /
51 int8 / 95 bf16). Total on-device ~80 GB: the shape of an H100 80 GB (tight), an H200, an RTX PRO 6000 (96 GB),
or 128 GB of Apple unified memory with the n-gram table alongside.


## 6. Plan of work

Each phase ends with the parity tests green on a synthetic configuration of the new architecture (the synthetic
builder gains a second config: 8 layers, hidden 64, 8 experts of width 32 with top-2, QSA with `r = 2` and
`K_B = 3`, GR with 4 branches and rank 8, a 256-entry n-gram table), checked against both the numpy golden and —
the new oracle — the `qwen4_exp` implementation in `transformers` run on the same synthetic weights, which is how
the *verify* items above get verified: write the synthetic checkpoint in HF layout, load it in both, compare taps
layer by layer.

0. **Read the reference.** The `qwen4_exp` modelling file settles every *verify* in this document: router
   formula, shared-expert gate, GR wiring and activation, n-gram hashing and row layout, the tail-block rule,
   indexer RoPE details, MTP index reuse, zero-centred-norm convention. Half a day that saves a week.
1. **Config and loader.** `Qwen4ExpConfig` (layer layout, expert counts, QSA and GR and n-gram parameters) from
   `config.json`; canonical names for the new tensors; expert stacking; vision tensors skipped; the n-gram table
   as a separately-loaded, host-resident parameter with its own cache variant; FP8-block-scale dequant for the
   official checkpoint. Synthetic HF writer extended to the new layout.
2. **Gated Residual.** The residual-stream strategy, the layer contract change, parity on the synthetic config.
   Done first because every later component writes through it.
3. **MoE.** Router and grouped-expert seam ops with composed references; the stacked-expert GEMV on torch;
   `gather_qmm` on MLX; grouped GEMM for prefill as a follow-up. Parity, then the real checkpoint's experts
   through the quantizer and cache (73,728 tensors into ~7,000 cache entries).
4. **QSA.** Indexer and block-key cache; scoring and top-k inside the static step; dense-equivalence below budget
   as the first milestone (the model runs at short contexts with existing kernels); then the sparse decode kernel,
   then sparse prefill; then MLX's gather-and-dense path.
5. **N-gram layer.** Hash, host table, pinned gather, step input; NVMe memory-map option.
6. **MTP head** on the new block; index reuse in the round.
7. **End to end.** The 27B's KL harness against a bf16 reference scored on a rented box (§7.4): int4 experts with
   dense parts at int8 vs all-int4 vs the FP8 checkpoint dequantised; tool calls, JSON mode, prefix hits, long
   context on whichever machine runs it (§7).

Sizing: loader and synthetic model a few days; GR two days; MoE a week; QSA one to two weeks; n-gram three days;
MTP and end-to-end a few days. A month of focused work, all in Python, Triton and MLX — no CUDA. The UNTANGLING.md
refactor should land first or at least phase 2 of it (the loader pipeline) and the residual/mixer strategies,
because MoE, QSA and GR are precisely new implementations of those extension points, and adding them to the
tangled version would double the untangling work.


## 7. Running it on our hardware

The hardware: a Threadripper 3960X workstation (24 Zen 2 cores, quad-channel DDR4, **256 GB of RAM**, PCIe 4.0)
holding a **5090 (32 GB, ~1.8 TB/s) and a 5080 (16 GB, ~960 GB/s)** — both Blackwell, so one kernel-tuning class
and the same fp8/FP4 features; an **M4 Max with 128 GB** of unified memory; and a **4060 Ti (16 GB) in a separate
home server**, reachable only over the network. Four strategies, in the order they become available.

### 7.1 The M4 Max (128 GB): the primary target

Everything fits in unified memory with no offload: backbone int4 ~70 GB + MTP 2 + n-gram int4 26 + KV at 64k
~1.5 = ~100 GB, under the 128 GB with room for prefix snapshots (Ollama's MLX build is 105 GB on disk). Expected
decode ~50-70 tok/s plain, more with speculation; the floor computed in §5 is ~7 ms per token. This is the machine
that runs the model first and the one on which the MLX backend's `gather_qmm` and the gather-and-dense QSA path get
built. The n-gram table needs no host/device distinction at all here. int8 for the dense parts (another ~3.5 GB)
is affordable and is the quality setting to prefer.

### 7.2 The workstation: 5090 + 5080 as a two-card pipeline over 256 GB of host RAM

48 GB of GPU memory does not hold the 70 GB int4 backbone, so experts stream — but the workstation's two real
assets change the picture from "offload" to "a large cache in front of a comfortable host": 256 GB of RAM holds
the entire int4 backbone pinned (70 GB), the n-gram table at int8 (51 GB) or even bf16 (95 GB), and a prefix-cache
host tier of tens of GB, all at once; and two cards means two PCIe links.

**Partition by layers.** The dense parts of all 48 layers are ~7 GB at int4 (~12 at int8), the MTP head 2, KV at
64k ~1.5, the block keys and buffers under 1. Split the layers across the cards in proportion to memory — roughly
32 on the 5090 and 16 on the 5080 — and each card holds its layers' dense weights plus as many of its layers'
experts as fit: ~20 GB of the 5090's 42 GB of experts and ~10 GB of the 5080's 21 GB, the same ~45-50% fraction on
each. The rest stream from pinned host memory *over each card's own PCIe 4.0 x16 link* (~25 GB/s practical, the
TRX40 board being PCIe 4), so the two cards fetch in parallel at ~50 GB/s aggregate — the same as one PCIe 5 link
would give a single card. Inter-card traffic is the residual `R` (20 KB per token) once per boundary, over PCIe,
negligible. Pipeline parallelism for one sequence has no bubbles to worry about: the cards simply take turns.

**The arithmetic.** With no expert cache, ~1.25 GB of expert weights per token at int4 over ~50 GB/s aggregate is
~25 ms, plus the cards' own memory time (~2 ms) and 48 layers of launch and copy overhead: ~30 tok/s. With the
resident fraction at ~50% and expert usage as skewed as it is on a single workload, an LRU hot-expert cache
should hit 70-85%, cutting the streamed bytes to 0.2-0.4 GB per token: ~8-16 ms of transfer, so **~50-70 tok/s**
is a reasonable expectation, with speculation on top (the verify step's T rows need the union of their experts,
which is roughly a wash for traffic per accepted token, so speculation's gain here is the usual one in rounds,
not in bytes). Measure the expert-usage histogram first — one more statistic from the round on the Mac — before
building the cache; it decides whether the cache is an LRU or a static "pin the popular ones" list, which is
simpler and may be as good.

**What this needs**, beyond §4: expert offload infrastructure (pinned host stacks per layer, async fetch of the
union of selected experts into a staging buffer, a device-resident LRU or pinned set), and the two-card pipeline:
a captured step per card for its layer range, device-to-device copies of `R` between them, the Decoder's flat
state partitioned by card, the draft head on the 5090. The CPU-compute route (ktransformers-style experts on the
host) is a poor fit for this CPU — Zen 2 has AVX2 only, no AVX-512, bf16 or AMX, and quad-channel DDR4 gives
~70-100 GB/s — and would land around 15-20 tok/s; streaming to the GPUs beats it here and is dropped.

**The same two cards for the 27B.** Independently of Flash-Next: the 5080 is a second serving device. The cheapest
form of "many agents" (NEXT.md 3.1) is two servers on two cards, each a single stream — the 27B at int4 does not
fit the 5080's 16 GB (14.3 GB of weights plus KV), but a 3-bit recipe (NEXT.md 2.2, ~11 GB) would, which is one
more concrete reason for that item.

### 7.3 The 4060 Ti in the home server

A separate machine, so it cannot join a pipeline; it is a network-attached second server. Uses: the 27B at 3-bit
once that exists (not at int4: 14.3 GB plus KV does not fit 16 GB), smaller Qwen3.8 siblings for cheap background
agents, and the device-profile tooling's first test on a different architecture (Ada, sm89: fp8 tensor cores, no
FP4, 288 GB/s). It is not part of the Flash-Next picture.

### 7.4 A rented box

An H200 (141 GB) or RTX PRO 6000 (96 GB) runs everything resident at int4 with the n-gram table in host RAM, and
an 8 x H100 node runs the official FP8 checkpoint through vLLM for the bf16-quality **reference log-probabilities**
the KL harness needs: a few thousand tokens of agent transcript, saved as an `.npz` of ~2 GB, brought home, and
every local quantization recipe scored against it. This is the afternoon's rental NEXT.md 2.6 mentions, and the
device-profile tooling (GEMV tuner, attention ladders, capacity and cache budgets written per device) is what
makes it an afternoon rather than a day.

### 7.5 Order of operations

Build on the Mac (everything fits, nothing to offload, `gather_qmm` for free); validate against the HF reference
there at small scale and against a rented-box bf16 reference at full scale; then the workstation: a single 5090
with streamed experts as the first "runs here" milestone, then the 5080 added as the second pipeline stage with the
hot-expert cache, which is the configuration that should settle at 50-70 tok/s.


## 8. Things to verify before building

Collected from the sections above — each is a question the `qwen4_exp` reference answers in a few lines:

- Router: activation (softmax vs sigmoid), top-k renormalisation, any bias term; shared-expert size and gate.
- Expert tensor layout in the checkpoint (per-expert `gate_proj` / `up_proj` / `down_proj` vs fused 3-D).
- Gated Residual: the bottleneck's input (flattened `4 x H` or per branch), where the norm sits, the gate's
  activation, the static initialisation, and how the n-gram embedding and the final norm interact with the
  branches.
- QSA: the tail-block rule when the current position completes a block; whether `-inf` scores are excluded from
  top-k or padded; the indexer's RoPE base and dims; whether the indexer sees the GR-read input or the normed one.
- N-gram: hash functions and seeds, number of heads per order, table partitioning, row dimension, the gate's form,
  and which residual branch receives the sum.
- MTP: whether the head includes its own n-gram lookup; exactly which indices are reused across draft steps.
- Norms: the zero-centred `(1 + w)` convention, confirmed per norm (the 27B loader already handles it; the new
  indexer and GR norms must too).
- Template: the `reasoning_effort` field's rendering and defaults.


## 9. Relation to the rest of the plan

Everything here is an instance of something already in NEXT.md or UNTANGLING.md: MoE (2.5) and expert offload
(3.2), device profiles (2.6), the FP4 question (2.4, since experts-only NVFP4 checkpoints exist for this model),
and in the untangled layout: two new mixer implementations (MoE feed-forward, QSA), a residual-stream strategy
(GR), an embedding-augmentation hook at a layer index (the n-gram layer), a KV state tuple one array longer (block
keys), and a draft source that takes indices from the verify step. If each of those lands as one implementation of
one extension point, the layout has done its job; if any of them needs the loop or the Decoder to learn something
new, that is the hole to fix before the model lands.
