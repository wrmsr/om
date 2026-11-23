# ruff: noqa: N803 N806
"""
Inkling 2 checkpoints (HF `inkling2_loop`; INKLING.md): a Hugging Face checkpoint directory as the lab releases it --
config.json, tokenizer.json, safetensors with `model.llm.*` names -- read into the canonical parameters
`arch/inkling2.py` builds from. The canonical names are the checkpoint's own with the `model.llm.` prefix dropped,
and effective values, except where the checkpoint's layout is not the model's:

    unembed.weight                              [vocab, hidden]: the rows of ids the model produces (the checkpoint
                                                pads the table to the embedding's size)
    output_query                                [1, hidden]       attn_res.output_query
    layers.{i}.attn_queries                     [1 | 3, hidden]   attn_res.attn_queries.{i - 1}: none for layer 0
    layers.{i}.mlp_query                        [1, hidden]       attn_res.mlp_queries.{i}
    layers.{i}.message_queries                  [4, hidden]: query, key, value, mlp -- a looped layer's rows of the
                                                two middle_cycle_cross_pass_* tables (two rows a layer each: query
                                                and mlp in the one, key and value in the other)
    layers.{i}.attn.rel_logits_proj.weight      [extent, rel_dim]: the checkpoint's `.proj`, transposed
    layers.{i}.*sconv.weight                    [C, K]: a static convolution's taps, the unit axis dropped
    layers.{i}.attn.{k,v}_sconv.static_w        [K, C]: a dynamic convolution's static taps, by lag
    layers.{i}.attn.{k,v}_sconv.proj.weight     [heads * K, hidden]: its `weight_proj`
    layers.{i}.mlp.experts.gate_up              [E, 2 I, hidden]: `w13_weight` with the gate rows first, then the up
                                                rows (the checkpoint alternates them)
    layers.{i}.mlp.experts.down                 [E, hidden, I]: `w2_weight`

Norm weights are used as stored (nothing is added to them). `model.visual.*` (the vision tower) is not read.

The draft model (core/dspark/) is a file of its own beside the model's, `mtp.safetensors`, and its canonical names
are that file's under `mtp.`, except:

    mtp.tap_mix                                 [readers, taps] float32: `fuse_weight` softmaxed over the taps (and
                                                rounded as bfloat16 holds it, which is how the reference uses it)
    mtp.markov_head.state_proj.weight           [3 R, 2 R]: `rnn_proj`'s columns for the state and the last token
    mtp.markov_head.input_proj.weight           [3 R, 2 H]: its columns for the block's output and the head's view
    mtp.markov_head.out.weight                  [vocab, R]: unembed hidden_out -- the head's correction is made in
    mtp.markov_head.out.bias                    [vocab]     hidden space and goes through the target's output
                                                projection; folded, a draft costs a pass over R columns, not H

The experts are stored in microscaled float formats (ops/microscaled.py) -- NVFP4 in most layers, MXFP8 in the last
few, told apart by the tensors' dtypes -- with their scales beside them (`*_weight_scale`, and for NVFP4 a per-expert
`*_weight_amax` over one `*_weight_outer_scale_denominator`). `get_microscaled` hands them over as they are; `get`
decodes them, as it reads a checkpoint that stores them dense (the reference library writes those).
"""
import json
import os.path
import typing as ta

from omcore import check
from omcore import lang

from ..core.inkling2.config import Inkling2Config
from ..core.inkling2.config import inkling2_config_from_hf
from ..ops.microscaled import MicroscaledWeight
from ..tokenizer import PRE_REGEX
from .weights import SafetensorsFile
from .weights import TensorSource


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


INKLING2_PRETOKENIZER = 'inkling2'


class Inkling2HFSource(TensorSource):
    config: Inkling2Config

    _PREFIX: ta.ClassVar[str] = 'model.llm.'

    _DRAFT_FILE: ta.ClassVar[str] = 'mtp.safetensors'
    _DRAFT_PREFIX: ta.ClassVar[str] = 'mtp.'

    def __init__(self, path: str) -> None:
        super().__init__()

        self.path = path = os.path.expanduser(str(path))

        with open(os.path.join(path, 'config.json')) as f:
            self.hf_config = json.load(f)
        self.config = inkling2_config_from_hf(self.hf_config)
        self.config.extra['format'] = 'hf'

        self.tokenizer_spec = self._build_tokenizer_spec()

        self._files: dict[str, SafetensorsFile] = {}  # raw tensor name -> its file
        for fn in sorted(self._shards()):
            st = SafetensorsFile(os.path.join(path, fn))  # type: ignore[arg-type]
            for raw in st.names():
                self._files[raw] = st
        if not self._files:
            raise FileNotFoundError(f'{path}: no *.safetensors')

        self._draft: SafetensorsFile | None = None
        draft = os.path.join(path, self._DRAFT_FILE)
        if self.config.draft is not None and os.path.exists(draft):
            self._draft = SafetensorsFile(draft)  # type: ignore[arg-type]

        self._recipes = self._build_recipes()

    def _shards(self) -> list[str]:
        index = os.path.join(self.path, 'model.safetensors.index.json')
        if os.path.exists(index):
            with open(index) as f:
                return sorted(set(json.load(f)['weight_map'].values()))
        # (every shard of the model, and not the draft model's file beside them)
        return [fn for fn in os.listdir(self.path) if fn.endswith('.safetensors') and fn.startswith('model')]

    def _build_tokenizer_spec(self) -> dict:
        def load(fn: str) -> ta.Any:
            fp = os.path.join(self.path, fn)
            if not os.path.exists(fp):
                return None
            with open(fp) as f:
                return json.load(f)

        tj = load('tokenizer.json')
        if tj is not None:
            self._check_pretokenizer(tj)

        template: str | None = None
        tp = os.path.join(self.path, 'chat_template.jinja')
        if os.path.exists(tp):
            with open(tp) as f:
                template = f.read()

        return {
            'kind': 'hf',
            'tokenizer_json': tj,
            'tokenizer_config': load('tokenizer_config.json'),
            'eos_id': self.config.eos_id,
            'pre': INKLING2_PRETOKENIZER,
            'chat_template': template,
        }

    @staticmethod
    def _check_pretokenizer(tj: ta.Mapping[str, ta.Any]) -> None:
        """The split pattern must be the one this code tokenizes with: a tokenizer.json with another is refused."""

        pats = [
            p.get('pattern', {}).get('Regex')
            for p in ((tj.get('pre_tokenizer') or {}).get('pretokenizers') or [])
        ]
        pats = [p for p in pats if p]
        if pats and pats != [PRE_REGEX[INKLING2_PRETOKENIZER]]:
            raise ValueError('tokenizer.json has a pre-tokenizer pattern other than the inkling2 one')

    # canonical name -> how it is read

    def _build_recipes(self) -> dict[str, tuple]:
        c = self.config
        P = self._PREFIX
        have = self._files

        r: dict[str, tuple] = {}

        def add(canon: str, kind: str, raw: str, *args: ta.Any) -> None:
            if P + raw in have:
                r[canon] = (kind, P + raw, *args)

        add('embed.weight', 'plain', 'embed.weight')
        add('embed_norm.weight', 'plain', 'embed_norm.weight')
        add('norm.weight', 'plain', 'norm.weight')
        add('unembed.weight', 'rows', 'unembed.weight', c.vocab_size)
        add('output_query', 'query', 'attn_res.output_query')

        for i in range(c.num_layers):
            q = f'layers.{i}.'

            for n in ('wq_du', 'wk_dv', 'wv_dv', 'wr_du', 'wo_ud', 'attn_sink_proj', 'gate_attn'):
                add(q + f'attn.{n}.weight', 'plain', q + f'attn.{n}.weight')
            add(q + 'attn.q_l2_clip.scale', 'plain', q + 'attn.q_l2_clip.scale')
            add(q + 'attn.rel_l2_clip.scale', 'plain', q + 'attn.rel_l2_clip.scale')
            add(q + 'attn.rel_logits_proj.weight', 'transpose', q + 'attn.rel_logits_proj.proj')

            for n in ('k_sconv', 'v_sconv'):
                add(q + f'attn.{n}.weight', 'conv', q + f'attn.{n}.weight')
                add(q + f'attn.{n}.static_w', 'plain', q + f'attn.{n}.static_w')
                add(q + f'attn.{n}.proj.weight', 'plain', q + f'attn.{n}.weight_proj')
            add(q + 'attn_sconv.weight', 'conv', q + 'attn_sconv.weight')
            add(q + 'mlp_sconv.weight', 'conv', q + 'mlp_sconv.weight')

            for n in ('attn_norm', 'q_input_norm', 'k_input_norm', 'v_input_norm', 'mlp_norm'):
                add(q + f'{n}.weight', 'plain', q + f'{n}.weight')

            if i:
                add(q + 'attn_queries', 'query', f'attn_res.attn_queries.{i - 1}')
            add(q + 'mlp_query', 'query', f'attn_res.mlp_queries.{i}')

            add(q + 'mlp.gate.weight', 'plain', q + 'mlp.gate.weight')
            add(q + 'mlp.gate.bias', 'plain', q + 'mlp.gate.bias')
            add(q + 'mlp.experts.gate_up', 'experts', q + 'mlp.experts.w13_weight', True)
            add(q + 'mlp.experts.down', 'experts', q + 'mlp.experts.w2_weight', False)

            if c.loop_start <= i < c.loop_end:
                for n in ('attn', 'k', 'v', 'mlp'):
                    for w in ('down_weight', 'forget_weight', 'gain_weight'):
                        add(q + f'controllers.{n}.{w}', 'plain', q + f'controllers.{n}.{w}')
                if P + 'middle_cycle_cross_pass_queries' in have and P + 'middle_cycle_cross_pass_kv_queries' in have:
                    r[q + 'message_queries'] = ('messages', i - c.loop_start)

        if self._draft is not None and c.draft is not None:
            r.update(self._build_draft_recipes(self._draft, c.draft.markov_rank))

        return r

    def _build_draft_recipes(self, st: SafetensorsFile, rank: int) -> dict[str, tuple]:
        D = self._DRAFT_PREFIX
        r: dict[str, tuple] = {}

        derived: dict[str, dict[str, tuple]] = {
            'fuse_weight': {'tap_mix': ('draft_softmax',)},
            'markov_head.rnn_proj.weight': {
                'markov_head.state_proj.weight': ('draft_columns', 0, 2 * rank),
                'markov_head.input_proj.weight': ('draft_columns', 2 * rank, None),
            },
            'markov_head.hidden_out.weight': {'markov_head.out.weight': ('draft_unembedded',)},
            'markov_head.hidden_out.bias': {'markov_head.out.bias': ('draft_unembedded',)},
        }

        for raw in st.names():
            if raw not in derived:
                r[D + raw] = ('draft', raw)
                continue
            for canon, (kind, *args) in derived[raw].items():
                if kind != 'draft_unembedded' or self._PREFIX + 'unembed.weight' in self._files:
                    r[D + canon] = (kind, raw, *args)

        return r

    def names(self) -> list[str]:
        return list(self._recipes)

    def has(self, name: str) -> bool:
        return name in self._recipes

    # reading

    def _f32(self, raw: str) -> np.ndarray:
        return np.ascontiguousarray(self._files[raw].get(raw), dtype=np.float32)

    def _gate_first(self) -> np.ndarray:
        """The row order that puts an expert's gate rows (the checkpoint's even ones) before its up rows."""

        n = 2 * self.config.moe_intermediate_size
        return np.concatenate([np.arange(0, n, 2), np.arange(1, n, 2)])

    def _expert_format(self, raw: str) -> str | None:
        """'nvfp4' / 'mxfp8' for an expert tensor stored so (by its and its scales' dtypes), None for a dense one."""

        st = self._files[raw]
        dt = st.dtype(raw)
        scale = raw + '_scale'
        if scale not in self._files:
            if dt in ('U8', 'F8_E4M3'):
                raise ValueError(f'{raw}: stored as {dt} with no scales beside it')
            return None

        dts = (dt, self._files[scale].dtype(scale))
        if dts == ('U8', 'F8_E4M3'):
            return 'nvfp4'
        if dts == ('F8_E4M3', 'U8'):
            return 'mxfp8'
        raise ValueError(f'{raw}: unsupported expert storage {dts}')

    def get_microscaled(self, name: str) -> MicroscaledWeight | None:
        recipe = self._recipes[name]
        if recipe[0] != 'experts':
            return None
        _, raw, gate_up = recipe

        fmt = self._expert_format(raw)
        if fmt is None:
            return None

        st = self._files[raw]
        codes = st.raw(raw)
        scales = self._files[raw + '_scale'].raw(raw + '_scale')
        E, N = int(codes.shape[0]), int(codes.shape[1])

        outer: np.ndarray | None = None
        if fmt == 'nvfp4':
            amax = self._f32(raw + '_amax')
            denom = self._f32(raw + '_outer_scale_denominator')
            outer = (amax / denom.reshape(-1)[0]).astype(np.float32)
            K = int(codes.shape[2]) * 2
        else:
            K = int(codes.shape[2])

        mw = MicroscaledWeight(fmt, codes, scales, outer, (E, N, K))
        return mw.rows(self._gate_first()) if gate_up else mw

    def get(self, name: str) -> np.ndarray:
        recipe = self._recipes[name]
        kind = recipe[0]

        if kind == 'messages':
            c = self.config
            n = c.loop_end - c.loop_start
            layer = recipe[1]
            P = self._PREFIX
            qm = self._f32(P + 'middle_cycle_cross_pass_queries').reshape(n, 2, -1)
            kv = self._f32(P + 'middle_cycle_cross_pass_kv_queries').reshape(n, 2, -1)
            return np.stack([qm[layer, 0], kv[layer, 0], kv[layer, 1], qm[layer, 1]], 0)

        raw = recipe[1]

        if kind.startswith('draft'):
            return self._get_draft(kind, raw, *recipe[2:])

        if kind == 'experts':
            mw = self.get_microscaled(name)
            if mw is not None:
                return mw.dequantize()
            x = self._f32(raw)
            return np.ascontiguousarray(x[:, self._gate_first()]) if recipe[2] else x

        x = self._f32(raw)
        if kind == 'plain':
            return x
        if kind == 'rows':
            return np.ascontiguousarray(x[:recipe[2]])
        if kind == 'query':
            return x.reshape(-1, x.shape[-1])
        if kind == 'transpose':
            return np.ascontiguousarray(x.T)
        if kind == 'conv':
            check.state(x.ndim == 3 and x.shape[1] == 1, f'{raw}: {x.shape}')
            return np.ascontiguousarray(x[:, 0, :])
        raise ValueError(kind)

    def _get_draft(self, kind: str, raw: str, *args: ta.Any) -> np.ndarray:
        x = np.ascontiguousarray(check.not_none(self._draft).get(raw), dtype=np.float32)
        if kind == 'draft':
            return x

        if kind == 'draft_softmax':
            e = np.exp(x - x.max(-1, keepdims=True))
            return _inkling2_as_bf16(e / e.sum(-1, keepdims=True))

        if kind == 'draft_columns':
            return np.ascontiguousarray(x[:, args[0]:args[1]])

        if kind == 'draft_unembedded':
            # (the reference folds in float64 and holds the result as bfloat16; float32 here, held as the model's
            # dense weights are)
            u = self._f32(self._PREFIX + 'unembed.weight')[:self.config.vocab_size]
            return np.ascontiguousarray(u @ x)

        raise ValueError(kind)


def _inkling2_as_bf16(x: np.ndarray) -> np.ndarray:
    """float32 values rounded to the nearest bfloat16 (ties to even), as float32."""

    u = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    u = (u + np.uint32(0x7fff) + ((u >> np.uint32(16)) & np.uint32(1))) & np.uint32(0xffff0000)
    return u.view(np.float32)
