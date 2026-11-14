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
