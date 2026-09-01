"""
Integration tests against the GFM-extension spec fixtures (vendored under the pulldown-cmark submodule's
third_party/GitHub/). Tables / strikethrough / tasklists are required to be enabled via the GFM preset; without enabling
the extensions these tests are not meaningful.
"""
import os.path
import re

import pytest

from ..options import GFM
from ..parsing import parse
from ..rendering.html import render_html
from .spec_runner import SpecCase
from .spec_runner import load_spec_file


def _gfm_paths(pulldown_cmark_root: str) -> dict[str, str]:
    base = os.path.join(pulldown_cmark_root, 'third_party', 'GitHub')
    return {
        'gfm_strikethrough.txt': os.path.join(base, 'gfm_strikethrough.txt'),
        'gfm_table.txt': os.path.join(base, 'gfm_table.txt'),
        'gfm_tasklist.txt': os.path.join(base, 'gfm_tasklist.txt'),
    }


@pytest.fixture(scope='module')
def gfm_caseses(pulldown_cmark_root) -> dict[str, list[SpecCase]]:
    return {name: load_spec_file(p) for name, p in _gfm_paths(pulldown_cmark_root).items()}


def _passes(c: SpecCase) -> bool:
    try:
        return render_html(parse(c.markdown, GFM)) == c.expected_html
    except Exception:  # noqa
        return False


_GFM_FLOORS = {
    'gfm_strikethrough.txt': 3,
    'gfm_table.txt': 9,
    'gfm_tasklist.txt': 2,
}


@pytest.mark.parametrize('name', list(_GFM_FLOORS))
def test_gfm_file_meets_floor(gfm_caseses, name):
    cases = gfm_caseses[name]
    passes = sum(1 for c in cases if _passes(c))
    assert passes >= _GFM_FLOORS[name], (
        f'{name}: {passes}/{len(cases)} below floor {_GFM_FLOORS[name]}'
    )


##


def _structural(html: str) -> str:
    """Whitespace between tags dropped: pulldown's own fixtures compact table markup onto single lines."""

    return re.sub(r'>\s+<', '><', html).strip()


@pytest.fixture(scope='module')
def pulldown_table_cases(pulldown_cmark_root) -> list[SpecCase]:
    return load_spec_file(os.path.join(pulldown_cmark_root, 'specs', 'table.txt'))


# pulldown-cmark's `specs/table.txt` is stricter than the GFM fixtures. Three cases miss by design: two deliberate
# divergences that follow cmark-gfm / GitHub instead of pulldown (a header row may be the last line of a multi-line
# paragraph without a leading pipe; a `- | -` delimiter row is a list item), and one that references refdefs defined
# below the tables - the documented forward-reference tradeoff of default (streaming-equivalent) mode, which
# `prescan_refdefs=True` recovers.
_PULLDOWN_TABLE_FLOOR = 25


def test_pulldown_table_suite_meets_floor(pulldown_table_cases):
    passes = 0
    total = 0
    for c in pulldown_table_cases:
        if c.disabled:
            continue
        total += 1
        try:
            got = render_html(parse(c.markdown, GFM))
        except Exception:  # noqa
            continue
        if _structural(got) == _structural(c.expected_html):
            passes += 1
    assert passes >= _PULLDOWN_TABLE_FLOOR, f'table.txt: {passes}/{total} below floor {_PULLDOWN_TABLE_FLOOR}'
