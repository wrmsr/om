import argparse
import typing as ta

from ..config import UiConfig
from ..main import _build_frontend_parser
from ..tui.config import TuiConfig
from ..web.config import WebConfig


##


# The config of every frontend the dispatcher may choose.
_FRONTEND_CONFIG_CLSS: ta.Sequence[type[UiConfig]] = [
    TuiConfig,
    WebConfig,
]


def _option_strings(parser):
    return {s for a in parser._actions for s in a.option_strings}  # noqa


def test_no_frontend_flag_is_also_a_frontends_own():
    # The dispatcher takes its flags out of the arguments before the chosen frontend's parser sees them, so a flag of
    # both would be unreachable as the frontend's.
    frontend_flags = _option_strings(_build_frontend_parser())
    assert frontend_flags

    for config_cls in _FRONTEND_CONFIG_CLSS:
        config_parser = config_cls.configure_argument_parser(argparse.ArgumentParser())
        assert not (frontend_flags & _option_strings(config_parser)), config_cls


def test_web_tools_reach_every_frontend():
    for frontend_args in [[], ['--bare'], ['--web']]:
        ns, rest = _build_frontend_parser().parse_known_args([*frontend_args, '--web-tools'])

        assert ns.bare == (frontend_args == ['--bare'])
        assert ns.web == (frontend_args == ['--web'])
        assert rest == ['--web-tools']

        for config_cls in _FRONTEND_CONFIG_CLSS:
            assert config_cls.parse_from_arguments(rest).web is True
            assert not config_cls.parse_from_arguments([]).web
