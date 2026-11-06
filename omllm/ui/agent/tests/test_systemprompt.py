from .... import agent as agn
from ..systemprompt import DEFAULT_SYSTEM_PROMPT
from ..systemprompt import ExtraSystemPromptContributor
from ..systemprompt import StandardSystemPromptContributor


def _build(*contributors):
    return agn.SystemPromptManager(agn.SystemPromptContributors(list(contributors))).build_system_prompt()


def test_standard_defaults():
    assert _build(StandardSystemPromptContributor()) == DEFAULT_SYSTEM_PROMPT


def test_standard_override():
    assert _build(StandardSystemPromptContributor(text='Be terse.')) == 'Be terse.'


def test_standard_empty_override_contributes_nothing():
    assert _build(StandardSystemPromptContributor(text='')) == ''


def test_extra_absent_contributes_nothing():
    assert ExtraSystemPromptContributor().get_system_prompt_parts() is None
    assert _build(ExtraSystemPromptContributor()) == ''


def test_extra_follows_mission():
    # Given in the other order, to show the priorities decide the order.
    out = _build(
        ExtraSystemPromptContributor(text='Reply in haiku.'),
        StandardSystemPromptContributor(),
    )
    assert out == '\n\n'.join([DEFAULT_SYSTEM_PROMPT, 'Reply in haiku.'])
