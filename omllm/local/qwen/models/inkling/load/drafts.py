# ruff: noqa: N806
"""
Inkling 2's draft model as the lab releases it (models/inkling/core/dspark/; INKLING.md 4.7): a file of its own beside a
checkpoint's shards, `mtp.safetensors`, which the checkpoint's config.json describes (`mtp_config`). `Inkling2DraftFile`
reads it into the drafter's canonical parameters, whose names are the file's under `mtp.`, except:

    mtp.tap_mix                                 [readers, taps] float32: `fuse_weight` softmaxed over the taps (and
                                                rounded as bfloat16 holds it, which is how the reference uses it)
    mtp.markov_head.state_proj.weight           [3 R, 2 R]: `rnn_proj`'s columns for the state and the last token
    mtp.markov_head.input_proj.weight           [3 R, 2 H]: its columns for the block's output and the head's view
    mtp.markov_head.out.weight                  [vocab, R]: unembed hidden_out -- the head's correction is made in
    mtp.markov_head.out.bias                    [vocab]     hidden space and goes through the target's output
                                                projection; folded, a draft costs a pass over R columns, not H

The file is no one source's. The checkpoint's source reads it from the checkpoint's directory; a GGUF of the model
holds no draft model, and its source reads the same two files -- config.json and mtp.safetensors, as the checkpoint
has them -- from beside the GGUF (`inkling2_draft_config_beside`). Either hands this the model's own output table for
the folded head, so a GGUF that stores that table with loss folds what it runs.
"""
import json
import os.path
import typing as ta

from omcore import check
from omcore import lang

from ....load.weights import SafetensorsFile
from ..core.dspark.config import DsparkConfig
from ..core.dspark.config import dspark_config_from_hf


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class Inkling2DraftFile:
    FILE: ta.ClassVar[str] = 'mtp.safetensors'
    PREFIX: ta.ClassVar[str] = 'mtp.'

    def __init__(
            self,
            path: str,
            *,
            rank: int,
            unembed: ta.Callable[[], np.ndarray] | None = None,
    ) -> None:
        """
        `path`: the file; `rank`: the Markov head's (the config's `markov_rank`); `unembed`: reads the model's output
        table, [vocab, hidden] float32, for the head's folded output -- None where the model's source has no such
        table, and the folded names are then not among this file's.
        """

        super().__init__()

        self.path = path

        self._file = SafetensorsFile(path)  # type: ignore[arg-type]
        self._unembed = unembed

        self._recipes = self._build_recipes(rank)

    def _build_recipes(self, rank: int) -> dict[str, tuple]:
        D = self.PREFIX
        r: dict[str, tuple] = {}

        derived: dict[str, dict[str, tuple]] = {
            'fuse_weight': {'tap_mix': ('softmax',)},
            'markov_head.rnn_proj.weight': {
                'markov_head.state_proj.weight': ('columns', 0, 2 * rank),
                'markov_head.input_proj.weight': ('columns', 2 * rank, None),
            },
            'markov_head.hidden_out.weight': {'markov_head.out.weight': ('unembedded',)},
            'markov_head.hidden_out.bias': {'markov_head.out.bias': ('unembedded',)},
        }

        for raw in self._file.names():
            if raw not in derived:
                r[D + raw] = ('plain', raw)
                continue
            for canon, (kind, *args) in derived[raw].items():
                if kind != 'unembedded' or self._unembed is not None:
                    r[D + canon] = (kind, raw, *args)

        return r

    def names(self) -> list[str]:
        return list(self._recipes)

    def has(self, name: str) -> bool:
        return name in self._recipes

    def get(self, name: str) -> np.ndarray:
        kind, raw, *args = self._recipes[name]

        x = np.ascontiguousarray(self._file.get(raw), dtype=np.float32)
        if kind == 'plain':
            return x

        if kind == 'softmax':
            e = np.exp(x - x.max(-1, keepdims=True))
            return _inkling2_draft_as_bf16(e / e.sum(-1, keepdims=True))

        if kind == 'columns':
            return np.ascontiguousarray(x[:, args[0]:args[1]])

        if kind == 'unembedded':
            # (the reference folds in float64 and holds the result as bfloat16; float32 here, held as the model's
            # dense weights are)
            return np.ascontiguousarray(check.not_none(self._unembed)() @ x)

        raise ValueError(kind)


def _inkling2_draft_as_bf16(x: np.ndarray) -> np.ndarray:
    """float32 values rounded to the nearest bfloat16 (ties to even), as float32."""

    u = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    u = (u + np.uint32(0x7fff) + ((u >> np.uint32(16)) & np.uint32(1))) & np.uint32(0xffff0000)
    return u.view(np.float32)


##


def inkling2_draft_config_beside(
        path: str,
        *,
        model_types: ta.Collection[str],
        hidden_size: int,
) -> tuple[str, DsparkConfig] | None:
    """
    The draft model put beside a file of the model at `path` that holds none itself: the checkpoint's
    `mtp.safetensors` and the config.json that describes it, in the file's directory. Its path and config, or None
    where either file is missing or the config.json is not one of a checkpoint of `model_types` with a draft model.
    A draft model of another width than the model's is an error: the two files are then not this model's.
    """

    d = os.path.dirname(os.path.abspath(path))
    draft = os.path.join(d, Inkling2DraftFile.FILE)
    config = os.path.join(d, 'config.json')
    if not (os.path.exists(draft) and os.path.exists(config)):
        return None

    with open(config) as f:
        hf = json.load(f)
    if not isinstance(hf, dict) or hf.get('model_type') not in model_types or not hf.get('mtp_config'):
        return None

    cfg = dspark_config_from_hf(hf['mtp_config'])
    if cfg.hidden_size != hidden_size:
        raise ValueError(f'{draft}: a draft model {cfg.hidden_size} wide beside a model {hidden_size} wide')

    return draft, cfg
