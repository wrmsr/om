"""
Which source a path gets: a GGUF by the architecture its metadata names -- Qwen's files the reader they always had,
Inkling 2's its own -- and the ones no source reads refused with what to do instead.
"""
import os.path
import shutil
import tempfile

import gguf
import pytest

from ...arch.tests.inkling2checkpoints import inkling2_test_config
from ...arch.tests.inkling2checkpoints import write_inkling2_checkpoint
from ...tests.test_parity import synthetic_source
from ..families import GGUF_SOURCES
from ..families import UnreadGgufArchitectureError
from ..families import open_gguf_source
from ..gguffiles import GgufFile
from ..inkling2 import Inkling2HFSource
from ..inkling2gguf import Inkling2GgufSource
from ..weights import GGUFSource
from ..weights import open_source
from .inkling2ggufs import write_inkling2_gguf


##


def _write_bare(path: str, architecture: str) -> str:
    """A GGUF with nothing in it but the architecture it names."""

    w = gguf.GGUFWriter(path, architecture)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()
    return path


def test_gguf_sources_by_architecture():
    _, _, qwen = synthetic_source()

    with tempfile.TemporaryDirectory() as tmp:
        checkpoint = os.path.join(tmp, 'checkpoint')
        write_inkling2_checkpoint(checkpoint, inkling2_test_config(moe_intermediate_size=64))
        path = os.path.join(tmp, 'inkling.gguf')
        write_inkling2_gguf(path, checkpoint)

        assert isinstance(open_source(checkpoint), Inkling2HFSource)
        assert isinstance(open_source(path), Inkling2GgufSource)

        # a Qwen file gets the reader it always had, and reads as it does opened directly
        src = open_source(str(qwen.path))
        assert type(src) is GGUFSource and src.names() == qwen.names()
        assert src.tokenizer_spec == qwen.tokenizer_spec and src.config == qwen.config

        # a blob without the extension is told by its magic, then by its architecture
        blob = os.path.join(tmp, 'sha256-blob')
        shutil.copyfile(path, blob)
        assert isinstance(open_source(blob), Inkling2GgufSource)

        # a source may be handed the opened file, which is how the table's entries are called
        file = GgufFile(path)
        assert file.architecture == 'inkling2_loop' and file.akv('block_count') == 8
        assert isinstance(GGUF_SOURCES['inkling2_loop'](file), Inkling2GgufSource)
        with pytest.raises(ValueError, match='unsupported GGUF architecture'):
            GGUFSource(file)


def test_unread_architectures():
    with tempfile.TemporaryDirectory() as tmp:
        for architecture, why in (
                ('inkling2', "Unsloth's earlier layout.*inkling2_loop"),
                ('dflash', "a draft model's GGUF.*mtp.safetensors"),
                ('llama', 'not one of qwen35, inkling2_loop'),
        ):
            path = _write_bare(os.path.join(tmp, f'{architecture}.gguf'), architecture)

            with pytest.raises(UnreadGgufArchitectureError, match=f'architecture {architecture!r}: .*{why}'):
                open_source(path)
            with pytest.raises(ValueError, match=architecture):
                open_gguf_source(path)
