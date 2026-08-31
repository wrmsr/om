import typing as ta

from omcore import lang

from .base import MarkdownStream
from .base import MarkdownStreamBackend


if ta.TYPE_CHECKING:
    from . import markdownit
    from . import pdcmark
else:
    markdownit = lang.proxy_import('.markdownit', __package__)
    pdcmark = lang.proxy_import('.pdcmark', __package__)


##


MARKDOWN_BACKEND_NAMES: ta.Sequence[str] = ('pdcmark', 'internal', 'markdown-it')

_MARKDOWN_BACKEND_ALIASES: ta.Mapping[str, str] = {
    'internal': 'internal',
    'pdcmark': 'pdcmark',
    'markdown-it': 'markdown-it',
    'markdownit': 'markdown-it',
    'mdit': 'markdown-it',
}


def get_markdown_stream(name: str | None = None) -> MarkdownStreamBackend:
    """
    A fresh streaming backend by name: 'pdcmark' (omcore's pulldown-cmark translation, the default), 'internal' (the
    tinier zero-dep line parser), or 'markdown-it' (external, optional). Raises LookupError for unknown or unavailable
    backends.
    """

    if (resolved := _MARKDOWN_BACKEND_ALIASES.get((name or 'pdcmark').strip().lower())) is None:
        raise LookupError(f'unknown markdown backend: {name!r}')
    if resolved == 'internal':
        return MarkdownStream()
    if resolved == 'pdcmark':
        return pdcmark.PdcmarkStream()
    if not markdownit.markdown_it_available():
        raise LookupError('markdown-it backend requested but markdown_it is not installed')
    return markdownit.MarkdownItStream()
