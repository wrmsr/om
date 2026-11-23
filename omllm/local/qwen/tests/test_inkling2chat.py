"""
Inkling 2's chat protocol (serve/inkling2.py): prompts rendered as the checkpoint's template renders them, answers
read into reasoning, content and tool calls -- whole and streamed, however the text is cut -- and the serving engine
running on it: the protocol picked from the tokenizer, a follow-up's ids an extension of the first request's.
"""
import json
import tempfile
import typing as ta

import pytest

from ..api import ManualGenerationRunner
from ..arch.qwen35 import load_qwen35
from ..arch.tests.inkling2checkpoints import write_inkling2_checkpoint
from ..load.weights import open_source
from ..prefix.cache import PrefixCache
from ..serve.chatml import ChatmlProtocol
from ..serve.inkling2 import Inkling2ChatProtocol
from ..serve.inkling2 import Inkling2Reader
from ..serve.inkling2 import inkling2_effort_level
from ..serve.inkling2 import parse_inkling2
from ..serve.inkling2 import render_inkling2
from ..serve.inkling2 import render_inkling2_assistant
from ..serve.registry import chat_protocol_for
from ..serve.serving import Engine
from ..serve.serving import Request
from ..serve.serving import SamplingDefaults
from ..tokenizer import Tokenizer
from .inkling2templatecases import INKLING2_TEMPLATE_CASES
from .test_synthetic import tiny_tokenizer_fields


##


END = '<|content_model_end_sampling|>'
USER = {'role': 'user', 'content': 'Hi'}


def test_renders_as_the_template():
    for case in INKLING2_TEMPLATE_CASES:
        got = render_inkling2(case['messages'], case['tools'], effort=case['effort'])
        assert got == case['text'], case['name']

    # a conversation continued: neither the tools nor the effort again
    more = render_inkling2([USER], [{'name': 'f'}], continuation=True)
    assert more == '<|message_user|><|content_text|>Hi<|end_message|>'


def test_efforts():
    assert inkling2_effort_level(None) == 0.9 and inkling2_effort_level('max') == inkling2_effort_level('xhigh') == 0.99
    assert inkling2_effort_level(0) == 0 and inkling2_effort_level(0.25) == 0.25

    for bad in (1, '0.3', 'bogus', True, 'HIGH', -0.1, [0.5]):  # as the template refuses them
        with pytest.raises(ValueError, match='reasoning_effort'):
            render_inkling2([USER], effort=bad)


def test_departures_from_the_template():
    # an OpenAI client's arguments are JSON text: parsed, then written as an object's are
    call = {'id': 'c', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"b": 2, "a": 1}'}}
    turn = render_inkling2_assistant({'role': 'assistant', 'content': None, 'tool_calls': [call]})
    assert turn == (
        '<|message_model|>add<|content_invoke_tool_json|>{"name":"add","args":{"a":1,"b":2}}<|end_message|>' + END
    )

    with pytest.raises(ValueError, match='not JSON'):
        render_inkling2_assistant({'tool_calls': [{'function': {'name': 'f', 'arguments': '{oops'}}]})

    # a tool result that is not text is written as JSON
    result = render_inkling2([{'role': 'tool', 'name': 'f', 'content': {'k': [1, 2]}}], continuation=True)
    assert result == '<|message_tool|>f<|content_text|>{"k":[1,2]}<|end_message|>'

    with pytest.raises(ValueError, match='text-only'):
        render_inkling2([{'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': 'x'}}]}])
    with pytest.raises(ValueError, match='role'):
        render_inkling2([{'role': 'developer', 'content': 'x'}])


def _read(text: str, cuts: ta.Sequence[int] = ()) -> list:
    """The reader's deltas over `text` fed in pieces cut at `cuts`, merged: (reasoning, content, calls)."""

    reader = Inkling2Reader()
    events = []
    at = 0
    for c in [*cuts, len(text)]:
        events.extend(reader.feed(text[at:c]))
        at = c
    events.extend(reader.finish())

    reasoning = ''.join(p for k, p in events if k == 'reasoning')
    content = ''.join(p for k, p in events if k == 'content')
    calls: list[dict] = []
    for k, p in events:
        if k == 'tool_call':
            if 'id' in p:
                assert p['index'] == len(calls) and p['function']['arguments'] == ''
                calls.append({'id': p['id'], 'name': p['function']['name'], 'arguments': ''})
            else:
                calls[p['index']]['arguments'] += p['function']['arguments']
    return [reasoning, content, calls]


def test_reads_a_turn():
    think = '<|message_model|><|content_thinking|>Check <it>.<|end_message|>'
    text = '<|message_model|><|content_text|>Hello | there.<|end_message|>'
    add = (
        '<|message_model|>add<|content_invoke_tool_json|>'
        '{"name":"add","args":{"a":1,"b":{"c":[2,"}"]}}}<|end_message|>'
    )
    write = (
        '<|message_model|>write_file<|content_invoke_tool_json|>'
        '{"name": "write_file", "args": {"path": "a.py", "content": "x = {}\\n<|notatoken|> <| y"}}\n<|end_message|>'
    )

    p = parse_inkling2(think + text)
    assert (p.reasoning, p.content, p.tool_calls) == ('Check <it>.', 'Hello | there.', [])

    p = parse_inkling2(text)
    assert p.reasoning is None and p.content == 'Hello | there.'

    # several messages of a kind follow one another after a blank line; calls keep their order
    p = parse_inkling2(think + think + text + add + text + write)
    assert p.reasoning == 'Check <it>.\n\nCheck <it>.' and p.content == 'Hello | there.\n\nHello | there.'
    assert [c['function']['name'] for c in p.tool_calls] == ['add', 'write_file']
    assert [c['id'] for c in p.tool_calls] == ['call_0', 'call_1']
    assert json.loads(p.tool_calls[0]['function']['arguments']) == {'a': 1, 'b': {'c': [2, '}']}}
    assert json.loads(p.tool_calls[1]['function']['arguments']) == {
        'path': 'a.py',
        'content': 'x = {}\n<|notatoken|> <| y',
    }

    # however the stream is cut -- inside markers, the header, the JSON, a string's escapes -- the deltas are the same
    whole = think + add + text + write
    want = _read(whole)
    assert want[2][0] == {'id': 'call_0', 'name': 'add', 'arguments': '{"a":1,"b":{"c":[2,"}"]}}'}
    for cut in range(1, len(whole)):
        assert _read(whole, [cut]) == want, cut
    assert _read(whole, list(range(1, len(whole)))) == want  # a character at a time

    # a call's head goes out as soon as its message's header has named it, before any of the JSON
    reader = Inkling2Reader()
    events = reader.feed('<|message_model|>add<|content_invoke_tool_json|>{"na')
    assert [(k, p['function']['name']) for k, p in events] == [('tool_call', 'add')]

    # a call that names itself only in its JSON, or puts its arguments first, or is cut short
    p = parse_inkling2('<|message_model|><|content_invoke_tool_json|>{"name":"f","args":{"x":1}}<|end_message|>')
    assert [(c['function']['name'], c['function']['arguments']) for c in p.tool_calls] == [('f', '{"x":1}')]
    p = parse_inkling2('<|message_model|>f<|content_invoke_tool_json|>{"args":{"x":1},"name":"f"}<|end_message|>')
    assert [(c['function']['name'], json.loads(c['function']['arguments'])) for c in p.tool_calls] == [('f', {'x': 1})]
    p = parse_inkling2('<|message_model|>f<|content_invoke_tool_json|>{"name":"f","args":{}}<|end_message|>')
    assert p.tool_calls[0]['function']['arguments'] == '{}'
    p = parse_inkling2('<|message_model|><|content_invoke_tool_json|>{"name":"f","ar')  # the budget ran out
    assert p.tool_calls == [] and p.content == ''

    # an answer cut short mid-message is what there is of it; text outside any message is content
    assert parse_inkling2('<|message_model|><|content_thinking|>still thinki').reasoning == 'still thinki'
    assert parse_inkling2('stray').content == 'stray'


def test_round_trips():
    """An assistant message rendered for the history reads back as that message."""

    msgs: list[dict[str, ta.Any]] = [
        {'content': 'Hello.', 'reasoning_content': 'Check.'},
        {'content': 'Just this.'},
        {'content': None, 'reasoning_content': 'R', 'tool_calls': [
            {'id': 'call_0', 'type': 'function', 'function': {'name': 'add', 'arguments': '{"a":1,"b":2}'}},
            {'id': 'call_1', 'type': 'function', 'function': {'name': 'f', 'arguments': '{"s":"a\\n\\"b\\" é"}'}},
        ]},
    ]
    for m in msgs:
        turn = render_inkling2_assistant({'role': 'assistant', **m})
        assert turn.endswith(END)
        p = parse_inkling2(turn[:-len(END)])
        assert p.content == (m.get('content') or '') and p.reasoning == m.get('reasoning_content')
        assert p.tool_calls == (m.get('tool_calls') or [])


def _tokenizer(tmp: str) -> Tokenizer:
    write_inkling2_checkpoint(tmp)
    return Tokenizer.from_spec(open_source(tmp).tokenizer_spec)


def test_protocol():
    with tempfile.TemporaryDirectory() as tmp:
        tok = _tokenizer(tmp)
        assert tok.pre == 'inkling2' and tok.ignore_merges

        protocol = chat_protocol_for(tok)
        assert isinstance(protocol, Inkling2ChatProtocol) and protocol.name == 'inkling2'

        # where a turn ends: the end of sampling, not the end of a message
        end = tok.special[END]
        assert end in protocol.eos_ids and tok.special['<|end_message|>'] not in protocol.eos_ids
        assert protocol.close_answer([5, 6]) == [5, 6, end] and protocol.close_answer([5, end]) == [5, end]
        assert protocol.generation_prompt('anything') == '' and protocol.answer_prefix() == ''

        # the effort a prompt states: the request's, none with thinking off, else the server's
        def effort(p: Inkling2ChatProtocol, **kw: ta.Any) -> str:
            text = p.render([USER], **kw)
            return text[text.index('level: ') + 7:text.index('<|end_message|>')]

        assert effort(protocol) == '0.9' and effort(protocol, enable_thinking=False) == '0'
        assert effort(protocol, reasoning_effort='low') == '0.2' and effort(protocol, reasoning_effort=0.5) == '0.5'
        assert effort(protocol, enable_thinking=False, reasoning_effort='medium') == '0.7'
        low = Inkling2ChatProtocol(tok, reasoning_effort='low')
        assert effort(low) == '0.2' and effort(low, reasoning_effort='xhigh') == '0.99'
        assert low.describe()['reasoning_effort'] == 'low' and protocol.describe()['chat_format'] == 'inkling2'

        assert protocol.reasoning_effort(None) == (None, None) and protocol.reasoning_effort('low') == ('low', None)
        assert protocol.reasoning_effort('none') == ('none', False) and protocol.reasoning_effort(0.3) == (0.3, None)
        with pytest.raises(ValueError, match='reasoning_effort'):
            protocol.reasoning_effort('enormous')
        with pytest.raises(ValueError, match='reasoning_effort'):
            Inkling2ChatProtocol(tok, reasoning_effort='enormous')

        # every request has its grammar (tests/test_framed.py)
        tools = [{'type': 'function', 'function': {'name': 'f'}}]
        assert protocol.constraint(tools, 'auto', None) is not None
        assert protocol.constraint(None, None, {'type': 'json_object'}) is not None
        assert protocol.constraint(None, None, None) is not None

    # a tokenizer without the protocol's tokens speaks ChatML, and cannot be made to speak this
    tokens, types, merges = tiny_tokenizer_fields()
    qwen = Tokenizer.from_gguf_spec({
        'kind': 'gguf',
        'model': 'gpt2',
        'tokens': tokens,
        'token_type': [int(t) for t in types],
        'merges': merges,
    })
    assert isinstance(chat_protocol_for(qwen), ChatmlProtocol)
    with pytest.raises(ValueError, match='tokenizer has no'):
        Inkling2ChatProtocol(qwen)


def test_engine():
    """
    The serving engine on a synthetic Inkling 2 checkpoint (random weights: what it says is noise, read all the same):
    the protocol is the tokenizer's, a streamed answer is the unstreamed one, a follow-up resumes the first request's
    ids and its answer's, and a request the protocol cannot serve is refused before it is queued.
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        pytest.skip('torch not installed')

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        src = open_source(tmp)
        tok = Tokenizer.from_spec(src.tokenizer_spec)
        ops = TorchOps('cpu', capture_mode='static', triton=False)
        model = load_qwen35(src, ops, dtype='f32', verbose=False)

        pc = PrefixCache(ops, 1 << 30, 0)
        engine = Engine(
            ManualGenerationRunner(model, capacity=256, prefix_cache=pc),
            tok,
            prefix_cache=pc,
            defaults=SamplingDefaults(temperature=0.0, max_tokens=24),
            log=None,
        )
        assert isinstance(engine.protocol, Inkling2ChatProtocol)
        assert engine.describe_format() == {
            'chat_format': 'inkling2',
            'open_think': False,
            'reasoning_effort': 'high',
            'thinking': True,
        }
        engine.start()

        def request(body: dict) -> Request:
            req = Request.from_json(body, engine.defaults, engine.enable_thinking, engine.protocol.reasoning_effort)
            engine.check(req)
            return req

        msgs = [{'role': 'system', 'content': 'S'}, {'role': 'user', 'content': 'the thing in the tin'}]
        first = request({'messages': msgs, 'reasoning_effort': 'low'})
        assert engine.render(first) == (
            '<|message_system|><|content_text|>S<|end_message|>'
            '<|message_system|><|content_text|>Thinking effort level: 0.2<|end_message|>'
            '<|message_user|><|content_text|>the thing in the tin<|end_message|>'
        )
        res = engine.run_sync(first)
        assert res.completion_tokens == len(res.ids) > 0 and res.prompt_reused == 0
        assert res.finish_reason in ('stop', 'length', 'tool_calls')

        # the same request streamed: the deltas are the answer
        job = engine.submit(request({'messages': msgs, 'reasoning_effort': 'low', 'stream': True}))
        content, reasoning = '', ''
        while True:
            ev = job.events.get(timeout=60)
            if ev[0] == 'done':
                streamed = ev[1]
                break
            assert ev[0] == 'delta', ev
            if ev[1] == 'content':
                content += ev[2]
            elif ev[1] == 'reasoning':
                reasoning += ev[2]
        assert streamed.ids == res.ids
        assert (content, reasoning or None) == (res.content, res.reasoning)

        # a follow-up: the answer comes back as a message, and its ids are the ones generated
        answer = engine.message_json(res)
        more = [*msgs, answer, {'role': 'user', 'content': 'in the end'}]
        res2 = engine.run_sync(request({'messages': more, 'reasoning_effort': 'low'}))
        closed = len(engine.protocol.close_answer(res.ids))
        assert res2.prompt_reused >= res.prompt_tokens + len(res.ids), (res2.prompt_reused, res.prompt_tokens, closed)
        assert res2.prompt_tokens == res.prompt_tokens + closed + len(tok.encode(engine.protocol.render(
            more[-1:],
            continuation=True,
        )))

        for bad in (
                {'messages': msgs, 'reasoning_effort': 'enormous'},
                {'messages': [{'role': 'user', 'content': [{'type': 'image_url'}]}]},
        ):
            with pytest.raises(ValueError):  # noqa: PT011
                request(bad)
