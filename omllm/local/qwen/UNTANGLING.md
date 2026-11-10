# UNTANGLING

How to take an inference engine that works and is tested, and whose optimisations are woven through one another
the way they are in every engine of its kind, and lay it out so that the core is oblivious to the optimisations,
the optimisations are oblivious to each other, and which of them run is decided at boot. This is not a tidying
pass. It is the reason the engine was written from scratch rather than forked from one of the real ones, and it
is the experiment the rest of the project exists to make possible.

This document is for the session that does the work. It is detailed about the current state, the target shape and
the order of operations, and deliberately not detailed about line-by-line decisions: those get made in the
session, with the code open. Read NEXT.md first for what the engine does and where it is going, because the
features listed there are the test of the layout -- each one should land in one place.


## 1. Why

Every serious LLM engine looks the same inside: a forward pass that was clean for a week, then quantization, a
static decode step, speculative decoding, a prefix cache, constrained decoding, batching, each threaded through
the same functions as more arguments, more branches and more state on the same objects, until the generation
loop is a place where eight features meet and none can be understood alone. The authors are not careless. The
features really do interact -- a grammar mask really must be applied to every verify row of a speculative round
at that row's own position -- and the fastest way to make them interact correctly is to put them in the same
function. The result is code that cannot be changed without understanding all of it, and that cannot be forked
and restructured because it churns too fast to backport.

Two earlier attempts at this problem failed from opposite ends: a from-scratch model that was clean and useless
(too slow, too small to matter), and real engines that were useful and could not be bent without a hard fork that
would rot. This engine is the third attempt: real enough to serve an agent at 140 tok/s on a consumer card, small
enough to restructure, with golden-parity tests that pin every optimised path to a reference implementation so
that restructuring can be proven to change nothing.

One warning before the plan, because it applies to whoever does the work, human or model: the clean layout
described here flies in the face of essentially all existing code in this space, and both people and language
models code-switch back into writing what that code looks like -- the extra branch in the loop, the flag on the
shared object, the "just for now" field -- despite explicit instructions, nearby examples and reminders. This
very codebase, written with that intent, drifted into the same shape within a few features. Expect to catch
yourself doing it. The defence is to decide the extension point first and the implementation second, every time,
and to treat "I'll add a parameter to `generate`" as the signal that` an interface is missing.


## 2. State of affairs

What the code is, where the tangles are, and the one part that already got it right.

### 2.1 Inventory

`omllm/local/qwen/`, ~15k lines including tests. The parts, by role:

- **Config and weights.** `weights.py`: the Ollama manifest / GGUF / tensor-blob / Hugging Face sources,
  canonical HF-layout parameter names, config parsing. `quant.py`: the quantized weight format (`QWeight`,
  MLX's layout) and the canonical numpy quantizer with the error-minimising search. `paramcache.py`: the on-disk
  cache of finished parameters.
- **The seam.** `ops.py`: `Ops`, an abstract interface of array operations with composed reference
  implementations of the compound ones (the DeltaNet recurrence and its chunked form, attention over static
  buffers, the KV-state format methods, the fused DeltaNet step), plus `NumpyOps`, the float64 golden.
  `backends/`: `TorchOps` (with the Triton kernels in `torch_triton.py`), `MlxOps` (Metal kernels in
  `mlx_metal.py`), `TinygradOps`.
- **The model.** `model.py`, 1,700 lines: the layers (`Attention`, `GatedDeltaNet`, `MLP`, `Block`), the
  functional `Cache`, `required_param_names` and the precision policies and fusion table, `Qwen35` with
  `from_source` (loading, fusion, quantization, caching), `prefill` / `forward`, the static `step_fn` builder,
  and `generate`; `MtpHead` (the draft head); `Sampler` (device-side sampling, warped distributions, the
  rejection-sampling helper); `Decoder` (static buffers, capacity, buckets, capture, snapshot/restore);
  `SpecDecoder` (the speculative round).
- **Around the model.** `prefixcache.py` (snapshots, device + host tiers), `grammar.py` (the constrained-
  decoding acceptor, token masks, the tool and JSON controllers), `chat.py` (Qwen's chat format, output
  parsing, streaming parser), `serving.py` (Engine, HTTP server, client), `tokenizer.py`.
- **Entrypoints and tests.** `entrypoints/`: generate, serve, kl, tune, validate, agent, and the shared model
  arguments. `tests/`: a synthetic model builder (`test_synthetic.py`), golden parity across backends
  (`test_parity.py`), quantization, kernels, the sampler, the prefix cache, chat, serving, grammar, fp8 KV.

### 2.2 The part that already works: the Ops seam

The model is written against `Ops`. Every compound operation has a composed reference in the base class, every
backend overrides what it can fuse (the Triton GEMV, the DeltaNet step kernel, the attention kernels, Metal's
DeltaNet step, `mx.fast` attention), the backend is chosen at boot, and `test_parity.py` pins every override to
the numpy float64 golden. Features that are *implementations of the same semantic operation* went in this way
and stayed clean: the fp8 KV format is four methods on the seam and the model never looks inside a KV state;
the length-aware attention kernel replaced the composed `sdpa_static` without the layer knowing; the fused
projections are a loader transform the layers accept or not.

The discipline, stated so it can be reused: **composed reference, optional override, selected at boot, pinned by
a parity test.** It generalises to everything below the generation loop. It does not reach the loop itself.

### 2.3 Where the tangles are

**`Qwen35.generate`** is the centre of it. It takes fourteen parameters -- `spec`, `capacity`, `draft_vocab`,
`prefix_cache`, `constraint`, `prefill_chunk`, `should_stop`, `on_token`, `eos_ids`, `static` -- and threads all
of them: it looks up and resumes a prefix snapshot (including the draft head's KV and the one-off `start`
arithmetic for the hidden rows), prefills in chunks with cancellation polled between them, brings the draft head
up to date, stores a snapshot, then forks into a speculative loop (`SpecDecoder`) or a plain one (`Decoder` or
the functional cache), each with its own EOS / budget / cancellation handling, its own sampling with grammar
masks, and its own snapshot at the end. The serving `Engine` wraps it in another layer of stop-string and
streaming logic through `on_token`, and strips the end-of-turn token itself. Adding prompt-lookup drafting,
jump-forward, or checkpointed prefill (NEXT.md 1.1-1.3) to this function means another parameter and another
set of branches in two loops.

**`SpecDecoder.round`** is the second centre. One hundred lines that draft on the device with the head (sampling
from its warped distribution, keeping q and q(d) for the acceptance test, recursing through the head's own step
function), apply the grammar mask to the first draft and compute per-row masks for the verify by cloning the
constraint and feeding it the drafts, run the verify step, do rejection sampling, commit the accepted prefix
into the Decoder, refresh the draft head from the true hiddens, and track statistics. The constraint handling
alone is a quarter of it, and it is correct only because the two features were written in the same place.

**`Qwen35.from_source`** knows everything about loading: which names are required, which are fusable and the
fusion table, the precision policy, whether the source is natively quantized at the requested width (re-pack)
or not (quantize, with or without the search), the cache's key and hit/miss accounting, the draft head's
extra names, dtype placement of the small float32 tensors. It is one function because each of those was added
to it.

**The layers know things layers should not.** `Attention.decode` takes a `bucket` argument because the Decoder
buckets the attention window on backends whose kernel is not length-aware. `Block.decode` forwards `all_states`
and `bucket` to the mixers. `Decoder` computes `state_offsets` from the backend's KV arity. `MtpHead` has its own
step-function builder, bucketed and compiled like the target's. None of this is wrong; it is the shape of
features reaching through objects that were not designed with a place for them.

**Flags on the backend object.** `TorchOps` carries `triton`, `compile`, `compile_cache`, `capture_mode`,
`kv_dtype`, `attn_bucketed`, `attn_splits`, `gdn_block_dv`, `quant_native`, `triton_tuned`: a bag of booleans and
strings that the layers and the Decoder read to decide behaviour. That is configuration by inspection, and it is
how the fp8 KV format ended up as `if self.kv_dtype == 'fp8'` in six methods of one class.

**`serving.Engine`** owns the prefix-cache-friendliness trick (memoising the ids of every answer under the
assistant-turn text it renders to, so a follow-up's ids are an exact extension), the thinking-preservation
choice, the stop-string scanning, and the streaming-parser delivery, in one `_run` method of two hundred lines.

**Smaller instances of the same thing.** `Sampler.sample` and `Sampler.probs` both take an optional mask because
the grammar needed one; the `MaskCache` lives in the grammar module but is used by the model; `generate` writes
`self.last_prefix` and `self.last_spec` on the model as a side channel for statistics the Engine reads back.

### 2.4 What the tests pin down

This is the safety net and it is good. `test_parity.py` runs the synthetic model (random weights, the real
architecture at toy size, built as a GGUF, an Ollama tensor blob and an HF directory) through every backend and
compares per-layer taps, the chunked and recurrent DeltaNet, the static decode step across capacity growth and
attention buckets, speculative decoding against greedy (with the real head and with oracle drafts), the prefix
resume against a cold run. The kernel tests compare every Triton and Metal kernel against the composed reference
under the Triton interpreter. The sampler test checks the rejection-sampling theorem numerically. The grammar
tests fuzz the masks and run the Engine end to end. The serving tests cover streaming, follow-ups, tools, stop
sequences, cancellation and the queue. The fp8 test covers the four-array KV state through everything.

What the tests do not pin down is performance. A restructuring that doubles the Python work per round, breaks
the CUDA-graph static-input protocol, or adds a host sync would pass every test and halve the speed. Step 0 of
the plan fixes that.


## 3. The target shape

Three principles, then the interfaces, then a layout. The layout is a proposal; the principles and interfaces
are the point.

### 3.1 Principles

1. **Composed reference, optional override, selected at boot, pinned by a test.** Already the rule below the
   generation loop (the seam); becomes the rule everywhere. Every feature has a reference form that is obviously
   correct and an optimised form that is tested against it.
2. **Extension points, not parameters.** The generation loop is written once against a small set of
   interfaces. A feature is an implementation of one of them; a feature that needs two is two implementations
   with an explicit protocol between them; a feature that needs a new parameter on the loop has found a missing
   interface. Composite implementations (a draft source that tries lookup then the head; a logit processor that
   chains two) are how features combine without knowing of each other.
3. **Assembly at boot.** An injector or a recipe builds the engine from chosen implementations: which backend,
   which KV format, which token source with which draft sources, which processors, which store. The core model
   and the loop take their collaborators as objects and read no flags. `omcore`'s injection machinery is the
   natural home; how far to push explicit injection versus a plain recipe function is a session decision --
   Guice-style wiring is the aim, dogma about every `if` becoming an interface is not.

Also: no new IR and no compiler. The pure step function that the backends compile (`torch.compile`,
`mx.compile`, TinyJit) and capture (CUDA graphs) is the IR this engine has, and it is enough; a home-grown one
would be a third compiler and a different project. Interface/implementation pairs plus composites are the tool,
and if they prove insufficient somewhere, that is the moment to reconsider, not before.

### 3.2 The generation loop's extension points

(Revised after the first review session, 2026-11-10: the interfaces below were sharpened by bugs found in the tangled
code -- each revision names the bug that motivated it.)

The loop, written once: resume or prefill; then repeat (ask the token source for a round of *accepted* tokens; let
the terminator choose how many of them to keep; tell the source to commit exactly that many; hand them to the
processors and observers) until the terminator says stop; then hand the state to the store. Everything else is one
of these:

- **TokenSource** -- one implementation, `VerifyTokenSource`: draft (0..k tokens from a draft source), verify
  `[next, d_1..d_n]` in one captured step, rejection-sample, return a `Round` of 1..n+1 accepted tokens *without
  committing it*; `commit(n)` then keeps the state after exactly n of them (the verify step returns the state after
  every token, so any cut is a slice). Plain decode is the same source with the null draft source: a round of one
  token, which takes the cheap path (one T=1 step, `Sampler.sample`, no per-token state stacking). There is no
  second "plain" token source: a speculative source whose drafts miss *is* plain decode, so a separate one would be
  a duplicate, and every draft-based feature (prompt lookup, jump-forward) would need implementing twice or be
  speculative-only -- useless on the models without an MTP head (the Qwen3.5 sizes). Verify steps are captured per
  draft-length bucket (padded; the pad positions are rewritten before anything attends to them, as the static
  prefill already does), so a lookup draft of 8 does not mean a compile per length. Mind the kernel limits: the decode
  attention kernel holds `G * T <= 32` query rows (T <= 5 on the 27B) and the fused DeltaNet step `T <= 8`; longer
  drafts need the row-block loop in the attention kernel or the prefill kernel past that.
  *Why commit is separate (bug):* with `next() -> committed tokens`, a round that commits four tokens past an EOS or
  the budget leaves the recurrent state four tokens ahead of the answer, and since the DeltaNet state cannot be
  rewound, the end-of-generation prefix snapshot never matched a follow-up.
- **DraftSource** -- `propose(gen, k) -> Drafts` (device token ids, and their draft distributions q, or point masses
  for drafts that are certain), `on_commit(gen, verified, n)` (the verify step's outputs -- the target's final-normed
  hidden states today, the QSA indices with Flash-Next -- and how many tokens were kept), `resume(gen, state)` /
  `export(gen)` for the store, `prefill(gen, ...)` to bring it up over a prompt. The MTP head is one (it owns its KV,
  its captured steps, the draft-vocabulary restriction, its refresh from the verify hiddens); `NullDraftSource`,
  `LookupDraftSource`, a grammar-forced source (jump-forward) and test oracles are others. Combination is by
  *wrapping*, not by a list: `LookupDraftSource(wrapped=mtp)` proposes from the lookup and falls back to what it
  wraps -- a fallback chain whose order is its meaning, bound with `inj.wrapper_binder_helper`.
- **LogitProcessor** -- contributes to the *target's* distribution at defined points: `for_rows(gen, drafts)` (one
  contribution per verify row, given the drafts before it, drafts as a device array -- a processor that needs them on
  the host pulls them itself, so the second host sync of a round exists only when such a processor is present) and
  `after(tokens)` (advance on a commit). A contribution is a mask (allowed ids) and/or an additive bias, and the
  composite combines them by AND and +: commutative, so the processors are an *unordered* set (a Guice multibinding)
  and no ordering is needed or expressible. The order-dependent warping -- temperature, top-k, top-p, min-p -- is
  the Sampler's own fixed pipeline, not a processor. The grammar controller is one processor (mask);
  presence/frequency penalties are another (bias), and through `for_rows` they become *exact* under speculation:
  row i's histogram includes the drafts before it (the tangled version gave every verify row the histogram as of
  the round's start, so penalised speculative sampling was not quite the target's distribution). Processors apply
  to the target only -- the rejection step makes the output exact whatever the drafts are -- and a draft source may
  ask them for its first draft as an acceptance heuristic, cut to its vocabulary prefix.
  *Why (bug):* the penalties lived in the shared Sampler and were applied to the draft head's 64k-wide logits with the
  full 248k-wide histogram -- a crash whenever `--draft-vocab` met a presence penalty.
- **Sampler** -- `probs(logits)` (the full warped distribution) and `draw(probs)` are the reference; `sample(logits)`
  is the optimised override (top-k candidates only) and a test pins `sample` to `draw(probs(.))` in distribution,
  degenerate cases included -- principle 1 applied to sampling. *Why (bug):* the two were maintained by hand and
  disagreed on exact ties of the bf16 logits under greedy, so greedy speculative output depended on the seed.
- **Terminator** -- `cut(tokens) -> n | None` (how many of a round's accepted tokens to keep, and whether to stop:
  EOS ids, stop strings over the decoded text, the token budget) and `poll() -> cancel?`. The Engine's stop-string scan
  and end-of-turn stripping move here.
- **StateStore** -- `lookup(ids) -> resumable state | None`, `store(ids, state)`: the prefix cache; checkpointed
  prefill is the same interface with more entries. The state is a bundle the token source and its draft source
  know how to resume from; the store treats it as opaque. **Invariant:** the state stored after a generation covers
  exactly prompt + emitted tokens, EOS included -- the tangled version left EOS out on the plain path and kept junk
  past it on the speculative one.
- **Observer** -- `on_tokens`, `on_round(stats)`, `on_prefill(stats)`: streaming delivery, statistics (the
  `last_prefix` / `last_spec` side channels become events), logging.

A `Generation` object holds the state the loop needs (the Decoder, the committed ids, the position, the pending next
token) so that sources, processors and terminators share it by reference rather than by argument lists -- narrowly:
it is the per-request state, not a context object for everything. Batched decode later (NEXT.md 3.1) makes that
state per sequence; design the object so that is an extension rather than a rewrite, without building B > 1 now.

Testing consequence: the synthetic model's random draft head almost never has a draft accepted, which is how the
snapshot bug above passed `test_prefix.py` -- every round committed one token. An `OracleDraftSource` (drafts from
a reference transcript, optionally corrupted at chosen positions) is a first-class implementation, not a test hook
attribute, and the loop's tests use it to force full rounds, EOS and the budget falling mid-round, and grammar
violations at every draft position.

### 3.3 Below the loop

- **The loader as a pipeline.** Source -> canonical parameters (names, dtypes, the transforms a source needs)
  -> transforms (fusion, precision policy, quantization with or without search, native re-pack) -> cache ->
  model construction. Each transform is a function from a parameter dict to a parameter dict with a cache key
  contribution; `from_source` becomes the composition of a chosen list of them. The draft head is a second
  small model built by the same pipeline from its own names.
- **Strategies into layers, not flags onto Ops.** `Attention` takes its KV format and its attention operation
  as objects (the format already *is* an object's worth of methods on the seam; make it one). The bucketing
  that today reaches into `Attention.decode` through a parameter becomes a property of the attention strategy:
  a bucketed strategy slices and captures per window, a length-aware one does not, and the Decoder asks the
  strategy for its step key rather than computing buckets itself. `Decoder` takes a capture strategy (CUDA
  graph, static-input protocol, plain, with compile as a wrapper) instead of reading `capture_mode` and
  `compile`. `TorchOps` keeps the kernels and loses the bag of flags; the flags become the choice of strategy
  objects at boot. Whether `Ops` itself stays one wide interface or splits into the array primitives and the
  compound operations is a session decision; the parity tests do not care.
- **The block as a composition (Flash-Next drives this).** A block is a residual stream strategy (plain; later
  Flash-Next's four-branch Gated Residual), a mixer (gated attention, Gated DeltaNet; later QSA) and a feed-forward
  (dense SwiGLU; later MoE), built from the config by an architecture object rather than chosen by `kind == 'full'`
  branches inside `Block`. The architecture also owns the canonical parameter names and the fusion table for its
  layers, so a second architecture (`qwen4_exp`) is a second implementation, not edits to the first. The older and
  smaller Qwen3.5 checkpoints (no MTP head, tied embeddings) are the same architecture with fewer parts loaded.
- **Mixers own their state.** Each mixer says how many arrays its decode state has, builds the empty state, pads it
  to a capacity, exports and adapts it; the Decoder walks the mixers instead of computing `state_offsets` from layer
  kinds and the backend's KV arity. QSA's block-key cache is then one more array in its mixer's state, with nothing
  else learning about it.
- **Step inputs beyond tokens.** The captured step's argument list gets room for per-step side inputs supplied by the
  host before each replay (Flash-Next's n-gram rows are the first), through the static-input protocol that already
  carries the token ids.
- **Parameters explicit.** Each layer exposes its parameters by name (a method, not `__dict__` scanning) and
  keeps its fields private; the differentiable mode (NEXT.md 2.1), adapters and exporters build on that.
- **Statistics are events.** Nothing writes `last_*` onto the model.

### 3.4 A layout (proposal)

Roughly one subpackage per role, so that each item in NEXT.md lands in one of them:

- `core/` -- config, canonical parameter names, the layers and the functional forward, `Cache`. Imports the
  seam and nothing else in the package.
- `ops/` -- the seam, composed references, `NumpyOps`; `backends/` beneath it.
- `load/` -- sources, transforms, the parameter cache, the pipeline.
- `decode/` -- the Decoder and its capture strategies, the Sampler, the generation loop and the extension-point
  interfaces, the token source (`VerifyTokenSource`, with rejection sampling) and the null draft source, the
  terminators, the observers.
- `spec/` -- draft sources: the MTP head's (its KV, steps and refresh), prompt lookup over it; later trees.
- `constrain/` -- the grammar: acceptor, masks, controllers, as logit processors.
- `prefix/` -- snapshots and the store; later checkpoints.
- `serve/` -- chat format, Engine, HTTP, client; `agent` with the entrypoints.
- `quality/` -- the KL harness, calibration later.

The names are not important; the direction of dependency is: core knows nothing of decode, decode knows nothing
of spec / constrain / prefix, those know nothing of each other, serve knows all of them, and the boot-time
assembly is the only place that names every piece. (An import-graph test to enforce this was considered and
rejected for now -- the repo will get a mechanism for that later; until then it is a rule, not a check.)

### 3.5 Assembly: the injector

Decided 2026-11-10: real `omcore.inject` usage, in the shape `omllm/ui/agent/inject` grew into, and the engine stays
fully usable without it.

- **The core never mentions the injector.** Every piece is a plain class taking its collaborators as keyword
  arguments, with no IO and no work in its constructor (loading weights, capturing steps, reading files happen in
  explicit methods or providers). Tests build what they need by hand from the synthetic model and a few
  `Null*` / `Oracle*` implementations. No hand-written recipe for the full real model is kept beside the bindings.
- **Wiring lives only in `inject.py` modules and an `inject/` package.** Each role package that has something to
  bind gets an `inject.py` exposing `bind_<role>(config) -> inj.Elements`; the top-level `inject/` package composes
  them. Configuration is one small dataclass per role, not one large config object.
- **Two lifetimes.** Singletons: the backend `Ops`, the loaded model, its compiled and captured steps, the prefix
  store, the tokenizer. A *generation scope*, seeded with the request (`GenerationParams`: prompt ids, sampling,
  constraint spec, budget, stop strings), holds the token source and draft sources, the processors, the terminator,
  the observers and the `Generation` state. The bridge is the agent's `ScopedTurnRunner` pattern: a plain
  `GenerationRunner` interface the Engine depends on, and an injector-backed implementation in `inject.py` that opens
  the scope and asks for the loop. The engine is synchronous with one worker thread, so it uses the sync injector.
- **Flags become bindings.** `--kv-dtype fp8` binds the fp8 KV format; `--spec k` binds the MTP draft source (and
  `--lookup` would wrap it); `--compile` wraps the capture strategy; a request with tools adds the grammar processor
  to its scope's processor set. The bag of booleans on `TorchOps` disappears into those choices.
- **Ordering.** Multibindings are unordered on purpose. Where order is meaning -- a draft-source fallback chain, the
  compile-around-capture stack -- it is a wrapper chain built with `inj.wrapper_binder_helper`; where it is not, the
  contract is made order-free (the processors' commutative contributions, 3.2).


## 4. Plan of attack

In order. Every step ends with the full test suite green and the bench within noise of the previous step; a step
that cannot meet both is not finished. Steps are sized so that each is one or two sittings with the code open.

**Status (2026-11-10).** Steps 0-8 and 10 have landed, each its own commit with the suite green. The 27B bench at the
end against step 0's: greedy transcripts identical; speculative decode the same (148.3 vs 148.7 tok/s, 18.1 vs 18.0
ms and 2.68 tokens a round); everything host-side better -- a short prompt's first token 24.9 vs 31.6 ms per prompt
token, a follow-up's 872 vs 986 ms on a prefix miss and 492 vs 3102 ms on a hit (step 6's state invariant made the
hits real), a 32k prefill 1253 vs 1145 tok/s at a peak of 21.2 vs 21.6 GiB. (Plain decode reads 65.1 vs 17.1 tok/s;
step 0's number was a mismeasurement.) What is left:

- Step 6: done. Stop strings are a terminator; the answer -- ids, text, end-of-turn stripping, streamed deltas, stop
  trimming -- is an observer (`serve/serving.py`'s `_ChatStream`), so `Engine._run` is assembly plus translation.
- Step 7: half done. The block as a composition and mixers owning their state layouts (the part Flash-Next needs
  first) landed; the KV format, the attention strategy and the capture / compile strategy are still `TorchOps` flags.
- Step 9: done for the code each step touched; the loaders, `arch/` and the backends still print.
- Older and smaller models: qwen3.5:4b (no MTP head, tied embeddings, 32 layers) runs through the same code, by hand
  and through the injector, plain and with prompt lookup (the numbers are in NEXT.md 1.1).
- Step 10: prompt lookup (`spec/lookup.py`, NEXT.md 1.1) is one draft source, which wraps the next one down the chain,
  and one binder. Nothing else changed except a hole it found in the MTP source, which assumed it drafted every round
  (it grew its KV only when proposing, so a refresh after a lookup round could write past it), and a recompile it
  exposed (below). What lookup is worth on the 27B is in NEXT.md 1.1.

Found on the way and fixed, each with a test that fails without the fix: the ways a compiled step silently
recompiled or never compiled at all -- an omcore dataclass inside the step, a guard on the size of the GEMV launch
table, and guards on the strides of the DeltaNet conv state, which was a slice of the step's input: a prefill's
depended on the prompt's length (every request of a new length recompiled every step, ~22 s on the 27B), and a plain
round's differed from a verify commit's (plain and verify rounds mixing in one generation recompiled: minutes); and
the draft head's next input, a slice of its refresh output, whose strides followed the last round's draft count (a
follow-up turn under prompt lookup recompiled the head's step mid-request). The general rule: state that a compiled
step takes is copied with `Ops.copy`, which lays it out canonically (TorchOps' `clone()` had kept a size-1 slice's
strides). `tests/test_tracing.py` pins them all.

### Step 0 -- The safety net gets a performance arm

Add a `bench` entrypoint that loads the model once and reports, over a fixed prompt and a fixed number of
rounds: prefill time per token, decode round time, tokens per round and acceptance with speculation on, first-
token latency with and without a prefix hit, host syncs per round (count them: a round should have exactly
one). Run it on the synthetic model on CPU (for the Python-side costs, which is what restructuring threatens) and
on the 27B on the GPU (for the real numbers). Record both before touching anything. The CPU numbers will move
with Python overhead -- a few percent is fine; doubling is not. Also capture a reference transcript: the exact
token ids the 27B produces greedy for a handful of prompts at a fixed capacity, so that "identical output" is a
diff, not an impression.

Done as `tests/bench.py` (a test-support utility with an entrypoint). Beyond the above it reports the configuration
that actually took effect -- compiled graphs, graph breaks, how many quantized shapes the tuned GEMV table covers --
peak memory over a long prompt, and whether greedy speculative output equals plain greedy, because the regressions
found while writing it were exactly of that kind: a `--triton-tuned` file that did not exist (silently 0 configs,
127 instead of 173 tok/s), a `--compile` that compiled nothing (an omcore frozen dataclass inside the step; see
`backends/torch_triton.py` and `tests/test_tracing.py`), prefills that ran out of memory at 8k tokens.

### Step 1 -- Split `model.py` mechanically

No semantic change. Move the classes to the subpackages of 3.4 (or whatever names the session settles on),
leaving `model.py` as a re-export shim for one step so entrypoints and tests keep working, then update imports
and delete the shim. Keep `generate`, `SpecDecoder.round` and `from_source` exactly as they are in this step --
the point is that the next steps diff cleanly against something already in its final place. Expect this to be
the step where the code-switching warning first applies: the temptation to "fix a small thing on the way" is
exactly how a mechanical move becomes an unreviewable change. Don't. One allowed exception to 3.4's direction of
dependency while the shim and `generate` remain: whichever module holds `generate` imports the speculative and
prefix code until steps 3-6 have moved it out.

### Step 2 -- The loader pipeline

Break `from_source` into the pipeline of 3.3: a source stage that yields canonical parameters with the
small-float32 placement decided, transforms for fusion (the table moves with it), the precision policy, native
re-pack versus quantization (search or not), the cache (key composition from the transforms' contributions,
hit/miss accounting as an event, not a print), and construction. The draft head goes through the same pipeline.
The parameter cache's identity and variant scheme must come out byte-identical -- `test_quant.py` checks the
caches built on two backends are identical and that `km` loads with the right widths cached and uncached; both
stay as they are. This step also establishes the explicit-parameters convention on the layers.

### Step 3 -- The generation loop, plain decode first

Write the loop of 3.2 and the interfaces, with `VerifyTokenSource` over the null draft source (plain decode is
that), the sampler without its mask argument,
a terminator covering EOS / budget / cancellation, an observer that delivers tokens, and a null processor and
null store. Make `generate` call it for the non-speculative, non-prefix, non-constrained case and keep the old
paths for the rest, temporarily. The parity test for static decode and the serve tests for plain requests cover
it. Resist widening the interfaces for the features not yet moved; the next steps will tell you what they
actually need.

### Step 4 -- Speculative decoding as a token source; the head as a draft source

Move `SpecDecoder`'s round into `VerifyTokenSource` (verify, rejection sampling, the cut-before-commit protocol)
and its drafting and refresh into the MTP draft source.
Move `MtpHead` behind the draft-source interface (its prefill, its KV, its captured steps, the draft-vocabulary
restriction stay inside it). The round's constraint handling is *removed* in this step and comes back through
the processor in step 5 -- do them in that order, so that the token source is seen to work with no knowledge of
grammars before the protocol is reintroduced through an interface. To keep every step green, constrained requests
stay on the old path during step 4 (as step 3 keeps the old path for what it has not moved), or steps 4 and 5 land
together. `test_parity.py`'s speculative tests (real
head and oracle drafts, both equal to greedy) and `test_sampler.py`'s theorem test are the pin. Watch the host
sync count in the bench: the round has one, and the rejection step's device-side design is what keeps it at one.

### Step 5 -- The grammar as a logit processor; penalties too

Implement `LogitProcessor` for the tool and JSON controllers: `for_next` is `allowed()`, `for_rows` is the
clone-and-feed lookahead that was inline in the round, `after` is `feed`. The `MaskCache` goes with it. The
presence/frequency penalty that lives in the Sampler becomes a second processor -- exact under speculation through
`for_rows` -- and the composite combines their commutative contributions. The Sampler's `sample` gets pinned to
`draw(probs(.))` by a test (`test_sampler.py`), and the theorem test extends to penalties.
`test_grammar.py`'s engine tests (random weights, `tool_choice: required`, valid calls with and without
speculation) are the pin; they are the tests most likely to fail on a protocol mistake, which is why they exist.

### Step 6 -- The prefix cache as a state store; the terminator takes the Engine's scanning

Move the resume/snapshot logic out of `generate` into the store interface and the token source's resume method
(the draft-head KV and the `start` arithmetic belong to the MTP draft source). The stored state covers exactly
prompt + emitted tokens (3.2). `test_prefix.py` (resumed
follow-up equals cold run, plain and speculative, across tiers) is the pin. Then move the Engine's stop-string
scan and end-of-turn stripping into a terminator, and its streaming delivery into an observer, so `Engine._run`
becomes assembly plus request/response translation. The serve tests cover both.

### Step 7 -- Strategies into the layers and the Decoder

The KV format as an object held by `Attention`; the attention strategy (bucketed or length-aware) owning the
window decision and the step key; the capture strategy held by the Decoder; `TorchOps` losing its flags; the block
as a composition of residual stream, mixer and feed-forward, built by an architecture object; mixers owning their
state layout (3.3) -- what Flash-Next needs before any of its components can land as single implementations. This is
the step with the most risk of a performance regression, because the CUDA-graph static-input protocol and the
in-place KV write aliasing live here (see 5.1). `test_parity.py`'s bucket test and `test_fp8kv.py` are the pins;
the GPU bench is the judge.

### Step 8 -- Assembly at boot

Replace the entrypoints' flag plumbing with injector bindings (3.5): backend, KV format, capture, draft sources,
processors, store, observers, from per-role config objects. `generate` becomes a thin
convenience over the loop for scripts. The serve entrypoint and the agent are the first consumers; the
warm-up becomes a method of the assembled engine rather than a fake generate call.

### Step 9 -- The style pass, interleaved

Section 0 of NEXT.md: logging instead of prints, the spacing and one-per-line conventions, private fields,
import discipline, the internal HTTP stack, a look at the internal JSON and ABNF machinery for the chat parser
and the grammar's value states. Do these per subpackage as it is touched in steps 1-8 rather than as a final
sweep, so each diff stays readable, and do not let them become an excuse for the obsessive-DRY failure mode:
adopt what reads better, leave the rest.

### Step 10 -- Prove it with a feature

The test of the layout is NEXT.md 1.1, prompt-lookup drafting: it should be one new draft-source implementation
and one composite, with no change to the loop, the speculative source, the grammar or the store. If it needs
more than that, the layout has a hole, and finding it now is the cheapest time.


## 5. Things that are easy to break

Known invariants that are not obvious from the code and that a restructuring can violate while every test
passes. Each has a test or a bench signal noted; keep them in mind at every step.

### 5.1 The static step's protocol

- The step functions take *everything* as arguments (tokens, position, the `arange` and rope tables, the
  flat state) and close over no tensors, so that one compiled function serves every Decoder with the same
  shapes. Closing over a table re-traces 64 layers per Decoder (that cost 20 s per `generate` once).
- The captured step is keyed by (T, all_states, return_hidden, bucket) and the capacity; a different capacity
  is a different graph and, with compile, a different compile. The warm-up must use the serving capacity.
- `kv_write` is in place and returns the same buffer object. `CudaGraphStep` skips copying static inputs whose
  object identity is unchanged; the fp8 format writes in place for the same reason, by item assignment on the fp8
  buffer itself. Breaking the aliasing silently adds a full KV copy per step.
- Nothing inside a step may allocate from the host or index with a 0-d tensor (that is a `.item()` and illegal
  under capture); positions are indexed with a 1-element array.
- Compile runs once eagerly before tracing (`_DeferredCompile`) so that the Triton wrappers resolve their launch
  configurations off the traced path; the jitted kernels must be plain module globals for dynamo to lower
  launches as kernels rather than trace Triton's launcher (that regression cost 30% once and showed up only as a
  warning).
- User-defined Triton kernels inside the compiled step must not take float scalar arguments — torch.compile passes them
  as fp64.
- Nothing inside the compiled step may make an indexed write through a dtype view of one of its arguments
  (`buf.view(torch.uint8).index_copy_(...)`): inductor stores the view-typed value through the buffer's own typed
  pointer. For a uint8 view of an fp8 buffer Triton refuses the store (`cannot cast uint8[..] to fp8e4nv`); for
  pairs it can convert by value, such as an int32 view of a float32 buffer, the result is silently wrong. Reading
  through such a view is fine. `x/torch_/dtypeviewrepro.py` reproduces the bug on its own;
  `test_torch_triton.py::test_fp8_compiled_write` pins the fp8 write on CUDA.

### 5.2 One host sync per round

The speculative round sends exactly one thing to the host: the accept flags, the corrections and the drafts
together, after the verify. Drafts are sampled on the device, q and q(d) stay on the device, the corrections are
pre-drawn for every row. The grammar's per-row lookahead needs the drafts on the host *before* the verify's
distribution is masked, which is a second, earlier read; it is paid only when a constraint is active. The bench
counts syncs; a restructuring that adds one shows up there and nowhere else.

### 5.3 Snapshot semantics

A prefix snapshot is valid only at the position it was taken, because the DeltaNet state cannot be rewound;
matching is on token ids exactly; the draft head's KV in a snapshot covers entries 0..n-2 and the resume logic's
`start` arithmetic depends on it. The functional `Cache` holds exact-length KV, the Decoder holds capacity-
length buffers; conversion between them and between KV formats (`kv_adapt`) is where off-by-ones live.
`test_prefix.py` and `test_fp8kv.py` are the pins.

### 5.4 The chat/prefix contract

Two serving choices keep the prefix cache hitting across turns: reasoning blocks are preserved in every rendered
assistant turn (the stock template strips them, rewriting history each turn), and the ids of every answer are
memoised under the assistant-turn text they render to and substituted when that turn reappears, because
re-tokenising text does not reproduce ids across a turn boundary. Moving the memo must keep its key exactly.

### 5.5 Lazy imports

No third-party module is imported at import time anywhere outside `tests/`: proxies via the lazy-import
mechanism, dtype tables as functions, no third-party default arguments, no decorators that need the library
(the Triton kernels are jitted into module globals on first use by `ensure_kernels`, which also replaces the
`triton` / `tl` proxies with the real modules because Triton resolves `tl` through the kernel's globals).
A probe that imports every module with numpy/torch/mlx/tinygrad/triton blocked exists in the lazy-imports work
and should stay runnable; annotations are lazy on 3.14, which this package targets, so do not add
`from __future__ import annotations`.

### 5.6 The quantizer is canonical

The numpy quantizer produces identical bytes on every machine and backend (fixed-order reductions, IEEE
arithmetic), so a parameter cache built on the CUDA box and one built on the Mac checksum equal. The on-device
torch search is an opt-in that is faster and not byte-identical. The cache's identity scheme (Ollama digest; HF
shard names and sizes, deliberately not path or mtime) is what lets caches share names across machines.

### 5.7 Numerics that look like bugs

The chunked DeltaNet inverts a unit-triangular matrix by forward substitution; the Neumann-product form is the
same matrix in exact arithmetic and is unusable on repeated tokens (1e6 relative error even in float64, NaN in
the model). The attention kernels' shared-memory ladders resolve launch configurations on first use because
head_dim 256 tiles do not fit Blackwell's 99 KB at the default pipeline depth. Both have regression tests; both
are the kind of thing a well-meaning simplification reintroduces.


## 6. What not to do

- Do not add a parameter to the loop. Find the interface.
- Do not put a flag on `Ops`. Make a strategy object.
- Do not fix things on the way during the mechanical split; note them and do them in their step.
- Do not build an IR, a graph of the step, or a scheduler. The backends' compilers are the compilers.
- Do not write the import-graph test; the repo will get its own mechanism.
- Do not comb the code for `omcore` helpers to apply. Coupling to helpers is worse than repetition.
- Do not design batched decode in. Design so that per-sequence state is an extension, and stop there.
- Do not accept a step whose bench numbers moved without an explanation you can write down.
