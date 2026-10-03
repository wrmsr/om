from omcore import collections as col

from .base import PromptContext
from .base import PromptContributors


##


class PromptBuilder:
    def __init__(self, *, contributors: PromptContributors) -> None:
        super().__init__()

        by_name = col.make_map(((c.name, c) for c in contributors), strict=True)
        self._contributors = tuple(sorted(by_name.values(), key=lambda c: (c.order, c.name)))

    def build(self, context: PromptContext) -> str:
        return '\n\n'.join(
            text.strip()
            for contributor in self._contributors
            if (text := contributor.render(context)) is not None and text.strip()
        )
