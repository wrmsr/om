"""
Which reader a source of weights gets, by the family it names.

A Hugging Face checkpoint directory: by the model type of its config.json. The Qwen reader (weights.py's HFSource,
which tells its own families apart) takes whatever is not listed, as it did when it was the only one.

A GGUF: by its `general.architecture`. Nothing takes one that is not listed; the ones known and not read say why.
"""
import json
import os.path
import typing as ta

from .gguffiles import GgufFile
from .inkling2 import Inkling2HFSource
from .inkling2gguf import INKLING2_GGUF_ARCHITECTURE
from .inkling2gguf import Inkling2GgufSource
from .weights import GGUFSource
from .weights import HFSource
from .weights import TensorSource


##


HF_SOURCES: ta.Mapping[str, ta.Callable[[str], TensorSource]] = {
    'inkling2_loop': Inkling2HFSource,
    'inkling2_loop_text': Inkling2HFSource,
}


def open_hf_source(path: str) -> TensorSource:
    """The source for the checkpoint directory `path` (the one holding config.json)."""

    with open(os.path.join(path, 'config.json')) as f:
        model_type = str(json.load(f).get('model_type', ''))

    return HF_SOURCES.get(model_type, HFSource)(path)


##


GGUF_SOURCES: ta.Mapping[str, ta.Callable[[GgufFile], TensorSource]] = {
    'qwen35': GGUFSource,
    INKLING2_GGUF_ARCHITECTURE: Inkling2GgufSource,
}

# architectures a GGUF is known to name that no source here reads, and what to do about each
UNREAD_GGUF_ARCHITECTURES: ta.Mapping[str, str] = {
    'inkling2': (
        "Inkling 2 in Unsloth's earlier layout, which is not read: take the file in llama.cpp's layout "
        f'(general.architecture {INKLING2_GGUF_ARCHITECTURE}), which holds the same tensors'
    ),
    'dflash': (
        "a draft model's GGUF, which is not read: Inkling 2's draft model is read from the Hugging Face checkpoint "
        '(its mtp.safetensors)'
    ),
}


class UnreadGgufArchitectureError(ValueError):
    pass


def open_gguf_source(path: str) -> TensorSource:
    """The source for the GGUF at `path`. The file is opened once and handed to its source."""

    file = GgufFile(path)
    arch = file.architecture or ''

    source = GGUF_SOURCES.get(arch)
    if source is None:
        why = UNREAD_GGUF_ARCHITECTURES.get(arch, f'not one of {", ".join(GGUF_SOURCES)}')
        raise UnreadGgufArchitectureError(f'{file.path}: unsupported GGUF architecture {arch!r}: {why}')

    return source(file)
