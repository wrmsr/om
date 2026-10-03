import os

import pytest

from omcore import lang

from ..catalogs import SkillNotFoundError
from ..files import read_skill_file
from ..loading import LocalSkillLoader


##


def _skill(root, directory, name):
    path = root / directory
    path.mkdir(parents=True)
    (path / 'SKILL.md').write_text(
        f'---\nname: {name}\ndescription: >-\n  A description with\n  multiple lines.\n---\n\nInstructions.\n',
    )
    return path


def test_discovery_parses_yaml_and_reports_bad_skills(tmp_path):
    _skill(tmp_path, 'z', 'zeta')
    _skill(tmp_path, 'a', 'alpha')
    bad = tmp_path / 'bad'
    bad.mkdir()
    (bad / 'SKILL.md').write_text('no metadata')
    loader = LocalSkillLoader(LocalSkillLoader.Config(directories=[str(tmp_path), str(tmp_path)]))
    catalog = loader.load()
    assert [s.name for s in catalog.skills] == ['alpha', 'zeta']
    assert catalog.get('alpha').description == 'A description with multiple lines.'
    assert len(catalog.diagnostics) == 1
    assert catalog.diagnostics[0].path == str(bad / 'SKILL.md')
    with pytest.raises(SkillNotFoundError):
        catalog.get('missing')


def test_duplicate_names_are_not_silently_overridden(tmp_path):
    _skill(tmp_path, 'one', 'same')
    _skill(tmp_path, 'two', 'same')
    with pytest.raises(lang.DuplicateKeyError):
        LocalSkillLoader(LocalSkillLoader.Config(directories=[str(tmp_path)])).load()


def test_missing_explicit_roots_are_diagnosed(tmp_path):
    directories = [str(tmp_path / 'missing')]
    assert LocalSkillLoader(LocalSkillLoader.Config(directories=directories)).load().diagnostics
    loader = LocalSkillLoader(LocalSkillLoader.Config(directories=directories, ignore_missing=True))
    assert not loader.load().diagnostics


def test_resources_are_bounded_text_within_the_skill(tmp_path):
    skill = _skill(tmp_path, 'skill', 'example')
    (skill / 'reference.txt').write_text('useful text')
    (skill / 'inside').symlink_to(skill / 'reference.txt')
    assert read_skill_file(str(skill), 'inside') == 'useful text'

    outside = tmp_path / 'outside'
    outside.write_text('not a skill resource')
    (skill / 'escape').symlink_to(outside)
    for path in ['../outside', str(outside), 'escape', '.']:
        with pytest.raises(ValueError, match=r'relative|escapes|regular'):
            read_skill_file(str(skill), path)
    with pytest.raises(ValueError, match='exceeds'):
        read_skill_file(str(skill), 'reference.txt', max_bytes=3)
    os.mkfifo(skill / 'fifo')
    with pytest.raises(ValueError, match='regular'):
        read_skill_file(str(skill), 'fifo')
    (skill / 'binary').write_bytes(b'\xff')
    with pytest.raises(UnicodeDecodeError):
        read_skill_file(str(skill), 'binary')
