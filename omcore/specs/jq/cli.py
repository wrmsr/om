import argparse
import json
import sys
import typing as ta

from ...formats.json.stream.utils import stream_parse_values
from .errors import JqError
from .jsonstream import parse_json_structural_events
from .program import compile_jq
from .streaming import encode_jq_stream
from .values import JqValueOps


##


def _read_chunks(stream: ta.TextIO, size: int = 64 * 1024) -> ta.Iterator[str]:
    while chunk := stream.read(size):
        yield chunk


def _with_inputs(
        files: ta.Sequence[str],
        function: ta.Callable[[ta.TextIO], ta.Iterable[ta.Any]],
) -> ta.Iterator[ta.Any]:
    if not files:
        yield from function(sys.stdin)
        return

    for file_name in files:
        with open(file_name, encoding='utf-8') as stream:
            yield from function(stream)


def _json_values(stream: ta.TextIO) -> ta.Iterator[ta.Any]:
    yield from stream_parse_values(_read_chunks(stream))


def _stream_values(stream: ta.TextIO) -> ta.Iterator[ta.Any]:
    yield from encode_jq_stream(parse_json_structural_events(_read_chunks(stream)))


def _raw_lines(stream: ta.TextIO) -> ta.Iterator[str]:
    for line in stream:
        yield line.removesuffix('\n')


def _raw_text(stream: ta.TextIO) -> ta.Iterator[str]:
    yield stream.read()


def _render(value: ta.Any, *, compact: bool, raw: bool) -> str:
    if raw and isinstance(value, str):
        return value
    canonical = JqValueOps().canonicalize(value)
    if compact:
        return json.dumps(canonical, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return json.dumps(canonical, ensure_ascii=False, indent=2, allow_nan=False)


def _parse_arguments(arguments: ta.Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='python -m omcore.specs.jq')
    parser.add_argument('filter')
    parser.add_argument('files', nargs='*')
    parser.add_argument('-c', '--compact-output', action='store_true')
    parser.add_argument('-r', '--raw-output', action='store_true')
    parser.add_argument('-n', '--null-input', action='store_true')
    parser.add_argument('-s', '--slurp', action='store_true')
    parser.add_argument('-R', '--raw-input', action='store_true')
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--arg', action='append', nargs=2, default=[], metavar=('NAME', 'VALUE'))
    parser.add_argument('--argjson', action='append', nargs=2, default=[], metavar=('NAME', 'JSON'))
    return parser.parse_args(arguments)


def _main(arguments: ta.Sequence[str] | None = None) -> int:
    args = _parse_arguments(arguments)
    variables = dict(args.arg)
    try:
        variables.update({name: json.loads(value) for name, value in args.argjson})

        if args.raw_input:
            producer = _raw_text if args.slurp else _raw_lines
        elif args.stream:
            producer = _stream_values
        else:
            producer = _json_values

        inputs: ta.Iterable[ta.Any] = _with_inputs(args.files, producer)
        if args.slurp and not args.raw_input:
            inputs = (list(inputs),)

        program = compile_jq(args.filter)
        for value in program.run(inputs, null_input=args.null_input, variables=variables):
            print(_render(value, compact=args.compact_output, raw=args.raw_output))
        return 0

    except (JqError, json.JSONDecodeError, OSError, ValueError) as exc:
        print(f'jq: {exc}', file=sys.stderr)
        return 1
