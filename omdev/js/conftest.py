import typing as ta

from omcore.testing.pytest import plugins as ptp


BACKEND_DEPSKIP_MODULES: ta.Mapping[str, ta.Sequence[str]] = {
    'quickjs': [f'{__package__}.quickjs._pyqjsng'],
}


def pytest_addhooks(pluginmanager):
    for mod, imp_mods in BACKEND_DEPSKIP_MODULES.items():
        ptp.depskip.module_register(
            pluginmanager,
            [f'{__package__}.{mod}'],
            imp_mods,
        )
