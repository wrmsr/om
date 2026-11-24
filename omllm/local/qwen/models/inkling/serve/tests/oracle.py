"""
An Inkling 2 checkpoint's own chat template as the oracle for the hand-written renderer
(models/inkling/serve/protocols.py): the template is rendered with Jinja for a set of conversations -- tools, calls with
arguments of every type, results, reasoning in the history, every reasoning effort -- and compared with ours, character
for character.

    python -m omllm.local.qwen.models.inkling.serve.tests.oracle --model ~/hf/Inkling-2-Mini [--write-cases]

The exit status says whether they agree. The template is treated as a black box: rendered, never read. Where this
code departs from it on purpose the oracle does not go: tool-call arguments given as JSON text (the template refuses
them; parsed here), a tool result that is not text, an image (refused here), and an assistant message's reasoning
under the key `reasoning` (read here as `reasoning_content` is). What the template refuses, ours must refuse too.

`--write-cases` prints the conversations with the template's renderings as the module the suite keeps
(models/inkling/serve/tests/templatecases.py), for a new checkpoint revision. Jinja is needed only here.
"""
import argparse
import json
import pprint
import sys
import typing as ta

from .....load.weights import open_source
from .....tokenizer import Tokenizer
from ..protocols import render_inkling2


##


def template_renderer(template: str) -> ta.Callable[..., str]:
    import jinja2
    import jinja2.ext
    import jinja2.sandbox

    def raise_exception(message: str) -> ta.NoReturn:
        raise jinja2.exceptions.TemplateError(message)

    def tojson(x: ta.Any, ensure_ascii: bool = False, **kw: ta.Any) -> str:
        return json.dumps(x, ensure_ascii=ensure_ascii, **kw)

    class GenerationTag(jinja2.ext.Extension):
        """
        `{% generation %} ... {% endgeneration %}`: the span a model generated, for the libraries that mask by it.
        Its body renders as it stands.
        """

        tags = {'generation'}  # noqa: RUF012

        def parse(self, parser: ta.Any) -> ta.Any:
            lineno = next(parser.stream).lineno
            body = parser.parse_statements(['name:endgeneration'], drop_needle=True)
            return jinja2.nodes.CallBlock(self.call_method('_body'), [], [], body).set_lineno(lineno)

        def _body(self, caller: ta.Callable[[], str]) -> str:
            return caller()

    env = jinja2.sandbox.ImmutableSandboxedEnvironment(
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[GenerationTag],
    )
    env.filters['tojson'] = tojson
    env.globals['raise_exception'] = raise_exception
    compiled = env.from_string(template)

    def render(**kw: ta.Any) -> str:
        return compiled.render(**kw)

    return render


ORACLE_TOOLS: list[dict] = [
    {'type': 'function', 'function': {'name': 'add', 'description': 'Add two numbers.', 'parameters': {
        'type': 'object',
        'properties': {'b': {'type': 'integer', 'description': 'second'}, 'a': {'type': 'integer'}},
        'required': ['a', 'b'],
    }}},
    {'type': 'function', 'function': {
        'name': 'read_file',
        'description': 'Read a file \u2014 naïve \u201ctext\u201d <b>&\'q\'</b>.',
        'parameters': {
            'type': 'object',
            'properties': {'path': {'type': 'string', 'enum': ['z', 'a']}},
            'required': ['path'],
            'zz': 1,
        },
        'strict': True,
    }},
]


def oracle_cases() -> dict[str, dict[str, ta.Any]]:
    """name -> {messages, tools, effort}: `effort` absent is the template's default."""

    def call(args: dict, name: str = 'add', i: str = 'c1') -> dict:
        return {
            'role': 'assistant',
            'content': '',
            'tool_calls': [{'id': i, 'type': 'function', 'function': {'name': name, 'arguments': args}}],
        }

    def calls(*cs: tuple[str, str, dict], **m: ta.Any) -> dict:
        return {
            'role': 'assistant',
            'tool_calls': [{'id': i, 'type': 'function', 'function': {'name': n, 'arguments': a}} for i, n, a in cs],
            **m,
        }

    def result(content: ta.Any, **kw: ta.Any) -> dict:
        return {'role': 'tool', 'content': content, **kw}

    user = {'role': 'user', 'content': 'Hi'}
    hello = {'role': 'assistant', 'content': 'Hello.'}
    add, read = ORACLE_TOOLS

    def system(text: str) -> dict:
        return {'role': 'system', 'content': text}

    def parts(*texts: str) -> list[dict]:
        return [{'type': 'text', 'text': t} for t in texts]

    cases: dict[str, tuple[list[dict], list[dict] | None]] = {
        'user': ([user], None),
        'sys+user': ([system('Be concise.'), user], None),
        'two sys': ([system('A'), system('B'), user], None),
        'only sys': ([system('A')], None),
        'sys late': ([user, hello, system('Late'), user], None),
        'reasoning': ([user, {**hello, 'reasoning_content': 'Check.'}, user], None),
        'empty reasoning': ([user, {**hello, 'reasoning_content': ''}, user], None),
        'reasoning only': ([user, {'role': 'assistant', 'content': '', 'reasoning_content': 'R'}, user], None),
        'asst last': ([user, hello], None),
        'asst empty': ([user, {'role': 'assistant', 'content': ''}, user], None),
        'asst none': ([user, {'role': 'assistant', 'content': None}, user], None),
        'asst parts': ([user, {'role': 'assistant', 'content': parts('A', 'B')}, user], None),
        'user parts': ([{'role': 'user', 'content': parts('A', 'B')}], None),
        'user empty': ([{'role': 'user', 'content': ''}], None),
        'tools': ([user], [add]),
        'tools 2 + sys': ([system('S'), user], [add, read]),
        'tools bare/minimal': (
            [user],
            [
                {'name': 'f', 'description': 'd', 'parameters': {'type': 'object', 'properties': {}}},
                {'type': 'function', 'function': {'name': 'g'}},
            ],
        ),
        'call + result': ([user, call({'b': 2, 'a': 1}), result('3', tool_call_id='c1')], [add]),
        'call + content + reasoning': (
            [
                user,
                calls(('c1', 'add', {'a': 1, 'b': 2}), content='Let me add.', reasoning_content='Need add.'),
                result('3', name='add'),
                {'role': 'assistant', 'content': 'It is 3.'},
            ],
            [add],
        ),
        'two calls, results swapped': (
            [
                user,
                calls(('a', 'f', {'x': 1}), ('b', 'g', {'y': 2}), content='C', reasoning_content='R'),
                result('B', tool_call_id='b'),
                result('A', tool_call_id='a'),
            ],
            None,
        ),
        'args nested/unsorted': (
            [user, call({'z': {'b': 1, 'a': {'d': 1, 'c': 2}}, 'y': [{'q': 1, 'p': 2}], 'A': 1.5})],
            None,
        ),
        'args strings': (
            [user, call({'s': "<a href='x'>&amp;</a> / \\ \t \u2028 \x7f é \u65e5\u672c \U0001f600 \"q\"\n"})],
            None,
        ),
        'args numbers': (
            [user, call({
                'i': 3, 'f': 1.5, 'big': 1e20, 'small': 1e-7, 'neg': -0.0, 't': True, 'n': None, 'e': [], 'o': {},
            })],
            None,
        ),
        'args empty': ([user, call({})], None),
        'tool no name': ([user, call({'x': 1}), result('3')], None),
        'tool unknown id': ([user, call({'x': 1}), result('A', tool_call_id='zzz')], None),
        'tool name wins': ([user, call({'x': 1}), result('A', tool_call_id='c1', name='other')], None),
        'tool parts': ([user, call({'x': 1}), result(parts('P1', 'P2'), tool_call_id='c1')], None),
        'tool first': ([result('x', name='f'), user], None),
        'long': (
            [
                system('S'),
                user,
                {**hello, 'reasoning_content': 'R1'},
                user,
                call({'a': 1, 'b': 2}),
                result('3', tool_call_id='c1'),
                {'role': 'assistant', 'content': 'Three.', 'reasoning_content': 'R2'},
                {'role': 'user', 'content': 'Thanks'},
            ],
            [add],
        ),
    }

    out: dict[str, dict[str, ta.Any]] = {
        name: {'messages': messages, 'tools': tools}
        for name, (messages, tools) in cases.items()
    }
    for effort in ('none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 0.5, 0, 0.99, 0.25, 0.0, 0.70, 0.123456):
        out[f'effort {effort!r}'] = {'messages': [user], 'tools': None, 'effort': effort}
    return out


# what the template refuses: ours must too
REFUSED_EFFORTS: ta.Sequence[ta.Any] = (1, '0.3', 'bogus', True, 'HIGH')


def _template_kwargs(case: ta.Mapping[str, ta.Any]) -> dict[str, ta.Any]:
    kw: dict[str, ta.Any] = {'messages': case['messages']}
    if case.get('tools') is not None:
        kw['tools'] = case['tools']
    if 'effort' in case:
        kw['reasoning_effort'] = case['effort']
    return kw


def cases_module(rendered: ta.Sequence[ta.Mapping[str, ta.Any]], source: str) -> str:
    head = (
        '# ruff: noqa: E501\n'
        '# flake8: noqa: E501\n'
        '"""\n'
        "Conversations as the released Inkling 2 checkpoint's chat template renders them: the template run as a black\n"
        f"box over each case's messages, tools and reasoning effort ({source}). `serve/protocols.py`'s renderer must\n"
        'give the same text; serve/tests/oracle.py makes the comparison live, against a checkpoint, and writes this\n'
        'module (`--write-cases`).\n'
        '"""\n'
        'import typing as ta\n'
        '\n'
        '\n'
        '##\n'
        '\n'
        '\n'
        'INKLING2_TEMPLATE_CASES: ta.Sequence[ta.Mapping[str, ta.Any]] = (\n'
    )
    body = pprint.pformat(list(rendered), width=112, compact=True, sort_dicts=False)
    body = body.encode('ascii', 'backslashreplace').decode('ascii')  # (escapes, where the texts are not ASCII)
    return head + ''.join('    ' + line + '\n' for line in body.splitlines()) + ')\n'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--write-cases', action='store_true')
    args = ap.parse_args()

    tok = Tokenizer.from_spec(open_source(args.model).tokenizer_spec)
    if not tok.chat_template:
        print(f'[oracle] {args.model} carries no chat template')
        sys.exit(2)
    render = template_renderer(tok.chat_template)

    ok = True
    rendered = []
    for name, case in oracle_cases().items():
        theirs = render(**_template_kwargs(case))
        mine = render_inkling2(case['messages'], case.get('tools'), effort=case.get('effort'))
        rendered.append({
            'name': name,
            'messages': case['messages'],
            'tools': case.get('tools'),
            'effort': case.get('effort'),
            'text': theirs,
        })
        if theirs == mine:
            if not args.write_cases:
                print(f'[oracle]   {name:28s} same')
            continue
        ok = False
        d = next((i for i, (a, b) in enumerate(zip(theirs, mine)) if a != b), min(len(theirs), len(mine)))
        print(
            f'[oracle]   {name:28s} DIFFERS at {d}: template {json.dumps(theirs[max(0, d - 30):d + 80])} / '
            f'ours {json.dumps(mine[max(0, d - 30):d + 80])}',
            file=sys.stderr,
        )

    user = [{'role': 'user', 'content': 'Hi'}]
    for effort in REFUSED_EFFORTS:
        refused = []
        for fn in (
                lambda e=effort: render(messages=user, reasoning_effort=e),
                lambda e=effort: render_inkling2(user, effort=e),
        ):
            try:
                fn()
                refused.append(False)
            except Exception:  # noqa
                refused.append(True)
        if refused != [True, True]:
            ok = False
            print(f'[oracle]   effort {effort!r}: refused by the template / by ours: {refused}', file=sys.stderr)

    if args.write_cases:
        sys.stdout.write(cases_module(rendered, f'`inkling2oracle --model {args.model} --write-cases`'))
    else:
        print(f'[oracle] {args.model}: {"same" if ok else "DIFFERS"}')

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
