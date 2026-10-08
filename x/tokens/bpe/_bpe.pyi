import typing as ta

##


GPT4_PATTERN: ta.Final[str]


@ta.final
class Tokenizer:
    def __init__(self) -> None: ...

    @property
    def vocab_size(self) -> int: ...

    def train_from_iterator(
            self,
            iterator: ta.Iterable[str],
            vocab_size: int,
            buffer_size: int = 8192,
            pattern: str | None = None,
            *,
            num_threads: int | None = None,
    ) -> None: ...

    def get_pattern(self) -> str: ...

    def get_mergeable_ranks(self) -> list[tuple[bytes, int]]: ...

    def encode(self, text: str) -> list[int]: ...

    def batch_encode(
            self,
            texts: ta.Iterable[str],
            *,
            num_threads: int | None = None,
    ) -> list[list[int]]: ...

    def decode(self, ids: ta.Iterable[int]) -> str: ...
