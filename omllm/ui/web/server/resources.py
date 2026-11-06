import importlib.resources
import typing as ta

from omcore import dataclasses as dc


##


@ta.final
@dc.dataclass(frozen=True)
class WebResource:
    path: str
    content_type: str
    body: bytes


class WebResources:
    """
    The browser's files - the page, its scripts and styles, and its vendored dependencies - as packaged beside this
    code. Read afresh on every request, so that an edit to one shows on a reload.
    """

    CONTENT_TYPES: ta.ClassVar[ta.Mapping[str, str]] = {
        'css': 'text/css; charset=utf-8',
        'html': 'text/html; charset=utf-8',
        'ico': 'image/x-icon',
        'js': 'text/javascript; charset=utf-8',
        'json': 'application/json; charset=utf-8',
        'md': 'text/markdown; charset=utf-8',
        'mjs': 'text/javascript; charset=utf-8',
        'svg': 'image/svg+xml',
    }

    def __init__(self, *, anchor: str | None = None) -> None:
        super().__init__()

        self._anchor = anchor if anchor is not None else __package__.rpartition('.')[0] + '.resources'

    def read(self, path: str) -> WebResource | None:
        """The resource at the slash-separated path, or None for one which is not there or is not to be served."""

        parts = path.split('/')
        if any(not p or p.startswith('.') for p in parts):
            return None

        if (content_type := self.CONTENT_TYPES.get(parts[-1].rpartition('.')[2])) is None:
            return None

        resource = importlib.resources.files(self._anchor).joinpath(*parts)
        if not resource.is_file():
            return None

        return WebResource(
            path=path,
            content_type=content_type,
            body=resource.read_bytes(),
        )
