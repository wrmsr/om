import re
import typing as ta

import pytest

from ..dumped import DUMPED_RG_FLAG_SPECS
from ..parsing import FlagForm
from ..parsing import RgArgvError
from ..parsing import RgArgvParser
from ..parsing import RgFlagSpec
from ..parsing import RgOption
from ..parsing import RgPositional


_SWITCH_SPEC = RgFlagSpec(
    aliases=('switch-alias',),
    is_switch=True,
    long='switch',
    negated='no-switch',
    short='s',
)

_VALUE_SPEC = RgFlagSpec(
    aliases=('value-alias',),
    is_switch=False,
    long='value',
    negated='no-value',
    short='v',
)

_DOT_SPEC = RgFlagSpec(
    is_switch=True,
    long='hidden',
    short='.',
)

_PARSER = RgArgvParser([
    _SWITCH_SPEC,
    _VALUE_SPEC,
    _DOT_SPEC,
])

_DUMPED_PARSER = RgArgvParser(DUMPED_RG_FLAG_SPECS)
_DUMPED_ALIASES = [
    (spec, alias)
    for spec in DUMPED_RG_FLAG_SPECS
    for alias in spec.aliases
]
_DUMPED_NEGATED = [spec for spec in DUMPED_RG_FLAG_SPECS if spec.negated is not None]
_DUMPED_SHORT = [spec for spec in DUMPED_RG_FLAG_SPECS if spec.short is not None]


##


def _assert_single_option(
        parser: RgArgvParser,
        argv: ta.Sequence[str],
        *,
        flag: RgFlagSpec,
        spelling: str,
        form: FlagForm,
        value: bool | str,
        argv_index: int = 0,
        value_argv_index: int | None = None,
        attached: bool | None = None,
) -> None:
    parsed = parser.parse(argv)

    assert parsed == (RgOption(
        flag=flag,
        spelling=spelling,
        form=form,
        value=value,
        argv_index=argv_index,
        value_argv_index=value_argv_index,
        attached=attached,
    ),)
    assert isinstance(parsed[0], RgOption)
    assert parsed[0].flag is flag


def test_empty_argv() -> None:
    assert _PARSER.parse([]) == ()


def test_long_switch_forms() -> None:
    _assert_single_option(
        _PARSER,
        ['--switch'],
        flag=_SWITCH_SPEC,
        spelling='--switch',
        form='standard',
        value=True,
    )
    _assert_single_option(
        _PARSER,
        ['--switch-alias'],
        flag=_SWITCH_SPEC,
        spelling='--switch-alias',
        form='alias',
        value=True,
    )
    _assert_single_option(
        _PARSER,
        ['--no-switch'],
        flag=_SWITCH_SPEC,
        spelling='--no-switch',
        form='negated',
        value=False,
    )


@pytest.mark.parametrize(
    ('argv', 'value', 'value_argv_index', 'attached'),
    [
        (['--value', 'needle'], 'needle', 1, False),
        (['--value=needle'], 'needle', 0, True),
        (['--value='], '', 0, True),
        (['--value==needle'], '=needle', 0, True),
    ],
)
def test_long_value_forms(argv, value, value_argv_index, attached) -> None:
    _assert_single_option(
        _PARSER,
        argv,
        flag=_VALUE_SPEC,
        spelling='--value',
        form='standard',
        value=value,
        value_argv_index=value_argv_index,
        attached=attached,
    )


def test_long_value_alias_and_negation() -> None:
    _assert_single_option(
        _PARSER,
        ['--value-alias=needle'],
        flag=_VALUE_SPEC,
        spelling='--value-alias',
        form='alias',
        value='needle',
        value_argv_index=0,
        attached=True,
    )
    _assert_single_option(
        _PARSER,
        ['--no-value'],
        flag=_VALUE_SPEC,
        spelling='--no-value',
        form='negated',
        value=False,
    )


@pytest.mark.parametrize('option_value', ['--', '-s', '-'])
def test_long_detached_value_consumes_option_looking_token(option_value) -> None:
    _assert_single_option(
        _PARSER,
        ['--value', option_value],
        flag=_VALUE_SPEC,
        spelling='--value',
        form='standard',
        value=option_value,
        value_argv_index=1,
        attached=False,
    )


def test_options_can_follow_positionals() -> None:
    assert _PARSER.parse(['needle', '--switch', 'path']) == (
        RgPositional('needle', 0),
        RgOption(
            flag=_SWITCH_SPEC,
            spelling='--switch',
            form='standard',
            value=True,
            argv_index=1,
            value_argv_index=None,
            attached=None,
        ),
        RgPositional('path', 2),
    )


def test_double_dash_ends_option_parsing_and_is_omitted() -> None:
    assert _PARSER.parse(['', '-', '--', '--switch', '-s', '--']) == (
        RgPositional('', 0),
        RgPositional('-', 1),
        RgPositional('--switch', 3),
        RgPositional('-s', 4),
        RgPositional('--', 5),
    )


def test_short_switch_cluster() -> None:
    assert _PARSER.parse(['-s.s']) == (
        RgOption(_SWITCH_SPEC, '-s', 'standard', True, 0, None, None),
        RgOption(_DOT_SPEC, '-.', 'standard', True, 0, None, None),
        RgOption(_SWITCH_SPEC, '-s', 'standard', True, 0, None, None),
    )


@pytest.mark.parametrize(
    ('argv', 'value', 'value_argv_index', 'attached'),
    [
        (['-v', 'needle'], 'needle', 1, False),
        (['-vneedle'], 'needle', 0, True),
        (['-v=needle'], 'needle', 0, True),
        (['-v='], '', 0, True),
        (['-v==needle'], '=needle', 0, True),
    ],
)
def test_short_value_forms(argv, value, value_argv_index, attached) -> None:
    _assert_single_option(
        _PARSER,
        argv,
        flag=_VALUE_SPEC,
        spelling='-v',
        form='standard',
        value=value,
        value_argv_index=value_argv_index,
        attached=attached,
    )


def test_value_taking_short_option_consumes_cluster_remainder() -> None:
    assert _PARSER.parse(['-svneedle']) == (
        RgOption(_SWITCH_SPEC, '-s', 'standard', True, 0, None, None),
        RgOption(_VALUE_SPEC, '-v', 'standard', 'needle', 0, 0, True),
    )


def test_short_detached_value_consumes_option_looking_token() -> None:
    assert _PARSER.parse(['-v', '-s', '--switch']) == (
        RgOption(_VALUE_SPEC, '-v', 'standard', '-s', 0, 1, False),
        RgOption(_SWITCH_SPEC, '--switch', 'standard', True, 2, None, None),
    )


def test_mixed_argv_preserves_source_indices() -> None:
    assert _PARSER.parse([
        'needle',
        '--value=first',
        '-sv',
        'second',
        '--switch-alias',
        '--no-value',
        '--',
        '-s',
    ]) == (
        RgPositional('needle', 0),
        RgOption(_VALUE_SPEC, '--value', 'standard', 'first', 1, 1, True),
        RgOption(_SWITCH_SPEC, '-s', 'standard', True, 2, None, None),
        RgOption(_VALUE_SPEC, '-v', 'standard', 'second', 2, 3, False),
        RgOption(_SWITCH_SPEC, '--switch-alias', 'alias', True, 4, None, None),
        RgOption(_VALUE_SPEC, '--no-value', 'negated', False, 5, None, None),
        RgPositional('-s', 7),
    )


@pytest.mark.parametrize(
    ('argv', 'message'),
    [
        (['--unknown'], 'unrecognized ripgrep flag --unknown'),
        (['-q'], 'unrecognized ripgrep flag -q'),
        (['-é'], 'unrecognized ripgrep flag -é'),
        (['--switch=value'], '--switch does not take a value'),
        (['--switch='], '--switch does not take a value'),
        (['--switch-alias=value'], '--switch-alias does not take a value'),
        (['--no-switch=value'], '--no-switch does not take a value'),
        (['--no-value=value'], '--no-value does not take a value'),
        (['--value'], 'missing value for --value'),
        (['-v'], 'missing value for -v'),
        (['-s=value'], '-s does not take an attached value'),
        (['-sq'], 'unrecognized ripgrep flag -q'),
    ],
)
def test_parse_errors(argv, message) -> None:
    with pytest.raises(RgArgvError, match=f'^{re.escape(message)}$'):
        _PARSER.parse(argv)


def test_parse_rejects_non_string_before_parsing() -> None:
    with pytest.raises(TypeError, match=r'^ripgrep argv\[1\] is not a string: 42$'):
        _PARSER.parse(['--', ta.cast(str, 42)])


def test_parse_rejects_nul_before_parsing() -> None:
    with pytest.raises(RgArgvError, match=r'^ripgrep argv\[1\] contains a NUL byte$'):
        _PARSER.parse(['--', 'bad\0value'])


@pytest.mark.parametrize('name', ['', 'x', 'bad!', 'bad_name', 'bäd'])
def test_rejects_invalid_long_names(name) -> None:
    with pytest.raises(ValueError, match=r'^invalid ripgrep long flag name:'):
        RgArgvParser([RgFlagSpec(long=name, is_switch=True)])


def test_rejects_invalid_long_alias() -> None:
    with pytest.raises(ValueError, match=r"^invalid ripgrep long flag name: 'x'$"):
        RgArgvParser([RgFlagSpec(long='valid', is_switch=True, aliases=('x',))])


def test_rejects_invalid_negated_long_name() -> None:
    with pytest.raises(ValueError, match=r"^invalid ripgrep long flag name: 'x'$"):
        RgArgvParser([RgFlagSpec(long='valid', is_switch=True, negated='x')])


@pytest.mark.parametrize('name', ['', 'ab', '-', '_', 'é'])
def test_rejects_invalid_short_names(name) -> None:
    with pytest.raises(ValueError, match=r'^invalid ripgrep short flag name:'):
        RgArgvParser([RgFlagSpec(long='valid', is_switch=True, short=name)])


def test_rejects_duplicate_long_names_across_forms() -> None:
    with pytest.raises(ValueError, match=r'^duplicate ripgrep long flag name: --beta$'):
        RgArgvParser([
            RgFlagSpec(long='alpha', is_switch=True, aliases=('beta',)),
            RgFlagSpec(long='beta', is_switch=True),
        ])


def test_rejects_duplicate_short_names() -> None:
    with pytest.raises(ValueError, match=r'^duplicate ripgrep short flag name: -a$'):
        RgArgvParser([
            RgFlagSpec(long='alpha', is_switch=True, short='a'),
            RgFlagSpec(long='beta', is_switch=True, short='a'),
        ])


@pytest.mark.parametrize('spec', DUMPED_RG_FLAG_SPECS, ids=[spec.long for spec in DUMPED_RG_FLAG_SPECS])
def test_all_dumped_standard_long_forms(spec) -> None:
    if spec.is_switch:
        argv = [f'--{spec.long}']
        value: bool | str = True
        value_argv_index = None
        attached = None
    else:
        argv = [f'--{spec.long}=value']
        value = 'value'
        value_argv_index = 0
        attached = True

    _assert_single_option(
        _DUMPED_PARSER,
        argv,
        flag=spec,
        spelling=f'--{spec.long}',
        form='standard',
        value=value,
        value_argv_index=value_argv_index,
        attached=attached,
    )


@pytest.mark.parametrize(
    ('spec', 'alias'),
    _DUMPED_ALIASES,
    ids=[alias for _, alias in _DUMPED_ALIASES],
)
def test_all_dumped_long_aliases(spec, alias) -> None:
    if spec.is_switch:
        argv = [f'--{alias}']
        value: bool | str = True
        value_argv_index = None
        attached = None
    else:
        argv = [f'--{alias}=value']
        value = 'value'
        value_argv_index = 0
        attached = True

    _assert_single_option(
        _DUMPED_PARSER,
        argv,
        flag=spec,
        spelling=f'--{alias}',
        form='alias',
        value=value,
        value_argv_index=value_argv_index,
        attached=attached,
    )


@pytest.mark.parametrize(
    'spec',
    _DUMPED_NEGATED,
    ids=[spec.negated for spec in _DUMPED_NEGATED],
)
def test_all_dumped_negated_long_forms(spec) -> None:
    assert spec.negated is not None

    _assert_single_option(
        _DUMPED_PARSER,
        [f'--{spec.negated}'],
        flag=spec,
        spelling=f'--{spec.negated}',
        form='negated',
        value=False,
    )


@pytest.mark.parametrize(
    'spec',
    _DUMPED_SHORT,
    ids=[spec.short for spec in _DUMPED_SHORT],
)
def test_all_dumped_short_forms(spec) -> None:
    assert spec.short is not None

    if spec.is_switch:
        argv = [f'-{spec.short}']
        value: bool | str = True
        value_argv_index = None
        attached = None
    else:
        argv = [f'-{spec.short}value']
        value = 'value'
        value_argv_index = 0
        attached = True

    _assert_single_option(
        _DUMPED_PARSER,
        argv,
        flag=spec,
        spelling=f'-{spec.short}',
        form='standard',
        value=value,
        value_argv_index=value_argv_index,
        attached=attached,
    )
