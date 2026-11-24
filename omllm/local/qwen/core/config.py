from omcore import dataclasses as dc


##


@dc.dataclass()
class ModelConfig:
    """
    What the engine around a model reads of its configuration, whatever the architecture: `vocab_size` is the width
    of its logits (the ids it can produce).
    """

    vocab_size: int
    hidden_size: int

    def summary(self) -> str:
        raise NotImplementedError
