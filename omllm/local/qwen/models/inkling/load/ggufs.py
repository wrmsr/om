# ruff: noqa: N806
"""
Inkling 2 from a GGUF in llama.cpp's layout for it (`general.architecture = inkling2_loop`; INKLING.md): the canonical
parameters `Inkling2HFSource` reads from the lab's checkpoint (inkling2.py has the list), from the tensors llama.cpp's
converter writes of it. Most are the checkpoint's own under another name. Where the converter changed a layout, the
change is undone here or is already the one the canonical scheme makes:

    output.weight                       padded to the embedding's rows: cut to the ids the model produces
    *_res_query.weight                  a lone query is stored flat: [1, hidden]
    blk.{i}.attn_{k,v}_conv.weight      a dynamic convolution's static taps (a global layer's: the ones with a
                                        `*_conv_proj` beside them) are stored as a static one's, [C, K] oldest first:
                                        back to [K, C] by lag
    blk.{i}.attn_rel_bias.weight        already [extent, rel_dim]
    blk.{i}.ffn_gate_up_exps.weight     already the gate rows first, then the up rows
    blk.{i}.loop_msg_query.weight       already a looped layer's four rows: query, key, value, mlp

Experts stored as GGML NVFP4 are the checkpoint's own codes and block scales, regrouped (ggufmicroscaled.py), with
each expert's factor in a tensor beside the weight (`*.scale`): `get_microscaled` hands them over packed, bit for bit
what the checkpoint's source hands over. Everything else is dequantized by the vendored quantizers and held dense:
whatever a file quantizes its projections to, and the experts of the last layers, which the checkpoint stores as
MXFP8 and a GGUF has no type for (BF16 in the lossless file, where they are the same weights exactly; Q8_0 and
k-quants in smaller ones).

A GGUF of the model holds no draft model (llama.cpp's is a GGUF of its own, `dflash`, which is not read) and no
vision tower (`mmproj`). The checkpoint's draft model is taken from beside the GGUF when it is there -- its
`mtp.safetensors` and the config.json that describes it, in the GGUF's directory (inkling2draft.py) -- and served
under `mtp.` as the checkpoint's source serves it, its head folded with this file's output table.
"""
import typing as ta

from omcore import check
from omcore import lang

from ....load.gguffiles import GgufFile
from ....load.ggufmicroscaled import microscaled_from_ggml_nvfp4
from ....load.weights import TensorSource
from ....ops.microscaled import MicroscaledWeight
from ..core.config import Inkling2Config
from ..core.config import inkling2_config_from_gguf
from .checkpoints import INKLING2_HF_MODEL_TYPES
from .checkpoints import INKLING2_PRETOKENIZER
from .drafts import Inkling2DraftFile
from .drafts import inkling2_draft_config_beside


if ta.TYPE_CHECKING:
    import numpy as np

    from ....load.gguf import constants as gguf_constants
else:
    np = lang.proxy_import('numpy')
    gguf_constants = lang.proxy_import('....load.gguf.constants', __package__)


##


INKLING2_GGUF_ARCHITECTURE = 'inkling2_loop'


class Inkling2GgufSource(TensorSource):
    config: Inkling2Config

    def __init__(self, file: GgufFile | str) -> None:
        super().__init__()

        self._file = file = file if isinstance(file, GgufFile) else GgufFile(file)
        self.path = file.path

        if file.architecture != INKLING2_GGUF_ARCHITECTURE:
            raise ValueError(f'{file.path}: a GGUF of {file.architecture!r}, not {INKLING2_GGUF_ARCHITECTURE}')

        self.config = inkling2_config_from_gguf(file.akv, eos_id=file.kv('tokenizer.ggml.eos_token_id'))
        self.config.extra.update(format='gguf', file_type=file.kv('general.file_type'))

        self.tokenizer_spec = self._build_tokenizer_spec()

        self._draft: Inkling2DraftFile | None = None
        beside = inkling2_draft_config_beside(
            file.path,
            model_types=INKLING2_HF_MODEL_TYPES,
            hidden_size=self.config.hidden_size,
        )
        if beside is not None:
            draft, self.config.draft = beside
            self._draft = Inkling2DraftFile(
                draft,
                rank=self.config.draft.markov_rank,
                unembed=self._unembed if 'output.weight' in file.tensors else None,
            )

        self._recipes = self._build_recipes()

    def _unembed(self) -> np.ndarray:
        """The output table, [vocab, hidden] float32, as this file holds it."""

        return self.get('unembed.weight')

    def _build_tokenizer_spec(self) -> dict:
        spec = self._file.tokenizer_spec()
        if spec['pre'] != INKLING2_PRETOKENIZER:
            raise ValueError(f'{self.path}: a pre-tokenizer of {spec["pre"]!r}, not {INKLING2_PRETOKENIZER}')

        # A GGUF has no field for it, and llama.cpp tokenizes without it. The checkpoint's tokenizer.json sets it, and
        # one model's two sources must give the same ids.
        return {**spec, 'ignore_merges': True}

    # canonical name -> how it is read

    def _build_recipes(self) -> dict[str, tuple]:
        c = self.config
        have = self._file.tensors

        r: dict[str, tuple] = {}

        def add(canon: str, kind: str, raw: str, *args: ta.Any) -> None:
            if raw in have:
                r[canon] = (kind, raw, *args)

        add('embed.weight', 'plain', 'token_embd.weight')
        add('embed_norm.weight', 'plain', 'token_embd_norm.weight')
        add('norm.weight', 'plain', 'output_norm.weight')
        add('unembed.weight', 'rows', 'output.weight', c.vocab_size)
        add('output_query', 'query', 'output_res_query.weight')

        for i in range(c.num_layers):
            p = f'blk.{i}.'
            q = f'layers.{i}.'

            for n, g in (
                    ('wq_du', 'attn_q'),
                    ('wk_dv', 'attn_k'),
                    ('wv_dv', 'attn_v'),
                    ('wr_du', 'attn_rel'),
                    ('wo_ud', 'attn_output'),
                    ('attn_sink_proj', 'attn_sink_proj'),
                    ('gate_attn', 'attn_gate'),
                    ('rel_logits_proj', 'attn_rel_bias'),
            ):
                add(q + f'attn.{n}.weight', 'plain', p + f'{g}.weight')
            add(q + 'attn.q_l2_clip.scale', 'plain', p + 'attn_q_clip.weight')
            add(q + 'attn.rel_l2_clip.scale', 'plain', p + 'attn_rel_clip.weight')

            for n in ('k', 'v'):
                if p + f'attn_{n}_conv_proj.weight' in have:
                    add(q + f'attn.{n}_sconv.static_w', 'lags', p + f'attn_{n}_conv.weight')
                    add(q + f'attn.{n}_sconv.proj.weight', 'plain', p + f'attn_{n}_conv_proj.weight')
                else:
                    add(q + f'attn.{n}_sconv.weight', 'plain', p + f'attn_{n}_conv.weight')
            add(q + 'attn_sconv.weight', 'plain', p + 'attn_post_conv.weight')
            add(q + 'mlp_sconv.weight', 'plain', p + 'ffn_post_conv.weight')

            add(q + 'attn_norm.weight', 'plain', p + 'attn_norm.weight')
            for n in ('q', 'k', 'v'):
                add(q + f'{n}_input_norm.weight', 'plain', p + f'attn_{n}_inp_norm.weight')
            add(q + 'mlp_norm.weight', 'plain', p + 'ffn_norm.weight')

            add(q + 'attn_queries', 'query', p + 'attn_res_query.weight')
            add(q + 'mlp_query', 'query', p + 'ffn_res_query.weight')

            add(q + 'mlp.gate.weight', 'plain', p + 'ffn_gate_inp.weight')
            add(q + 'mlp.gate.bias', 'plain', p + 'exp_probs_b.bias')
            add(q + 'mlp.experts.gate_up', 'experts', p + 'ffn_gate_up_exps.weight')
            add(q + 'mlp.experts.down', 'experts', p + 'ffn_down_exps.weight')

            if c.loop_start <= i < c.loop_end:
                for n, g in (('attn', 'q'), ('k', 'k'), ('v', 'v'), ('mlp', 'ffn')):
                    for w in ('down', 'forget', 'gain'):
                        add(q + f'controllers.{n}.{w}_weight', 'plain', p + f'loop_{g}_ctrl_{w}.weight')
                add(q + 'message_queries', 'plain', p + 'loop_msg_query.weight')

        if self._draft is not None:
            for name in self._draft.names():
                r[name] = ('draft',)

        return r

    def names(self) -> list[str]:
        return list(self._recipes)

    def has(self, name: str) -> bool:
        return name in self._recipes

    # reading

    def _outer(self, raw: str, matrices: int) -> np.ndarray | None:
        """
        float32 [matrices]: the factors a GGUF keeps beside the weight `raw` (`<name>.scale`: one for each matrix of a
        stack, or one for all), which multiply what the weight's own bytes decode to. None for a weight without them.
        """

        scale = raw.removesuffix('.weight') + '.scale'
        if scale not in self._file.tensors:
            return None

        s = self._file.dense(scale).reshape(-1)
        if s.shape[0] not in (1, matrices):
            raise ValueError(f'{scale}: {s.shape[0]} factors for {matrices} matrices')
        return np.ascontiguousarray(np.broadcast_to(s, (matrices,)))

    def _dense(self, raw: str) -> np.ndarray:
        x = self._file.dense(raw)

        stack = x.ndim == 3
        outer = self._outer(raw, x.shape[0] if stack else 1)
        if outer is None:
            return x

        return x * (outer.reshape(-1, 1, 1) if stack else outer[0])

    def get_microscaled(self, name: str) -> MicroscaledWeight | None:
        recipe = self._recipes[name]
        if recipe[0] != 'experts':
            return None
        raw = recipe[1]

        t = self._file.tensors[raw]
        if t.tensor_type != gguf_constants.GGMLQuantizationType.NVFP4:
            return None

        E = int(t.data.shape[0])
        outer = self._outer(raw, E)
        return microscaled_from_ggml_nvfp4(t.data, outer if outer is not None else np.ones(E, dtype=np.float32))

    def get(self, name: str) -> np.ndarray:
        if self._recipes[name][0] == 'draft':
            return check.not_none(self._draft).get(name)

        kind, raw, *args = self._recipes[name]

        if kind == 'experts':
            # (as the checkpoint's source decodes them: the same float32 products in the same order)
            mw = self.get_microscaled(name)
            return mw.dequantize() if mw is not None else self._dense(raw)

        x = self._dense(raw)
        if kind == 'plain':
            return x
        if kind == 'rows':
            return np.ascontiguousarray(x[:args[0]])
        if kind == 'query':
            return x.reshape(-1, x.shape[-1])
        if kind == 'lags':
            return np.ascontiguousarray(x.T[::-1])
        raise ValueError(kind)
