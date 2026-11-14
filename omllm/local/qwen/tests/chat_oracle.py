"""
A checkpoint's own chat template as the oracle for the hand-written chat format (serve/chat.py, tokenizer.py): the
template is rendered with Jinja for a set of conversations and compared with ours, character for character.

    python -m omllm.local.qwen.tests.chat_oracle --model qwen3.8:27b

Two reports, and the exit status says whether both agree. The reasoning-effort instruction
(`Tokenizer.reasoning_instruction`) against what the template inserts for each level. And every conversation rendered
by `render_chat` in the format chosen for the checkpoint (`chat_format_for`) against the template's rendering, thinking
on and off: system turn and tools block, tool calls of every argument type, tool results, reasoning in the history, the
generation prompt.

Where this code departs from the templates on purpose, the oracle does not go: a system message after the first turn
(the templates refuse it; it is rendered as a turn here), reasoning written inside an assistant message's content
(split out here), and `preserve_thinking`, which is compared at the template's own setting.

The template is treated as a black box: rendered, never read. Jinja is needed only here.
"""
import argparse
import json
import sys
import typing as ta

from ..load.weights import open_source
from ..serve.chat import QWEN38
from ..serve.chat import chat_format_for
from ..serve.chat import render_chat
from ..tokenizer import REASONING_EFFORT_INSTRUCTIONS
from ..tokenizer import Tokenizer


##


ORACLE_TOOLS: list[dict] = [
    {'type': 'function', 'function': {'name': 'read_file', 'description': 'Read a file.', 'parameters': {
        'type': 'object',
        'properties': {'path': {'type': 'string', 'description': 'the path'}, 'limit': {'type': 'integer'}},
        'required': ['path'],
    }}},
    {'type': 'function', 'function': {'name': 'now', 'description': 'The time.', 'parameters': {
        'type': 'object', 'properties': {},
    }}},
]


def oracle_cases() -> dict[str, dict[str, ta.Any]]:
    def call(args: dict, name: str = 'read_file', i: str = 'c1') -> dict:
        return {'id': i, 'type': 'function', 'function': {'name': name, 'arguments': args}}

    user = {'role': 'user', 'content': 'Hi'}
    system = {'role': 'system', 'content': 'SYS'}
    values = {
        's': 'text', 'empty': '', 'multi': 'a\nb', 'pad': '  pad  ', 'i': 3, 'fl': 1.5, 't': True, 'f': False,
        'n': None, 'l': [1, 'x', True], 'd': {'k': 'v', 'n': None}, 'u': 'é"<\\',
    }
    loop = [
        system,
        user,
        {'role': 'assistant', 'content': 'Let me look.', 'reasoning_content': 'hm',
         'tool_calls': [call({'path': 'a/b.py', 'limit': 3}), call({}, 'now', 'c2')]},
        {'role': 'tool', 'content': 'R1', 'tool_call_id': 'c1'},
        {'role': 'tool', 'content': [{'type': 'text', 'text': 'R2'}], 'tool_call_id': 'c2'},
        {'role': 'assistant', 'content': 'done', 'reasoning_content': 'ok'},
        {'role': 'user', 'content': 'More'},
    ]
    return {
        'user': dict(messages=[user]),
        'system + user': dict(messages=[system, user]),
        'two turns': dict(messages=[user, {'role': 'assistant', 'content': 'Yo'}, {'role': 'user', 'content': 'More'}]),
        'reasoning in history': dict(messages=[
            user, {'role': 'assistant', 'content': 'A1', 'reasoning_content': 'R1'}, {'role': 'user', 'content': 'Q2'},
            {'role': 'assistant', 'content': 'A2', 'reasoning_content': 'R2'}, {'role': 'user', 'content': 'Q3'},
        ]),
        'content in parts': dict(messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': 'P1'}, {'type': 'text', 'text': 'P2'},
        ]}]),
        'tools': dict(messages=[user], tools=ORACLE_TOOLS),
        'system + tools': dict(messages=[system, user], tools=ORACLE_TOOLS),
        'tool loop': dict(messages=loop, tools=ORACLE_TOOLS),
        'call pending': dict(messages=loop[:3], tools=ORACLE_TOOLS),
        'call answered': dict(messages=loop[:5], tools=ORACLE_TOOLS),
        'argument types': dict(messages=[
            user, {'role': 'assistant', 'content': '', 'tool_calls': [call(values)]},
            {'role': 'tool', 'content': 'R', 'tool_call_id': 'c1'},
        ], tools=ORACLE_TOOLS),
        'bare call': dict(messages=[
            user, {'role': 'assistant', 'content': None, 'tool_calls': [call({'path': 'x'})]},
            {'role': 'tool', 'content': 'R', 'tool_call_id': 'c1'},
            {'role': 'assistant', 'content': 'A'}, {'role': 'user', 'content': 'Q2'},
        ], tools=ORACLE_TOOLS),
    }


def template_renderer(template: str) -> ta.Callable[..., str]:
    import jinja2.sandbox

    def raise_exception(msg: str) -> ta.NoReturn:
        raise ValueError(msg)

    env = jinja2.sandbox.ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    env.filters['tojson'] = lambda x, **kw: json.dumps(x, ensure_ascii=False)
    env.globals['raise_exception'] = raise_exception
    compiled = env.from_string(template)

    def render(**kw: ta.Any) -> str:
        return compiled.render(add_generation_prompt=True, **kw)

    return render


def _json_args(messages: list[dict]) -> list[dict]:
    """The messages as an OpenAI client sends them: tool-call arguments as JSON text (the template wants a mapping)."""

    out = []
    for m in messages:
        if m.get('tool_calls'):
            m = dict(m, tool_calls=[
                dict(c, function=dict(c['function'], arguments=json.dumps(c['function']['arguments'])))
                for c in m['tool_calls']
            ])
        out.append(m)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    args = ap.parse_args()

    tok = Tokenizer.from_spec(open_source(args.model).tokenizer_spec)
    if not tok.chat_template:
        print(f'[oracle] {args.model} carries no chat template')
        sys.exit(2)
    render = template_renderer(tok.chat_template)
    cases = oracle_cases()
    fmt = chat_format_for(tok)
    preserve = fmt is QWEN38  # the template's own way with the reasoning of earlier turns (qwen3.8 keeps it)
    ok = True
    print(f'[oracle] {args.model}: chat format {fmt.name}; takes a reasoning effort: {tok.reasoning_efforts}')

    def ours(kw: dict[str, ta.Any], think: bool, instruction: str | None = None) -> str:
        return render_chat(
            _json_args(kw['messages']),
            kw.get('tools'),
            enable_thinking=think,
            preserve_thinking=preserve,
            reasoning_instruction=instruction,
            fmt=fmt,
        )

    # 1. reasoning effort: each level against the template's rendering of it
    if tok.reasoning_efforts:
        for name, kw in cases.items():
            for level in [None, *REASONING_EFFORT_INSTRUCTIONS]:
                extra = {} if level is None else {'reasoning_effort': level}
                same = render(enable_thinking=True, **kw, **extra) == ours(kw, True, tok.reasoning_instruction(level))
                same = same and render(enable_thinking=False, **kw, **extra) == ours(kw, False)
                ok = ok and same
                if not same:
                    print(f'[oracle]   {name:22s} effort={level!s:7s} DIFFERS')
        try:
            render(enable_thinking=True, reasoning_effort='no-such-level', **cases['user'])
            print('[oracle]   the template accepts any level name')
        except Exception as e:  # noqa
            print(f'[oracle]   an unknown level: {e}')
        print(f'[oracle]   reasoning effort, every level over every conversation: {"same" if ok else "DIFFERS"}')

    # 2. the format, at the level with no instruction
    quiet = {'reasoning_effort': 'medium'} if tok.reasoning_efforts else {}
    for name, kw in cases.items():
        for think in (True, False):
            theirs = render(enable_thinking=think, **kw, **quiet)
            mine = ours(kw, think)
            if theirs == mine:
                print(f'[oracle]   {name:22s} thinking={think!s:5s} same')
                continue
            ok = False
            d = next((i for i, (a, b) in enumerate(zip(theirs, mine)) if a != b), min(len(theirs), len(mine)))
            print(f'[oracle]   {name:22s} thinking={think!s:5s} DIFFERS at {d}: template '
                  f'{json.dumps(theirs[max(0, d - 30):d + 80])} / ours {json.dumps(mine[max(0, d - 30):d + 80])}')

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
