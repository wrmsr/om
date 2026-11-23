"""
Constrained decoding for a framed-message protocol (constrain/framed.py), on Inkling 2's: what the controllers offer
at each point of a turn; that whatever token sequence they admit, the protocol's own reader reads as calls of
declared tools with arguments of the declared types (or, in JSON mode, as one value of the schema); and the serving
engine on a synthetic checkpoint, whose random weights say nothing and are held to a valid call all the same.
"""
import json
import random
import tempfile
import typing as ta

import pytest

from ..api import ManualGenerationRunner
from ..arch.qwen35 import load_qwen35
from ..arch.tests.inkling2checkpoints import inkling2_test_config
from ..arch.tests.inkling2checkpoints import write_inkling2_checkpoint
from ..constrain.framed import FramedJsonConstraint
from ..constrain.framed import FramedPlainConstraint
from ..constrain.framed import FramedToolConstraint
from ..constrain.grammar import Acceptor
from ..constrain.grammar import JsonCallSpelling
from ..load.weights import open_source
from ..serve.inkling2 import INKLING2_CALL_SPELLING
from ..serve.inkling2 import Inkling2ChatProtocol
from ..serve.registry import chat_protocol_for
from ..serve.serving import Engine
from ..serve.serving import Request
from ..serve.serving import SamplingDefaults
from ..tokenizer import Tokenizer


##


MODEL = '<|message_model|>'
END_MESSAGE = '<|end_message|>'
THINKING = '<|content_thinking|>'
TEXT = '<|content_text|>'
CALL = '<|content_invoke_tool_json|>'
END = '<|content_model_end_sampling|>'

# (no free-form strings: a random walk inside one would need about a vocabulary of tokens to find the closing quote)
TOOLS = [
    {'type': 'function', 'function': {'name': 'get_weather', 'parameters': {
        'type': 'object',
        'properties': {
            'city': {'type': 'string', 'enum': ['Oslo', 'Rome']},
            'days': {'type': 'integer'},
        },
        'required': ['city'],
        'additionalProperties': False,
    }}},
    {'type': 'function', 'function': {'name': 'get', 'parameters': {
        'type': 'object',
        'properties': {'x': {'type': 'number'}, 'flags': {'type': 'array', 'items': {'type': 'boolean'}}},
        'required': ['x'],
        'additionalProperties': False,
    }}},
]

NAMED = {'type': 'function', 'function': {'name': 'get'}}

SCHEMA = {
    'type': 'object',
    'properties': {'a': {'type': 'integer'}, 'b': {'type': 'array', 'items': {'type': 'boolean'}}},
    'required': ['a'],
    'additionalProperties': False,
}


def _check_args(name: str, args: ta.Any) -> None:
    if name == 'get_weather':
        assert args['city'] in ('Oslo', 'Rome') and set(args) <= {'city', 'days'}
        assert isinstance(args.get('days', 0), int) and not isinstance(args.get('days', 0), bool)
    elif name == 'get':
        assert isinstance(args['x'], (int, float)) and not isinstance(args['x'], bool)
        assert all(isinstance(f, bool) for f in args.get('flags', [])) and set(args) <= {'x', 'flags'}
    else:
        raise AssertionError(name)


def _check_value(v: ta.Any) -> None:
    assert isinstance(v['a'], int) and not isinstance(v['a'], bool) and set(v) <= {'a', 'b'}
    assert all(isinstance(x, bool) for x in v.get('b', []))


def _protocol(tmp: str) -> tuple[Tokenizer, Inkling2ChatProtocol]:
    write_inkling2_checkpoint(tmp)
    tok = Tokenizer.from_spec(open_source(tmp).tokenizer_spec)
    protocol = chat_protocol_for(tok)
    assert isinstance(protocol, Inkling2ChatProtocol)
    return tok, protocol


def test_call_spelling():
    """
    The acceptor in another spelling of the JSON call syntax: no text closes a call, and a call may be held to one
    of the acceptor's names.
    """

    acc = Acceptor(TOOLS, spelling=INKLING2_CALL_SPELLING)

    def accepts(text: str, names: ta.Any = None) -> bool:
        st = acc.initial(names)
        for c in text.encode():
            st = acc.advance(st, c)
            if not st:
                return False
        return acc.is_complete(st)

    assert accepts('{"name":"get","args":{"x":1}}')
    assert accepts('{ "name" : "get_weather" , "args" : {"city": "Oslo", "days": 2} }')
    assert not accepts('{"name":"get","args":{"x":1}}\n')  # nothing follows the object
    assert not accepts('\n{"name":"get","args":{"x":1}}')
    assert not accepts('{"name":"get","arguments":{"x":1}}')
    assert not accepts('{"name":"get","args":{}}') and not accepts('{"name":"got","args":{"x":1}}')

    assert accepts('{"name":"get","args":{"x":1}}', ('get',))
    assert not accepts('{"name":"get_weather","args":{"city":"Oslo"}}', ('get',))
    with pytest.raises(ValueError, match='not functions'):
        acc.initial(('got',))

    # the default spelling is the legacy ChatML one, as it was
    legacy = Acceptor(TOOLS)
    assert legacy.spelling == JsonCallSpelling()
    st = legacy.initial()
    for c in b'\n{"name": "get", "arguments": {"x": 1}}\n</tool_call>':
        st = legacy.advance(st, c)
    assert legacy.is_complete(st)


def test_controller():
    with tempfile.TemporaryDirectory() as tmp:
        tok, protocol = _protocol(tmp)
        sp = tok.special

        def names(c: ta.Any) -> list[str] | None:
            al = c.allowed()
            return None if al is None else sorted(tok.tokens[i] for i in al)

        def feed(c: ta.Any, text: str, *, checked: bool = True) -> None:
            for t in tok.encode(text):
                al = c.allowed()
                if checked:
                    assert al is None or t in al, (text, tok.tokens[t])
                c.feed(t)

        # auto: nothing is restricted but a model message's header and a call's body
        c = protocol.constraint(TOOLS, 'auto', None)
        assert isinstance(c, FramedToolConstraint) and c.allowed() is None
        feed(c, f'{MODEL}{THINKING}let me see{END_MESSAGE}')
        assert c.allowed() is None
        feed(c, MODEL)
        assert names(c) == sorted([TEXT, THINKING, '<|content_xml|>', 'g'])  # a channel, or toward a tool's name
        feed(c, 'get')
        assert names(c) == sorted([CALL, '_'])  # a tool's name, and on the way to another's
        feed(c, '_weather')
        assert names(c) == [CALL]
        feed(c, CALL)
        assert names(c) == ['{']
        feed(c, '{"name":"get_')
        assert names(c) == ['w']  # the body names the tool the header named
        feed(c, 'weather","args":{"city":"Oslo","days":3}')
        assert c.calls == 0
        feed(c, '}')
        assert c.calls == 1 and names(c) == [END_MESSAGE]
        feed(c, END_MESSAGE)
        assert c.allowed() is None
        feed(c, f'{MODEL}get{CALL}' + '{"name":"get","args":{"x":1.5}}' + END_MESSAGE + END)
        assert c.calls == 2 and c.done and c.violations == 0

        # the markers are text anywhere but where the framing has them: nothing is opened by one in a body
        c = protocol.constraint(TOOLS, 'auto', None)
        feed(c, f'{MODEL}{TEXT}a {CALL} b')
        assert c.kind == 'content' and c.allowed() is None

        # required: a message of the model's, which is reasoning (once, and only with thinking) or a call, and no end
        # of the turn before the call is complete
        c = protocol.constraint(TOOLS, 'required', None)
        assert names(c) == [MODEL]
        feed(c, MODEL)
        assert names(c) == sorted([THINKING, 'g'])
        feed(c, THINKING)
        assert sp[END] not in c.allowed() and sp[END_MESSAGE] in c.allowed() and len(c.allowed()) == len(tok.tokens) - 2
        feed(c, f'well{END_MESSAGE}')
        assert names(c) == [MODEL]
        feed(c, MODEL)
        assert names(c) == ['g']
        feed(c, f'get{CALL}' + '{"name":"get","args":{"x":1}}' + END_MESSAGE)
        assert c.calls == 1 and c.allowed() is None  # the call made, the rest of the turn is the model's

        c = protocol.constraint(TOOLS, 'required', None, enable_thinking=False)
        feed(c, MODEL)
        assert names(c) == ['g']

        # a named function: its name alone, and that call is the turn
        c = protocol.constraint(TOOLS, NAMED, None, enable_thinking=False)
        feed(c, f'{MODEL}get')
        assert names(c) == [CALL]
        feed(c, CALL + '{"name":"get","args":{"x":1}}')
        assert names(c) == [END_MESSAGE]
        feed(c, END_MESSAGE)
        assert names(c) == sorted({tok.tokens[i] for i in protocol.eos_ids})

        # layout whitespace is rationed: two tokens of it in a row, then the JSON goes on; inside a string it is
        # content, and is not counted
        text_tool = [{'type': 'function', 'function': {'name': 'say', 'parameters': {
            'type': 'object',
            'properties': {'text': {'type': 'string'}},
            'required': ['text'],
        }}}]
        c = protocol.constraint(text_tool, 'required', None, enable_thinking=False)
        feed(c, f'{MODEL}say{CALL}' + '{"name":"say","args":{')
        space = tok.encode(' ')[0]
        blanks = {space, tok.encode('\n')[0], tok.encode('\t')[0]}
        assert blanks <= c.allowed()
        feed(c, ' \n')
        assert not blanks & c.allowed() and names(c) == ['"']
        feed(c, '"text" ')
        assert blanks <= c.allowed()  # (the run starts again after anything else)
        feed(c, ':"a')
        feed(c, '      ')
        assert space in c.allowed() and c.blank == 0
        feed(c, '" }')
        feed(c, '  ')
        assert names(c) == ['}']
        feed(c, '}' + END_MESSAGE)
        assert c.calls == 1 and c.violations == 0

        # none: the call channel is never offered
        c = protocol.constraint(TOOLS, 'none', None)
        assert c.allowed() is None
        feed(c, MODEL)
        assert sp[CALL] not in c.allowed() and len(c.allowed()) == len(tok.tokens) - 1
        feed(c, f'get{TEXT}')
        assert c.allowed() is None

        # a draft that breaks the grammar (fed to a clone, never committed) leaves the controller it was cloned from
        c = protocol.constraint(TOOLS, 'required', None)
        feed(c, f'{MODEL}get{CALL}')
        look = c.clone()
        feed(look, '}', checked=False)
        assert look.violations == 1 and c.violations == 0 and names(c) == ['{']

        # JSON mode: reasoning once, then one text message that is the value, then the end of the turn
        j = protocol.constraint(None, None, {'type': 'json_schema', 'json_schema': {'schema': SCHEMA}})
        assert isinstance(j, FramedJsonConstraint) and names(j) == [MODEL]
        feed(j, MODEL)
        assert names(j) == sorted([THINKING, TEXT])
        feed(j, f'{THINKING}hm{END_MESSAGE}{MODEL}')
        assert names(j) == [TEXT]
        feed(j, TEXT)
        assert END_MESSAGE not in (names(j) or ())
        feed(j, '{"a": 1')
        assert END_MESSAGE not in (names(j) or ())
        feed(j, '}')
        assert END_MESSAGE in (names(j) or ())
        feed(j, '\n\n')
        assert names(j) == [END_MESSAGE]  # (the whitespace after the value is rationed too)
        feed(j, END_MESSAGE)
        assert names(j) == sorted({tok.tokens[i] for i in protocol.eos_ids})
        feed(j, END)
        assert j.done and j.violations == 0

        # no tools and no format: a message is opened on a channel, which is not the call's; nothing else is held
        c = protocol.constraint(None, None, None)
        assert isinstance(c, FramedPlainConstraint) and c.allowed() is None
        feed(c, MODEL)
        assert names(c) == sorted([TEXT, THINKING, '<|content_xml|>'])
        feed(c, f'{THINKING}hm{END_MESSAGE}')
        assert c.allowed() is None

        # thinking off: the reasoning channel is not offered either -- here, and with tools
        c = protocol.constraint(None, None, None, enable_thinking=False)
        feed(c, MODEL)
        assert names(c) == sorted([TEXT, '<|content_xml|>'])
        feed(c, f'{TEXT}hello{END_MESSAGE}{MODEL}')
        assert names(c) == sorted([TEXT, '<|content_xml|>'])
        feed(c, f'{TEXT}more{END_MESSAGE}{END}')
        assert c.done and c.allowed() is None

        c = protocol.constraint(TOOLS, 'auto', None, enable_thinking=False)
        feed(c, MODEL)
        assert names(c) == sorted([TEXT, '<|content_xml|>', 'g'])
        c = protocol.constraint(TOOLS, 'none', None, enable_thinking=False)
        feed(c, MODEL)
        assert names(c) == sorted(set(tok.tokens) - {THINKING, CALL})

        # a tool choice with no tools is no tools; and nothing is refused any more
        assert isinstance(protocol.constraint(None, 'required', None), FramedPlainConstraint)
        protocol.check(TOOLS, 'required', {'type': 'json_object'})


def _walk(c: ta.Any, rng: random.Random, n_tokens: int, n_vocab: int, bias: ta.Sequence[int]) -> list[int]:
    """A random turn under the controller: any allowed token, the framing's own made likelier where all are."""

    out: list[int] = []
    for _ in range(n_tokens):
        if c.done:
            break
        al = c.allowed()
        pool = sorted(al) if al is not None else list(range(n_vocab))
        if len(pool) > 50:
            pool = [*[i for i in bias if al is None or i in al] * 8, *rng.sample(pool, 20)]
        t = rng.choice(pool)
        out.append(t)
        c.feed(t)
    return out


def test_what_is_admitted_reads_well():
    with tempfile.TemporaryDirectory() as tmp:
        tok, protocol = _protocol(tmp)
        bias = [tok.special[t] for t in (MODEL, END_MESSAGE, TEXT, THINKING, CALL, END)]
        rng = random.Random(0)
        n_vocab = len(tok.tokens)

        made = {}
        for choice in ('auto', 'required', 'none', NAMED):
            n_calls = 0
            for seed in range(150):
                rng.seed(seed)
                thinking = bool(seed % 2)
                c = protocol.constraint(TOOLS, choice, None, enable_thinking=thinking)
                ids = _walk(c, rng, 400, n_vocab, bias)
                assert c.violations == 0
                text = tok.decode([i for i in ids if i not in protocol.eos_ids])
                parsed = protocol.parse(text)
                assert thinking or not parsed.reasoning, text

                calls = parsed.tool_calls
                if not c.done and c.kind == 'call' and c.calls < len(calls):
                    calls = calls[:-1]  # (the walk's length ran out inside a call)
                assert len(calls) == c.calls, text
                for call in calls:
                    _check_args(call['function']['name'], json.loads(call['function']['arguments']))
                n_calls += len(calls)

                if choice == 'none':
                    assert not parsed.tool_calls, text
                elif choice != 'auto' and c.done:
                    assert calls, text
                    if choice is NAMED:
                        assert [call['function']['name'] for call in calls] == ['get'], text
                    # before the first call: nothing but, with thinking, one message of reasoning
                    head = text[:text.index(CALL)]
                    assert not protocol.parse(head).content and head.count(MODEL) <= 1 + thinking, text

            made[str(choice)] = n_calls

        assert made['auto'] and made['required'] >= 100 and made[str(NAMED)] >= 100 and not made['none'], made

        done = 0
        for seed in range(150):
            rng.seed(seed)
            thinking = bool(seed % 2)
            c = protocol.constraint(
                None,
                None,
                {'type': 'json_schema', 'json_schema': {'schema': SCHEMA}},
                enable_thinking=thinking,
            )
            ids = _walk(c, rng, 400, n_vocab, bias)
            assert c.violations == 0
            if not c.done:
                continue
            text = tok.decode([i for i in ids if i not in protocol.eos_ids])
            parsed = protocol.parse(text)
            _check_value(json.loads(parsed.content))
            assert not parsed.tool_calls and text.count(MODEL) <= 1 + thinking, text
            done += 1
        assert done >= 100, done


def test_engine():
    """
    The serving engine on a synthetic Inkling 2 checkpoint (a small one: four layers, two of them looped), sampling
    at a temperature that flattens its random logits -- left peaked, they pick whitespace wherever JSON allows it and
    never finish a value: a forced call comes out valid, plain and under prompt-lookup drafts (rejection under the
    masks), streamed and not; 'none' never calls; JSON mode answers with a value of the schema.
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        pytest.skip('torch not installed')

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp, inkling2_test_config(
            num_hidden_layers=4,
            layer_types=['hybrid_sliding', 'hybrid'] * 2,
            loop_layer_index_start=2,
            loop_layer_index_end=4,
            loop_num_passes=2,
        ))
        src = open_source(tmp)
        tok = Tokenizer.from_spec(src.tokenizer_spec)
        ops = TorchOps('cpu', capture_mode='static', triton=False)
        model = load_qwen35(src, ops, dtype='f32', verbose=False)
        defaults = SamplingDefaults(temperature=40.0, top_k=0, top_p=1.0, max_tokens=200)
        msgs = [{'role': 'user', 'content': 'weather? weather? weather?'}]

        drafted = 0
        for lookup in (0, 1):
            engine = Engine(
                ManualGenerationRunner(model, capacity=768, lookup_ngram=lookup, lookup_k=3),
                tok,
                defaults=defaults,
                log=None,
            ).start()

            def run(body: dict) -> ta.Any:
                req = Request.from_json(
                    {'messages': msgs, 'seed': 7, **body},
                    defaults,
                    True,
                    engine.protocol.reasoning_effort,  # noqa: B023
                )
                engine.check(req)  # noqa: B023
                return engine.run_sync(req)  # noqa: B023

            for choice, stream in (('required', False), (NAMED, True)):
                res = run({'tools': TOOLS, 'tool_choice': choice, 'stream': stream, 'enable_thinking': False})
                assert res.finish_reason == 'tool_calls' and res.tool_calls, (lookup, choice, res.text)
                calls = res.tool_calls
                if res.completion_tokens == defaults.max_tokens and len(calls) > 1:
                    calls = calls[:-1]  # (a later call the length may have cut)
                for call in calls:
                    _check_args(call['function']['name'], json.loads(call['function']['arguments']))
                if choice is NAMED:
                    assert calls[0]['function']['name'] == 'get'
                drafted += res.spec_rounds

            res = run({'tools': TOOLS, 'tool_choice': 'none', 'max_tokens': 40})
            assert not res.tool_calls and res.finish_reason != 'tool_calls'

            res = run({'enable_thinking': False, 'max_tokens': 60})
            assert not res.reasoning and not res.tool_calls, res.text
            res = run({'max_tokens': 60})
            assert not res.tool_calls, res.text

            res = run({
                'response_format': {'type': 'json_schema', 'json_schema': {'name': 'v', 'schema': SCHEMA}},
                'enable_thinking': False,
                'max_tokens': 400,
            })
            assert res.finish_reason == 'stop', res.text
            _check_value(json.loads(res.content))

        assert drafted  # (the lookup engine's rounds verified drafts, under the masks)
