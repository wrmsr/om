"""
A small local agent: drives the chat server with a tool loop over a working directory.

    python -m omllm.local.qwen.entrypoints.agent --url http://localhost:8000 --cwd ~/src/thing \\
        "Find where the config is parsed and add a --verbose flag"

Each turn sends the conversation with the tool schemas below; a `tool_calls` finish runs the calls (shell commands are
shown and need a y/N unless --yes) and feeds the results back as `tool` messages; a `stop` finish prints the answer. It
prints per turn what the server reported: prompt tokens, how many of them the prefix cache reused, and generation time
-- which is how to see that the loop stays warm (every turn after the first should reuse the whole previous prompt plus
its answer).

This exists to exercise and time the engine end to end; it is deliberately a thin loop, not a product.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import typing as ta

from ..serving import client


##


TOOLS: list[dict] = [
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': 'Read a text file (optionally a line range) relative to the working directory.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                    'start': {'type': 'integer', 'description': '1-based first line'},
                    'end': {'type': 'integer', 'description': '1-based last line, inclusive'},
                },
                'required': ['path'],
                'additionalProperties': False,
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'write_file',
            'description': 'Write a text file (creating directories), replacing its content.',
            'parameters': {
                'type': 'object',
                'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}},
                'required': ['path', 'content'],
                'additionalProperties': False,
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_dir',
            'description': 'List a directory (names, sizes).',
            'parameters': {
                'type': 'object',
                'properties': {'path': {'type': 'string'}},
                'required': [],
                'additionalProperties': False,
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'grep',
            'description': 'Search files under a directory for a regular expression; returns file:line: text.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'pattern': {'type': 'string'},
                    'path': {'type': 'string', 'description': 'file or directory, default the working directory'},
                    'glob': {'type': 'string', 'description': "file name pattern, e.g. '*.py'"},
                },
                'required': ['pattern'],
                'additionalProperties': False,
            },
        },
    },
]

SHELL_TOOL: dict = {
    'type': 'function',
    'function': {
        'name': 'shell',
        'description': 'Run a shell command in the working directory and return its output (stdout and stderr, '
                       'truncated) and exit code.',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {'type': 'string', 'description': 'the command line, run with /bin/sh -c'},
                'timeout': {'type': 'integer', 'description': 'seconds before the command is killed'},
            },
            'required': ['command'],
            'additionalProperties': False,
        },
    },
}


MAX_OUT = 8000  # characters of tool output sent back


class Tools:
    def __init__(
            self,
            cwd: pathlib.Path,
            *,
            shell: ta.Literal['ask', 'unsafe-allow'] | None = None,
    ) -> None:
        super().__init__()

        self.cwd = cwd.resolve()
        self.shell = shell

    def _path(self, p: str | None) -> pathlib.Path:
        q = (self.cwd / (p or '.')).resolve()
        if self.cwd not in q.parents and q != self.cwd:
            raise ValueError(f'{p!r} is outside the working directory')
        return q

    def run(self, name: str, args: dict) -> str:
        fn = getattr(self, 't_' + name, None)
        if fn is None:
            return f'error: no such tool {name!r}'
        try:
            out = fn(**args)
        except Exception as e:  # noqa
            out = f'error: {type(e).__name__}: {e}'
        if len(out) > MAX_OUT:
            out = out[:MAX_OUT // 2] + f'\n... [{len(out) - MAX_OUT} characters elided] ...\n' + out[-MAX_OUT // 2:]
        return out

    def t_shell(self, command: str, timeout: int = 60) -> str:
        if not self.shell:
            raise RuntimeError('Shell tool not permitted')
        elif self.shell == 'ask':
            sys.stderr.write(f'\n$ {command}\nrun? [y/N] ')
            sys.stderr.flush()
            if sys.stdin.readline().strip().lower() not in ('y', 'yes'):
                return 'error: the user declined to run this command'
        elif self.shell == 'unsafe-allow':
            pass
        else:
            raise ValueError(self.shell)

        try:
            p = subprocess.run(  # noqa
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return f'error: timed out after {timeout}s'
        out = p.stdout
        if p.stderr:
            out += ('\n' if out else '') + '[stderr]\n' + p.stderr
        return f'{out}\n[exit {p.returncode}]'

    def t_read_file(
            self,
            path: str,
            start: int | None = None,
            end: int | None = None,
    ) -> str:
        lines = self._path(path).read_text(errors='replace').split('\n')
        a = max(1, start or 1)
        b = min(len(lines), end or len(lines))
        return '\n'.join(f'{i:5d}| {lines[i - 1]}' for i in range(a, b + 1))

    def t_write_file(self, path: str, content: str) -> str:
        p = self._path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f'wrote {len(content)} characters to {path}'

    def t_list_dir(self, path: str | None = None) -> str:
        p = self._path(path)
        rows = []
        for q in sorted(p.iterdir()):
            rows.append(f'{q.name}/' if q.is_dir() else f'{q.name}  {q.stat().st_size}')
        return '\n'.join(rows) or '(empty)'

    def t_grep(
            self,
            pattern: str,
            path: str | None = None,
            glob: str | None = None,
    ) -> str:
        rx = re.compile(pattern)
        root = self._path(path)
        files = [root] if root.is_file() else sorted(root.rglob(glob or '*'))
        hits = []
        for f in files:
            if not f.is_file() or '.git' in f.parts:
                continue
            try:
                for i, line in enumerate(f.read_text(errors='replace').split('\n'), 1):
                    if rx.search(line):
                        hits.append(f'{f.relative_to(self.cwd)}:{i}: {line.strip()}')
                        if len(hits) >= 200:
                            return '\n'.join(hits) + '\n... (stopped at 200 matches)'
            except OSError:
                continue
        return '\n'.join(hits) or '(no matches)'


##


def run(
        url: str,
        task: str,
        cwd: pathlib.Path,
        *,
        max_turns: int = 20,
        shell: ta.Literal['ask', 'unsafe-allow'] | None = None,
        system: str | None = None,
        thinking: bool = True,
        write: ta.Callable[[str], None] = sys.stdout.write,  # type: ignore[assignment]
        **params: ta.Any,
) -> list[dict]:
    """The loop; returns the final message list."""

    tools = Tools(
        cwd,
        shell=shell,
    )

    messages: list[dict] = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': task})

    for turn in range(1, max_turns + 1):
        t0 = time.time()
        got = client(
            url,
            messages,
            stream=True,
            write=write,
            tools=[*TOOLS, *([SHELL_TOOL] if shell else [])],
            enable_thinking=thinking,
            **params,
        )
        dt = time.time() - t0

        msg = got['message']
        usage = got.get('usage') or {}
        write(
            f"\n[turn {turn}] {got['finish_reason']}; prompt {usage.get('prompt_tokens')} "
            f"(reused {usage.get('prompt_tokens_reused')}), {usage.get('completion_tokens')} tokens in {dt:.1f}s\n",
        )

        assistant: dict = {'role': 'assistant', 'content': msg['content'] or None}
        if msg.get('reasoning_content'):
            assistant['reasoning_content'] = msg['reasoning_content']
        if msg['tool_calls']:
            assistant['tool_calls'] = msg['tool_calls']
        messages.append(assistant)

        if got['finish_reason'] != 'tool_calls' or not msg['tool_calls']:
            return messages

        for call in msg['tool_calls']:
            fn = call['function']

            try:
                args = json.loads(fn['arguments'] or '{}')
            except json.JSONDecodeError as e:
                result = f'error: arguments are not valid JSON: {e}'
            else:
                write(f"  -> {fn['name']}({', '.join(f'{k}={v!r}' for k, v in args.items())})\n")
                result = tools.run(fn['name'], args)

            messages.append({'role': 'tool', 'tool_call_id': call.get('id', ''), 'content': result})

    write(f'\n[stopped after {max_turns} turns]\n')

    return messages


##


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        'task',
        help='what to do',
    )
    ap.add_argument(
        '--url',
        default='http://localhost:8000',
    )
    ap.add_argument(
        '--cwd',
        default='.',
        help='working directory the tools operate in',
    )
    ap.add_argument(
        '--max-turns',
        type=int,
        default=20,
    )
    ap.add_argument(
        '--shell',
        action='store_true',
        help='allow running shell commands',
    )
    ap.add_argument(
        '--unsafe-shell',
        action='store_true',
        help='allow running shell commands without asking',
    )
    ap.add_argument(
        '--no-thinking',
        action='store_true',
    )
    ap.add_argument(
        '--temperature',
        type=float,
        default=None,
    )
    ap.add_argument(
        '--system',
        default=None,
        help='system prompt (default: a short one naming the directory)',
    )
    ap.add_argument(
        '--transcript',
        default=None,
        help='write the final message list as JSON here',
    )
    args = ap.parse_args()

    cwd = pathlib.Path(os.path.expanduser(args.cwd)).resolve()

    system = args.system or (
        f'You are a coding agent working in the directory {cwd}. Use the tools to look before you change anything, '
        f'make the smallest change that does the job, verify it, and then answer with what you did.'
    )

    params: dict[str, ta.Any] = {}
    if args.temperature is not None:
        params['temperature'] = args.temperature

    messages = run(
        args.url,
        args.task,
        cwd,
        max_turns=args.max_turns,
        shell='unsafe-allow' if args.unsafe_shell else 'ask' if args.shell else None,
        system=system,
        thinking=not args.no_thinking,
        **params,
    )

    if args.transcript:
        pathlib.Path(args.transcript).write_text(json.dumps(messages, indent=2))


if __name__ == '__main__':
    main()
