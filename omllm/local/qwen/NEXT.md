# NEXT

Where the engine goes from here, by horizon. Within a horizon items are in rough priority order. Each entry says
why it is wanted, how it fits the code as it stands, and roughly how it would be done -- the kind of context that
was obvious in the session that built this and is not obvious from the code.

Two framing notes. First, the code is about to be restructured (see UNTANGLING.md), so this document refers to
parts of the engine by role -- "the generation loop", "the Ops seam", "the loader" -- rather than by file name
where a file name would be stale within the month. Second, the measure of "done" for anything below is the same
as it has been: the golden-parity and kernel tests stay green, and the KL harness or the bench says what it cost
or bought. Numbers quoted are from the 27B (Qwen3.8 27B dense) at int4 on a 5090 unless said otherwise.

For orientation, what exists: int4/int8 weight-only quantization with an error-minimising search and per-tensor
precision policies, cached on disk; a static-shape decode step captured into CUDA graphs (`mx.compile` on MLX,
TinyJit on tinygrad) and optionally `torch.compile`d; MTP speculative decoding with rejection sampling and a
restricted draft vocabulary (~140 tok/s greedy, ~125 sampled, 20 ms rounds at ~63% acceptance); Triton kernels for
the GEMV, the DeltaNet step, length-aware decode attention and flash prefill; fused DeltaNet on Metal; fp8 KV as an
option; prefix snapshots with device and pinned-host tiers; an OpenAI-dialect server with grammar-constrained tool
calls and JSON mode; a KL harness for quality; a small local agent for exercising the loop.


## 0. Immediate: a citizen of the repo

This code was written in a chat session against stubs of `omcore`; it works, it is tested, and it is alien to the
repository around it. Before or alongside anything below it gets brought into line. The structural half of that --
untangling the features from one another -- is the subject of UNTANGLING.md and is the bigger job. The rest is a
list of known chores, recorded here so they are not forgotten rather than because they need explaining:

- Serve on the internal HTTP server stack, not `http.server`.
- Look at the internal streaming JSON parser and the ABNF engine for the chat-output parsing and, possibly, for
  the grammar's value parsing; adopt them where they fit without contorting either side.
- Code style per `CODESTYLE.md`: blank lines between logical sections of a function (a comment is not required to
  justify one); no paired assignment `x, y = foo, bar` (real unpacking is fine); definitions and calls with more
  than three parameters go one per line; in general less dense -- the reader is trying to understand the math,
  not admire its compression.
- No `print` outside `entrypoints/`; `log = get_module_logger(globals())` from `omcore.logs.modules` instead
  (load progress, warm-up timings, server request lines all go through it).
- Python-side complexity where it is careless: string accumulation through `+=` in the streaming parser and the
  grammar's tag tracking, lists where a deque or an existing `omcore.collections` structure is meant.
- Implementation hiding: most layer instance fields private; anything a training loop or an exporter would need
  (the parameters) exposed explicitly by each layer, never discovered by scanning `__dict__` for tensors.
- Import discipline: the existing lazy-import mechanism makes the inner imports in the tests unnecessary; use it.
- What this does *not* mean: combing the code to substitute every `omcore` helper that could apply. Coupling to
  helpers is worse than a little repetition; adopt what reads better, leave the rest.


## 1. Short term (days each)

### 1.1 Prompt-lookup drafting beside the MTP head

**Why.** A coding agent's output copies its own context constantly: rewriting a file after a small edit, quoting
a function, echoing a tool result, repeating a path. When the last few generated tokens match an n-gram that
occurred earlier in the context, the tokens that followed it there are a draft that costs nothing to produce
and is accepted most of the time on those spans -- 80-90% over runs of 8-16 tokens is typical for edits. The MTP
head's drafts cost a few launches per round and are accepted ~63%; the lookup, when it fires, is both cheaper
and better. vLLM ships this as its "ngram" speculator; here it is a second draft source, not a replacement.

**How it fits.** Speculative decoding already verifies k+1 rows in one target step whatever produced the
drafts, and the acceptance step is rejection sampling against a draft distribution q. A lookup draft is a point
mass (q = 1 at the copied token), so acceptance reduces to "the target would have sampled it" -- the same
`speculative_accept` works. The draft head's KV must still be brought up to date after a lookup round (the
refresh step that runs after every commit does that already). The verify step is shape-specialised per k, so
a longer lookup draft (k up to 8-16) wants its own captured step; capacity and buckets are unaffected.

**Roughly how.** Keep a rolling hash index of the committed token stream (prompt + generation) keyed on the last
n tokens (n = 3 or 4 works). Each round: if the current tail hits, take the following tokens up to k_lookup as
the draft and run the verify at that length; otherwise draft with the head at k = 3 as now. After the
untangling this is the second implementation of the DraftSource interface and a small composite that chooses
between them. Measure acceptance and tokens per round on a file-rewrite transcript before and after.

### 1.2 Checkpointed prefill: resume at chunk boundaries

**Why.** The prefix cache hits only when a cached state's tokens are an exact prefix taken at a request boundary
(after a prompt, after a generation), because the 48 DeltaNet layers carry a recurrent state that cannot be
rewound to an arbitrary position. That is enough for turn-by-turn agent loops and nothing else: a second session
with the same 5k-token system prompt and tool block starts cold; a harness that compacts or edits history
loses everything. Pure-attention engines solve this with block-level KV sharing (SGLang's radix tree); the
hybrid model needs the state checkpointed at the boundaries it can resume from.

**How it fits.** Prefill is already chunked (4096 tokens by default) and the KV half of a snapshot is a slice
that can be cut at any position for free. The missing piece is the DeltaNet state at intermediate positions:
~150 MB per checkpoint on the 27B, so every chunk boundary of a 32k prompt is ~1.2 GB -- the host tier's job --
and the cache's budgets and LRU already handle demotion.

**Roughly how.** During prefill, after each chunk (or every N chunks), store a checkpoint: the token prefix, the
DeltaNet states, the logits/hidden at that position, with the KV taken by slicing the eventual full snapshot
(store once, reference by length). Lookup becomes "longest checkpoint whose tokens are a prefix", which is the
existing exact-prefix match over more entries; a hit resumes there and prefills the remainder. Keep whole-request
snapshots as they are (they are the common hit). A radix-tree index over token ids replaces the linear scan once
the entry count makes it matter.

### 1.3 Jump-forward in constrained decoding

**Why.** Inside a tool call the grammar often admits exactly one continuation for a stretch: `{"name": "`, then
after the name `", "arguments": {`, the `"` before a known key, the `: ` after it. Decoding those one round at a
time is wasted model time; speculative decoding recovers some of it (the draft head predicts scaffolding well),
not all. xgrammar calls this jump-forward.

**How it fits.** The acceptor knows when a state admits a single token (or a single byte string): walk forward
while the allowed set has one element, collect the forced tokens, and process them as a prefill chunk through the
static step's T>1 path instead of one decode round each. The constraint controller feeds them as if generated.
With speculation on, the forced run can simply be supplied as the draft at length = run length and verified
(it is accepted with certainty); without, it is a verify-shaped step with no sampling. Tokenisation subtlety:
the forced bytes must be split into tokens the model would have produced (the trie gives a canonical split; the
grammar then accepts any tokenisation of the same bytes, so it is safe).

### 1.4 Measurements owed on the real model

Not a feature; listed so they happen. On the 27B: the KL cost of `--kv-dtype fp8` against the int8 reference
(expected a few thousandths of a nat); the first-turn latency of the tool grammar on the real 248k vocabulary
(trie build, free-string mask walks) and the per-turn cost after memoisation; prefill and decode timings at 32k,
100k and the full 262k; the int4-from-bf16 and `km` recipes against a bf16 reference scored on the Mac
(the int8 reference is biased toward Ollama-derived candidates because it carries the blob's Q4_K rounding).


## 2. Mid term (a week or two each)

### 2.1 LoRA: PEFT adapters at inference, and a differentiable model mode

**Why.** Loading adapters trained elsewhere (PEFT) is the cheap way to experiment with what the model does; it
is also most of why the brain is open. Training is not a target for this engine, but if a fully differentiable
mode of the torch backend is a short path from what exists -- and it is -- it should exist: composed ops only,
slow, correct, enough to fine-tune a draft head or run gradient-based analysis without leaving the codebase.

**How it fits.** Inference: keep the base weights quantized and the adapters in bf16; a rank-16 adapter on a
5120x17408 projection is ~0.7 MB against the weight's 45 MB, so memory traffic is nothing and the cost is two
small launches per adapted projection (~900 per step across 64 layers, a couple of milliseconds). The GEMV
kernel can absorb that as an epilogue (`+ B(Ax)`, with `Ax` computed once) when it matters. Merging into the
weights at load (dequantize, add BA, requantize) is free at runtime and loses swapping plus a little quality:
offer it as a parameter-cache variant for a fixed adapter. Fused projections are not an obstacle: three rank-r
adapters on q, k, v concatenate into one rank-3r adapter on the fused weight exactly. Name mapping goes through
the same canonicalisation the loader applies to weights. The DeltaNet layers' in/out projections are ordinary
linear targets; nobody adapts A_log, dt_bias or the conv. One real interaction: an adapter moves the target
distribution and the MTP head was trained for the base, so acceptance drops until the head is tuned alongside
(2.3). Differentiable mode: the torch backend's composed implementations of every seam op are plain tensor code
(the chunked DeltaNet included) and autograd works through them; the fused kernels have no backward. A flag that
selects composed ops only, keeps activations, and exposes each layer's parameters explicitly (see section 0)
is the whole feature; QLoRA-style training of the 27B at int4 fits 32 GB with gradient checkpointing, slowly.

**Roughly how.** An adapter loader for the PEFT format (`adapter_config.json`, `adapter_model.safetensors`); a
linear-layer decoration that adds the low-rank term, selectable per projection; the merge variant through the
quantizer; a test that a merged and an unmerged adapter agree with the HF reference on the synthetic model.
Multi-adapter serving (per-request selection, batched adapters) belongs to the many-agent horizon (3.1).

### 2.2 Calibrated quantization, and 3-bit

**Why.** The quantizer is round-to-nearest with an error-minimising scale search: 0.025 nats KL at int4 on the
27B, a good 4-bit, but a ceiling. Calibration against activation statistics from the user's own text
(GPTQ's error feedback across columns, or AWQ's per-channel scaling before rounding) typically takes int4 to
~0.015 and makes 3-bit usable -- which is what fits a 70B-class dense model in 32 GB (~26 GB at 3 bits).
This is the item that changes which models can run, and the harness exists to prove each step.

**How it fits.** Everything it needs is in place: the HF checkpoint source (bf16, one rounding), the KL harness
with a saved reference, the parameter cache keyed on the recipe so calibrated variants coexist with plain ones,
the precision policies for mixing widths. The torch backend's composed forward gives the per-layer inputs for
calibration by running the reference over a few thousand tokens. 3-bit needs a packing the GEMV kernel can read
(3 bits do not pack into bytes evenly; 10 values per 32-bit word is the usual trick) and a kernel variant.

**Roughly how.** GPTQ in torch is a few hundred lines (Hessian from calibration inputs, columns quantized in
order with error propagated); AWQ is simpler and often enough at int4. Add `--calibrate TEXT`; store under a
new cache variant; measure. Then the 3-bit packing and kernel path, measured against int4 on the same text.

### 2.3 Better drafts: trees, and a draft head tuned on your traffic

**Why.** Acceptance (63% greedy, 57% sampled) is the largest remaining lever on tokens per second, and it is
bounded by the draft, not the verify. Two routes, in order of cost: a tree of drafts (several candidates per
position, EAGLE-2 style, verified in one step with a tree mask) typically lifts tokens-per-round from ~3 to ~4
at the same target cost; fine-tuning the MTP head on the model's own outputs over the user's workload is the
only way past that, and also what makes a LoRA'd base (2.1) keep its acceptance.

**How it fits.** The verify step is T rows with per-row causal masks; a tree needs an explicit [T, T]
attention mask, which the decode attention kernel can take as a bitmap argument, and the DeltaNet per-token
states already come back stacked so any root-to-leaf path can be committed. Rejection sampling over a tree is
the multi-draft generalisation (each node accepted against its parent's residual), well described in the
EAGLE-2 and SpecInfer papers. Training the head needs the differentiable mode (2.1) or an external loop over
exported hiddens: the head conditions on the target's final hidden and the next token, so a few hours of
agent transcripts is the dataset.

### 2.4 FP4 on Blackwell tensor cores (asterisk: only if it does not need hand-written CUDA)

**Why.** The Triton GEMV streams at ~60-65% of the 5090's DRAM bandwidth and that is where Triton tops out on this
shape; the decode step is the GEMV. NVFP4 weights (e2m1 values, fp8 block scales) through the tensor cores'
hardware dequantization is ninfer's path and worth roughly 1.4x on the step. It is the one place the "good, not
maximal" rule bends, because it is the whole remaining gap.

**How it fits, and the asterisk.** This may not need custom CUDA at all: `torch._scaled_mm` supports NVFP4
operands on Blackwell through cuBLASLt, so it is a weight layout (a quantizer output and cache variant) plus a
linear-op override, both of which the seam already accommodates. If it does need a kernel outside Triton, it is
the one exception the project will take, and only if the measured gain is there. The open question is quality:
e2m1 with 16-wide fp8 scales versus asymmetric int4 with 64-wide scales. The harness decides before any kernel
work; if NVFP4 lands near 0.03 nats it is a trade, if it lands at 0.06 it is not.

### 2.5 Mixture of experts

**Why.** The architecture descends from Qwen3-Next 80B-A3B and the family's MoE members are the interesting
larger models: at int4 an 80B-A3B is ~40 GB of weights with ~3B active per token -- too big for the 5090's 32 GB,
right for the Mac's 128 GB, where it would decode at roughly 60-80 tok/s (3B active at int4 is ~1.6 GB of weight
traffic per token). On the 5090 it is an expert-offload problem (most experts in host memory, the active few
fetched per token), a later step (3.2).

**How it fits.** A new mixer type beside Attention and GatedDeltaNet: a router and a set of expert MLPs; the
rest of the layer, the static step and speculation are indifferent. The hot path is the grouped expert GEMV
(gather the active experts' weights, run them as one batched launch) -- a `mx.gather_qmm`-shaped op on MLX,
a Triton grouped GEMV on torch -- and it is one more seam op with a composed reference. The loader needs the
expert tensor naming and per-expert quantization (the cache then has thousands of entries; it copes). Spec
decoding's draft head exists in these checkpoints too.

### 2.6 Device profiles: the 3090, the 4060 Ti, rented boxes, and the Mac's memory split

**Why.** Every device-specific knob exists -- the GEMV tuner, the attention launch ladder, the capacity and
cache budgets, the KV dtype, the draft vocabulary -- and each is set by hand on the command line. A different
GPU (the idle 4060 Ti, the retired 3090, a rented H100 for an afternoon) should be a one-time profiling run,
not a session of flags, and the Mac should be able to choose its memory trade-offs (weights vs. KV vs. prefix
snapshots) from one setting.

**How it fits.** The tuner already writes a JSON keyed by shape; the attention ladder resolves itself at first
use; what is missing is a `profile` step that runs those once, measures free memory and bandwidth, picks
capacity and cache budgets from them, and writes a device-keyed profile the loader reads by default. On MLX the
knobs are fewer (the Metal kernel variant, buffer sizes) and the memory split matters more.

### 2.7 tinygrad performance

**Why.** The tinygrad backend passes parity and is slow on both machines. The intent is tier-2: reasonable and
kept current, never the fastest. "Slow on both" points at the structure -- a realization or JIT boundary that
does not kick in, a per-step rebuild, the quantized matmul expressed in a way the scheduler cannot fuse --
rather than at kernels, and that is diagnosable with tinygrad's own profiling.

**How it fits.** The static step is a pure function already (that was done for TinyJit's benefit); the
quantized linear and the KV write are the two places tinygrad was given something it may dislike. Profile one
decode step, fix what the trace shows, re-measure; accept the result when it is within a small factor of torch.

### 2.8 A ggml backend (tier-3)

**Why.** Interesting rather than needed: ggml's quantized kernels are the reference everyone compares to, its
CPU path is strong, and a backend that drives it through the C bindings would let the same model run where
neither torch nor MLX is wanted. Tier-3 means: only if it can be done cheaply and costs the torch and MLX
backends nothing in speed, maintainability or flexibility. Dropped without regret if it does not.

**How it fits.** The Ops seam is the whole interface; a ggml backend implements it with ggml tensors and graphs.
The weight format is the friction: ggml's Q4_1 is affine with 32-wide groups, ours is 64-wide, so either the
quantizer targets Q4_1 as a cache variant (cheap) or the backend repacks. Prefill and the chunked DeltaNet
would be composed from ggml ops; the fused steps would be absent. Judge by how much of the seam it covers for
how many lines.


## 3. Long term

### 3.1 Many-agent serving: batched decode, continuous batching, paged KV, multi-LoRA, chunked-prefill interleaving

**Why.** The server will only ever serve its owner, but the owner intends to have several agents wandering
around at once. That is the vLLM problem at small scale: more than one sequence in flight, each at its own
position, prefill of a new request overlapping decode of the others, memory shared rather than reserved per
stream, possibly a different adapter per agent.

**How it fits, and why it is long term.** Pieces of it are nearly free and pieces are not. Batched decode at
B = 2-4 is almost free throughput because the step is memory-bound (an M=4 GEMV costs what M=1 does) and the
kernels take a batch dimension already; what it needs is a per-sequence position in the attention kernel (today
`pos` is one scalar) and a Decoder whose flat state is per sequence. Speculative decoding per row is the hard
part: different rows accept different numbers of drafts, so the committed length is ragged and the DeltaNet
state selection is per row. Paged KV is unnecessary until sequences of different lengths share a pool; when it
is, the two attention kernels are ours and take a block table with a modest change, and the Decoder's state
handling takes more surgery than the kernels. Continuous batching (admitting a new sequence mid-flight,
retiring finished ones) sits on top of batched decode and is where the single-worker Engine becomes a scheduler.
Multi-LoRA is 2.1 plus a per-row adapter index in the epilogue. Chunked-prefill interleaving is the scheduler
alternating prefill chunks of one request with decode rounds of the rest, which the chunked prefill already
makes possible. The order, when the time comes: batched decode without speculation; speculation with ragged
commits; the scheduler; paged KV last and only if memory forces it. The untangled generation loop (UNTANGLING.md)
is what makes this a sequence of additions rather than a rewrite.

### 3.2 Expert offload for MoE on the 5090

The follow-on to 2.5: experts resident in pinned host memory, the active ones for the next token prefetched
across PCIe while the current token computes, as ktransformers and llama.cpp's MoE offload do. Bandwidth-bound by
PCIe (a few GB/s of experts per token at 3B active is tens of ms), so it is a way to run the model, not a fast
one; worth having for the 80B-class checkpoints on the card that is actually plugged in.


## 4. Maybe later (not planned)

Named so they are not mistaken for omissions. Neither is on any horizon above.

- **Vision.** If the checkpoints that matter carry a vision tower, it is an encoder plus a projector feeding
  image tokens into the same prefill; the engine would not change below the embedding. Not until a model makes
  it necessary.
- **Multi-GPU.** Tensor or pipeline parallel across the cards that happen to be in the house. The 5090 runs
  everything that fits it; the others are for profiles (2.6), not for ganging. Revisit only if a model that
  matters does not fit one card and MoE offload (3.2) is not enough.


## 5. Non-goals

Explicitly out, so nobody spends a weekend on them:

- **Embeddings and logprobs endpoints, model management.** The API will not outgrow what a plain Ollama-style
  server does; the harness needs chat completions with tools, streaming and cancellation, and has them.
- **Competitive throughput.** Good, not maximal: the engine should be more than reasonable and will not chase
  vLLM for paying users. The remaining 90% of the work for the last 10% of speed is not this project.
- **A persistent megakernel, and hand-written CUDA in general.** Triton is already a heavier dependency than
  is comfortable; custom CUDA is accepted only for the FP4 path (2.4) and only if measured to be worth it. If
  maximal speed ever becomes the goal, the route is pushing tinygrad further, not writing kernels by hand.
- **A home-grown IR or compiler.** The pure step function that the backends compile and capture is the IR;
  a third compiler beside inductor and tinygrad would be a distraction (see UNTANGLING.md).
- **Training as a framework.** A differentiable mode (2.1) yes; optimisers, data pipelines, distributed
  training, no. Adapters are trained with PEFT and loaded here.
