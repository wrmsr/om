"""
Which reader a Hugging Face checkpoint directory gets: by the model type its config.json names. The Qwen reader
(weights.py's HFSource, which tells its own families apart) takes whatever is not listed, as it did when it was the
only one.
"""
import json
import os.path
import typing as ta

from .inkling2 import Inkling2HFSource
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
