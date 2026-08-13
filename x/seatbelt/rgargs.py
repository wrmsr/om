"""
cargo test dump_flag_schema -- --ignored --nocapture

----

#[test]
#[ignore]
fn dump_flag_schema() {
    let schema = FLAGS
        .iter()
        .map(|flag| {
            serde_json::json!({
                "long": flag.name_long(),
                "short": flag
                    .name_short()
                    .map(|b| char::from(b).to_string()),
                "aliases": flag.aliases(),
                "negated": flag.name_negated(),
                "is_switch": flag.is_switch(),
            })
        })
        .collect::<Vec<_>>();

    println!(
        "{}",
        serde_json::to_string_pretty(&schema).unwrap(),
    );
}
"""
import dataclasses as dc
import typing as ta

from omcore import lang


FlagForm: ta.TypeAlias = ta.Literal['standard', 'alias', 'negated']


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
    def __init__(self, specs: ta.Sequence[RgFlagSpec]) -> None:
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
    ) -> tuple[RgOption | RgPositional, ...]:
        argv = tuple(argv)

        # Python cannot eventually pass NUL through execve anyway.
        for i, token in enumerate(argv):
            if not isinstance(token, str):
                raise TypeError(f'ripgrep argv[{i}] is not a string: {token!r}')
            if '\0' in token:
                raise RgArgvError(f'ripgrep argv[{i}] contains a NUL byte')

        parsed: list[RgOption | RgPositional] = []
        parsing_options = True
        i = 0

        while i < len(argv):
            token = argv[i]

            if not parsing_options:
                parsed.append(RgPositional(token, i))
                i += 1
                continue

            if token == '--':
                parsing_options = False
                i += 1
                continue

            if token.startswith('--'):
                option_i = i
                name, equals, joined_value = token[2:].partition('=')

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

            if token.startswith('-') and token != '-':
                option_i = i
                cluster = token[1:]
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
                        value = remainder[1:] if remainder.startswith('=') else remainder
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

            parsed.append(RgPositional(token, i))
            i += 1

        return tuple(parsed)


##


DUMPED_ARGS = [
  {
    'aliases': [],
    'is_switch': False,
    'long': 'regexp',
    'negated': None,
    'short': 'e',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'file',
    'negated': None,
    'short': 'f',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'after-context',
    'negated': None,
    'short': 'A',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'before-context',
    'negated': None,
    'short': 'B',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'binary',
    'negated': 'no-binary',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'block-buffered',
    'negated': 'no-block-buffered',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'byte-offset',
    'negated': 'no-byte-offset',
    'short': 'b',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'case-sensitive',
    'negated': None,
    'short': 's',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'color',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'colors',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'column',
    'negated': 'no-column',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'context',
    'negated': None,
    'short': 'C',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'context-separator',
    'negated': 'no-context-separator',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'count',
    'negated': None,
    'short': 'c',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'count-matches',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'crlf',
    'negated': 'no-crlf',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'debug',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'dfa-size-limit',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'encoding',
    'negated': 'no-encoding',
    'short': 'E',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'engine',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'field-context-separator',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'field-match-separator',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'files',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'files-with-matches',
    'negated': None,
    'short': 'l',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'files-without-match',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'fixed-strings',
    'negated': 'no-fixed-strings',
    'short': 'F',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'follow',
    'negated': 'no-follow',
    'short': 'L',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'generate',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'glob',
    'negated': None,
    'short': 'g',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'glob-case-insensitive',
    'negated': 'no-glob-case-insensitive',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'heading',
    'negated': 'no-heading',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'help',
    'negated': None,
    'short': 'h',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'hidden',
    'negated': 'no-hidden',
    'short': '.',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'hostname-bin',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'hyperlink-format',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'iglob',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'ignore-case',
    'negated': None,
    'short': 'i',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'ignore-file',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'ignore-file-case-insensitive',
    'negated': 'no-ignore-file-case-insensitive',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'include-zero',
    'negated': 'no-include-zero',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'index',
    'negated': None,
    'short': 'X',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'x-crud',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'x-force',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'x-path',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'invert-match',
    'negated': 'no-invert-match',
    'short': 'v',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'json',
    'negated': 'no-json',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'line-buffered',
    'negated': 'no-line-buffered',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'line-number',
    'negated': None,
    'short': 'n',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-line-number',
    'negated': None,
    'short': 'N',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'line-regexp',
    'negated': None,
    'short': 'x',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'max-columns',
    'negated': None,
    'short': 'M',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'max-columns-preview',
    'negated': 'no-max-columns-preview',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'max-count',
    'negated': None,
    'short': 'm',
  },
  {
    'aliases': [
      'maxdepth',
    ],
    'is_switch': False,
    'long': 'max-depth',
    'negated': None,
    'short': 'd',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'max-filesize',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'mmap',
    'negated': 'no-mmap',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'multiline',
    'negated': 'no-multiline',
    'short': 'U',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'multiline-dotall',
    'negated': 'no-multiline-dotall',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-config',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore',
    'negated': 'ignore',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-dot',
    'negated': 'ignore-dot',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-exclude',
    'negated': 'ignore-exclude',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-files',
    'negated': 'ignore-files',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-global',
    'negated': 'ignore-global',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-messages',
    'negated': 'ignore-messages',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-parent',
    'negated': 'ignore-parent',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-ignore-vcs',
    'negated': 'ignore-vcs',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-messages',
    'negated': 'messages',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-require-git',
    'negated': 'require-git',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-unicode',
    'negated': 'unicode',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'null',
    'negated': None,
    'short': '0',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'null-data',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'one-file-system',
    'negated': 'no-one-file-system',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'only-matching',
    'negated': None,
    'short': 'o',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'path-separator',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [
      'passthrough',
    ],
    'is_switch': True,
    'long': 'passthru',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'pcre2',
    'negated': 'no-pcre2',
    'short': 'P',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'pcre2-version',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'pre',
    'negated': 'no-pre',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'pre-glob',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'pretty',
    'negated': None,
    'short': 'p',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'quiet',
    'negated': None,
    'short': 'q',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'regex-size-limit',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'replace',
    'negated': None,
    'short': 'r',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'search-zip',
    'negated': 'no-search-zip',
    'short': 'z',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'smart-case',
    'negated': None,
    'short': 'S',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'sort',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'sortr',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'stats',
    'negated': 'no-stats',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'stop-on-nonmatch',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'text',
    'negated': 'no-text',
    'short': 'a',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'threads',
    'negated': None,
    'short': 'j',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'trace',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'trim',
    'negated': 'no-trim',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'type',
    'negated': None,
    'short': 't',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'type-not',
    'negated': None,
    'short': 'T',
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'type-add',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': False,
    'long': 'type-clear',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'type-list',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'unrestricted',
    'negated': None,
    'short': 'u',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'version',
    'negated': None,
    'short': 'V',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'vimgrep',
    'negated': None,
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'with-filename',
    'negated': None,
    'short': 'H',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-filename',
    'negated': None,
    'short': 'I',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'word-regexp',
    'negated': None,
    'short': 'w',
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'auto-hybrid-regex',
    'negated': 'no-auto-hybrid-regex',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'no-pcre2-unicode',
    'negated': 'pcre2-unicode',
    'short': None,
  },
  {
    'aliases': [],
    'is_switch': True,
    'long': 'sort-files',
    'negated': 'no-sort-files',
    'short': None,
  },
]
