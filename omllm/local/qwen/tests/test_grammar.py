# ruff: noqa: SLF001
"""
Constrained tool-call decoding (grammar.py): the byte-level acceptor accepts exactly the well-formed calls, the token
masks admit only continuations the acceptor accepts (random walks under the mask always end in a valid call matching the
schemas), the controller forces / forbids calls as tool_choice says, and -- the real test -- the Engine turns the
synthetic model's random weights into well-formed tool calls with and without speculative decoding, because the grammar
leaves it no other choice.
"""
import json
import pathlib
import random
import tempfile

from ..grammar import WS
from ..grammar import Acceptor
from ..grammar import TokenMasks
from ..grammar import ToolConstraint
from ..grammar import Vocab
from ..tokenizer import Tokenizer
from ..weights import GGUFSource
from ..weights import Qwen35Config
from .test_synthetic import CFG
from .test_synthetic import make_hf_params
from .test_synthetic import write_gguf


##


TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': 'weather',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string'},
                    'days': {'type': 'integer'},
                    'units': {'type': 'string', 'enum': ['c', 'f']},
                },
                'required': ['city'],
                'additionalProperties': False,
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get',
            'parameters': {
                'type': 'object',
                'properties': {
                    'x': {'type': 'number'},
                    'flags': {'type': 'array', 'items': {'type': 'boolean'}},
                    'meta': {'type': 'object'},
                    'opt': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
                },
                'required': ['x'],
                'additionalProperties': False,
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'shell',
            'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'}}, 'required': ['command']},
        },
    },
]


def _tokenizer() -> Tokenizer:
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    write_gguf(tmp / 't.gguf', cfg, make_hf_params(cfg), quantize=False)
    return Tokenizer.from_spec(GGUFSource(tmp / 't.gguf').tokenizer_spec)


def _accepts(acc: Acceptor, text: str) -> bool:
    st = acc.initial()
    for c in text.encode():
        st = acc.advance(st, c)
        if not st:
            return False
    return acc.is_complete(st)


def _check_args(name: str, args: dict) -> None:
    if name == 'get_weather':
        assert isinstance(args['city'], str) and set(args) <= {'city', 'days', 'units'}
        assert isinstance(args.get('days', 0), int) and not isinstance(args.get('days', 0), bool)
        assert args.get('units', 'c') in ('c', 'f')
    elif name == 'get':
        assert isinstance(args['x'], (int, float)) and not isinstance(args['x'], bool)
        assert all(isinstance(f, bool) for f in args.get('flags', []))
        assert isinstance(args.get('meta', {}), dict) and isinstance(args.get('opt'), (str, type(None)))
        assert set(args) <= {'x', 'flags', 'meta', 'opt'}
    elif name == 'shell':
        assert isinstance(args['command'], str)
    else:
        raise AssertionError(name)


def test_acceptor():
    acc = Acceptor(TOOLS)
    good = [
        '\n{"name": "get_weather", "arguments": {"city": "Oslo"}}\n</tool_call>',
        '\n{"name": "get_weather", "arguments": {"days": 3, "city": "Rome", "units": "c"}}\n</tool_call>',
        (
            '\n{ "name" : "get" , "arguments" : { "x" : -1.5e3 , "flags" : [true, false], '
            '"meta": {"a": [1, {"b": null}]} } }\n</tool_call>'
        ),
        '\n{"name": "get", "arguments": {"x": 0, "opt": null}}\n</tool_call>',
        '\n{"name": "get", "arguments": {"x": 2, "opt": "s"}}\n</tool_call>',
        '\n{"name": "shell", "arguments": {"command": "echo \\"hi\\" \\\\n ls", "extra": [1, "two"]}}\n</tool_call>',
    ]
    bad = [
        '\n{"name": "get_weather", "arguments": {}}\n</tool_call>',  # required key missing
        '\n{"name": "get_weather", "arguments": {"city": 5}}\n</tool_call>',  # wrong type
        '\n{"name": "get_weather", "arguments": {"city": "x", "zzz": 1}}\n</tool_call>',  # no extra keys
        '\n{"name": "get_weather", "arguments": {"units": "k", "city": "x"}}\n</tool_call>',  # enum
        '\n{"name": "nope", "arguments": {}}\n</tool_call>',  # undeclared tool
        '\n{"name": "get", "arguments": {"x": 01}}\n</tool_call>',  # not a JSON number
        '\n{"name": "get", "arguments": {"flags": [1], "x": 1}}\n</tool_call>',  # item type
        '\n{"name": "get", "arguments": {"x": 1, "x": 2}}\n</tool_call>',  # duplicate key
        '\n{"name": "get", "arguments": {"x": 1,}}\n</tool_call>',  # trailing comma
        '\n{"name": "get", "arguments": {"x": 1}}</tool_call>',  # missing newline before the close
    ]
    assert all(_accepts(acc, t) for t in good), [_accepts(acc, t) for t in good]
    assert not any(_accepts(acc, t) for t in bad), [_accepts(acc, t) for t in bad]
    only = Acceptor(TOOLS, only='shell')
    assert _accepts(only, good[-1]) and not _accepts(only, good[0])
    print('acceptor: accepts the well-formed calls, rejects the ten malformed ones')


def test_token_masks():
    """Random walks under the token masks always terminate in a call the acceptor accepts and the schemas allow."""

    tok = _tokenizer()
    vocab = Vocab.for_tokenizer(tok)
    acc = Acceptor(TOOLS[:2])
    masks = TokenMasks(acc, vocab)
    ws_only = {i for i in range(vocab.n) if vocab.bytes[i] and all(c in WS for c in vocab.bytes[i])}
    closers = {i for i in range(vocab.n) if any(ch in vocab.bytes[i] for ch in (b'}', b']', b'"', b'<'))}
    rng = random.Random(0)
    for _ in range(150):
        st = acc.initial()
        text = b''
        steps = 0
        while not acc.is_complete(st) and steps < 1000:
            allowed = masks.allowed(st)
            assert allowed, (text, st)
            cand = allowed - ws_only or allowed
            close = cand & closers
            pool = sorted(close) if (close and rng.random() < 0.7) else sorted(cand)
            tid = rng.choice(pool)
            for c in vocab.bytes[tid]:
                st = acc.advance(st, c)
            assert st, (text, vocab.bytes[tid])  # a token the mask allowed is one the acceptor takes
            text += vocab.bytes[tid]
            steps += 1
        assert acc.is_complete(st), text[-100:]
        body = text.decode('utf-8', errors='replace')
        assert body.endswith('\n</tool_call>')
        obj = json.loads(body[:-len('\n</tool_call>')])
        _check_args(obj['name'], obj['arguments'])
    print(f'token masks: 150 random constrained walks all valid ({len(masks.memo)} memoised states)')


def test_controller():
    tok = _tokenizer()
    vocab = Vocab.for_tokenizer(tok)
    # auto: free until '<tool_call>' (several tokens on this tokenizer), constrained until the call closes, free again
    c = ToolConstraint(tok, TOOLS, 'auto', thinking=True)
    assert c.allowed() is None
    for t in tok.encode('hello <tool_call>'):
        c.feed(t)
    assert c.mode == 'call' and c.allowed()
    for t in tok.encode('\n{"name": "get", "arguments": {"x": 1}}\n</tool_call>'):
        c.feed(t)
    assert c.mode == 'free' and c.calls == 1 and c.allowed() is None
    # required: only whitespace and the tag until a call opens; a reasoning block first is allowed
    f = ToolConstraint(tok, TOOLS, 'required', thinking=True)
    rng = random.Random(1)
    steps = 0
    while f.mode == 'free' and steps < 40:
        al = f.allowed()
        assert al is not None
        pick = [i for i in al if i not in f._ws_tokens] or sorted(al)
        f.feed(rng.choice(sorted(pick)))
        steps += 1
    assert f.mode == 'call', f.tail
    f2 = ToolConstraint(tok, TOOLS, 'required', thinking=True)
    for t in tok.encode('<think>'):
        f2.feed(t)
    assert f2.allowed() is None  # reasoning: unconstrained
    for t in tok.encode('thoughts</think>'):
        f2.feed(t)
    assert f2.allowed() is not None
    # a named function
    g = ToolConstraint(tok, TOOLS, {'type': 'function', 'function': {'name': 'shell'}}, thinking=False)
    for t in tok.encode('<tool_call>'):
        g.feed(t)
    assert g.mode == 'call'
    for t in tok.encode('\n{"name": "'):
        g.feed(t)
    assert all(vocab.bytes[i][:1] in (b's', b'"') or b'shell'.startswith(vocab.bytes[i]) for i in g.allowed())  # type: ignore  # noqa
    # none: nothing may complete the tag, even when it is spelled out token by token
    n = ToolConstraint(tok, TOOLS, 'none')
    for t in tok.encode('<tool_cal'):
        n.feed(t)
    assert all(b'<tool_call>' not in (n._pending_tag() + vocab.bytes[i]) for i in n.allowed())  # type: ignore
    print('controller: auto / required / named / none behave')


def test_engine_constrained_calls():
    """
    The synthetic model knows nothing; with tool_choice 'required' the grammar makes it emit a valid call anyway,
    with speculative decoding (rejection sampling under the masks) and without, streamed and not.
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..serving import Engine
    from ..serving import Request
    from ..serving import SamplingDefaults
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    from ..model import Qwen35

    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
    defaults = SamplingDefaults(temperature=1.0, top_k=0, top_p=1.0, max_tokens=200)
    # no free-form strings: a random model inside one would need ~vocab tokens to find the closing quote
    tools = [
        {'type': 'function', 'function': {'name': 'get_weather', 'parameters': {
            'type': 'object',
            'properties': {
                'city': {'type': 'string', 'enum': ['Oslo', 'Rome']},
                'days': {'type': 'integer'},
                'units': {'type': 'string', 'enum': ['c', 'f']},
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
    for spec in (0, 3):
        engine = Engine(
            model,
            tok,
            spec=spec,
            capacity=512,
            defaults=defaults,
            model_name='tiny',
            log=lambda s: None,
        )
        for stream in (False, True):
            req = Request.from_json({
                'messages': [{'role': 'user', 'content': 'weather?'}],
                'tools': tools,
                'tool_choice': 'required',
                'stream': stream,
                'seed': 7,
                'enable_thinking': False,
            }, defaults, True)
            res = engine.run_sync(req)  # streamed requests deliver deltas on the job and the same Result at the end
            finish = res.finish_reason
            res_calls = res.tool_calls
            assert finish == 'tool_calls', (spec, stream, finish)
            assert len(res_calls) >= 1, (spec, stream)
            for call in res_calls:
                fn = call['function']
                args = json.loads(fn['arguments'])
                _check_args(fn['name'], args)
        # 'none' with the same tools: never a call
        req = Request.from_json({
            'messages': [{'role': 'user', 'content': 'weather?'}],
            'tools': tools,
            'tool_choice': 'none',
            'seed': 7,
            'max_tokens': 40,
        }, defaults, True)
        res = engine.run_sync(req)
        assert not res.tool_calls and res.finish_reason != 'tool_calls'
    print('engine: random weights + tool_choice required -> valid calls (spec 0 / 3, streamed or not); none -> none')


def test_json_mode():
    """
    JSON mode on the same acceptor: a bare value of a schema is accepted exactly, the controller allows the end of turn
    only once the value can end, and the Engine with `response_format` returns parseable JSON matching the schema from
    the random model (thinking on and off, spec on and off).
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..grammar import JsonConstraint
    from ..model import Qwen35
    from ..serving import Engine
    from ..serving import Request
    from ..serving import SamplingDefaults
    from .test_parity import synthetic_source

    schema = {
        'type': 'object',
        'properties': {'answer': {'type': 'string', 'enum': ['yes', 'no']}, 'score': {'type': 'integer'}},
        'required': ['answer'],
        'additionalProperties': False,
    }
    acc = Acceptor(value_schema=schema)

    def run(text: str):
        st = acc.initial()
        for c in text.encode():
            st = acc.advance(st, c)
            if not st:
                return None
        return st

    for good in ('{"answer": "yes"}', ' {"answer":"no","score":3}\n', '{"score": -2, "answer": "yes"}'):
        st = run(good)
        assert st is not None and acc.can_end(st), good
    for bad in ('{"answer": "maybe"}', '{"score": 1}', '[1]', '{"answer": "yes", "x": 1}', '{"answer": "yes"} x'):
        st = run(bad)
        assert st is None or not acc.can_end(st), bad
    # any-value mode: a bare number can end without a closing byte
    anyacc = Acceptor(value_schema={})
    st = anyacc.initial()
    for c in b'42':
        st = anyacc.advance(st, c)
    assert anyacc.can_end(st) and not Acceptor.is_complete(st)

    cfg, hf, src = synthetic_source()
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    ops = TorchOps('cpu', capture_mode='static')
    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
    defaults = SamplingDefaults(temperature=1.0, top_k=0, top_p=1.0, max_tokens=120)
    cons = JsonConstraint(tok, schema, thinking=False)
    end = next(iter(cons.end_ids))
    assert end not in cons.allowed()  # type: ignore  # nothing to end yet
    for spec in (0, 3):
        engine = Engine(
            model,
            tok,
            spec=spec,
            capacity=512,
            defaults=defaults,
            model_name='tiny',
            log=lambda s: None,
        )
        for thinking in (False, True):
            req = Request.from_json({
                'messages': [{'role': 'user', 'content': 'yes or no?'}],
                'response_format': {'type': 'json_schema', 'json_schema': {'name': 'a', 'schema': schema}},
                'seed': 3,
                'enable_thinking': thinking,
            }, defaults, True)
            res = engine.run_sync(req)
            obj = json.loads(res.content)
            assert obj.get('answer') in ('yes', 'no') and set(obj) <= {'answer', 'score'}, (spec, thinking, obj)
            if 'score' in obj:
                assert isinstance(obj['score'], int)
        req = Request.from_json({
            'messages': [{'role': 'user', 'content': 'anything'}],
            'response_format': {'type': 'json_object'},
            'seed': 5,
            'enable_thinking': False,
        }, defaults, True)
        res = engine.run_sync(req)
        json.loads(res.content)  # any JSON value, but JSON
    print('json mode: schema acceptor exact; engine + response_format -> parseable JSON of the schema (spec 0 / 3)')


def test_agent_loop():
    """
    The agent runner against the synthetic server: a forced call is executed by the local tools (list_dir on a temp
    dir), its result goes back as a tool message, and the loop ends on a non-call turn or max_turns.
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..entrypoints import agent
    from ..model import Qwen35
    from ..serving import Engine
    from ..serving import SamplingDefaults
    from ..serving import serve
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
    engine = Engine(
        model,
        tok,
        spec=2,
        capacity=512,
        model_name='tiny',
        log=lambda s: None,
        defaults=SamplingDefaults(
            temperature=1.0,
            top_k=0,
            top_p=1.0,
            max_tokens=250,
        ),
    )
    srv = serve(engine, '127.0.0.1', 0)
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / 'hello.txt').write_text('hi')
    saved = agent.TOOLS
    # the one tool a random model can complete: list_dir with its path pinned (a free string would take it ~vocab
    # tokens to close)
    agent.TOOLS = [{'type': 'function', 'function': {'name': 'list_dir', 'parameters': {
        'type': 'object',
        'properties': {'path': {'type': 'string', 'enum': ['.']}},
        'required': [],
        'additionalProperties': False,
    }}}]
    out: list[str] = []
    try:
        msgs = agent.run(
            base,
            'look around',
            tmp,
            max_turns=2,
            thinking=False,
            write=out.append,
            tool_choice='required',
            seed=3,
        )
    finally:
        agent.TOOLS = saved
        srv.shutdown()
    kinds = [m['role'] for m in msgs]
    assert kinds[:3] == ['user', 'assistant', 'tool'], kinds
    assert 'hello.txt' in msgs[2]['content'], msgs[2]
    assert any('[turn 1] tool_calls' in s for s in out)
    print('agent loop: forced call -> executed locally -> result fed back; transcript', kinds)
