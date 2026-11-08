import datetime

from omcore import lang

from .... import agent as agn
from ..systemprompt import DEFAULT_SYSTEM_PROMPT
from ..systemprompt import REMOTE_ENVIRONMENT_SYSTEM_PROMPT
from ..systemprompt import ExtraSystemPromptContributor
from ..systemprompt import StandardSystemPromptContributor
from ..systemprompt import render_environment_system_prompt


def _build(*contributors):
    return lang.sync_await(
        agn.SystemPromptManager(agn.SystemPromptContributors(list(contributors))).build_system_prompt(),
    )


##


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


##


_INFO = agn.EnvironmentInfo(
    cwd='/work/git',
    system='Linux',
    release='6.8.0-138-generic',
    machine='x86_64',
    hostname='box',
    user=agn.EnvironmentInfo.User(
        name='om',
        home='/home/om',
        shell='/bin/bash',
    ),
)

_DATE = datetime.date(2026, 11, 7)


def test_render_environment():
    assert render_environment_system_prompt(_INFO, start_date=_DATE) == '\n'.join([
        'Environment at startup:',
        '- Platform: Linux 6.8.0-138-generic, x86_64',
        '- Host: box',
        '- User: om, shell /bin/bash, home /home/om',
        '- Working directory: /work/git',
        "- Start date: 2026-11-07, the user's local date",
    ])


def test_render_environment_says_less_when_it_knows_less():
    info = agn.EnvironmentInfo(
        cwd='/',
        system='Darwin',
        release='24.0.0',
        machine='arm64',
        hostname='mac',
        user=agn.EnvironmentInfo.User(
            name='me',
        ),
    )

    assert render_environment_system_prompt(info, start_date=_DATE) == '\n'.join([
        'Environment at startup:',
        '- Platform: Darwin 24.0.0, arm64',
        '- Host: mac',
        '- User: me',
        '- Working directory: /',
        "- Start date: 2026-11-07, the user's local date",
    ])

    nobody = agn.EnvironmentInfo(
        cwd='/',
        system='Linux',
        release='6.8.0',
        machine='x86_64',
        hostname='box',
    )
    assert '- User:' not in render_environment_system_prompt(nobody, start_date=_DATE)


def test_render_environment_container_and_remote():
    # A container the harness itself runs in is said to be one; nothing is said of its being remote, since it is not.
    local_docker = agn.EnvironmentInfo(**{**_INFO.__dict__, 'container': 'docker'})
    text = render_environment_system_prompt(local_docker, start_date=_DATE)
    assert '- Host: box (a Docker container)' in text
    assert REMOTE_ENVIRONMENT_SYSTEM_PROMPT not in text

    # Reached remotely, that is said as well - whatever it is, container or not.
    remote_docker = agn.EnvironmentInfo(**{**local_docker.__dict__, 'remote': True})
    text = render_environment_system_prompt(remote_docker, start_date=_DATE)
    assert '- Host: box (a Docker container)' in text
    assert text.endswith('\n\n' + REMOTE_ENVIRONMENT_SYSTEM_PROMPT)

    remote_plain = agn.EnvironmentInfo(**{**_INFO.__dict__, 'remote': True})
    text = render_environment_system_prompt(remote_plain, start_date=_DATE)
    assert '- Host: box\n' in text
    assert text.endswith('\n\n' + REMOTE_ENVIRONMENT_SYSTEM_PROMPT)

    # A runtime it has no nicer name for is named as detected.
    other = agn.EnvironmentInfo(**{**_INFO.__dict__, 'container': 'lxc'})
    assert '- Host: box (a lxc container)' in render_environment_system_prompt(other, start_date=_DATE)
