import html

import pytest

from ..building import D
from ..building import d
from ..rendering import InvalidTagError
from ..rendering import Renderer
from ..rendering import StrForbiddenError


def test_escape():
    root = D.div('<unsafe & text>', title='"unsafe & value"')

    assert Renderer.render_to_str(root, escape=html.escape) == (
        '<div title="&quot;unsafe &amp; value&quot;">'
        '&lt;unsafe &amp; text&gt;'
        '</div>'
    )


def test_invalid_tag():
    with pytest.raises(InvalidTagError) as exc_info:
        Renderer.render_to_str(d('<invalid>'), escape=html.escape)
    assert exc_info.value.args == ('<invalid>',)


def test_forbid_str():
    with pytest.raises(StrForbiddenError) as exc_info:
        Renderer.render_to_str(D.div('text'), forbid_str=True)
    assert exc_info.value.args == ('text',)
