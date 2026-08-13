# flake8: noqa: E122
r"""
(cd ~/src/burntsushi/ripgrep && cargo test dump_flag_schema -- --ignored --nocapture) | \
  ./python -m omllm.agent.exec.ripgrep.args.dumped | \
  pbcopy

----

#[test]
#[ignore]
fn dump_flag_schema() {
    let schema = FLAGS
        .iter()
        .map(|flag| {
            let mut obj = serde_json::Map::new();

            obj.insert("long".into(), serde_json::json!(flag.name_long()));
            obj.insert("is_switch".into(), serde_json::json!(flag.is_switch()));

            if let Some(short) = flag.name_short() {
                obj.insert(
                    "short".into(),
                    serde_json::json!(char::from(short).to_string()),
                );
            }

            if !flag.aliases().is_empty() {
                obj.insert("aliases".into(), serde_json::json!(flag.aliases()));
            }

            if let Some(negated) = flag.name_negated() {
                obj.insert("negated".into(), serde_json::json!(negated));
            }

            serde_json::Value::Object(obj)
        })
        .collect::<Vec<_>>();

    println!(
        "{}",
        serde_json::to_string_pretty(&schema).unwrap(),
    );
}
"""
import typing as ta

from .parsing import RgFlagSpec


##


DUMPED_RG_FLAG_SPECS: ta.Final[ta.Sequence[RgFlagSpec]] = \
[
    RgFlagSpec(
        long='regexp',
        is_switch=False,
        short='e',
    ),
    RgFlagSpec(
        long='file',
        is_switch=False,
        short='f',
    ),
    RgFlagSpec(
        long='after-context',
        is_switch=False,
        short='A',
    ),
    RgFlagSpec(
        long='before-context',
        is_switch=False,
        short='B',
    ),
    RgFlagSpec(
        long='binary',
        is_switch=True,
        negated='no-binary',
    ),
    RgFlagSpec(
        long='block-buffered',
        is_switch=True,
        negated='no-block-buffered',
    ),
    RgFlagSpec(
        long='byte-offset',
        is_switch=True,
        short='b',
        negated='no-byte-offset',
    ),
    RgFlagSpec(
        long='case-sensitive',
        is_switch=True,
        short='s',
    ),
    RgFlagSpec(
        long='color',
        is_switch=False,
    ),
    RgFlagSpec(
        long='colors',
        is_switch=False,
    ),
    RgFlagSpec(
        long='column',
        is_switch=True,
        negated='no-column',
    ),
    RgFlagSpec(
        long='context',
        is_switch=False,
        short='C',
    ),
    RgFlagSpec(
        long='context-separator',
        is_switch=False,
        negated='no-context-separator',
    ),
    RgFlagSpec(
        long='count',
        is_switch=True,
        short='c',
    ),
    RgFlagSpec(
        long='count-matches',
        is_switch=True,
    ),
    RgFlagSpec(
        long='crlf',
        is_switch=True,
        negated='no-crlf',
    ),
    RgFlagSpec(
        long='debug',
        is_switch=True,
    ),
    RgFlagSpec(
        long='dfa-size-limit',
        is_switch=False,
    ),
    RgFlagSpec(
        long='encoding',
        is_switch=False,
        short='E',
        negated='no-encoding',
    ),
    RgFlagSpec(
        long='engine',
        is_switch=False,
    ),
    RgFlagSpec(
        long='field-context-separator',
        is_switch=False,
    ),
    RgFlagSpec(
        long='field-match-separator',
        is_switch=False,
    ),
    RgFlagSpec(
        long='files',
        is_switch=True,
    ),
    RgFlagSpec(
        long='files-with-matches',
        is_switch=True,
        short='l',
    ),
    RgFlagSpec(
        long='files-without-match',
        is_switch=True,
    ),
    RgFlagSpec(
        long='fixed-strings',
        is_switch=True,
        short='F',
        negated='no-fixed-strings',
    ),
    RgFlagSpec(
        long='follow',
        is_switch=True,
        short='L',
        negated='no-follow',
    ),
    RgFlagSpec(
        long='generate',
        is_switch=False,
    ),
    RgFlagSpec(
        long='glob',
        is_switch=False,
        short='g',
    ),
    RgFlagSpec(
        long='glob-case-insensitive',
        is_switch=True,
        negated='no-glob-case-insensitive',
    ),
    RgFlagSpec(
        long='heading',
        is_switch=True,
        negated='no-heading',
    ),
    RgFlagSpec(
        long='help',
        is_switch=True,
        short='h',
    ),
    RgFlagSpec(
        long='hidden',
        is_switch=True,
        short='.',
        negated='no-hidden',
    ),
    RgFlagSpec(
        long='hostname-bin',
        is_switch=False,
    ),
    RgFlagSpec(
        long='hyperlink-format',
        is_switch=False,
    ),
    RgFlagSpec(
        long='iglob',
        is_switch=False,
    ),
    RgFlagSpec(
        long='ignore-case',
        is_switch=True,
        short='i',
    ),
    RgFlagSpec(
        long='ignore-file',
        is_switch=False,
    ),
    RgFlagSpec(
        long='ignore-file-case-insensitive',
        is_switch=True,
        negated='no-ignore-file-case-insensitive',
    ),
    RgFlagSpec(
        long='include-zero',
        is_switch=True,
        negated='no-include-zero',
    ),
    RgFlagSpec(
        long='index',
        is_switch=True,
        short='X',
    ),
    RgFlagSpec(
        long='x-crud',
        is_switch=True,
    ),
    RgFlagSpec(
        long='x-force',
        is_switch=True,
    ),
    RgFlagSpec(
        long='x-path',
        is_switch=False,
    ),
    RgFlagSpec(
        long='invert-match',
        is_switch=True,
        short='v',
        negated='no-invert-match',
    ),
    RgFlagSpec(
        long='json',
        is_switch=True,
        negated='no-json',
    ),
    RgFlagSpec(
        long='line-buffered',
        is_switch=True,
        negated='no-line-buffered',
    ),
    RgFlagSpec(
        long='line-number',
        is_switch=True,
        short='n',
    ),
    RgFlagSpec(
        long='no-line-number',
        is_switch=True,
        short='N',
    ),
    RgFlagSpec(
        long='line-regexp',
        is_switch=True,
        short='x',
    ),
    RgFlagSpec(
        long='max-columns',
        is_switch=False,
        short='M',
    ),
    RgFlagSpec(
        long='max-columns-preview',
        is_switch=True,
        negated='no-max-columns-preview',
    ),
    RgFlagSpec(
        long='max-count',
        is_switch=False,
        short='m',
    ),
    RgFlagSpec(
        long='max-depth',
        is_switch=False,
        short='d',
        aliases=(
            'maxdepth',
        ),
    ),
    RgFlagSpec(
        long='max-filesize',
        is_switch=False,
    ),
    RgFlagSpec(
        long='mmap',
        is_switch=True,
        negated='no-mmap',
    ),
    RgFlagSpec(
        long='multiline',
        is_switch=True,
        short='U',
        negated='no-multiline',
    ),
    RgFlagSpec(
        long='multiline-dotall',
        is_switch=True,
        negated='no-multiline-dotall',
    ),
    RgFlagSpec(
        long='no-config',
        is_switch=True,
    ),
    RgFlagSpec(
        long='no-ignore',
        is_switch=True,
        negated='ignore',
    ),
    RgFlagSpec(
        long='no-ignore-dot',
        is_switch=True,
        negated='ignore-dot',
    ),
    RgFlagSpec(
        long='no-ignore-exclude',
        is_switch=True,
        negated='ignore-exclude',
    ),
    RgFlagSpec(
        long='no-ignore-files',
        is_switch=True,
        negated='ignore-files',
    ),
    RgFlagSpec(
        long='no-ignore-global',
        is_switch=True,
        negated='ignore-global',
    ),
    RgFlagSpec(
        long='no-ignore-messages',
        is_switch=True,
        negated='ignore-messages',
    ),
    RgFlagSpec(
        long='no-ignore-parent',
        is_switch=True,
        negated='ignore-parent',
    ),
    RgFlagSpec(
        long='no-ignore-vcs',
        is_switch=True,
        negated='ignore-vcs',
    ),
    RgFlagSpec(
        long='no-messages',
        is_switch=True,
        negated='messages',
    ),
    RgFlagSpec(
        long='no-require-git',
        is_switch=True,
        negated='require-git',
    ),
    RgFlagSpec(
        long='no-unicode',
        is_switch=True,
        negated='unicode',
    ),
    RgFlagSpec(
        long='null',
        is_switch=True,
        short='0',
    ),
    RgFlagSpec(
        long='null-data',
        is_switch=True,
    ),
    RgFlagSpec(
        long='one-file-system',
        is_switch=True,
        negated='no-one-file-system',
    ),
    RgFlagSpec(
        long='only-matching',
        is_switch=True,
        short='o',
    ),
    RgFlagSpec(
        long='path-separator',
        is_switch=False,
    ),
    RgFlagSpec(
        long='passthru',
        is_switch=True,
        aliases=(
            'passthrough',
        ),
    ),
    RgFlagSpec(
        long='pcre2',
        is_switch=True,
        short='P',
        negated='no-pcre2',
    ),
    RgFlagSpec(
        long='pcre2-version',
        is_switch=True,
    ),
    RgFlagSpec(
        long='pre',
        is_switch=False,
        negated='no-pre',
    ),
    RgFlagSpec(
        long='pre-glob',
        is_switch=False,
    ),
    RgFlagSpec(
        long='pretty',
        is_switch=True,
        short='p',
    ),
    RgFlagSpec(
        long='quiet',
        is_switch=True,
        short='q',
    ),
    RgFlagSpec(
        long='regex-size-limit',
        is_switch=False,
    ),
    RgFlagSpec(
        long='replace',
        is_switch=False,
        short='r',
    ),
    RgFlagSpec(
        long='search-zip',
        is_switch=True,
        short='z',
        negated='no-search-zip',
    ),
    RgFlagSpec(
        long='smart-case',
        is_switch=True,
        short='S',
    ),
    RgFlagSpec(
        long='sort',
        is_switch=False,
    ),
    RgFlagSpec(
        long='sortr',
        is_switch=False,
    ),
    RgFlagSpec(
        long='stats',
        is_switch=True,
        negated='no-stats',
    ),
    RgFlagSpec(
        long='stop-on-nonmatch',
        is_switch=True,
    ),
    RgFlagSpec(
        long='text',
        is_switch=True,
        short='a',
        negated='no-text',
    ),
    RgFlagSpec(
        long='threads',
        is_switch=False,
        short='j',
    ),
    RgFlagSpec(
        long='trace',
        is_switch=True,
    ),
    RgFlagSpec(
        long='trim',
        is_switch=True,
        negated='no-trim',
    ),
    RgFlagSpec(
        long='type',
        is_switch=False,
        short='t',
    ),
    RgFlagSpec(
        long='type-not',
        is_switch=False,
        short='T',
    ),
    RgFlagSpec(
        long='type-add',
        is_switch=False,
    ),
    RgFlagSpec(
        long='type-clear',
        is_switch=False,
    ),
    RgFlagSpec(
        long='type-list',
        is_switch=True,
    ),
    RgFlagSpec(
        long='unrestricted',
        is_switch=True,
        short='u',
    ),
    RgFlagSpec(
        long='version',
        is_switch=True,
        short='V',
    ),
    RgFlagSpec(
        long='vimgrep',
        is_switch=True,
    ),
    RgFlagSpec(
        long='with-filename',
        is_switch=True,
        short='H',
    ),
    RgFlagSpec(
        long='no-filename',
        is_switch=True,
        short='I',
    ),
    RgFlagSpec(
        long='word-regexp',
        is_switch=True,
        short='w',
    ),
    RgFlagSpec(
        long='auto-hybrid-regex',
        is_switch=True,
        negated='no-auto-hybrid-regex',
    ),
    RgFlagSpec(
        long='no-pcre2-unicode',
        is_switch=True,
        negated='pcre2-unicode',
    ),
    RgFlagSpec(
        long='sort-files',
        is_switch=True,
        negated='no-sort-files',
    ),
]


##


def _main() -> None:
    import io
    import json
    import sys

    all_lines = sys.stdin.read().splitlines()
    start_pos = all_lines.index('[')
    end_pos = all_lines.index(']', start_pos)
    json_lines = all_lines[start_pos:end_pos + 1]
    json_src = '\n'.join(json_lines)
    dct_lst = json.loads(json_src)

    out = io.StringIO()
    out.write('[\n')
    for dct in dct_lst:
        out.write(f'    RgFlagSpec(\n')
        out.write(f'        long={dct["long"]!r},\n')
        out.write(f'        is_switch={dct["is_switch"]!r},\n')
        if short := dct.get('short'):
            out.write(f'        short={short!r},\n')
        if aliases := dct.get('aliases'):
            out.write(f'        aliases=(\n')
            for alias in aliases:
                out.write(f'            {alias!r},\n')
            out.write(f'        ),\n')
        if negated := dct.get('negated'):
            out.write(f'        negated={negated!r},\n')
        out.write('    ),\n')
    out.write(']\n')

    print(out.getvalue(), end='')


if __name__ == '__main__':
    _main()
