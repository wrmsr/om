"""
chat.py: rendering (system, tools, tool calls / results, thinking preserved or stripped) and parsing (final and
streaming) of Qwen's chat format.

Run:  python -m pytest omllm/local/qwen/tests/test_chat.py -q      or      python -m omllm.local.qwen.tests.test_chat
"""
import json

from ..chat import StreamParser
from ..chat import parse_output
from ..chat import render_assistant_turn
from ..chat import render_chat


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
        '<think>\nlet me\nsee\n</think>\n\nHello <b> world\n'
        '<tool_call>\n{"name": "f", "arguments": {}}\n</tool_call>'
    )
    for step in (1, 3, 7, len(text)):
        sp = StreamParser()
        events = []
        for i in range(0, len(text), step):
            events += sp.feed(text[i:i + step])
        events += sp.finish()
        reasoning = ''.join(p for k, p in events if k == 'reasoning')
        content = ''.join(p for k, p in events if k == 'content')
        calls = [p for k, p in events if k == 'tool_call']
        assert reasoning.rstrip('\n') == 'let me\nsee', (step, reasoning)
        assert content == 'Hello <b> world\n', (step, content)
        assert len(calls) == 1 and calls[0]['function']['name'] == 'f', (step, calls)


if __name__ == '__main__':
    test_render_basic()
    test_render_tools_and_calls()
    test_render_thinking_policy()
    test_parse_output()
    test_stream_parser()
    print('chat rendering / parsing OK')
