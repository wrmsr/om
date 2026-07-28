import abc
import typing as ta

from ... import lang
from ..transforms.types import ByteStreamTransform


##


class Compression(lang.Abstract):
    @abc.abstractmethod
    def compress(self, d: lang.Bytes) -> lang.Bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decompress(self, d: lang.Bytes) -> lang.Bytes:
        raise NotImplementedError


class IncrementalCompression(lang.Abstract):
    @abc.abstractmethod
    def compress_incremental(self) -> ByteStreamTransform[ta.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def decompress_incremental(self) -> ByteStreamTransform[ta.Any]:
        raise NotImplementedError
