"""
An opened GGUF: its metadata and its tensors as the vendored reader (gguf/) has them, parsed once -- a file's header
can be megabytes of tokenizer -- and handed to whichever source reads its architecture (families.py). What every such
source asks of a file is here: a metadata value, a tensor as float32 whatever type it is stored as, the tokenizer's
fields.
"""
import os
import typing as ta

from omcore import lang


if ta.TYPE_CHECKING:
    import numpy as np

    from .gguf import quants as gguf_quants
    from .gguf import reader as gguf_reader
else:
    np = lang.proxy_import('numpy')
    gguf_quants = lang.proxy_import('.gguf.quants', __package__)
    gguf_reader = lang.proxy_import('.gguf.reader', __package__)


##


class GgufFile:
    def __init__(self, path: str) -> None:
        super().__init__()

        self._path = os.path.expanduser(os.fspath(path))
        self._reader = gguf_reader.GGUFReader(self._path)
        self._tensors = {t.name: t for t in self._reader.tensors}
        self._architecture: str | None = self.kv('general.architecture')

    @property
    def path(self) -> str:
        return self._path

    @property
    def reader(self) -> gguf_reader.GGUFReader:
        return self._reader

    @property
    def tensors(self) -> ta.Mapping[str, gguf_reader.ReaderTensor]:
        """By name, as the reader has them: `data` is the stored bytes or values, memory-mapped."""

        return self._tensors

    @property
    def architecture(self) -> str | None:
        """`general.architecture`: the name the file's own keys are under."""

        return self._architecture

    # metadata

    def kv(self, key: str, default: ta.Any = None) -> ta.Any:
        f = self._reader.fields.get(key)
        return default if f is None else f.contents()

    def akv(self, key: str, default: ta.Any = None) -> ta.Any:
        """A key of the file's architecture: `<general.architecture>.<key>`."""

        return self.kv(f'{self._architecture}.{key}', default)

    def tokenizer_spec(self) -> dict[str, ta.Any]:
        """The `tokenizer.ggml.*` fields as `Tokenizer.from_gguf_spec` takes them."""

        kv = self.kv
        return {
            'kind': 'gguf',
            'model': kv('tokenizer.ggml.model'),
            'pre': kv('tokenizer.ggml.pre'),
            'tokens': kv('tokenizer.ggml.tokens'),
            'token_type': kv('tokenizer.ggml.token_type'),
            'merges': kv('tokenizer.ggml.merges'),
            'eos_id': kv('tokenizer.ggml.eos_token_id'),
            'bos_id': kv('tokenizer.ggml.bos_token_id'),
            'pad_id': kv('tokenizer.ggml.padding_token_id'),
            'add_bos': bool(kv('tokenizer.ggml.add_bos_token', False)),
            'chat_template': kv('tokenizer.chat_template'),
        }

    # tensors

    def shape(self, name: str) -> tuple[int, ...]:
        """A tensor's shape as numpy has it, [out, in]: a GGUF stores dimensions innermost first."""

        return tuple(reversed([int(d) for d in self._tensors[name].shape]))

    def dense(self, name: str) -> np.ndarray:
        """A tensor as float32 in its numpy shape, dequantized by the vendored quantizers whatever it is stored as."""

        t = self._tensors[name]
        arr = gguf_quants.dequantize(t.data, t.tensor_type)
        return np.ascontiguousarray(arr, dtype=np.float32).reshape(self.shape(name))
