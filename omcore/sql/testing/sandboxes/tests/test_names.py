import pytest

from ..config import SandboxesConfig
from ..errors import SandboxNameError
from ..names import SandboxNames
from ..names import new_run_id


def test_config_validation():
    SandboxesConfig()
    with pytest.raises(Exception):  # noqa
        SandboxesConfig(database='public')
    with pytest.raises(Exception):  # noqa
        SandboxesConfig(prefix='osbx')
    with pytest.raises(Exception):  # noqa
        SandboxesConfig(prefix='bad-prefix_')
    assert SandboxesConfig().internal_prefix == '_osbx__'


def test_names():
    names = SandboxNames(SandboxesConfig())
    run_id = new_run_id()
    assert '-' in run_id

    name = names.sandbox_name(run_id, 3)
    assert name == f'_osbx_{run_id}_3'
    assert names.parse_sandbox_name(name) is not None
    assert names.parse_sandbox_name(name).run_id == run_id  # type: ignore[union-attr]
    assert names.parse_sandbox_name(name).seq == 3  # type: ignore[union-attr]
    assert names.check_sandbox_name(name) == name

    for bad in [
        '_osbx__registry',
        '_osbx_foo',
        f'_osbx_{run_id}',
        f'_osbx_{run_id}_',
        f'osbx_{run_id}_1',
        f'_osbx_{run_id}_1x',
        f'_osbx_{run_id.replace("-", "")}_1',
    ]:
        assert names.parse_sandbox_name(bad) is None
        with pytest.raises(SandboxNameError):
            names.check_sandbox_name(bad)

    with pytest.raises(SandboxNameError):
        names.sandbox_name('nope', 1)

    assert names.is_internal_name('_osbx__registry')
    assert not names.is_internal_name(name)

    assert names.application_name(run_id) == f'_osbx_{run_id}'
