"""
chat.py: rendering (system, tools, tool calls / results, thinking preserved or stripped) and parsing (final and
streaming) of Qwen's chat format.
"""
import json

from ..serve.chat import StreamParser
from ..serve.chat import parse_output
from ..serve.chat import render_assistant_turn
from ..serve.chat import render_chat


##


TOOL = {
    'type': 'function',
    'function': {
        'name': 'get_weather',
        'description': 'Weather for a city',
        'parameters': {'type': 'object', 'properties': {'city': {'type': 'string'}}, 'required': ['city']},
    },
}


def test_render_basic():
    s = render_chat([{'role': 'user', 'content': 'hi'}], enable_thinking=False)
    assert s == '<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    s = render_chat([{'role': 'system', 'content': 'be terse'}, {'role': 'user', 'content': 'hi'}])
    assert s == '<|im_start|>system\nbe terse<|im_end|>\n<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\n'


def test_render_tools_and_calls():
    msgs = [
        {'role': 'system', 'content': 'sys'},
        {'role': 'user', 'content': 'weather in Oslo?'},
        {
            'role': 'assistant',
            'content': '',
            'reasoning_content': 'need the tool',
            'tool_calls': [
                {'id': 'c1', 'type': 'function', 'function': {'name': 'get_weather', 'arguments': '{"city": "Oslo"}'}},
            ],
        },
        {'role': 'tool', 'tool_call_id': 'c1', 'content': '{"temp": 4}'},
        {'role': 'tool', 'tool_call_id': 'c2', 'content': 'second'},
    ]
    s = render_chat(msgs, [TOOL])  # type: ignore
    assert s.startswith('<|im_start|>system\nsys\n\n# Tools\n\n')
    assert '<tools>\n' + json.dumps(TOOL, ensure_ascii=False) + '\n</tools>' in s
    assert (
        '<|im_start|>assistant\n<think>\nneed the tool\n</think>\n\n'
        '<tool_call>\n{"name": "get_weather", "arguments": {"city": "Oslo"}}\n</tool_call><|im_end|>\n'
    ) in s
    # consecutive tool results share one user turn
    assert (
        '<|im_start|>user\n<tool_response>\n{"temp": 4}\n</tool_response>\n'
        '<tool_response>\nsecond\n</tool_response><|im_end|>\n'
    ) in s
    assert s.endswith('<|im_start|>assistant\n')


def test_render_thinking_policy():
    msgs = [
        {'role': 'user', 'content': 'a'},
        {'role': 'assistant', 'content': '<think>\nr1\n</think>\n\nA1'},
        {'role': 'user', 'content': 'b'},
        {'role': 'assistant', 'content': 'A2', 'reasoning_content': 'r2'},
        {'role': 'user', 'content': 'c'},
    ]
    kept = render_chat(msgs, preserve_thinking=True)
    assert '<think>\nr1\n</think>\n\nA1' in kept and '<think>\nr2\n</think>\n\nA2' in kept
    stripped = render_chat(msgs, preserve_thinking=False)
    assert 'r1' not in stripped and 'r2' not in stripped
    assert '<|im_start|>assistant\nA1<|im_end|>' in stripped
    # the rendering of a turn is position-independent when preserving, so it can be memoised by its string
    turn = render_assistant_turn(msgs[1], with_reasoning=True)
    assert turn == '<|im_start|>assistant\n<think>\nr1\n</think>\n\nA1<|im_end|>\n'
    assert kept.count(turn) == 1


def test_parse_output():
    p = parse_output(
        '<think>\nplan\n</think>\n\nHere:\n'
        '<tool_call>\n{"name": "get_weather", "arguments": {"city": "Oslo"}}\n</tool_call>',
    )
    assert p.reasoning == 'plan' and p.content == 'Here:'
    assert p.tool_calls == [
        {'id': 'call_0', 'type': 'function', 'function': {'name': 'get_weather', 'arguments': '{"city": "Oslo"}'}},
    ]
    p = parse_output('plain answer')
    assert p.reasoning is None and p.content == 'plain answer' and p.tool_calls == []
    p = parse_output('<tool_call>\nnot json\n</tool_call>rest')
    assert p.tool_calls == [] and p.content == 'rest'


def test_stream_parser():
    text = (
        '<think>\n'
        'let me\nsee\n'
        '</think>\n'
        '\n'
        'Hello <b> world\n'
        '<tool_call>\n'
        '{"name": "f", "arguments": {}}\n'
        '</tool_call>'
        '<tool_call>\n'
        '{"name": "shell", "arguments": {"command": "echo \\"}\\" {} }", "n": [1, {"a": 2}]}}\n'
        '</tool_call>'
    )
    for step in (1, 3, 7, len(text)):
        sp = StreamParser()
        events = []
        for i in range(0, len(text), step):
            events += sp.feed(text[i:i + step])
        events += sp.finish()
        reasoning = ''.join(p for k, p in events if k == 'reasoning')
        content = ''.join(p for k, p in events if k == 'content')
        assert reasoning.rstrip('\n') == 'let me\nsee', (step, reasoning)
        assert content == 'Hello <b> world\n', (step, content)
        # tool calls stream as a head (id, name, empty arguments) followed by argument pieces, merged by index
        calls: dict[int, dict] = {}
        for k, p in events:
            if k != 'tool_call':
                continue
            cur = calls.setdefault(p['index'], {'id': None, 'name': '', 'arguments': ''})
            if p.get('id'):
                assert cur['id'] is None, (step, 'two heads')  # the head comes once
                cur['id'] = p['id']
                cur['name'] = p['function']['name']
            cur['arguments'] += p['function'].get('arguments') or ''
        assert [calls[i]['name'] for i in sorted(calls)] == ['f', 'shell'], (step, calls)
        assert json.loads(calls[0]['arguments']) == {} and calls[0]['id'] == 'call_0', (step, calls[0])
        assert json.loads(calls[1]['arguments']) == {'command': 'echo "}" {} }', 'n': [1, {'a': 2}]}, (step, calls[1])
        assert not calls[1]['arguments'][0].isspace() and calls[1]['arguments'].endswith('}'), (step, calls[1])


def test_reasoning_effort():
    """
    A checkpoint whose chat template takes a reasoning effort gets the level's instruction at the head of the system
    turn -- its default level when none is asked for, none at 'medium' or with thinking off -- and a request's
    `reasoning_effort` reaches it: the template's names as they are, OpenAI's others as the nearest, 'none' as thinking
    off.
    """

    from ..serve.serving import Engine
    from ..serve.serving import Request
    from ..serve.serving import SamplingDefaults
    from ..serve.serving import reasoning_effort_of
    from ..tokenizer import DEFAULT_REASONING_EFFORT
    from ..tokenizer import REASONING_EFFORT_INSTRUCTIONS
    from .test_grammar import _tokenizer

    low, top = REASONING_EFFORT_INSTRUCTIONS['low'], REASONING_EFFORT_INSTRUCTIONS[DEFAULT_REASONING_EFFORT]
    assert low and top and REASONING_EFFORT_INSTRUCTIONS['medium'] is None

    # where the instruction goes
    user = [{'role': 'user', 'content': 'hi'}]
    plain = render_chat(user)
    assert render_chat(user, reasoning_instruction=None) == plain
    assert render_chat(user, reasoning_instruction=low) == f'<|im_start|>system\n{low}<|im_end|>\n' + plain
    sys_msgs = [{'role': 'system', 'content': 'SYS'}, *user]
    assert render_chat(sys_msgs, reasoning_instruction=low).startswith(f'<|im_start|>system\n{low}\n\nSYS<|im_end|>\n')
    with_tools = render_chat(sys_msgs, [TOOL], reasoning_instruction=low)
    assert with_tools == render_chat(sys_msgs, [TOOL]).replace('system\nSYS', f'system\n{low}\n\nSYS', 1)
    tools_only = render_chat(user, [TOOL], reasoning_instruction=low)
    assert tools_only == render_chat(user, [TOOL]).replace('system\n', f'system\n{low}\n\n', 1)

    # the tokenizer knows whether the checkpoint's template has the switch
    without = _tokenizer()
    assert not without.reasoning_efforts and without.reasoning_instruction('low') is None
    assert without.apply_chat(user, think=True, reasoning_effort='low') == without.apply_chat(user, think=True)
    tok = _tokenizer()
    tok.chat_template = '{%- if reasoning_effort is defined %}...{%- endif %}'
    assert tok.reasoning_efforts
    assert tok.reasoning_instruction() == top and tok.reasoning_instruction('xhigh') == top
    assert tok.reasoning_instruction('low') == low and tok.reasoning_instruction('medium') is None
    assert tok.reasoning_instruction('low', think=False) is None
    assert tok.apply_chat(user, think=True).startswith(f'<|im_start|>system\n{top}<|im_end|>\n<|im_start|>user\n')
    assert tok.apply_chat(sys_msgs, think=True, reasoning_effort='low').startswith(f'<|im_start|>system\n{low}\n\nSYS')
    assert tok.apply_chat(user) == '<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    # a continuation of a rendered conversation gets no second instruction; an opened block when asked
    more = tok.apply_chat(user, think=True, continuation=True)
    assert more == '<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\n'
    assert tok.apply_chat(user, think=True, continuation=True, open_think=True) == more + '<think>\n'
    assert tok.apply_chat(user, open_think=True) == tok.apply_chat(user)  # (thinking off: nothing to open)
    try:
        tok.reasoning_instruction('high')
        raise AssertionError('accepted a level the template does not have')
    except ValueError:
        pass

    # a request's field
    assert reasoning_effort_of(None) == (None, None)
    assert reasoning_effort_of('low') == ('low', None) and reasoning_effort_of('XHIGH') == ('xhigh', None)
    assert reasoning_effort_of('high') == ('xhigh', None) and reasoning_effort_of('minimal') == ('low', None)
    assert reasoning_effort_of('none') == (None, False)
    try:
        reasoning_effort_of('enormous')
        raise AssertionError('accepted an unknown effort')
    except ValueError:
        pass

    d = SamplingDefaults()
    body: dict = {'messages': user}
    assert Request.from_json(body, d, True).reasoning_effort is None
    assert Request.from_json({**body, 'reasoning_effort': 'high'}, d, True).reasoning_effort == 'xhigh'
    via_kwargs = Request.from_json({**body, 'chat_template_kwargs': {'reasoning_effort': 'low'}}, d, True)
    assert via_kwargs.reasoning_effort == 'low'
    off = Request.from_json({**body, 'reasoning_effort': 'none'}, d, True)
    assert off.reasoning_effort is None and not off.enable_thinking
    assert Request.from_json({**body, 'reasoning_effort': 'none', 'enable_thinking': True}, d, True).enable_thinking

    # the engine: its default level, a request's, thinking off
    def prompt(engine, **extra):
        return engine.render(Request.from_json({**body, **extra}, d, engine.enable_thinking))

    eng = Engine(None, tok, log=None)  # type: ignore[arg-type]
    assert prompt(eng).startswith(f'<|im_start|>system\n{top}<|im_end|>\n')
    assert prompt(eng, reasoning_effort='low').startswith(f'<|im_start|>system\n{low}<|im_end|>\n')
    assert prompt(eng, reasoning_effort='medium') == plain
    assert prompt(eng, reasoning_effort='none') == render_chat(user, enable_thinking=False)
    assert prompt(eng, enable_thinking=False) == render_chat(user, enable_thinking=False)
    assert prompt(Engine(None, tok, reasoning_effort='medium', log=None)) == plain  # type: ignore[arg-type]
    low_eng = Engine(None, tok, reasoning_effort='low', log=None)  # type: ignore[arg-type]
    assert prompt(low_eng).startswith(f'<|im_start|>system\n{low}<|im_end|>\n')
    assert prompt(low_eng, reasoning_effort='xhigh').startswith(f'<|im_start|>system\n{top}<|im_end|>\n')

    # a checkpoint without the switch is rendered as before, whatever is asked
    assert prompt(Engine(None, without, log=None), reasoning_effort='low') == plain  # type: ignore[arg-type]


def test_open_think():
    """
    The generation prompt that opens the reasoning block (as the checkpoints' templates render it) and its readers:
    the parsers take the answer as starting inside the block, and so do the grammar's controllers -- a forced tool
    call or a JSON value waits for the block the prompt opened to close.
    """

    from ..constrain.grammar import JsonConstraint
    from ..constrain.grammar import ToolConstraint
    from ..serve.chat import THINK_OPEN
    from .test_grammar import TOOLS
    from .test_grammar import _tokenizer

    user = [{'role': 'user', 'content': 'hi'}]
    assert render_chat(user, open_think=True) == render_chat(user) + THINK_OPEN
    assert render_chat(user, enable_thinking=False, open_think=True) == render_chat(user, enable_thinking=False)

    # the answer, with and without the block's opening
    body = 'let me\nsee\n</think>\n\nHello\n<tool_call>\n{"name": "f", "arguments": {"a": 1}}\n</tool_call>'
    whole = parse_output(THINK_OPEN + body)
    inside = parse_output(body, think_open=True)
    assert inside == whole and inside.reasoning == 'let me\nsee' and inside.content == 'Hello'
    assert len(inside.tool_calls) == 1
    for step in (1, 3, 7, len(body)):
        ref, got = StreamParser(), StreamParser(think_open=True)
        want = ref.feed(THINK_OPEN)
        events = []
        for i in range(0, len(body), step):
            want += ref.feed(body[i:i + step])
            events += got.feed(body[i:i + step])
        assert events + got.finish() == want + ref.finish(), step
        assert ''.join(p for k, p in events if k == 'reasoning').rstrip('\n') == 'let me\nsee', step

    # the controllers
    tok = _tokenizer()
    forced = ToolConstraint(tok, TOOLS, 'required', thinking=True, think_open=True)
    assert forced.allowed() is None  # reasoning, already under way: unconstrained
    for t in tok.encode('thoughts</think>'):
        forced.feed(t)
    assert forced.allowed() is not None  # and now the call is due
    assert ToolConstraint(tok, TOOLS, 'required', thinking=False, think_open=True).allowed() is not None

    js = JsonConstraint(tok, {}, thinking=True, think_open=True)
    states = [js.in_think]
    assert not (js.allowed() or frozenset()) & js.end_ids  # no ending the turn inside the block
    for t in tok.encode('thoughts</think>'):
        js.feed(t)
    states.append(js.in_think)
    for t in tok.encode('{"a": 1}'):
        js.feed(t)
    assert states == [True, False]
    assert js.state is not None and js.acc.can_end(js.state) and (js.allowed() or frozenset()) & js.end_ids

    # a block that never closes is reasoning to the end, not content -- to both parsers
    cut = parse_output('still thinking', think_open=True)
    assert cut.reasoning == 'still thinking' and cut.content == '' and not cut.tool_calls
    assert parse_output('<think>\nstill thinking').reasoning == 'still thinking'
    sp = StreamParser(think_open=True)
    tail = sp.feed('still thinking') + sp.finish()
    assert all(k == 'reasoning' for k, _ in tail) and ''.join(p for _, p in tail) == 'still thinking'


FUNCTION_TOOL = {
    'type': 'function',
    'function': {
        'name': 'f',
        'description': 'd',
        'parameters': {'type': 'object', 'properties': {
            'a': {'type': 'integer'}, 'b': {'type': 'string'}, 's': {'type': 'string'}, 't': {'type': 'boolean'},
            'n': {'type': ['string', 'null']}, 'l': {'type': 'array'}, 'd': {'type': 'object'},
        }},
    },
}


def test_function_format():
    """
    The checkpoints' own chat formats (`QWEN35`, `QWEN38`): the strings below are what their templates render
    (tests/chat_oracle.py compares whole conversations against the templates themselves when a checkpoint is at hand),
    and what is rendered parses back, whole and streamed.
    """

    from ..serve.chat import CHAT_FORMATS
    from ..serve.chat import FUNCTION_TOOLS_POSTAMBLE
    from ..serve.chat import FUNCTION_TOOLS_PREAMBLE
    from ..serve.chat import LEGACY
    from ..serve.chat import QWEN35
    from ..serve.chat import QWEN38
    from ..serve.chat import chat_format_for
    from .test_grammar import _tokenizer

    # which format a checkpoint gets
    tok = _tokenizer()
    assert chat_format_for(tok) is LEGACY
    tok.chat_template = '... <function={{ name }}> ...'
    assert chat_format_for(tok) is QWEN35
    tok.chat_template += ' {% if reasoning_effort %}'
    assert chat_format_for(tok) is QWEN38
    assert set(CHAT_FORMATS) == {'legacy', 'qwen3.5', 'qwen3.8'}

    user = {'role': 'user', 'content': 'Q'}

    def call(args, i='c1'):
        return {'id': i, 'type': 'function', 'function': {'name': 'f', 'arguments': json.dumps(args)}}

    # the system turn: the tools first, then the system message; the generation prompt opens the reasoning block
    for fmt in (QWEN35, QWEN38):
        text = render_chat([{'role': 'system', 'content': 'SYS'}, user], [FUNCTION_TOOL], fmt=fmt)
        tools_block = FUNCTION_TOOLS_PREAMBLE + '\n' + json.dumps(FUNCTION_TOOL) + FUNCTION_TOOLS_POSTAMBLE
        assert text == (
            '<|im_start|>system\n' + tools_block + '\n\nSYS<|im_end|>\n'
            '<|im_start|>user\nQ<|im_end|>\n<|im_start|>assistant\n<think>\n'
        ), fmt.name
        assert tools_block.startswith('# Tools\n\nYou have access to the following functions:\n\n<tools>\n{"type"')
        assert tools_block.endswith('do not tell the user about function calls\n</IMPORTANT>')
        assert render_chat([user], fmt=fmt, enable_thinking=False).endswith('assistant\n<think>\n\n</think>\n\n')
        assert render_chat([user], fmt=fmt, open_think=False).endswith('<|im_start|>assistant\n')

    # an assistant turn: reasoning block, content, a blank line, the calls one per line
    turn = {'role': 'assistant', 'content': 'C', 'reasoning_content': 'R',
            'tool_calls': [call({'a': 1}), call({'b': 'x'}, 'c2')]}
    want = (
        '<|im_start|>assistant\n<think>\nR\n</think>\n\nC\n\n'
        '<tool_call>\n<function=f>\n<parameter=a>\n1\n</parameter>\n</function>\n</tool_call>\n'
        '<tool_call>\n<function=f>\n<parameter=b>\nx\n</parameter>\n</function>\n</tool_call><|im_end|>\n'
    )
    assert render_assistant_turn(turn, fmt=QWEN38) == want and render_assistant_turn(turn, fmt=QWEN35) == want

    # argument values: a string as it is, anything else as JSON -- but for qwen3.5's True / False / None
    values = {'s': 'two\nlines "q" <b>', 'b': '', 'a': 3, 't': True, 'n': None, 'l': [1, 'x', True], 'd': {'k': None}}
    bare = {'role': 'assistant', 'content': None, 'tool_calls': [call(values)]}
    body = (
        '<tool_call>\n<function=f>\n'
        '<parameter=s>\ntwo\nlines "q" <b>\n</parameter>\n'
        '<parameter=b>\n\n</parameter>\n'
        '<parameter=a>\n3\n</parameter>\n'
        '<parameter=t>\n{t}\n</parameter>\n'
        '<parameter=n>\n{n}\n</parameter>\n'
        '<parameter=l>\n[1, "x", true]\n</parameter>\n'
        '<parameter=d>\n{{"k": null}}\n</parameter>\n'
        '</function>\n</tool_call>'
    )
    head = '<|im_start|>assistant\n<think>\n\n</think>\n\n'
    assert render_assistant_turn(bare, fmt=QWEN38) == head + body.format(t='true', n='null') + '<|im_end|>\n'
    assert render_assistant_turn(bare, fmt=QWEN35) == head + body.format(t='True', n='None') + '<|im_end|>\n'

    # reasoning in the history. qwen3.8's template keeps a block in every turn (our preserve_thinking); qwen3.5's
    # drops the reasoning of turns before the last user query and keeps a block, empty or not, in those after it
    hist: list[dict] = [
        user, {'role': 'assistant', 'content': 'A1', 'reasoning_content': 'R1'}, {'role': 'user', 'content': 'Q2'},
        {'role': 'assistant', 'content': '', 'tool_calls': [call({'a': 1})]}, {'role': 'tool', 'content': 'RES'},
    ]
    one_call = '<tool_call>\n<function=f>\n<parameter=a>\n1\n</parameter>\n</function>\n</tool_call>'
    tail = (
        '<|im_end|>\n<|im_start|>user\nQ2<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n' + one_call +
        '<|im_end|>\n<|im_start|>user\n<tool_response>\nRES\n</tool_response><|im_end|>\n'
        '<|im_start|>assistant\n<think>\n'
    )
    start = '<|im_start|>user\nQ<|im_end|>\n<|im_start|>assistant\n'
    assert render_chat(hist, fmt=QWEN38) == start + '<think>\nR1\n</think>\n\nA1' + tail
    assert render_chat(hist, fmt=QWEN35, preserve_thinking=False) == start + 'A1' + tail
    assert render_chat(hist, fmt=QWEN35) == start + '<think>\nR1\n</think>\n\nA1' + tail  # (ours: the prefix stays)

    # back again: a parameter's text is typed by its schema
    for fmt in (QWEN35, QWEN38):
        text = render_assistant_turn({**bare, 'content': 'C', 'reasoning_content': 'R'}, fmt=fmt)
        text = text[len('<|im_start|>assistant\n'):-len('<|im_end|>\n')]
        got = parse_output(text, fmt=fmt, tools=[FUNCTION_TOOL])
        assert got.reasoning == 'R' and got.content == 'C' and len(got.tool_calls) == 1, fmt.name
        assert got.tool_calls[0]['function']['name'] == 'f'
        assert json.loads(got.tool_calls[0]['function']['arguments']) == values, fmt.name
        assert parse_output(text[len('<think>\n'):], think_open=True, fmt=fmt, tools=[FUNCTION_TOOL]) == got

        for step in (1, 3, 7, 50, len(text)):
            sp = StreamParser(fmt=fmt, tools=[FUNCTION_TOOL])
            events = []
            for i in range(0, len(text), step):
                events += sp.feed(text[i:i + step])
            events += sp.finish()
            assert ''.join(p for k, p in events if k == 'reasoning').strip('\n') == 'R', (fmt.name, step)
            assert ''.join(p for k, p in events if k == 'content').strip('\n') == 'C', (fmt.name, step)
            calls = [p for k, p in events if k == 'tool_call']
            assert calls[0]['function'] == {'name': 'f', 'arguments': ''} and calls[0]['id'] == 'call_0'
            joined = ''.join(c['function']['arguments'] for c in calls)
            assert joined == got.tool_calls[0]['function']['arguments'], (fmt.name, step, joined)
            if step <= 3:  # a string parameter streams as it is written, not when its block closes: many pieces
                assert len(calls) > 2 * len(values), (fmt.name, step, len(calls))

    def args_of(block: str, tools=(FUNCTION_TOOL,)) -> dict:
        (tc,) = parse_output(block, fmt=QWEN38, tools=list(tools)).tool_calls
        return json.loads(tc['function']['arguments'])

    def block(*params: tuple[str, str]) -> str:
        inner = ''.join(f'<parameter={k}>\n{v}\n</parameter>\n' for k, v in params)
        return f'<tool_call>\n<function=f>\n{inner}</function>\n</tool_call>'

    # a string parameter is its text whatever it looks like; others are JSON, in either spelling of the literals
    typed = args_of(block(('s', '3'), ('a', '3'), ('t', 'True'), ('n', 'None')))
    assert typed == {'s': '3', 'a': 3, 't': True, 'n': None}
    assert args_of(block(('s', 'true'), ('t', 'false'), ('n', 'null'))) == {'s': 'true', 't': False, 'n': None}
    assert args_of(block(('n', 'some text'), ('s', '  padded  \n'))) == {'n': 'some text', 's': '  padded  \n'}
    # an undeclared parameter, or an unknown function: JSON when it is JSON, text otherwise
    loose = args_of(block(('x', '{"k": 1}'), ('y', 'plain'), ('z', '"quoted"')))
    assert loose == {'x': {'k': 1}, 'y': 'plain', 'z': '"quoted"'}
    assert args_of(block(('a', '7')), tools=()) == {'a': 7}
    assert args_of('<tool_call>\n<function=f>\n</function>\n</tool_call>') == {}
    # two calls, content between and around them
    two = parse_output('before\n\n' + block(('a', '1')) + '\n' + block(('a', '2')), fmt=QWEN38, tools=[FUNCTION_TOOL])
    assert two.content == 'before'
    assert [json.loads(c['function']['arguments']) for c in two.tool_calls] == [{'a': 1}, {'a': 2}]
    assert [c['id'] for c in two.tool_calls] == ['call_0', 'call_1']
    # the legacy syntax is not this format's (and the other way about)
    assert not parse_output('<tool_call>\n{"name": "f", "arguments": {}}\n</tool_call>', fmt=QWEN38).tool_calls
    assert not parse_output(block(('a', '1'))).tool_calls
