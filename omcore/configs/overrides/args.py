import argparse
import typing as ta

from .dumping import OverrideDumpFormat
from .errors import OverrideSyntaxError
from .ops import JqOp
from .ops import OverrideOp
from .parsing import parse_override


##


OVERRIDE_DUMP_FORMATS: ta.Sequence[OverrideDumpFormat] = ta.get_args(OverrideDumpFormat)


def _parse_override_arg(s: str) -> OverrideOp:
    try:
        return parse_override(s)
    except OverrideSyntaxError as e:
        raise argparse.ArgumentTypeError(str(e)) from None


def add_override_arguments(
        parser: argparse._ActionsContainer,  # noqa
        *,
        set_flags: ta.Sequence[str] = ('-s', '--set'),
        jq_flags: ta.Sequence[str] = ('--jq',),
        dump_flags: ta.Sequence[str] = ('--dump',),
        dest: str = 'overrides',
        dump_dest: str = 'dump',
) -> None:
    """
    Adds override arguments to an argparse parser (or argument group). Statements and jq filters are collected - as ops,
    in the order given, whichever flag they were given by - into a single list at `dest`, which is left as `None` when
    there are none. No flags are added for a kind given no flags.
    """

    if set_flags:
        parser.add_argument(*set_flags, dest=dest, action='append', type=_parse_override_arg, metavar='OVERRIDE')

    if jq_flags:
        parser.add_argument(*jq_flags, dest=dest, action='append', type=JqOp, metavar='FILTER')

    if dump_flags:
        parser.add_argument(
            *dump_flags,
            dest=dump_dest,
            nargs='?',
            const=OVERRIDE_DUMP_FORMATS[0],
            choices=OVERRIDE_DUMP_FORMATS,
        )
