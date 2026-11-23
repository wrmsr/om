# INKLING

Inkling 2 Mini on this engine: what the model is, how it was fitted to the engine without teaching the engine about it,
what the code computes, what was verified against what, how it runs on the hardware in the house, and what is left.
Written 2026-11-22 from the handoff that specified the model (a prose and math description prepared from the lab's
release and the reference implementations), the released checkpoint's metadata, and black-box runs of the reference
implementation. Read README.md and UNTANGLING.md first; FLASHNEXT.md is the earlier document of the same kind.

Not a Qwen model. It lives in this package because the package is the engine.


## 1. What it is

`thinkingmachines/Inkling-2-Mini` (HF model type `inkling2_loop`), revision `b85c3cfa615fc413cc9af3379f491b963f3b586a`:
a 26.4B-parameter mixture-of-experts decoder of which ~3.4B distinct parameters are active per token, text and images
in, text out, 1,048,576 tokens of advertised context. 19.5 GB on disk, because the experts -- 24.5B of the parameters
-- are stored as 4-bit and 8-bit microscaled floats.

| | |
| --- | --- |
| Layers | 24 physical; layers 6..17 run three times a token: **48 visits** |
| Hidden | 2,304 |
| Attention | 24 query / 8 KV heads of 128 (not hidden / heads); no rotary embedding |
| Attention pattern | five local layers (a 1,024-token sliding window) and one global per block of six |
| Feed-forward | 128 experts, 8 routed per token, intermediate 1,152; no shared expert |
| Convolutions | four causal 4-tap convolutions over time per visit (keys, values, both sublayers' outputs) |
| Residual stream | block sums kept apart (blocks of six layers), read by learned queries |
| Vocabulary | 201,024 embedding rows, 200,058 ids produced |
| Experts on disk | NVFP4 in layers 0..19, MXFP8 in 20..23; everything else bf16 / float32 |

What is here: the text decoder, exact; the released checkpoint loaded with its experts as stored, from the lab's
Hugging Face repository or from a GGUF of it in llama.cpp's layout (section 2); cached and static decode,
prompt-lookup drafting and the checkpoint's own draft model (DSpark: section 4.7), prefix snapshots; the tokenizer;
the chat protocol with reasoning and tool calls, served over the OpenAI endpoint, tool calls and JSON mode held to a
grammar. What is not: the vision tower, and the sources section 9 lists.


## 2. Getting and running it

The checkpoint is the lab's own Hugging Face repository, pinned (20.2 GB; 0.6 of it is `mtp.safetensors`, the draft
model, which only `--spec` reads: `--exclude mtp.safetensors` leaves it out):

```bash
hf download thinkingmachines/Inkling-2-Mini --revision b85c3cfa615fc413cc9af3379f491b963f3b586a \
    --local-dir ~/hf/Inkling-2-Mini
```

`--model` takes the directory, as for any Hugging Face checkpoint; the architecture, the tokenizer and the chat
protocol follow from what is in it.

Or a GGUF in llama.cpp's layout for the model (`general.architecture = inkling2_loop`: what mainline llama.cpp
reads). Unsloth's `UD-Q8_K_XL` is the checkpoint without loss -- the NVFP4 experts as the lab packed them, the rest
bf16 -- pinned (22.9 GB):

```bash
hf download unsloth/Inkling-2-Mini-GGUF Inkling-2-Mini-UD-Q8_K_XL.gguf \
    --revision 8078d149286eec7193795413b9e0643da6d11fa1 --local-dir ~/hf/Inkling-2-Mini-GGUF
```

`--model` takes the file, and what loads is the checkpoint's model (sections 5 and 7), less two things. A GGUF of the
model holds no draft model, so `--spec` is refused. And the experts of layers 20..23 are held dense: 7.6 GiB at bf16
where the checkpoint's MXFP8 is 3.9, so 21.3 GiB of weights where the paragraphs below say 17.6. It is also slower
to load, 70 s where the checkpoint takes 13: fifteen for the reader over the file's header (the tokenizer's
lists), thirty regrouping the NVFP4 bytes on one core, the rest expanding the last layers' bf16. On the 5090 it
is 21.4 GiB on the device and decodes at 87 tokens/s where the checkpoint is at 92 (the last four layers' dense
experts are gathered and multiplied a token at a time); its first 160 greedy tokens are the checkpoint's. None of
the numbers below were taken from a GGUF.

```bash
python -m omllm.local.qwen.entrypoints.generate --model ~/hf/Inkling-2-Mini --think -n 256 \
    -p "Write a Python function that checks whether a number is prime."
python -m omllm.local.qwen.entrypoints.generate --model ~/hf/Inkling-2-Mini --spec 7 --lookup 6 --lookup-k 15 -p "..."
python -m omllm.local.qwen.entrypoints.serve --model ~/hf/Inkling-2-Mini --spec 7 --lookup 6 --lookup-k 15 \
    --capacity 131072 --warmup --port 8000
```

On the 5090: 17.6 GiB of weights, loaded in 12 s (the checkpoint's bytes go to the device as they are: there is
nothing to quantize). Options that matter:

- `--prefill-chunk N`: a long prompt's chunk; 4,096 is the default, and larger ones no longer buy anything here
  (section 8).
- `--capacity N`: the global layers' KV buffers, 32 KB per position at bf16 (8 visits x 8 KV heads x 128 x K and V).
  The other forty visits keep a 1,023-position window each, 160 MiB in all, whatever the capacity. 131,072 positions
  peak at 22 GiB.
- `--spec 7`: speculative decoding with the checkpoint's draft model (sections 4.7 and 8): 1.5 to 1.85 times the
  plain speed on reasoning, code and structured text, 1.1 on a chat answer, 0.95 on a story. A number is
  the most drafts a round hands the target (7 is all a block has); a list, e.g. `3,7`, the counts it may hand it.
  With `--lookup` a round drafts by lookup when the context has the continuation and by the draft model when not.
- `--compile`: torch.compile the steps. It was where the speed was while a decode step was twelve thousand small
  operations; now that its regular pieces are kernels of their own (section 8) it buys a twentieth more -- 132
  tokens/s against 127. The first run compiles for four minutes a step shape -- some thirteen for
  a server's three (plain, `--lookup`'s verify, `--step-prefill-max`'s), and one more for every draft count of
  `--spec`; with `--cache-dir` and `--warmup` the
  artifacts are kept, and a restart's warm-up of one shape is 45 s. Give the model a cache directory of its own:
  the compile cache is one file a directory, and another model's would be replaced. Unquantized, the directory
  also receives 6 GB of the dense parameters, copies that save nothing here (the parameter cache is for sources
  that are expensive to materialize); with `--quant` they are the quantized projections, which do save their 35 s.
- `--kv-dtype fp8`: halves the global KV (section 8 has what it costs).
- `--reasoning-effort`: `none`, `minimal`, `low`, `medium`, `high` (the default), `xhigh`, or a number in [0, 0.99].
- `--quant int8|int4` applies to the dense projections only (attention, embedding, output head: 3.9 GB at bf16). The
  experts are never requantized: they are held in the formats the checkpoint stores them in. int8: 16.3 GiB, 35 s
  to load, and no measurable cost (KL 1.2e-3 against the float32 reference, inside bf16's own 2.6e-3). int4: 15.6
  GiB at KL 3.5e-2 -- not worth it. Neither changes the decode speed.
- `--step-prefill-max 48`: a follow-up of a few tokens to a stored conversation through the captured step (31 ms
  for 16 tokens) rather than the eager forward, whose floor is 0.11 s whatever the length.

`dtype f32` computes exactly what the reference implementation computes in float32 (section 7) and fits the 5090
(20.8 GiB peak on a short prompt); bf16 is the default and the released checkpoint's own dtype.


## 3. How it fits the engine

The requirement was that the model reuse the engine and that the engine not learn about the model: no `if inkling`
anywhere, the dependency-injected decomposition doing what it was built for. What that came to:

**Reused as it was.** The generation loop, the one token source, samplers, logit processors, terminators, observers;
the static `Decoder`, its capture and its slabs; prompt-lookup drafting; the prefix cache and its tiers; the `Ops`
seam, the KV state formats (bf16 and fp8), the loader pipeline (plan, materialize, report), the HTTP server and the
engine around it; the BPE tokenizer core; the injector bindings, none of which changed shape.

**New implementations of existing extension points.**

| Extension point | Inkling 2's implementation |
| --- | --- |
| `Mixer` | `Inkling2Attention` (core/inkling2/attention.py) |
| `FeedForward` | `Inkling2MoE` (core/inkling2/moe.py), over the stacked-expert seam Flash-Next's MoE uses |
| `Connection` | `DepthAttentionConnection`, `DepthFeedForwardConnection` (core/inkling2/connections.py) |
| `ResidualStream` | `DepthResidualStream` (core/inkling2/depth.py) |
| `StateLayout` | `SlidingKvStateLayout`, `RunningKvStateLayout` (core/kvspans.py), `ShortConvStateLayout` (core/shortconv.py) |
| `TensorSource` | `Inkling2HFSource` (load/inkling2.py), `Inkling2GgufSource` (load/inkling2gguf.py) |
| architecture | `Inkling2Architecture` (arch/inkling2.py) |
| grammar constraint | `FramedToolConstraint`, `FramedJsonConstraint`, `FramedPlainConstraint` (constrain/framed.py), over the existing acceptor |

**Extension points the model found missing.** Each is generic, and the Qwen architectures now go through it too:

- `Layer` (core/mixing.py): what the model runs in order. `Block` is one; so is `SublayerBlock` (core/sublayers.py), a
  layer of stateful sublayers, and so are the loop's two markers. A model's execution order is a list of layers, each
  with its own slot of decode state, and need not be a list of distinct weights: this is where "24 layers, 48 visits"
  lives, and nowhere else. `Qwen35.new_cache()` sizes a cache by it (`Cache(cfg)` assumed one slot per config layer).
- `OutputHead` (core/heads.py): from the stream's exit to logits. Qwen's is the projection; Inkling's softcaps it.
- `StepPositions` (core/positions.py): what a static step is handed about positions. Qwen's is the rotary tables;
  Inkling's is nothing (its mixers work from the position itself). The step's table arguments are now as many as the
  architecture has, which is what `Decoder.tables()` returns.
- `ShortConv`, `ConvolvedMixer`, `FeedForwardMixer` (core/shortconv.py): a short causal convolution with its history
  as decode state, a mixer whose output passes through one, and a stateless feed-forward where a mixer is taken.
- `KvSpan` (core/kvspans.py): which earlier positions an attention layer sees and how their keys and values are kept:
  append-only capacity buffers (`FullKvSpan`), or a fixed-size sliding window (`SlidingKvSpan`).
- `Architecture` (arch/base.py), chosen by the config's type from a table (arch/registry.py) where there was an
  `isinstance` chain; `ModelConfig` (core/config.py) is what the engine reads of any config.
- `MicroscaledWeight` (ops/microscaled.py), `TensorSource.get_microscaled`, `Ops.microscaled`: a source's tensors in a
  packed float format adopted as stored, the way `get_quant` / `Ops.qweight` adopt affine ones.
- `ChatProtocol` (serve/protocols.py): how conversations are written and read. The engine was ChatML inside; it is
  now written against this, with the Qwen formats as `ChatmlProtocol` and Inkling's as `Inkling2ChatProtocol`, picked
  from the tokenizer (serve/registry.py). The generate entrypoint uses it too. A protocol also says how its rendered
  prompt becomes ids (`encode`), and its reader is handed an answer's special tokens as themselves (`mark`) and
  gives the finished answer (`parsed`): what lets a protocol keep a message's text apart from its framing. ChatML's
  are the tokenizer's encoding and the text reading they always were.
- `Constraint` (constrain/grammar.py): what a generation loop is handed of a grammar. The two ChatML controllers
  were the only ones and were named in the loops' types; the acceptor under them took its call spelling from class
  constants, now a `JsonCallSpelling` a protocol supplies (and `Acceptor.initial(names)` holds a call to some of its
  functions).
- `StateLayout.buffers`: which of a layer's state arrays are capacity buffers, so a decoder whose layers keep small
  histories beside their KV still passes its buffers and captured steps on (core/slab.py).
- `Readout` (core/readouts.py): what a model hands a draft head of each position, as its "hidden" output. The final
  normed state alone for Qwen (whose captured steps are what they were); for a model whose draft head reads states
  inside the stack, the architecture supplies one that keeps them as the layers run (`BlockSumReadout`,
  core/inkling2/readouts.py) -- so a tap is a place in the execution order and nothing in the decode loop knows of it.
- `DraftHead` (core/draftheads.py): the draft model that came with a checkpoint, `Model.mtp`; which draft source
  drafts with one is a table by its type (spec/registry.py: the MTP head's, the DSpark drafter's), where the MTP
  source was named.
- `StateLayout.commit` picks by an index held on the device, and the static decoder commits a verify step in one
  captured call (`Decoder._settle_fn`): section 8 has what the host's picking cost a model with 272 small states.
- `StateLayout.room` / `make_room`, and `RunningKvSpan` beside `SlidingKvSpan`: a fixed-size state that steps
  write in place, and the decoder making room in it when it runs out (section 8, "State"); `Ops.assign`, and a
  decoder's state kept in the arrays its captured steps are bound to (core/slab.py).

**Seam operations added** (ops/base.py, each with a composed reference): `tanh`, `sqrt`, `minimum`, `maximum`;
`sdpa_sink`, `rel_bias`, `sdpa_static_rel` (attention with a relative term and a sink); `sdpa_partials`,
`sdpa_causal_partials`, `sdpa_span_partials`, `sdpa_merge` (one softmax over sets of keys scored in different
ways); `expert_dense`, `expert_linear_grouped` (a prefill's rows, expert by expert); `kv_range`, `kv_join`,
`kv_take`, `kv_move`, `select_at`, `assign`, `sdpa_window_rel_at`. And the model's small regular pieces, each one operation whose composed form is its
definition, so that a backend can make it one kernel (section 8; torch does, in backends/torch_fused.py):
`unit_rms`, `rms_norm_to`, `depth_mix` (a depth read), `bottleneck_blend` (a message gate), `short_conv`,
`short_conv_dynamic`, `l2_clip`, `sdpa_window_rel` (a local layer's attention over its window), `sigmoid_route`,
`capped_gate`, `weighted_rows` (the experts' small work).

**Where a family is chosen**, all tables: `ARCHITECTURES` by config type; `HF_SOURCES` by a checkpoint's `model_type`
and `GGUF_SOURCES` by a GGUF's `general.architecture` (load/families.py: every GGUF used to be the Qwen reader's to
take or refuse); `PRE_REGEX` by pre-tokenizer name; `CHAT_PROTOCOL_FAMILIES` by what the tokenizer has.

Two names still say Qwen where they mean the engine: the model class `Qwen35` and `load_qwen35`. Both are left alone
(they are imported widely, and by code outside this repository's view); renaming them is a mechanical change for
whoever wants it.


## 4. The model, as the code computes it

All norms are RMS norms with epsilon 1e-6, their weights used as stored (nothing is added to them). "unit RMS" below
is the norm with no weight. Shapes are for Mini; B = 1.

### 4.1 The residual stream (core/inkling2/depth.py, connections.py)

The stream is not one running sum. It is the sums of whole blocks of six layers, kept apart, and a sublayer reads its
input from them through a query of its own:

    sources   = [the finished blocks' sums ..., the sum of the block under way], each at unit RMS, float32
    weights_q = softmax over sources of (q . source / sqrt(hidden))          one learned q per input read
    input_q   = sum over sources of weights_q * source                       keys and values are the same vectors

The stream starts as the normed token embedding with no block finished. A block's first layer (0, 6, 12, 18) archives
the sum it was handed, after its attention has read it, and its attention's output begins the next block's sum (it is
not added to what was archived). Every other sublayer adds its output to the sum under way. At the end one last query
reads all five sums, and the final norm follows.

A local layer's attention reads one input (one query, one norm); a global layer's reads three -- for its queries, keys
and values -- each with its own query and its own norm. Layer 0's attention has no query: it takes the embedding. Every
feed-forward reads one input.

The sum under way is float32 from the attention's write to the layer's end, where it is rounded to the model's dtype.

### 4.2 The loop (core/inkling2/loop.py, messages.py)

Layers 6..17 run three times. Every pass starts from the stream as it stood after layer 5; a pass leaves nothing in
the stream for the next but its own two block sums, which the next pass's sublayers read as *messages*: each looped
layer has four learned message queries (for its attention's query, key and value inputs and its feed-forward's
input), read over those two sums as in 4.1, and each input x is blended with its message m by a gate of rank 64:

    u = [unit_rms(x) | unit_rms(m)];    z = W_down u
    x' = (1 - tanh(W_forget z)) x + tanh(W_gain z) m

before the input's norm. A local layer's three attention inputs are one read that only the messages tell apart, so its
query, key and value projections do not share an input and are not fused. After the third pass layers 18..23 run on
the stream as that pass left it.

In the engine the loop is the execution order: `[0..5, LoopEntry, 6..17, LoopRestart, 6..17, LoopRestart, 6..17,
18..23]`, fifty-one entries. The three appearances of a looped layer are three `SublayerBlock`s over the same
sublayer objects -- one set of weights -- each with its own slot of decode state; the markers hold no state and act on
the stream value, which carries the loop's entry state and the previous pass's sums beside the block sums. Nothing
about passes is kept on any object.

### 4.3 Attention (core/inkling2/attention.py, core/kvspans.py)

    q    = clip(scale_q * W_q x_q)            per head, by l2 norm: v * min(1, sqrt(512) / (|v| + 1e-6))
    k    = clip(conv_k(W_k x_k))              stored
    v    = unit_rms(conv_v(W_v x_v))          stored
    rel  = clip_8(scale_r * W_r x_q) @ P      per query head: a bias for each distance back, 0 .. extent - 1
    sink = W_s x_q                            per query head: one more logit in the softmax, with nothing behind it
    a    = softmax([q . k / sqrt(128) + rel[distance] | sink])
    y    = W_o (sigmoid(W_g x_q) * sum over keys of a v)

Query head h reads KV head h // 3. A local layer's query sees the 1,024 positions up to its own. A global layer's sees
every earlier position; past the extent (1,024) the relative term is zero, which is not a mask; and its queries and
relative features are scaled by 1 + 0.1 log(max((pos + 1) / 8192, 1)) after the clip. A local layer's relative table
spans its window; a global layer's, the config's extent (they are the same number in Mini and need not be). The sink's
share of a softmax is not handed back to the keys.

### 4.4 The convolutions (core/shortconv.py)

Causal, per channel, four taps, no activation, with a residual:

    static    y[t] = (x[t] + sum_a w[a] x[t - 3 + a]) / sqrt(5)                 taps oldest first
    dynamic   y[t] = (x[t] + sum_lag (w[lag] + d[t, lag]) x[t - lag]) / 3       d = W_d x: 8 heads x 4 taps

Keys and values pass through one before they are clipped or normed (static in a local layer; dynamic in a global one,
its taps predicted from the key or value input at the output's position and shared by a head's 128 channels); each
sublayer's output passes through a static one on its way to the stream. Float32. The decode state is the last three
raw inputs, per convolution: four of them per visit.

### 4.5 The mixture of experts (core/inkling2/moe.py)

    s = sigmoid(W_r x)                            float32
    picked = top 8 of s + bias                    the bias moves which experts are picked, never their weights
    w = 8 * s[picked] / sum(s[picked])
    expert(x) = W_down((4 tanh(g / 4)) * sigmoid(g) * (25 tanh(u / 25))),   [g | u] = W_gate_up x

The sigmoid reads the gate as it is, not its capped value. Outputs are summed in float32.

### 4.6 The head (core/heads.py)

`30 * tanh(logits / 30)` over the first 200,058 rows of the checkpoint's output table (it is padded to the
embedding's 201,024). The cap leaves the greedy token alone and changes the distribution a sampler draws from.

### 4.7 The draft model (core/dspark/, spec/dspark.py)

DSpark, `mtp.safetensors` beside the checkpoint: 318M parameters in bfloat16, a block drafter. It was written from a
prose specification (section 7 has where that came from and how far to trust it). Three pre-norm layers of width
2,304 -- grouped-query attention, 24 query heads over 8 key / value heads of 128, queries and keys RMS-normed per
head and rotated (rotary, base 1e6, the head's first half paired with its second); a SwiGLU of 9,216 with no caps
-- a final norm, and a recurrent head of rank 256. It has no embedding and no output projection: it borrows the
target's.

**It never reads the past's tokens.** What it knows of a position the target has run on is four of the target's
states there: the sum of the block under way as visits 5, 23 and 41 receive it -- each the last layer of its block,
so three block sums one layer short of complete -- and the final normed state. A model hands these out as its hidden
output through its `Readout` (section 3): [1, T, 4 x 2,304] where Qwen's is the final state alone. Each of the
drafter's four readers, its three layers and the head, has a convex mix of its own of the four (a row of
`fuse_weight`, softmaxed) and an RMS norm over it. A layer turns its mix of a position straight into that position's
key (projected, normed per head, rotated at the position) and value (projected): **no layer is run over the past**.
That memory -- 12 KB a position over the three layers -- is the drafter's whole state, with the head's view of the
last position.

**A block** is eight slots at consecutive positions: the newest token -- chosen by the target, not yet run on -- as
the target's own normed embedding of it, then one learned vector in each of the seven others. The three layers run
over the block once, every slot attending to the memory and to all eight slots, later ones included (no causal
mask). Layer 1 sees all of the memory; layers 0 and 2 the 1,024 positions before the block (the window is the
block's, not each slot's). The seven mask slots' outputs through the target's output projection are logits for the
next seven positions at once.

**The head** then walks the seven left to right, correcting each position's logits by what was drafted before it:
a state of 256, zero at the block's start, stepped on the last token's row of a table of its own, the slot's
output and the head's view of the last committed position, as a gated recurrence; its output, through a second
projection, is a correction *in hidden space*, added to the slot's output before the target's output projection and
softcap. Without the head the drafts are barely usable (0.9 of seven kept where 2.3 are with it): it is what makes
the second draft depend on the first. The loader hands the correction over folded (load/inkling2.py) -- `unembed
hidden_out`, a [vocabulary, 256] matrix -- so a draft is a pass over 256 columns of the vocabulary and not 2,304;
the recurrence's projection comes in two halves, of which the one over the slots' outputs runs for all seven at
once.

**A round.** The block's drafts, as one captured call (2.6 ms: the layers' 0.5 GB, the output table once for seven
rows, seven walks). Then the count: a row of the target's step costs whether it is kept or not, so the source hands
the target as many drafts as the head's own word on them is worth (below). The target verifies them in one step,
the loop keeps the accepted prefix exactly as for any draft source -- greedy by match, sampled by rejection, the
drafts drawn from the head's warped distribution -- and the step's rows are written into the memory, as one more
captured call; rows past the accepted ones are junk that the next round's write covers before any block sees that
far. Under `--lookup` the drafter is what a round falls back to, and remembers a lookup round's rows all the same.

**How many drafts.** The head's probability of a draft says how likely the target is to keep it, optimistically: of
the drafts it gave 0.9 the target kept 0.6, of those it gave 0.99 and more, 0.95. Calibrated (a two-parameter fit on
6,137 drafts of seven kinds of text), the chance that each draft is reached and kept is known before the target
runs, and a round submits the count that makes the most tokens for the target's time: 1 + the sum of those chances,
over 1 + 0.3 for the block + 0.18 a row, in one-token steps. On the same rounds that is 1.69 tokens for a step's
time, against 1.60 taking the head at its word, 1.29 always submitting seven, and 1.93 with hindsight.

What a prefix snapshot keeps of it is the memory (12 KB a token); a follow-up resumes with it, and a prefill
checkpoint is a prefix of it. Not done: the logit processors' contribution is not applied to the drafts (the walk is
one captured run; the target's rows get theirs regardless, so a draft a grammar forbids is simply not kept); and a
long prompt's hidden output is held whole while the memory is written (18 KB a token, section 8).


## 5. The checkpoint (load/inkling2.py, ops/microscaled.py)

Canonical names are the checkpoint's with `model.llm.` dropped, except where its layout is not the model's: the
residual queries are regrouped per layer (`attn_res.attn_queries.{i - 1}` is layer i's; layer 0 has none), the two
`middle_cycle_cross_pass_*` tables become each looped layer's four message queries in the order query, key, value,
mlp, static convolution weights lose their unit axis, the relative table is transposed, and the output table is cut to
the ids the model produces. The module docstring has the list.

Experts are stored stacked, 128 to a tensor: `w13_weight` [128, 2304, 2304], whose rows alternate gate and up
(reordered here to gate rows first, then up), and `w2_weight` [128, 2304, 1152]. Their formats:

    nvfp4   w = e2m1(code) * e4m3(scale) * amax[expert] / denominator     two 4-bit codes a byte, low nibble first;
                                                                          a scale byte per 16 inputs of a row
    mxfp8   w = e4m3(code) * 2 ** (scale - 127)                           a scale byte per 32 inputs of a row

`e2m1` is the 4-bit float (0, .5, 1, 1.5, 2, 3, 4, 6 and their negatives), `e4m3` the 8-bit one. The formats are told
apart by the tensors' dtypes (codes `U8` with `F8_E4M3` scales, or the reverse), not by the config, which names only
one. `MicroscaledWeight` holds the bytes as the file has them (memory-mapped); the torch backend puts them on the
device as they are and decodes what a step reads (section 8), and so do tinygrad and MLX, without its kernels
(section 9). The default, the decoded dense weights, is the reference's and is only practical for a small model.

The weights are those products, exactly. What is *not* reproduced is the activation quantization the release
metadata describes for native NVFP4 / MXFP8 inference: activations here are bf16 or float32, as in the reference
implementation, which decodes the experts on load. This is a decoded-weights model with packed storage, not native
microscaled arithmetic.

Not read: `model.visual.*` (422 tensors), `mtp.safetensors`.

**As a GGUF** (load/inkling2gguf.py; the file's metadata and tensors through the vendored reader, load/gguffiles.py).
llama.cpp's converter keeps the checkpoint's tensors under its own names and changes few of them, and the canonical
parameters are the same ones: the output table is cut as above, a lone query gets its unit axis back, a global
layer's static taps -- stored oldest first, as a plain convolution's are -- go back to being by lag; the experts'
rows are already gate first, the message queries already a layer's four, the relative table already transposed. The
config is the file's `inkling2_loop.*` keys put back under config.json's names and read by the one parser, its
floats the nearest float32. The tokenizer is the file's lists with `ignore_merges` set, which a GGUF has no field for
(llama.cpp tokenizes without it) and the checkpoint's tokenizer.json has.

GGML's NVFP4 is the lab's bytes regrouped: a row in super-blocks of 64 weights, four scale bytes and then, per 16
weights, eight bytes holding weights 0..7 in their low nibbles and 8..15 in their high; `amax / denominator` is a
float32 tensor beside the weight, `*.scale`. Regrouped back (load/ggufmicroscaled.py) they are the checkpoint's
`MicroscaledWeight`s to the byte, so the same kernels run on them. Nothing in a GGUF holds MXFP8: layers 20..23's
experts are bf16 in the lossless file -- the MXFP8 products exactly, a float of four significant bits fitting bf16's
eight -- and are held dense, as whatever a smaller file quantizes its tensors to is, read through the vendored
quantizers.


## 6. Tokenizer and chat protocol

**Tokenizer** (tokenizer.py). Byte-level BPE with its own split pattern (`PRE_REGEX['inkling2']`, which the source
requires tokenizer.json to match exactly) and `ignore_merges`: a pre-tokenized word that is a token as it stands is
that token. 200,058 ids, the logits' width.

**Protocol** (serve/inkling2.py). A conversation is a run of framed messages:

    <|message_ROLE|> [name] <|content_CHANNEL|> body <|end_message|>

There is no generation prompt: the model opens its own messages. A model turn is one or more messages -- reasoning on
`<|content_thinking|>`, the answer on `<|content_text|>`, a tool call as `{"name": ..., "args": {...}}` on
`<|content_invoke_tool_json|>` under the tool's name -- ended by `<|content_model_end_sampling|>`, which is where
generation stops. `<|end_message|>` ends a message, not the turn.

Rendering was established by running the checkpoint's chat template as a black box over conversations
(tests/inkling2oracle.py; its source was not read): tools first, in one system message, as compact key-sorted JSON;
the leading system messages; one system message stating the thinking effort as a number (`none` 0, `minimal` 0.1,
`low` 0.2, `medium` 0.7, `high` 0.9 and the default, `xhigh` / `max` 0.99, or a number in [0, 0.99]); then the turns;
a call's arguments with their top-level keys sorted. Departures, on purpose: an OpenAI client's JSON-text arguments
are parsed (the template refuses them), a tool result that is not text is written as JSON, `reasoning` is read as
`reasoning_content` is, and images are refused.

Reading is one incremental reader. A call's head is delivered as soon as its message's header has named it, before
any JSON, then its arguments as the text of the `args` value as it is written; a streamed answer's deltas concatenate
to the unstreamed one's fields, however the stream is cut.

**What a message says is not framing.** The markers are special tokens, and a tokenizer asked to encode a rendered
prompt takes any text that spells one for one: a tool result that quotes `<|end_message|>` ended its message there,
and a user could write a system message. Both directions are closed:

- *Into a prompt.* The renderer writes a message's text -- bodies, a header's name -- escaped: U+241B between the
  `<` and the `|` that every marker opens with (and a U+241B of the text's own doubled, so the text comes back
  whatever it was). Escaped text holds no marker, so in a rendered prompt a marker is a marker and nothing else is;
  `Inkling2ChatProtocol.encode` splits the prompt at its markers and encodes what lies between, unescaped, as plain
  text. Text with no `<|` in it is written as it is, so the rendering still matches the template's character for
  character wherever the template's is not ambiguous. The engine's own bookkeeping gains from it: an earlier
  answer's ids are spliced in where its rendered turn is found in a prompt, and escaped text cannot hold one.
- *Out of an answer.* The engine hands the reader each special token as itself and everything else as text, and the
  reader reads no marker out of text. A model that writes about its protocol -- `<`, `|`, `end`, `_`, `message`,
  `|`, `>` as the ordinary tokens they are -- is read as having written that.

On the released model: a user message carrying a forged `<|end_message|><|message_system|>...` is summarized as the
note it is ("that text is an injection"); a call asked to write a line of markers into a file carries it exactly,
streamed and not; and the conversation continued reuses 569 of its 583 prompt tokens. `protocol.parse(text)` remains
for a reading of text alone, which cannot tell and takes what spells a marker for one.

Thinking off (`enable_thinking: false`, `reasoning_effort: none`) is effort 0 in the prompt, which has no other
switch -- and, since the model still reasons a little at 0, a turn held to no reasoning message by the grammar.

**Grammar** (constrain/framed.py). The framing's markers are single tokens, so where a turn stands is read off the
ids, as the reader reads it off the markers, and the acceptor and token masks are the ones ChatML's controllers use:

- With tools, a model message's header is held to nothing or a declared tool's name, the call channel is offered
  only after a whole name, and the body is `{"name": that name, "args": JSON of its parameters}` and then the end
  of the message. A call that comes out names a real tool and carries arguments of the declared types.
- `tool_choice` `none` never offers the call channel. `required`: at most one message of reasoning, then a call, and
  no end of the turn before it is complete; after it the turn is the model's again. A named function: the same, and
  the turn ends with that call (a model that wanted another tool otherwise goes on calling the one it is allowed).
- `response_format` `json_object` / `json_schema`: at most one message of reasoning, then one text message that is
  one JSON value of the schema, then the end of the turn.
- Thinking off: the thinking channel is not offered, in any of the above. The prompt can only state an effort, and
  at effort 0 the released model still opens a reasoning message; this is what makes off mean off.
- No tools and no format: a message is opened on a channel, with no header, and the channel is not the call's. So
  every request runs under a controller. This one exists because the released model, refused its reasoning on a
  request with no tools, called `ipython` -- a tool nobody had declared -- and a client that sent no tools was
  handed a tool call.

Whitespace between JSON tokens is rationed to two tokens in a row. Without that, the released model, refused what
it wanted next (a code fence before the value; a closing brace where a required key is owed), took the whitespace
it was still offered until the length limit: both happened on the first live requests. Inside strings whitespace is
content and is not counted. ChatML's controllers are as they were.

A body may spell a marker: the acceptor's vocabulary has no special token in it, so what a constrained body
writes is ordinary tokens, and the reader takes them for text (above).


## 7. What was verified, against what

The reference is transformers at commit `046bdb8cc2cee29d233964bb77fe6fd37cfe4aa3`, used as a black box: installed
into a directory of its own, run, its outputs and state-dict names compared. Its source was not read (this
repository is BSD-3, and Apache-licensed code is not read into it). The math came from the handoff's prose
specification.

| What | Against | Result |
| --- | --- | --- |
| Logits, synthetic checkpoint written by the reference (24 layers, 48 visits, toy widths) | its forward | 7e-6 abs (numpy), 1.5e-5 (torch f32) |
| Logits, synthetic checkpoint in the released layout with NVFP4 + MXFP8 experts | its forward, after its own decode | 6e-5 relative |
| Greedy tokens through the functional decoder, the static one, and verifying drafts | its own `generate()` | equal |
| One-shot prefill vs any chunking vs token by token | each other and the reference | equal to 2e-4 relative |
| **Released checkpoint, float32, 86 teacher-forced positions x 200,058 logits** | its forward on CPU | **max abs 1e-4; KL 8e-12; top-1 100%** |
| Released checkpoint, bf16 | its float32 forward | KL 2.6e-3 to 4.5e-3 (two states of the code), top-1 96.5% |
| ... the reference's own bf16 run | its float32 forward | KL 7.1e-3, top-1 97.7% |
| Tokenizer, 91,580 tokens of code, prose and awkward Unicode | the `tokenizers` library | no mismatch |
| **The released GGUF (`UD-Q8_K_XL`), all 704 parameters** | the checkpoint's, source against source | **equal: 40 NVFP4 stacks byte for byte, layers 20..23's bf16 the MXFP8 decode exactly, the rest to the bit** |
| ... its tokenizer, 59,285 tokens of documents and source | the checkpoint's | the same vocabulary, the same ids |
| ... float32 on the CPU, 8 positions x 200,058 logits | the checkpoint, the same way | equal to the bit |
| Renderer, 44 conversation shapes and the refused efforts | the checkpoint's template | character for character |
| Packed-expert kernels, length-aware attention (a step's and a prefill's) | the composed references | within 2e-5 relative (compiled and interpreted) |
| A prefill's attention in parts, 5,000 tokens of the released checkpoint at float32 | the one-softmax form it replaced | 1.5e-3 abs on the logits, inside what two chunkings of either differ by |
| Released checkpoint, float32, 40 tokens after a 2,674-token prompt (past the relative extent) | static decode, functional decode, a prefill in 512s | the same tokens |
| A passphrase in one comment of 52,876 tokens of source (at the start; in the middle), and of 116,311 (at the start) | asked for at the end, bf16 | returned exactly, all three |
| A message's text escaped and unescaped, 2,000 random strings of markers and escapes; a conversation of forged messages encoded | the text; plain encoding of each message between its own three markers | exact; no special token but the framing's |

So at float32 this is the reference's model on the released weights, and at bf16 it is as far from the float32
answer as the reference's own bf16 is: the difference is rounding moving a routing choice, which a mixture of experts
amplifies, not an error. bf16 greedy output can part ways between configurations for the same reason (a step's shape
is part of its arithmetic), as README.md already says of the 27B.

And the GGUF is the checkpoint (load/tests/comparesources.py: section 10). Its config differs in three floats by
their rounding to float32 (`rms_eps`, `qk_clip`, `log_scale_alpha`), which a float32 computation does not see.
Through the generate entrypoint on the CPU it answers as the checkpoint does, token for token, framed by the
protocol its tokenizer was found to speak. On the 5090 at bf16 its first 160 greedy tokens are the checkpoint's as
well, though layers 20..23 take the dense path there beside the others' packed one (a synthetic file's mix of the
two is also run on CUDA with the kernels on, in the suite). What the comparison does not reach is any of the
smaller files.

In the suite (no reference library needed: its values for the tests' own synthetic checkpoints are kept beside them,
`arch/tests/inkling2reference.py`): `arch/tests/test_inkling2.py` (config forms, the execution order and weight
sharing, reference logits and generation, partial acceptance at every count, prefix resume and prefill checkpoints,
decoder slabs, the window state, fp8 KV, CUDA graphs, kernels and compiled steps, the injector, and the live
comparison where a transformers with the model is installed), `load/tests/test_inkling2gguf.py` (a synthetic
checkpoint converted as llama.cpp's converter lays one out: the two sources' configs, parameters, packed bytes,
token ids and logits equal; a file of quantized types; what is refused), `tests/test_inkling2chat.py`,
`tests/test_microscaled.py`, `tests/test_relattention.py`, and `tests/test_framed.py` (the grammar: what is offered
at each point of a turn, that whatever token sequence the controllers admit the reader reads as valid calls or a
valid value, and the engine holding a random model to them).

On the released model, through the server: forced, named, forbidden and free tool calls and both JSON modes
answered as asked; and `tests/agent_eval.py` -- seventeen file tasks through the agent loop, with `--lookup 6
--lookup-k 7` and reasoning effort low. Its twelve small file tasks passed on every run. Its five byte-exact copies
of files that are hard to quote passed four, then (on the final tree, whose bf16 arithmetic and so whose greedy
paths differ) two, at the tool's 1,500-token limit: **16 of 17, then 14 of 17**, about 55 calls and 244 s a run,
one tool error between them. Every miss was the same -- the model set out to count the file's bytes in its
reasoning and ran to the limit without writing it. With `--max-tokens 6000` the final tree copies four of the five
exactly (the fifth with a blank line dropped: the model's mistake, in a well-formed call). And a server as one
would run it for speed -- `--compile --lookup 6 --lookup-k 7 --prefill-chunk 8192 --step-prefill-max 48` -- with
that limit: **17 of 17, 61 calls, no tool errors, 233 s**, at 74 tokens/s end to end on a plain request. So the
calls carry file contents exactly; what the score measures at the default limit is how soon this model stops
deliberating.
Both ways a prefill reads the packed experts (section 8) match the reference at float32 on the released weights.

tinygrad is left out of the suite's backends (tests/test_parity.py says why, and how to run it). Run by hand on
2026-11-23 against the submodule's revision (9f120c450), on its CPU device, the tests here pass with it as the only
backend beside numpy: the reference's logits in every chunking of the prompt, its tokens through the functional
decoder, the static one and prompt-lookup drafts, partial acceptance at every count, a resume from a stored state
(not from a checkpoint inside a prefill: a prefill through the captured step keeps none yet), and the draft model's
rounds against the by-the-book evaluation. And the released checkpoint at float32 gives torch's tokens three ways:
through the forward as it is built, with torch's logits to 5e-5 over the whole vocabulary at each of three positions
(eight to eleven minutes for a five-token prompt, one and a half to three a token); through the static decoder, six
minutes to the first token and ten seconds a token; and with the draft model, eight tokens in six rounds. 60 GiB
of host memory at the peak. None of it has been run on a GPU.

MLX has not been run at all: it is not installable here. It takes every operation above composed, over primitives
it had, and keeps the experts packed (section 9). What stands in for a run: tests/test_composed.py holds every
backend that imports to the numpy reference on each composed operation, a commit's captured call among them; the
packed experts' decode names no MLX function, and is held to the reference decode with numpy's arrays in MLX's
place (tests/test_microscaled.py); and the tests here that take one backend take MLX too wherever it is installed.
Its first run on a Mac is the test of all of it.

**Qwen is as it was.** The 27B's two transcript baselines (tests/bench.py `--check`: `--spec 3` with a 32,768-token
prefill, and `--spec 5,9,15`) are identical on the final tree, and the suite's Qwen tests pass unchanged apart from
type narrowing. One change did move them on the way: the decode attention kernel's split-merge, rewritten to hand
back partials, rounded differently inside a compiled step -- the several-lengths transcripts parted near token 209
while the one-length ones still matched. The merge is back as it was, and the partials have their own.

**The draft model** has no reference to run here. Neither public implementation of it is in the reference library
(it is in two serving stacks, whose classes compute through their servers' paged KV pools and cannot be called
alone), and both are Apache-licensed. So a separate reader read those two and wrote a prose specification -- symbols
its own, each statement marked as read, read from the checkpoint's files, run, or inferred, with the two
implementations' disagreements listed (none architectural: the precision of the recurrence's projection, and of the
SwiGLU) -- and the code here was written from that document and the checkpoint, never from the sources. What holds
it:

- The synthetic checkpoint has a synthetic draft model beside it, and every round's drafts equal a plain evaluation
  of the specification written in the test (spec/tests/test_dspark.py: float64, a loop per slot, head and key, the
  correction unfolded and the recurrence's projection whole, from the checkpoint's tensors and a teacher-forced
  pass's states) -- on numpy and on torch, alone and as the fallback of prompt lookup, resumed from a stored state
  and from a prefill checkpoint, across a growth of the buffers. The tokens are the plain run's.
- On the released checkpoint the specification's author had measured, with a float32 scratch evaluation over this
  repository's own target, 2.3 of seven drafts kept on terse reasoning and 5.0 on a tutorial's prose and code past
  its 1,100th token, and how far each plausible mistake moves that (adjacent rotary pairs: 0.4 to 0.7 kept; the
  mix's rows given to the wrong readers: 1.3 and 3.5; taps a visit early or late: 1.7 to 1.9 and 3.7 to 4.5; no
  head: 0.9 and 1.4). The implementation keeps 2.6 on the same reasoning prompt and 2.6 to 3.5 on a tutorial, a
  module, a code review and JSON within their first 1,200 tokens -- and 1.5 on a chat answer, 0.8 on a story.
- Not verified: the drafts themselves against a reference drafter's (the specification says how one could be had
  from a running server, and that it was not run), any bfloat16 rounding detail of the reference (norms and the
  residual are float32 here, which is at least as exact), and positions that hold images.

fp8 KV is checked for self-consistency only on the synthetic model, whose random weights amplify fp8's 2% on the keys
and values past any use as a measure; the real checkpoint's number is in section 8.


## 8. State, memory and speed

**State.** Per visit: the attention's KV, and four convolution histories of three positions (two of 1,024 channels,
two of 2,304: 80 KB in all). A global visit's KV is capacity buffers written in place, as Qwen's attention layers'
are. A local visit's is its window, the last 1,023 positions' keys and values, a fixed-size state kept one of two
ways (core/kvspans.py; the architecture picks by whether the backend writes buffers in place):

- `SlidingKvSpan`, where it does not: a step never writes into the state it was given -- the window after a step is
  a new one, and a T-token verify hands back the window T positions longer, which a commit of n tokens cuts at the
  n-th.
- `RunningKvSpan`, on torch: the window runs in buffers with as many slots again of room, with a count of the slots
  in use. A step appends its positions after those and reads its window where it lies (`Ops.sdpa_window_rel_at`);
  a commit advances the count and moves nothing; and when the room is used up, once in 1,023 positions, the decoder
  has the window moved back to the front (`StateLayout.room`, `make_room`). The sliding window was moved whole
  twice a token and three times a verified round, for forty visits: 0.4 ms of a plain token and 1.3 of a drafted
  round.

Either way a rejected draft leaves nothing to undo, which is what makes speculative verification safe with a
bounded window: the sliding one was never written, and the running one's slots past a commit are junk the next
step writes over before any query reaches them, as in the global layers' buffers (a ring of exactly the window's
size, written in place, could lose a still-needed key to a rejected write: the room is what prevents that). In a
snapshot a window is exactly as long as the positions there are.

A captured step is bound to the arrays it was first run on, and takes its arguments by copying them into those.
That was harmless while every state a step wrote in place lived in capacity buffers, which the next decoder is
handed whole; the running windows are written in place and are not, so a decoder now keeps its whole state in the
arrays its steps are bound to -- they are handed on with the steps (core/slab.py), and a new decoder's state is
assigned into them (`Ops.assign`) -- where before it could hold a second copy that the commit then wrote back
over what the step had just written.

**Memory** (bf16): 17.6 GiB of weights; 32 KB per position of capacity for the global layers; 335 MiB for the forty
windows and their room (168 for sliding ones). A prefix snapshot is the windows and histories (~170 MiB) plus 32
KB per token.

**Decode** (the 5090, bf16, greedy; steps captured as CUDA graphs, not compiled unless it says so):

| | tokens/s | |
| --- | --- | --- |
| plain | 127 | 7.9 ms a token; first token 0.11 s; the same at capacity 4,096 and 131,072 |
| `--compile` | 132 | 7.6 ms a token; 259 s to compile, once |
| `--spec 7` | 123 - 239 | by the text: the table below |
| `--lookup 6 --lookup-k 15`, copying a file (the bench's) | 297 | 8.7 tokens a round |

**Where a step's time went.** As first built the step was bound by its launches, not by memory: 12,600 device
kernels a token, replayed as one CUDA graph, nine thousand of them elementwise and a microsecond or two each --
22 ms a token, 47 tokens/s (75 compiled). By the part of the model that launched them (the static step run as plain
operations under the profiler, 1,400 tokens of context):

| | kernels | device time |
| --- | --- | --- |
| attention: projections, clips, the relative term, scores | 5,200 | 9.6 ms |
| message gates (the looped layers') | 2,394 | 3.5 ms |
| experts' small work: router, top-k, softcaps, sums | 1,584 | 2.2 ms |
| short convolutions | 1,600 | 2.0 ms |
| depth reads | 1,399 | 2.1 ms |
| stream writes, the stream's ends, the head | 396 | 1.0 ms |
| the expert kernels themselves | 96 | 2.1 ms |

Each of those groups is small and regular, so each became one operation of the seam -- its composed form the
definition, and what its parity test holds a kernel to (tests/test_fused.py, compiled and under Triton's
interpreter) -- and on torch a Triton kernel (backends/torch_fused.py), one launch for the whole piece over every
row of a step: a message gate (`bottleneck_blend`: two kernels where there were seventeen operations), a depth
read (`depth_mix`), a short convolution with its history (`short_conv`, `short_conv_dynamic`), the l2 clips, a
local layer's attention over its window with the relative term and the sink (`sdpa_window_rel`; a global layer's
near keys go through the same kernel), the experts' router, softcaps and weighted sum, a norm handed over in the
model's dtype, and a plain weight's product with one row (`dense_gemv`: cuBLAS is bound by its launch for the
small ones). `TorchOps(fused=False)` runs the composed forms, for an A/B on one machine.

What was learned about such kernels on this card, by microbenchmark inside a captured graph, since none of it is
obvious: a launch of anything costs about a microsecond; one program doing all of a piece's work is slow (a gate's
600,000 multiply-adds in one block: 48 us, against 28 for the seventeen operations it replaced) and the same work
spread over many programs, a tile each, is fast (4.4 us); a 1-D elementwise piece wants tiles of 128 to 256 on one
warp, and a 4,096-wide tile on four warps is pathological (80 us); a product wants a row or two of the weight a
program over the whole input axis; and a sum along a tile's axis is work across a program's threads, to be done
once and not once a loop iteration (the expert kernel: a tenth to a quarter of its time).

The step now, the same way:

| | launches | device time |
| --- | --- | --- |
| plain weights' products (`dense_gemv`) | 400 | 2.3 ms |
| the expert kernels | 96 | 1.7 ms |
| the other fused pieces | 1,256 | 2.6 ms |
| what is left as plain operations: the output head (0.6 ms, the memory's bandwidth), the global layers' far keys, reshapes | 601 | 1.3 ms |

Eight milliseconds for what a token must read -- about 6.7 GB, experts and dense projections together, some four and
a half milliseconds of this card's memory bandwidth. The products are near it (2.6 GB in 2.3 ms). The experts are
not bound by it at all, which is the thing to know about them: the kernel is bound by its instructions a weight --
a 4-bit code looked up, scaled, multiplied, added -- and reads 1.7 GB in 1.7 ms. Three ways of doing less of that
were built and measured, on the experts cold in a captured graph, and none is in the tree: reading each expert once
for all the rows of a step that selected it (eight consecutive tokens select 30 different experts of 128, not 64;
sixteen select 44 -- but the time did not move, there being as many multiply-adds as before); a tensor-core product
of each decoded tile with its rows (3.5 times slower: laying a decoded tile out for the product costs more than the
product saves); and a table of every byte's contribution for each pair of inputs, one gather a byte (8 times
slower).

**A step of several rows** -- a speculative round's verify -- costs, in milliseconds by its rows:

| rows | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 12 | 16 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ms | 8.1 | 9.7 | 11.8 | 13.4 | 15.1 | 16.7 | 19.8 | 26.6 | 31.8 |

1.7 ms a row, nearly all of it the row's own experts; the dense products are the same bytes for any number of
rows, and the small pieces are a launch each whatever the rows. (It was 14.2 at two rows and 24.1 at eight: the
products of a few rows went to cuBLAS, whose time for most of this model's shapes is ten microseconds of launch --
`dense_rows` multiplies each row of a weight, loaded once, into every row of the step, up to eight of them.) And a
round's commit is one captured call: a verify step returns a state per token, of which the kept count's is picked
-- 272 small arrays for this model, the four convolution histories of every visit and the window of every local
one -- and picking them on the host and copying each into the next step's inputs was 4.5 ms of every round, a
fifth of it. The count goes in as an index on the device now (`StateLayout.commit`), and the picked states are
written where the captured steps already look.

The plain round had the same kind of cost in a smaller way, found only once the device's part was down to nine
milliseconds: a one-token step's commit asked each of the 48 visits' layouts to pick a state that was already
whole -- a millisecond of Python a token with the device waiting on it, 92 tokens/s where the step allowed 108.
(What the host does between a round's read and its next launch is the thing to profile on this model now: the
step is short enough for a millisecond to be an eighth of it.)

And the last fifth, 108 to 127 tokens/s, was more of the first thing: the local layers' windows kept where they
run ("State", above), the global layers' nearest keys read in place where they were gathered, a step's key writes
and stream writes and the attention's output gate each one launch for four or five, and the norm a row a program
(3.1 to 1.2 us: its tiles each summed the row for themselves).

**The draft model** (`--spec 7`; section 4.7). What it buys follows the text, because the drafter is right about
what comes next in some kinds and not in others. Tokens/s from the first token on, greedy, the same prompt with and
without it:

| the text | plain | `--spec 7` | | drafts submitted / kept a round |
| --- | --- | --- | --- | --- |
| terse reasoning, then a short function (414 tokens) | 129 | 203 | 1.57 | 3.7 / 2.5 |
| a tutorial with code (its first 1,200 tokens) | 129 | 199 | 1.54 | 3.1 / 2.3 |
| a module with tests (1,200) | 129 | 201 | 1.55 | 3.3 / 2.3 |
| a code review (1,200) | 129 | 239 | 1.85 | 4.0 / 3.2 |
| JSON records (1,200) | 129 | 192 | 1.49 | 3.2 / 2.2 |
| a chat answer (347) | 128 | 143 | 1.11 | 2.1 / 1.2 |
| a story (862) | 129 | 123 | 0.95 | 1.6 / 0.7 |

A block costs 2.5 ms whether its drafts are used or not, and each submitted row 1.6 to 1.7 ms whether it is kept
or not: measured whole, a drafted round is 1.67 plain rounds (of 7.7 ms) with one draft submitted and 0.19 more
for each further one. The count rule (section 4.7) is what keeps free prose near par; nothing tried keeps it above
without costing more elsewhere (resting the drafter after rounds that lost: a story at par, the rest lower).
Sampled (temperature 0.7, top-p 0.95) a draft is drawn from the head's distribution at the sampler's temperature
and accepted by rejection, which keeps the target's distribution; the same seven texts then read 1.53, 1.71,
1.56, 1.83, 1.41, 1.03 and 0.93 times the plain speed (126 tokens/s): fewer drafts survive a rejection than a
match, and a sampled round does more besides (the target's rows are each warped, and the rejection step works on
whole rows of the vocabulary). Behind 30,000 tokens of context a question about code reads 119 tokens/s plain and
230 with the drafter. The agent evaluation (section 10) through a
server with `--spec 7 --lookup 6 --lookup-k 7 --step-prefill-max 48` takes 108 s where one without the drafter
takes 173: 15 and 16 of its 17 tasks, the twelve file tasks every time and the five copies as they fall (one
copy fails either way, another only in this drafted run; earlier in the day both failed either way).

The drafter's weights are 0.9 GiB on the device with the folded head, its memory 12 KB a position of capacity (6
with `--kv-dtype fp8`, which it follows, at no visible cost in drafts kept), and a 32,768-token prompt peaks 3.7
GiB higher with it than without: its memory, and the prompt's hidden output held whole while that is written.

The global layers' attention is length-aware: on torch with Triton, `sdpa_static_rel` sends the keys at least 1,024
back -- which carry no relative term -- through the decode attention kernel Qwen uses, at a position 1,024 earlier,
takes its softmax partials rather than its output, and merges them with the gathered nearest 1,023 + T keys and the
sink. A step's cost does not follow the capacity: the same at 4,096 positions and at 131,072 (it was half).

**Prefill** (tokens/s by prompt length; seconds, peak memory; chunks of 4,096, the default):

| prompt | 2026-11-22 | now |
| --- | --- | --- |
| 12,288 | 1,545 | 3,410 (3.6 s, 19.7 GiB) |
| 32,768 | 1,574 (20.8 s, 20.8 GiB) | 3,300 (9.9 s, 20.4 GiB) |

Flat in the length, which it was not at first (924 tokens/s at 65,536): a prefill's global attention scored every
key for every query with a bias gathered for each pair, though the relative term reaches 1,024 back. Now the keys
past a query's extent go through the decode attention kernel as plain causal attention ending 1,024 positions
before it (`Ops.sdpa_causal_partials`: every row of the chunk at once, no scores kept), the keys within it are a
window to the query -- for a local layer they are all it sees -- and one softmax is made of the two and the sink.

Two things then doubled it. The window's keys are scored by the operation a decode step scores them with
(`Ops.sdpa_window_rel`, which now takes other sets of keys under its softmax): on torch the window kernel, 256
queries a launch each against the keys it can see, where the composed form built a bias of every (query, key)
pair's relative term and mask and took a dozen passes over a quarter-gigabyte of scores a tile -- 0.8 s of a
4,096-token chunk's 1.4. And a long chunk's experts are applied expert by expert (`Ops.expert_linear_grouped`),
each decoded to dense once for the rows routed to it: on torch the rows are sorted on the device, the experts
decoded 32 at a launch, and each multiplied into its rows where they lie; decoding and multiplying one at a time,
with its slices and its concatenation, was a second of every chunk whatever its size -- 12,288 experts a chunk,
bound by their launches. A chunk is now about 1.2 s, of which the experts are 0.45 and attention 0.45; larger
chunks no longer buy anything (`--prefill-chunk 8192`: 3,430).

A short prefill -- a tool's result, a follow-up -- goes a row at a time through the expert kernel instead, which
costs the row's experts and nothing fixed. The two cross near 310 tokens (19 rows an expert), and the backend
switches at 20:

| new tokens | 16 | 64 | 128 | 256 | 384 | 512 | 768 | 1,024 | 2,048 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seconds | 0.11 | 0.11 | 0.17 | 0.36 | 0.44 | 0.48 | 0.51 | 0.54 | 0.73 |

The 0.11 s under it all is the eager forward's own: some 2,900 operations launched one by one from Python, with
the device waiting on the host (it was 0.25 s at 12,600 operations, and 0.155 until the window's scoring went to
its kernel). The captured 16-token step, `--step-prefill-max`, is 31 ms for 16 tokens and the better path below
about 50.

**fp8 KV** (`--kv-dtype fp8`; 86 teacher-forced positions against the reference's float32 logits):

| compute, KV | KL mean | KL median | top-1 |
| --- | --- | --- | --- |
| f32, bf16 | 8e-12 | 6e-14 | 100% |
| f32, fp8 | 1.5e-2 | 5e-5 | 95.3% |
| bf16, bf16 | 2.6e-3 | 2e-5 | 96.5% |
| bf16, fp8 | 1.0e-2 | 4e-5 | 96.5% |

Typically invisible, and at the few positions where a routing choice turns on it, not: the mean is four times
bf16's own. It saves 16 KB a position on a model whose weights are 17.6 GiB -- 2 GiB at 131,072 positions -- so it is
off by default here and worth turning on only for the context it buys.

(That table is 2026-11-22's. bf16's own row moves with the path a token takes, since each rounds in its own
places and the mean is two or three positions where a routing choice turns: measured again on 2026-11-23, after
the step's pieces became kernels, the forward reads KL 6.4e-3 mean / 3.0e-5 median with the experts by the row
and 7.2e-4 / 9.5e-6 with them grouped, the static step 8.1e-3 / 3.3e-5 a token at a time and 9.4e-3 / 4.2e-5 in
steps of eight rows, and the composed operations 4.3e-3 / 3.3e-5 -- top-1 96.5 to 97.7% throughout. At float32
every one of them matches the reference to 6e-5 in the logits.)

**Prompt lookup.** The table's rows are a 150-line file rewritten with one rename (884 prompt tokens, 900
generated). A verify step is the same captured step at T tokens; the local layers' windows make a rejected draft
free (above). At bf16 the drafted run's tokens part from the plain run's somewhere, as any two step shapes' do; at
float32 on the released checkpoint they do not: 500 tokens, plain and both lookup settings, the same, across the
1,024-position window -- and the functional decoder's first 60 with them.

**Prefix snapshots.** A follow-up of 20 new tokens to a stored conversation takes 0.41 s to its 8th generated
token whether the conversation is 100 tokens or 8,000 (cold: 5.0 s at 8,000). A snapshot is the windows and
histories plus the global layers' positions in use: 24 MiB at 100 tokens, 227 MiB at 2,000, 414 MiB at 8,000.


## 9. What is left

Roughly in the order it would matter to an agent loop:

1. **Markers as text, for ChatML.** Closed for this protocol (section 6); Qwen's formats still encode a rendered
   prompt whole and read an answer as text, so `<|im_end|>` in a tool result ends a turn and `</tool_call>` in an
   argument ends a call. The seam is there now (`ChatProtocol.encode`, `ChatReader.mark`); taking it changes what
   Qwen is sent for such text, which is why it was not taken unasked.
2. **The rest of a prefill chunk** (section 8): 1.2 s for 4,096 tokens, the experts' matmuls and the window
   kernel's scoring a little under half a second each. The window kernel is a program a (query, head, tile of
   keys); a prefill's thousands of queries want one that multiplies blocks of queries into blocks of keys.
3. **The draft model's loose ends** (section 4.7). The logit processors' contribution is not applied to its drafts,
   so under a grammar that forces a token the first draft is wasted; its count rule's calibration and costs are
   constants measured on one card and seven texts; a long prompt's hidden output is held whole while the memory is
   written (the prefill could hand it over a chunk at a time); and its drafts have not been compared with a
   reference drafter's (section 7).
4. **The step's remaining launches and bytes** (section 8). A step is 7.9 ms against a memory floor near 4.5. What
   is left as plain operations is 600 launches and 1.3 ms, 0.6 of it the output head's pass over its table: the
   global layers' far keys, the values' norms, the reshapes around every projection. The experts are bound by
   instructions a weight,
   and three ways around that did not work (section 8); what has not been tried is a kernel written below
   Triton. The products of a few rows past eight still go to cuBLAS. And of a drafted round: sampled, it costs
   1.7 ms more than greedy (the target's rows warped one by one, the rejection step over whole rows of the
   vocabulary), which is what puts a sampled story at 0.93 of the plain speed and a chat answer at par.
5. **Expert kernels on MLX and tinygrad.** Both keep the experts packed now, as torch does, and decode what a matmul
   reads: tinygrad by arithmetic on the bytes' bits (on its CPU device, ten seconds a token of the released
   checkpoint, 0.11 s for one expert product's eight rows), MLX by a table lookup a byte, a token's rows' experts
   at a time (backends/mlx_microscaled.py; its quantized matmul does not read these formats). Neither has a kernel
   that multiplies a row by an expert's packed bytes, which is what a step costs on torch -- the kernels here are
   the shape of what is needed, in Metal for MLX -- and MLX's path has never run (section 7).
6. **Other sources.** The Hugging Face checkpoint and a GGUF in llama.cpp's layout are read (sections 2 and 5). Of
   the GGUF path, left: layers 20..23's experts are held dense, where re-encoding the lossless file's bf16 as MXFP8
   would be exact (their values are MXFP8's: section 7) and give back 3.7 GiB and the packed kernels; the NVFP4
   bytes are regrouped at every load, thirty seconds of one core, where a kernel reading GGML's grouping would take
   them as they lie; a file's Q8_0 tensors are dequantized, and with `--quant` quantized again, where they are int8
   already; and only the lossless file was compared with the checkpoint, on the CPU -- the smaller ones that keep
   the NVFP4 experts (`UD-IQ4_XS` and up) go through the same code on a synthetic file only, and those below hold
   their experts in types that come out dense, 49 GB of them. Not read at all, each a `TensorSource` to write:
   Unsloth's earlier GGUF layout (`inkling2`: other names for the loop's tensors and keys), the draft model's GGUFs
   (`dflash`: so no `--spec` from a GGUF), and the Ollama library entry. The first two are refused by name with
   what to take instead.
7. **Vision.** `model.visual.*` is a 23-layer tower and a projector into the embedding; image content is refused.
8. **The first token.** 0.11 s before any request's first token, a prefix hit or not: the eager forward's
   launches, on however few tokens. `--step-prefill-max` gets under it for a short follow-up; compiling
   the eager forward, or capturing a prefill step at a few fixed lengths, would for all of them.


## 10. Reproducing the checks

The reference library, apart from the repository's environment:

```bash
pip install --no-deps --target /tmp/oracle \
    "git+https://github.com/huggingface/transformers@046bdb8cc2cee29d233964bb77fe6fd37cfe4aa3"
PYTHONPATH=/tmp/oracle ./python -m pytest omllm/local/qwen/arch/tests/test_inkling2.py   # the live comparison runs
./python -m omllm.local.qwen.tests.inkling2oracle --model ~/hf/Inkling-2-Mini           # the chat template
```

A GGUF against the checkpoint it was made from (section 7's rows): every parameter, the tokenizers over the texts
given, and a float32 forward of each on the CPU over the texts' first tokens -- 32 GiB of host memory for the
GGUF's model, ten minutes in all on two threads -- with the exit status saying whether they are one model:

```bash
./python -m omllm.local.qwen.load.tests.comparesources --against ~/hf/Inkling-2-Mini \
    --model ~/hf/Inkling-2-Mini-GGUF/Inkling-2-Mini-UD-Q8_K_XL.gguf --logits 8 \
    --text README.md CODESTYLE.md omllm/local/qwen/{README.md,INKLING.md,tokenizer.py,load/inkling2.py}
```

The bench (tests/bench.py), which for this model takes its prompts through the chat protocol and adds a copy under
prompt-lookup drafts; `--check` compares greedy transcripts against a saved run:

```bash
./python -m omllm.local.qwen.tests.bench --model ~/hf/Inkling-2-Mini --backend torch --device cuda \
    --prompts protocol --spec 7 --lookup 6 --lookup-k 15 --capacity 65536 -n 512 --transcript 256 \
    --long 32768 --check ./.cache/qwen/bench-inkling2-mini.json      # (--save, to record one)
```

It read, on the 5090 on 2026-11-23: plain 130 tok/s; with the draft model 138 (its prompt is free prose, where the
drafter is near par: section 8); the copy 297 tok/s; a 32,768-token prefill 3,280 tok/s at a 24.0 GiB peak; a
follow-up's first token 0.14 s cold and 0.16 resumed (0.08 with `--step-prefill-max 48`, which the bench does not
set). (On 2026-11-22, before the step's pieces were kernels: 46.6, no draft model, 169, 1,611 at 22.2 GiB, 0.26
s.) The saved run was re-recorded that day with `--spec 7`: every transcript had moved, the step's arithmetic
having been regrouped into kernels on purpose (bfloat16 rounds where it is done), and it reproduces run to run.
The agent evaluation is `tests/agent_eval.py --url ... --reasoning-effort low --max-tokens 6000` against a server
started with `--spec 7 --lookup 6 --lookup-k 7 --step-prefill-max 48`.

The draft model's acceptance and its count rule were measured with scratch scripts that are not in the tree; what
they did is small enough to say: generate greedily with `spec=(7,)` and a source whose row cost is 0 (every draft
submitted), record each round's seven probabilities and the count the target kept, and score a rule offline as
tokens over cost on those rounds.

The released checkpoint against the reference at float32 needs ~110 GB of host memory for the reference (it decodes
every expert to float32) and runs on the CPU in a few minutes: load `Inkling2LoopForConditionalGeneration` with
`dtype=torch.float32`, run it over a token sequence, and compare with `model.forward` here at `dtype='f32'`.
