import pytest

from omcore import lang

from ..base import PromptContext
from ..base import PromptContributors
from ..builders import PromptBuilder
from ..standard import CodingPromptContributor
from ..standard import TextPromptContributor
from ..standard import ToolsPromptContributor


##


def test_contributors_have_stable_order_and_unique_names():
    contributors = [
        TextPromptContributor('last', 'last', order=10),
        TextPromptContributor('b', ' b ', order=0),
        TextPromptContributor('a', 'a', order=0),
        TextPromptContributor('empty', '  ', order=0),
    ]
    for cs in [contributors, list(reversed(contributors))]:
        assert PromptBuilder(contributors=PromptContributors(cs)).build(PromptContext()) == 'a\n\nb\n\nlast'
    with pytest.raises(lang.DuplicateKeyError):
        PromptBuilder(contributors=PromptContributors([contributors[0], contributors[0]]))


def test_default_prompt_only_describes_available_capabilities():
    builder = PromptBuilder(contributors=PromptContributors([CodingPromptContributor(), ToolsPromptContributor()]))
    text = builder.build(PromptContext())
    assert 'No tools are available' in text
    assert 'AGENTS.md' not in text
    text = builder.build(PromptContext(tool_names=frozenset({'read', 'ripgrep', 'bash'})))
    assert 'Read the relevant files before editing' in text
    assert 'Use ripgrep' in text
    assert 'Fetch source pages' not in text
