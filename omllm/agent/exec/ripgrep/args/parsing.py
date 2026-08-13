import typing as ta

from omcore import dataclasses as dc
from omcore import lang


with lang.auto_proxy_import(globals()):
    from . import dumped


FlagForm: ta.TypeAlias = ta.Literal[
    'standard',
    'alias',
    'negated',
]


##


class RgArgvError(ValueError):
    pass


@dc.dataclass(frozen=True)
class RgFlagSpec:
    # Canonical long name, without "--".
    long: str

    # False means exactly one value per occurrence.
    is_switch: bool

    # Short name without "-", if any.
    short: str | None = None

    # Long aliases without "--".
    aliases: lang.SequenceNotStr[str] = ()

    # Explicit negated long spelling without "--", if any.
    negated: str | None = None


@dc.dataclass(frozen=True)
class RgOption:
    flag: RgFlagSpec

    # The spelling actually used, such as "-z" or "--search-zip".
    spelling: str

    form: FlagForm

    # True for an ordinary switch, False for an explicit negation, and str for a value-taking option.
    value: bool | str

    # Index of the argv element containing the option.
    argv_index: int

    # For a detached value, the index of the next argv element. For an attached value, the same index as argv_index.
    # None for switches.
    value_argv_index: int | None

    # True for --foo=x / -fx, False for --foo x / -f x, and None for switches.
    attached: bool | None


@dc.dataclass(frozen=True)
class RgPositional:
    value: str
    argv_index: int


class RgArgvParser:
    def __init__(self, specs: ta.Sequence[RgFlagSpec] | None = None) -> None:
        super().__init__()

        if specs is None:
            specs = dumped.DUMPED_RG_FLAG_SPECS

        self._long: dict[str, tuple[RgFlagSpec, FlagForm]] = {}
        self._short: dict[str, RgFlagSpec] = {}

        for spec in specs:
            self._put_long(spec.long, spec, 'standard')

            for alias in spec.aliases:
                self._put_long(alias, spec, 'alias')

            if spec.negated is not None:
                self._put_long(spec.negated, spec, 'negated')

            if spec.short is not None:
                short = spec.short
                if not (
                        len(short) == 1 and
                        short.isascii() and
                        (short.isalnum() or short == '.')
                ):
                    raise ValueError(f'invalid ripgrep short flag name: {short!r}')
                if short in self._short:
                    raise ValueError(f'duplicate ripgrep short flag name: -{short}')
                self._short[short] = spec

    def _put_long(
            self,
            name: str,
            spec: RgFlagSpec,
            form: FlagForm,
    ) -> None:
        if not (
                len(name) >= 2 and
                name.isascii() and
                all(c.isalnum() or c == '-' for c in name)
        ):
            raise ValueError(f'invalid ripgrep long flag name: {name!r}')
        if name in self._long:
            raise ValueError(f'duplicate ripgrep long flag name: --{name}')
        self._long[name] = (spec, form)

    def parse(
            self,
            argv: ta.Sequence[str],
    ) -> ta.Sequence[RgOption | RgPositional]:
        argv = tuple(argv)

        # Python cannot eventually pass NUL through execve anyway.
        for i, tok in enumerate(argv):
            if not isinstance(tok, str):
                raise TypeError(f'ripgrep argv[{i}] is not a string: {tok!r}')
            if '\0' in tok:
                raise RgArgvError(f'ripgrep argv[{i}] contains a NUL byte')

        parsed: list[RgOption | RgPositional] = []
        parsing_options = True
        i = 0

        while i < len(argv):
            tok = argv[i]

            if not parsing_options:
                parsed.append(RgPositional(tok, i))
                i += 1
                continue

            if tok == '--':
                parsing_options = False
                i += 1
                continue

            if tok.startswith('--'):
                option_i = i
                name, equals, joined_value = tok[2:].partition('=')

                try:
                    spec, form = self._long[name]
                except KeyError:
                    raise RgArgvError(f'unrecognized ripgrep flag --{name}') from None

                spelling = f'--{name}'

                # Explicit negations are always switches, including negations of value-taking flags.
                if form == 'negated' or spec.is_switch:
                    if equals:
                        raise RgArgvError(f'{spelling} does not take a value')

                    parsed.append(RgOption(
                        flag=spec,
                        spelling=spelling,
                        form=form,
                        value=form != 'negated',
                        argv_index=option_i,
                        value_argv_index=None,
                        attached=None,
                    ))
                    i += 1
                    continue

                if equals:
                    # Empty attached values are valid lexically: --hostname-bin=
                    value = joined_value
                    value_i = option_i
                    attached = True
                else:
                    i += 1
                    if i == len(argv):
                        raise RgArgvError(f'missing value for {spelling}')

                    # Deliberately consume this even when it is "--" or begins with "-".
                    value = argv[i]
                    value_i = i
                    attached = False

                parsed.append(RgOption(
                    flag=spec,
                    spelling=spelling,
                    form=form,
                    value=value,
                    argv_index=option_i,
                    value_argv_index=value_i,
                    attached=attached,
                ))
                i += 1
                continue

            if tok.startswith('-') and tok != '-':
                option_i = i
                cluster = tok[1:]
                j = 0

                while j < len(cluster):
                    name = cluster[j]

                    if not name.isascii():
                        raise RgArgvError(f'unrecognized ripgrep flag -{name}')

                    try:
                        spec = self._short[name]
                    except KeyError:
                        raise RgArgvError(f'unrecognized ripgrep flag -{name}') from None

                    spelling = f'-{name}'

                    if spec.is_switch:
                        parsed.append(RgOption(
                            flag=spec,
                            spelling=spelling,
                            form='standard',
                            value=True,
                            argv_index=option_i,
                            value_argv_index=None,
                            attached=None,
                        ))
                        j += 1

                        # lexopt treats this as an unexpected attached value for the preceding switch, rather than as a
                        # short option named "=".
                        if j < len(cluster) and cluster[j] == '=':
                            raise RgArgvError(f'{spelling} does not take an attached value')
                        continue

                    remainder = cluster[j + 1:]
                    if remainder:
                        # lexopt strips exactly one syntactic "=".
                        value = remainder.removeprefix('=')
                        value_i = option_i
                        attached = True
                    else:
                        i += 1
                        if i == len(argv):
                            raise RgArgvError(f'missing value for {spelling}')

                        # Again, consume option-looking values.
                        value = argv[i]
                        value_i = i
                        attached = False

                    parsed.append(RgOption(
                        flag=spec,
                        spelling=spelling,
                        form='standard',
                        value=value,
                        argv_index=option_i,
                        value_argv_index=value_i,
                        attached=attached,
                    ))

                    # A value-taking short option consumes the entire remainder of this cluster.
                    break

                i += 1
                continue

            parsed.append(RgPositional(tok, i))
            i += 1

        return tuple(parsed)
