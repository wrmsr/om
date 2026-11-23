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

What is here: the text decoder, exact; the released checkpoint loaded with its experts as stored; cached and static
decode, prompt-lookup drafting, prefix snapshots; the tokenizer; the chat protocol with reasoning and tool calls,
served over the OpenAI endpoint, tool calls and JSON mode held to a grammar. What is not: the vision tower, the
separate draft model (DSpark), and any source but the Hugging Face checkpoint (section 9).


## 2. Getting and running it

The checkpoint is the lab's own Hugging Face repository, pinned (19.5 GB; `mtp.safetensors`, the draft model, is not
read and need not be fetched):

```bash
hf download thinkingmachines/Inkling-2-Mini --revision b85c3cfa615fc413cc9af3379f491b963f3b586a \
    --exclude mtp.safetensors --local-dir ~/hf/Inkling-2-Mini
```

`--model` takes the directory, as for any Hugging Face checkpoint; the architecture, the tokenizer and the chat
protocol follow from what is in it.

```bash
python -m omllm.local.qwen.entrypoints.generate --model ~/hf/Inkling-2-Mini --think -n 256 \
    -p "Write a Python function that checks whether a number is prime."
python -m omllm.local.qwen.entrypoints.generate --model ~/hf/Inkling-2-Mini --lookup 6 --lookup-k 15 -p "..."
python -m omllm.local.qwen.entrypoints.serve --model ~/hf/Inkling-2-Mini --capacity 131072 --warmup --port 8000
```

On the 5090: 17.6 GiB of weights, loaded in 12 s (the checkpoint's bytes go to the device as they are: there is
nothing to quantize). Options that matter:

- `--prefill-chunk 8192`: a long prompt's chunk; 4,096 is the default, and this model's prefill is faster in larger
  ones (section 8).
- `--capacity N`: the global layers' KV buffers, 32 KB per position at bf16 (8 visits x 8 KV heads x 128 x K and V).
  The other forty visits keep a 1,023-position window each, 160 MiB in all, whatever the capacity. 131,072 positions
  peak at 22 GiB.
- `--compile`: torch.compile the steps. A decode step is some twelve thousand small operations, so this is where the
  speed is (section 8). The first run compiles for three and a half minutes a step shape -- twelve and a half for
  a server's three (plain, `--lookup`'s verify, `--step-prefill-max`'s); with `--cache-dir` and `--warmup` the
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
- `--step-prefill-max 48`: a follow-up of a few tokens to a stored conversation through the captured step (0.09 s
  for 16 tokens) rather than the eager forward, whose floor is 0.25 s whatever the length.
- `--spec` is refused: the model's draft head is a separate model that is not built. `--lookup` works.

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
| `StateLayout` | `SlidingKvStateLayout` (core/kvspans.py), `ShortConvStateLayout` (core/shortconv.py) |
| `TensorSource` | `Inkling2HFSource` (load/inkling2.py) |
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
  from the tokenizer (serve/registry.py). The generate entrypoint uses it too.
- `Constraint` (constrain/grammar.py): what a generation loop is handed of a grammar. The two ChatML controllers
  were the only ones and were named in the loops' types; the acceptor under them took its call spelling from class
  constants, now a `JsonCallSpelling` a protocol supplies (and `Acceptor.initial(names)` holds a call to some of its
  functions).
- `StateLayout.buffers`: which of a layer's state arrays are capacity buffers, so a decoder whose layers keep small
  histories beside their KV still passes its buffers and captured steps on (core/slab.py).

**Seam operations added** (ops/base.py, each with a composed reference): `tanh`, `sqrt`, `minimum`, `maximum`;
`sdpa_sink`, `rel_bias`, `sdpa_static_rel` (attention with a relative term and a sink); `sdpa_partials`,
`sdpa_causal_partials`, `sdpa_merge` (one softmax over sets of keys scored in different ways); `expert_dense`,
`expert_linear_grouped` (a prefill's rows, expert by expert); `kv_range`, `kv_join`.

**Where a family is chosen**, all tables: `ARCHITECTURES` by config type; `HF_SOURCES` by a checkpoint's `model_type`
(load/families.py); `PRE_REGEX` by pre-tokenizer name; `CHAT_PROTOCOL_FAMILIES` by what the tokenizer has.

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
device as they are and decodes what a step reads (section 8). Other backends take the default, the decoded dense
weights, which is the reference and is only practical for a small model.

The weights are those products, exactly. What is *not* reproduced is the activation quantization the release
metadata describes for native NVFP4 / MXFP8 inference: activations here are bf16 or float32, as in the reference
implementation, which decodes the experts on load. This is a decoded-weights model with packed storage, not native
microscaled arithmetic.

Not read: `model.visual.*` (422 tensors), `mtp.safetensors`.


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

What is not held: the reader works on decoded text, so a marker spelled out in ordinary tokens inside a body reads
as the marker (as `</tool_call>` does in ChatML). A model writing *about* this protocol through a tool call is the
case to remember.


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
| Renderer, 44 conversation shapes and the refused efforts | the checkpoint's template | character for character |
| Packed-expert kernels, length-aware attention (a step's and a prefill's) | the composed references | within 2e-5 relative (compiled and interpreted) |
| A prefill's attention in parts, 5,000 tokens of the released checkpoint at float32 | the one-softmax form it replaced | 1.5e-3 abs on the logits, inside what two chunkings of either differ by |
| Released checkpoint, float32, 40 tokens after a 2,674-token prompt (past the relative extent) | static decode, functional decode, a prefill in 512s | the same tokens |
| A passphrase in one comment of 52,876 tokens of source (at the start; in the middle), and of 116,311 (at the start) | asked for at the end, bf16 | returned exactly, all three |

So at float32 this is the reference's model on the released weights, and at bf16 it is as far from the float32
answer as the reference's own bf16 is: the difference is rounding moving a routing choice, which a mixture of experts
amplifies, not an error. bf16 greedy output can part ways between configurations for the same reason (a step's shape
is part of its arithmetic), as README.md already says of the 27B.

In the suite (no reference library needed: its values for the tests' own synthetic checkpoints are kept beside them,
`arch/tests/inkling2reference.py`): `arch/tests/test_inkling2.py` (config forms, the execution order and weight
sharing, reference logits and generation, partial acceptance at every count, prefix resume and prefill checkpoints,
decoder slabs, the window state, fp8 KV, CUDA graphs, kernels and compiled steps, the injector, and the live
comparison where a transformers with the model is installed), `tests/test_inkling2chat.py`,
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

Not run at all: MLX (not installable here) and tinygrad (disabled in the suite's backends, and its current release
does not construct this package's backend). Both gained a `tanh` and take every other new operation composed; the
model's parity on them is unverified.

**Qwen is as it was.** The 27B's two transcript baselines (tests/bench.py `--check`: `--spec 3` with a 32,768-token
prefill, and `--spec 5,9,15`) are identical on the final tree, and the suite's Qwen tests pass unchanged apart from
type narrowing. One change did move them on the way: the decode attention kernel's split-merge, rewritten to hand
back partials, rounded differently inside a compiled step -- the several-lengths transcripts parted near token 209
while the one-length ones still matched. The merge is back as it was, and the partials have their own.

fp8 KV is checked for self-consistency only on the synthetic model, whose random weights amplify fp8's 2% on the keys
and values past any use as a measure; the real checkpoint's number is in section 8.


## 8. State, memory and speed

**State.** Per visit: the attention's KV, and four convolution histories of three positions (two of 1,024 channels,
two of 2,304: 80 KB in all). A global visit's KV is capacity buffers written in place, as Qwen's attention layers'
are. A local visit's is its window: the last 1,023 positions' keys and values, a fixed-size state that a step never
writes into -- the window after a step is a new one, and a T-token verify hands back the window T positions longer,
which a commit of n tokens cuts at the n-th. A rejected draft therefore leaves nothing to undo, which is what makes
speculative verification safe with a bounded window (a ring written in place could lose a still-needed key to a
rejected write). In a snapshot a window is exactly as long as the positions there are.

**Memory** (bf16): 17.6 GiB of weights; 32 KB per position of capacity for the global layers; 168 MiB for the forty
windows. A prefix snapshot is the windows and histories (~170 MiB) plus 32 KB per token.

**Decode** (the 5090, bf16, greedy):

| | tokens/s | |
| --- | --- | --- |
| plain | 45 - 47 | first token 0.25 s; the same at capacity 4,096 and 131,072 |
| `--compile` | 74.8 | 13.4 ms a token; 212 s to compile, once |
| at a 32,768-token context | 43.2 | |
| `--lookup 6 --lookup-k 7`, rewriting a file | 81.9 | 2.07 tokens a round, 86% of drafts accepted |
| `--lookup 6 --lookup-k 15`, the same | 88.0 | 2.21 tokens a round, 71% accepted |
| `--lookup 6 --lookup-k 15`, copying a file (the bench's) | 167 | 8.7 tokens a round |

Without `--compile` the step is bound by its launches, not by memory: 12,500 device kernels a token (counted on
the one-token forward: nine thousand of them elementwise, seven hundred reductions), replayed as one CUDA graph.
The experts are the only large reads and they are fused: `torch_triton.mgemv_experts` reads the eight picked experts'
packed bytes -- 1.7 GB a token over the 48 visits -- and nothing is decoded to a dense weight. Before that kernel the
composed path (gather, decode, batched matmul) ran 15 tok/s.

The global layers' attention is length-aware: on torch with Triton, `sdpa_static_rel` sends the keys at least 1,024
back -- which carry no relative term -- through the decode attention kernel Qwen uses, at a position 1,024 earlier,
takes its softmax partials rather than its output, and merges them with the gathered nearest 1,023 + T keys and the
sink. A step's cost no longer follows the capacity: 45 tok/s at 4,096 positions and at 131,072 (25 before).

**Prefill** (tokens/s by prompt length and `--prefill-chunk`; seconds, peak memory):

| prompt | chunk 4,096 (the default) | chunk 8,192 | chunk 16,384 |
| --- | --- | --- | --- |
| 16,384 | 1,545 (10.6 s, 20.3 GiB) | 1,955 (8.4 s, 21.4 GiB) | 2,242 (7.3 s, 24.3 GiB) |
| 32,768 | 1,574 (20.8 s, 20.8 GiB) | 1,971 (16.6 s, 22.0 GiB) | 2,239 (14.6 s, 25.0 GiB) |
| 65,536 | 1,592 (41.2 s, 21.9 GiB) | 1,949 (33.6 s, 23.1 GiB) | 2,183 (30.0 s, 26.1 GiB) |

Flat in the length, which it was not at first (924 tokens/s at 65,536): a prefill's global attention scored every
key for every query with a bias gathered for each pair, though the relative term reaches 1,024 back. Now the keys
past a query's extent go through the decode attention kernel as plain causal attention ending 1,024 positions
before it (`Ops.sdpa_causal_partials`: every row of the chunk at once, no scores kept), the keys within it are
scored with the term a tile of queries at a time, and one softmax is made of the two and the sink
(`Ops.sdpa_merge`).

What is left of a chunk is its experts: a long chunk's are applied expert by expert (`Ops.expert_linear_grouped`),
each decoded to dense once for the rows routed to it, and a chunk of any size routes something to nearly all of
them -- about a second a chunk, whatever its size. So larger chunks are faster: `--prefill-chunk 8192` is a
quarter more throughput for a gigabyte.

A short prefill -- a tool's result, a follow-up -- goes a row at a time through the expert kernel instead, which
costs the row's expert and nothing fixed. The two cross near 860 tokens (54 rows an expert), and the backend
switches at 48 rows an expert:

| new tokens | 64 | 128 | 256 | 512 | 768 | 1,024 | 2,048 | 4,096 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seconds | 0.22 | 0.22 | 0.39 | 0.79 | 1.20 | 1.38 | 1.66 | 2.41 |

(The switch was first set at 8 rows an expert, by guess: 129 tokens then took 1.14 s where 128 took 0.24. The
captured 16-token step, `--step-prefill-max`, runs 350 tokens/s and is the better path only below about 60.)

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

1. **Markers as text.** The reader and the tokenizer both take marker text for the marker: a tool result or a file
   that contains `<|end_message|>` is encoded as the special token, and a model that spells one out is read as
   having ended its message. ChatML has the same hole with its own tags. The fix is at the token level on both
   sides: encode message bodies with special tokens off, and feed the reader ids, not text.
2. **The experts in a prefill.** A second of every chunk is decoding each expert to dense for its rows, and it is now
   most of a long prefill. A kernel that multiplies a group of rows by an expert's packed bytes -- the GEMV's inner
   loop over a block of rows -- would take the decode out; until then, larger chunks amortize it.
3. **The draft model** (DSpark, `mtp.safetensors`): three layers with rotary attention and a Markov head, conditioned
   on the target's stream at visits 5, 23, 41 and the final state. It would be a second `DraftSource` and an
   observer of those visits' outputs; the taps are already named by visit (`layers.{visit}.{sublayer}`).
4. **Fewer launches without compiling.** Nearly all of a step's 12,500 launches are the small elementwise work of
   the depth reads, message gates, norms and convolutions around the two kernels that read anything large. Fusing
   them by hand (they are small and regular) is what the compiler does for the 46 -> 75 tokens/s.
5. **Packed experts on MLX and tinygrad.** Both take the default, which decodes every expert at load: 49 GB dense.
   MLX's quantized matmul does not read these formats; the kernels here are the shape of what is needed.
6. **Other sources.** Only the Hugging Face checkpoint is read. The Ollama library entry and the community GGUFs are
   other layouts of the same tensors (and other quantizations of the experts), each a `TensorSource` to write.
7. **Vision.** `model.visual.*` is a 23-layer tower and a projector into the embedding; image content is refused.
8. **The first token.** 0.25 s before any request's first token, a prefix hit or not: the eager forward's twelve
   thousand launches, on however few tokens. `--step-prefill-max` gets under it for a short follow-up; compiling
   the eager forward, or capturing a prefill step at a few fixed lengths, would for all of them.


## 10. Reproducing the checks

The reference library, apart from the repository's environment:

```bash
pip install --no-deps --target /tmp/oracle \
    "git+https://github.com/huggingface/transformers@046bdb8cc2cee29d233964bb77fe6fd37cfe4aa3"
PYTHONPATH=/tmp/oracle ./python -m pytest omllm/local/qwen/arch/tests/test_inkling2.py   # the live comparison runs
./python -m omllm.local.qwen.tests.inkling2oracle --model ~/hf/Inkling-2-Mini           # the chat template
```

The bench (tests/bench.py), which for this model takes its prompts through the chat protocol, loads no draft head,
and adds a copy under prompt-lookup drafts; `--check` compares greedy transcripts against a saved run:

```bash
./python -m omllm.local.qwen.tests.bench --model ~/hf/Inkling-2-Mini --backend torch --device cuda \
    --prompts protocol --no-spec --lookup 6 --lookup-k 15 --capacity 65536 -n 512 --transcript 256 \
    --long 32768 --check ./.cache/qwen/bench-inkling2-mini.json      # (--save, to record one)
```

It read, on the 5090 on 2026-11-22: plain 46.6 tok/s; the copy 169 tok/s; a 32,768-token prefill 1,611 tok/s at a
22.2 GiB peak; a follow-up's first token 0.26 s. The agent evaluation is `tests/agent_eval.py --url ...
--reasoning-effort low` against a server started with `--lookup 6 --lookup-k 7`.

The released checkpoint against the reference at float32 needs ~110 GB of host memory for the reference (it decodes
every expert to float32) and runs on the CPU in a few minutes: load `Inkling2LoopForConditionalGeneration` with
`dtype=torch.float32`, run it over a token sequence, and compare with `model.forward` here at `dtype='f32'`.
