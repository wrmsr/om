"""
TODO:
 - baseline integration - report new-vs-baselined counts
"""
import argparse
import collections
import json
import subprocess
import sys
import typing as ta


##


DEFAULT_TIMEOUT_S: float = 60. * 60.


def run_basedpyright_json(
        args: ta.Sequence[str],
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
) -> tuple[ta.Any, int]:
    proc = subprocess.run(  # noqa
        [sys.executable, '-m', 'basedpyright', '--outputjson', *args],
        stdout=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
        check=False,
    )

    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError:
        sys.stdout.write(proc.stdout)
        raise

    return output, proc.returncode


##


_SEVERITIES: ta.Sequence[str] = ['error', 'warning', 'information']


def _print_counter_table(counter: ta.Mapping[str, int]) -> None:
    max_key_len = max(map(len, counter))
    for key, count in sorted(counter.items(), key=lambda kv: -kv[1]):
        print(f'{key.rjust(max_key_len)} : {count}')


def report_output(
        output: ta.Any,
        *,
        top_files: int = 0,
) -> None:
    diags: ta.Sequence[ta.Mapping[str, ta.Any]] = output.get('generalDiagnostics', [])

    rules_by_severity: ta.Mapping[str, collections.Counter] = {
        severity: collections.Counter(
            d.get('rule', '(none)')
            for d in diags
            if d.get('severity') == severity
        )
        for severity in _SEVERITIES
    }

    for severity in _SEVERITIES:
        if not (counter := rules_by_severity[severity]):
            continue

        print()
        print(f'## {severity}s')
        print()
        _print_counter_table(counter)

    if top_files and diags:
        count_by_file = collections.Counter(d['file'] for d in diags if 'file' in d)

        print()
        print(f'## top {top_files} files')
        print()
        _print_counter_table(dict(count_by_file.most_common(top_files)))

    summary: ta.Mapping[str, ta.Any] = output.get('summary', {})

    print()
    print(', '.join([
        f'{summary.get("filesAnalyzed", "?")} files',
        *[
            f'{summary.get(f"{severity}Count", 0)} {severity}s'
            for severity in _SEVERITIES
        ],
        f'{summary.get("timeInSec", "?")}s',
    ]))
    print()


##


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-files', type=int, default=0)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    ns = parser.parse_args()

    output, rc = run_basedpyright_json(ns.args)

    report_output(
        output,
        top_files=ns.top_files,
    )

    raise SystemExit(rc)


if __name__ == '__main__':
    _main()
