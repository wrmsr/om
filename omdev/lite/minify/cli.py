import argparse
import sys
import zlib

from .minifying import minify


##


def _report_stats(label: str, text: str) -> None:
    raw = text.encode('utf-8')
    print(f'{label:>9}: {len(raw):>9,} bytes  zlib-9: {len(zlib.compress(raw, 9)):>8,} bytes', file=sys.stderr)


def _main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog='minify')
    parser.add_argument('input', nargs='?', help='source file (default: stdin)')
    parser.add_argument('-o', '--output', help='output file (default: stdout)')
    parser.add_argument('--keep-literal-statements', action='store_true', help='keep docstrings and other literals')
    parser.add_argument('--no-verify', action='store_true', help='skip the AST round-trip check')
    parser.add_argument('--no-shebang', action='store_true', help='drop a leading #! line')
    parser.add_argument('--stats', action='store_true', help='report sizes on stderr')
    args = parser.parse_args(argv)

    if args.input is not None:
        with open(args.input, encoding='utf-8') as f:
            source = f.read()
    else:
        source = sys.stdin.read()

    out = minify(
        source,
        keep_literal_statements=args.keep_literal_statements,
        no_verify=args.no_verify,
        no_shebang=args.no_shebang,
    )

    if args.output is not None:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(out)
    else:
        sys.stdout.write(out)

    if args.stats:
        _report_stats('original', source)
        _report_stats('minified', out)


if __name__ == '__main__':
    _main()
