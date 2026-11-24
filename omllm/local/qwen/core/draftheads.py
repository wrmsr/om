"""
A draft model that came with a checkpoint: what `Model.mtp` holds. It says nothing of how drafts are made -- Qwen's
head recurses on the target's final state a token at a time, Inkling's drafts a block at once from states inside
the stack (each in its family's core/) -- so there is nothing to it but the name: which draft source drafts with one
is its type's (spec/registry.py).
"""
from omcore import lang


##


class DraftHead(lang.Abstract):
    pass
