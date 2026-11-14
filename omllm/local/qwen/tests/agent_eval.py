"""
A dozen small file tasks through the agent loop (entrypoints/agent.py), each with a check of what is on disk afterwards:
a way to compare two servers -- a chat format against another, a quantization, a draft policy -- on something like the
traffic the engine is for, rather than on transcripts.

    python -m omllm.local.qwen.entrypoints.serve --model qwen3.8:27b ... --port 8000 &
    python -m omllm.local.qwen.tests.agent_eval --url http://127.0.0.1:8000 --reasoning-effort medium

Each task runs in a fresh temporary directory with the agent's file tools (no shell); its check is a few lines of
Python run in a subprocess there. Two groups: twelve small file tasks, and five exact copies of files that are hard to
carry through a call's arguments (`--tasks`). A smoke test with a number on it, not a benchmark: read the per-task
table, not just the total.
"""
import argparse
import json
import os.path
import subprocess
import sys
import tempfile
import time
import typing as ta

from ..entrypoints.agent import run


##


FIZZ = ['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', '14', 'FizzBuzz']


def _agent_eval_task(name: str, files: dict[str, str], task: str, check: str) -> tuple[str, dict[str, str], str, str]:
    return name, files, task, check


# (name, files there at the start, the task, the check)
AGENT_EVAL_TASKS: list[tuple[str, dict[str, str], str, str]] = [
    _agent_eval_task(
        'hello',
        {},
        task=(
            "Create hello.py with a function greet(name) that returns the string 'Hello, <name>!' -- for example "
            "greet('Ada') returns 'Hello, Ada!'."
        ),
        check="from hello import greet\nassert greet('Ada') == 'Hello, Ada!'",
    ),
    _agent_eval_task(
        'fix a bug',
        {'calc.py': 'def add(a, b):\n    return a - b\n\n\ndef mul(a, b):\n    return a * b\n'},
        task='calc.py has a bug in add. Fix it without changing mul.',
        check='import calc\nassert calc.add(2, 3) == 5 and calc.mul(2, 3) == 6',
    ),
    _agent_eval_task(
        'edit json',
        {'config.json': '{\n  "host": "localhost",\n  "port": 8080,\n  "debug": false\n}\n'},
        task='In config.json change the port to 9090. Keep it valid JSON and leave the other settings alone.',
        check=(
            "import json\n"
            "assert json.load(open('config.json')) == {'host': 'localhost', 'port': 9090, 'debug': False}"
        ),
    ),
    _agent_eval_task(
        'rename',
        {
            'mod.py': 'def foo(x):\n    return x + 1\n',
            'main.py': 'from mod import foo\n\n\ndef go():\n    return foo(41)\n',
        },
        task='Rename the function foo to bar everywhere it is defined or used.',
        check="import main, mod\nassert main.go() == 42 and hasattr(mod, 'bar') and not hasattr(mod, 'foo')",
    ),
    _agent_eval_task(
        'quotes and backslashes',
        {},
        task=(
            'Create patterns.py with two module-level names: NUM, a compiled regular expression (re.compile with a '
            'raw string) matching one or more digits followed by any amount of whitespace, possibly none; and QUOTE, '
            'a string whose value is exactly these characters: She said "hi" \\ bye'
        ),
        check=(
            "import patterns\nassert patterns.NUM.fullmatch('123  ') and not patterns.NUM.fullmatch('x')\n"
            "assert patterns.QUOTE == 'She said \"hi\" \\\\ bye', repr(patterns.QUOTE)"
        ),
    ),
    _agent_eval_task(
        'find a definition',
        {
            'a.py': 'def alpha():\n    return 1\n',
            'b.py': 'def beta():\n    return needle_count()\n',
            'pkg/__init__.py': '',
            'pkg/deep.py': 'def needle():\n    return 3\n',
            'pkg/other.py': 'X = "needle"\n',
        },
        task=(
            'Find the file that defines the function needle and write its path, relative to the working directory, '
            'into answer.txt -- just the path.'
        ),
        check="assert open('answer.txt').read().strip().removeprefix('./') == 'pkg/deep.py'",
    ),
    _agent_eval_task(
        'count lines',
        {'long.txt': ''.join(f'line {i}\n' for i in range(1, 38))},
        task='How many lines does long.txt have? Write just the number into count.txt.',
        check="assert open('count.txt').read().strip() == '37'",
    ),
    _agent_eval_task(
        'a package',
        {},
        task=(
            "Create a Python package pkg2: pkg2/core.py with a function double(x) returning 2 * x, and "
            "pkg2/__init__.py that sets VERSION = '1.2.3' and imports double from the core module."
        ),
        check="import pkg2\nassert pkg2.VERSION == '1.2.3' and pkg2.double(21) == 42",
    ),
    _agent_eval_task(
        'add a function',
        {'calc2.py': 'def add(a, b):\n    return a + b\n'},
        task='Add a function sub(a, b) to calc2.py that returns a - b. Keep add as it is.',
        check='import calc2\nassert calc2.add(1, 2) == 3 and calc2.sub(5, 2) == 3',
    ),
    _agent_eval_task(
        'fizzbuzz',
        {},
        task=(
            "Create fizz.py with a function fizz(n) that returns the FizzBuzz sequence from 1 to n as a list of "
            "strings ('1', '2', 'Fizz', '4', 'Buzz', ...)."
        ),
        check=f'from fizz import fizz\nassert fizz(15) == {FIZZ!r}',
    ),
    _agent_eval_task(
        'a docstring',
        {'util.py': 'def area(w, h):\n    return w * h\n'},
        task='Add a docstring to the function area in util.py saying what it returns.',
        check='import util\nassert util.area(2, 3) == 6 and len((util.area.__doc__ or "").strip()) > 5',
    ),
    _agent_eval_task(
        'markdown',
        {},
        task=(
            "Create NOTES.md with a level-1 heading 'Notes', then a bullet list of exactly three items -- alpha, "
            "beta, gamma -- then a fenced code block containing the single line print('ok')."
        ),
        check=(
            "t = open('NOTES.md').read()\nlines = [x.strip() for x in t.splitlines()]\n"
            "assert lines[0] == '# Notes'\n"
            "assert [x[2:].strip() for x in lines if x[:2] in ('- ', '* ')] == ['alpha', 'beta', 'gamma']\n"
            "assert t.count('```') == 2 and \"print('ok')\" in t.split('```')[1]"
        ),
    ),
]

# Files that are hard to carry through a call's arguments: quotes inside quotes, backslashes, escapes of escapes, tabs
# and trailing spaces. The task is to copy each exactly, and the check is equality -- a test of the call syntax as a
# transport for file contents, which is most of what an agent sends through it.
AGENT_EVAL_NASTY_FILES: dict[str, str] = {
    'regex.py': r"""import re

WORD = re.compile(r"[\w'-]+")
PATH = re.compile(r'^(?:[A-Za-z]:\\|\\\\)[^\n"<>|]*$')
QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
ESCAPES = {'\\n': '\n', '\\t': '\t', '\\"': '"', "\\'": "'", '\\\\': '\\'}


def unescape(s: str) -> str:
    return re.sub(r'\\(.)', lambda m: ESCAPES.get('\\' + m.group(1), m.group(1)), s)
""",
    'data.json': r"""{
  "title": "He said \"it's a \\\"test\\\"\" and left",
  "path": "C:\\Users\\ada\\notes\\todo.txt",
  "pattern": "^\\s*(\\d+)\\.\\s+\"([^\"]*)\"$",
  "nested": "{\"k\": \"v with \\\"quotes\\\" and a \\\\ backslash\", \"n\": [1, 2]}",
  "unicode": "caf\u00e9 \u2014 na\u00efve \ud83d\ude00",
  "lines": "first\nsecond\tindented\r\n",
  "empty": ""
}
""",
    'run.sh': r"""#!/bin/sh
# quoting, three ways
name="world"
echo "Hello, \"$name\"! It's `date +%Y`."
echo 'single quotes keep $name and \n as they are'
printf '%s\t%s\n' "a b" 'c\d'
grep -E "^[[:space:]]*#|\\$\{[A-Z_]+\}" "$0" | sed 's/\\/\\\\/g; s/"/\\"/g'
cat <<'EOF'
  literal $HOME, `backticks` and "quotes" \ here
EOF
""",
    'paths.txt': 'C:\\Program Files\\App\\bin\\app.exe\t--config "C:\\Users\\ada\\My Documents\\app.ini"\n'
                 '\\\\server\\share\\dir with spaces\\file.txt   \n'
                 "/usr/local/bin/it's here\t\ttwo tabs before, two spaces after  \n"
                 '\n'
                 '    four leading spaces, then a backslash at the end \\\n',
    'notes.tex': r"""\documentclass{article}
\newcommand{\R}{\mathbb{R}}
\begin{document}
% a comment with 100\% of the percent signs escaped
Let $f\colon \R^n \to \R$ satisfy $\|f(x)\| \le C\,\|x\|^{\alpha}$ for ``most'' $x$ \& all $\alpha > 0$.
\[
  \int_0^1 \frac{\mathrm{d}x}{\sqrt{1 - x^2}} = \frac{\pi}{2} \qquad \text{(see \S\ref{sec:proof})}
\]
\verb|\n is not a newline here: "quoted" {braces} \\ \textbackslash|
\end{document}
""",
}

AGENT_EVAL_COPIES: list[tuple[str, dict[str, str], str, str]] = [
    _agent_eval_task(
        f'copy {name}',
        {f'src/{name}': content},
        task=f'Copy the file src/{name} to out/{name} exactly, byte for byte. Read it first.',
        check=(
            f"a = open('src/{name}', newline='').read()\nb = open('out/{name}', newline='').read()\n"
            f"assert a == b, [(i, x, y) for i, (x, y) in enumerate(zip(a.splitlines(), b.splitlines())) if x != y][:2]"
        ),
    )
    for name, content in AGENT_EVAL_NASTY_FILES.items()
]


SYSTEM = (
    'You are a coding agent working in the current directory. Use the tools to look before you change anything, make '
    'the smallest change that does the job, and then answer briefly with what you did.'
)


def run_task(url: str, files: dict[str, str], task: str, check: str, **params: ta.Any) -> dict[str, ta.Any]:
    with tempfile.TemporaryDirectory() as tmp:
        for path, content in files.items():
            full = os.path.join(tmp, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, 'w') as f:
                f.write(content)

        import pathlib  # (the agent's tools take the working directory as one)

        t0 = time.time()
        try:
            messages = run(url, task, pathlib.Path(tmp), max_turns=8, system=SYSTEM, write=lambda s: None, **params)
            error = None
        except Exception as e:  # noqa
            messages = []
            error = f'{type(e).__name__}: {e}'
        dt = time.time() - t0

        calls = [c for m in messages for c in m.get('tool_calls') or []]
        results = [m.get('content') or '' for m in messages if m.get('role') == 'tool']
        proc = subprocess.run(
            [sys.executable, '-I', '-c', 'import sys\nsys.path.insert(0, ".")\n' + check],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            'ok': error is None and proc.returncode == 0,
            'turns': sum(m.get('role') == 'assistant' for m in messages),
            'calls': len(calls),
            'tool_errors': sum(r.startswith('error:') for r in results),
            'seconds': dt,
            'why': error or (proc.stderr.strip().splitlines() or [''])[-1][:160],
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--url', default='http://127.0.0.1:8000')
    ap.add_argument('--reasoning-effort', default=None)
    ap.add_argument('--temperature', type=float, default=0.0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--max-tokens', type=int, default=1500)
    ap.add_argument('--label', default='')
    ap.add_argument('--tasks', choices=['files', 'copies', 'all'], default='all',
                    help='the twelve small file tasks, the exact copies of files that are hard to quote, or both')
    ap.add_argument('--save', default=None, help='write the per-task results as JSON here')
    args = ap.parse_args()

    params: dict[str, ta.Any] = dict(temperature=args.temperature, seed=args.seed, max_tokens=args.max_tokens)
    if args.reasoning_effort is not None:
        params['reasoning_effort'] = args.reasoning_effort

    tasks = [
        *(AGENT_EVAL_TASKS if args.tasks in ('files', 'all') else []),
        *(AGENT_EVAL_COPIES if args.tasks in ('copies', 'all') else []),
    ]

    rows = {}
    for name, files, task, check in tasks:
        r = rows[name] = run_task(args.url, files, task, check, **params)
        print(f'[eval] {args.label:10s} {name:24s} {"ok  " if r["ok"] else "FAIL"} {r["turns"]} turns, {r["calls"]} '
              f'calls ({r["tool_errors"]} errors), {r["seconds"]:.0f}s {"" if r["ok"] else r["why"]}', flush=True)

    n = sum(r['ok'] for r in rows.values())
    calls = sum(r['calls'] for r in rows.values())
    errors = sum(r['tool_errors'] for r in rows.values())
    seconds = sum(r['seconds'] for r in rows.values())
    print(f'[eval] {args.label:10s} {n} of {len(rows)} tasks; {calls} calls, {errors} tool errors, {seconds:.0f}s')
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(rows, f, indent=1)


if __name__ == '__main__':
    main()
