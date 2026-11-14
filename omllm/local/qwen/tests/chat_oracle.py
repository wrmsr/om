"""
A checkpoint's own chat template as the oracle for the hand-written chat format (serve/chat.py, tokenizer.py): the
template is rendered with Jinja for a set of conversations and compared with ours, character for character.

    python -m omllm.local.qwen.tests.chat_oracle --model qwen3.8:27b

Two reports. The reasoning-effort instruction (`Tokenizer.reasoning_instruction`) against what the template inserts for
each level -- which must agree, and the exit status says whether it does. And every conversation at the template's
no-instruction level against `render_chat`, where the first difference of each is printed: the template's tool format
(`<function=name>` / `<parameter=key>` blocks, its own preamble, the system message after the tools), its `<think>`
blocks in history and in the generation prompt are not what serve/chat.py renders yet (NEXT.md 0).

The template is treated as a black box: rendered, never read. Jinja is needed only here.
"""
import argparse
import json
import sys
import typing as ta

from ..load.weights import open_source
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
    args = {'path': 'a/b.py', 'limit': 3}
    call = {'id': 'c1', 'type': 'function', 'function': {'name': 'read_file', 'arguments': args}}
    user = {'role': 'user', 'content': 'Hi'}
    system = {'role': 'system', 'content': 'SYS'}
    loop = [
        system,
        user,
        {'role': 'assistant', 'content': 'Let me look.', 'reasoning_content': 'hm', 'tool_calls': [call]},
        {'role': 'tool', 'content': 'R1', 'tool_call_id': 'c1'},
        {'role': 'assistant', 'content': 'done', 'reasoning_content': 'ok'},
        {'role': 'user', 'content': 'More'},
    ]
    return {
        'user': dict(messages=[user]),
        'system + user': dict(messages=[system, user]),
        'two turns': dict(messages=[user, {'role': 'assistant', 'content': 'Yo'}, {'role': 'user', 'content': 'More'}]),
        'tools': dict(messages=[user], tools=ORACLE_TOOLS),
        'system + tools': dict(messages=[system, user], tools=ORACLE_TOOLS),
        'tool loop': dict(messages=loop, tools=ORACLE_TOOLS),
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

    # 1. reasoning effort: what the template adds for each level over its level with no instruction
    ok = True
    print(f'[oracle] {args.model}: the template takes a reasoning effort: {tok.reasoning_efforts}')
    if tok.reasoning_efforts:
        quiet = next(k for k, v in REASONING_EFFORT_INSTRUCTIONS.items() if v is None)
        for name, kw in cases.items():
            base = render(enable_thinking=True, reasoning_effort=quiet, **kw)
            ours_base = render_chat(_json_args(kw['messages']), kw.get('tools'), preserve_thinking=False)
            for level in [None, *REASONING_EFFORT_INSTRUCTIONS]:
                extra = {} if level is None else {'reasoning_effort': level}
                got = render(enable_thinking=True, **kw, **extra)
                instr = tok.reasoning_instruction(level)
                want = render_chat(
                    _json_args(kw['messages']),
                    kw.get('tools'),
                    preserve_thinking=False,
                    reasoning_instruction=instr,
                )
                # the same text inserted at the head of the system turn in both renderings
                added_theirs = len(got) - len(base)
                added_ours = len(want) - len(ours_base)
                head = len('<|im_start|>')
                own_turn = not base.startswith('<|im_start|>system')
                at = head if own_turn else head + len('system\n')
                theirs = got[at:at + added_theirs]
                mine = want[at:at + added_ours]
                same = theirs == mine and got == base[:at] + theirs + base[at:]
                ok = ok and same
                print(f'[oracle]   {name:15s} effort={level!s:7s} {"same" if same else "DIFFERS"}'
                      + ('' if same else f': template {json.dumps(theirs)} / ours {json.dumps(mine)}'))
            off = render(enable_thinking=False, reasoning_effort='low', **kw) == render(enable_thinking=False, **kw)
            ok = ok and off
        try:
            render(enable_thinking=True, reasoning_effort='no-such-level', **cases['user'])
            print('[oracle]   the template accepts any level name')
        except Exception as e:  # noqa
            print(f'[oracle]   an unknown level: {e}')

    # 2. the rest of the format, at the level with no instruction
    print('[oracle] the format itself, against render_chat (thinking on / off):')
    extra = {'reasoning_effort': 'medium'} if tok.reasoning_efforts else {}
    for name, kw in cases.items():
        for think in (True, False):
            theirs = render(enable_thinking=think, **kw, **extra)
            mine = render_chat(
                _json_args(kw['messages']),
                kw.get('tools'),
                enable_thinking=think,
                preserve_thinking=False,
            )
            if theirs == mine:
                print(f'[oracle]   {name:15s} thinking={think!s:5s} same')
                continue
            d = next((i for i, (a, b) in enumerate(zip(theirs, mine)) if a != b), min(len(theirs), len(mine)))
            print(f'[oracle]   {name:15s} thinking={think!s:5s} differs at {d}: template '
                  f'{json.dumps(theirs[max(0, d - 20):d + 70])} / ours {json.dumps(mine[max(0, d - 20):d + 70])}')

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
