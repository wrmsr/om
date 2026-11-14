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
import typing as ta

from ..api import ManualGenerationRunner
from ..arch.qwen35 import load_qwen35
from ..constrain.grammar import WS
from ..constrain.grammar import Acceptor
from ..constrain.grammar import TokenMasks
from ..constrain.grammar import ToolConstraint
from ..constrain.grammar import Vocab
from ..core.config import Qwen35Config
from ..load.weights import GGUFSource
from ..tokenizer import Tokenizer
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


def test_token_masks_equal_brute_force():
    """
    Every mask TokenMasks computes -- through its shortcuts for strings and free keys, and its union over a state's
    alternatives -- is exactly the set of tokens the acceptor takes byte by byte, along random walks through tool
    calls (declared and free keys together) and free-form and schema'd JSON values. And a free key's state forgets its
    text once it cannot become a declared name, so key characters do not multiply states.
    """

    tok = _tokenizer()
    vocab = Vocab.for_tokenizer(tok)

    def survives(acc: Acceptor, st: ta.Any, bs: bytes) -> bool:
        for c in bs:
            st = acc.advance(st, c)
            if not st:
                return False
        return True

    schema = {
        'type': 'object',
        'properties': {'city': {'type': 'string'}, 'n': {'type': 'integer'}},
        'required': ['city'],
    }  # (extra keys allowed: a key is a declared name or a free one, both alive until they part)
    rng = random.Random(1)
    kinds: set[str] = set()
    multi = 0
    for acc in (Acceptor(TOOLS), Acceptor(value_schema={}), Acceptor(value_schema=schema)):
        masks = TokenMasks(acc, vocab)
        for _ in range(40):
            st = acc.initial()
            steps = 0
            while not acc.is_complete(st) and steps < 60:
                allowed = masks.allowed(st)
                brute = {i for i in vocab_ids(vocab) if survives(acc, st, vocab.bytes[i])}
                assert allowed == brute, (sorted(allowed ^ brute)[:5], st)
                kinds |= {stack[-1][0] for stack in st if stack}
                multi += len(st) > 1
                if not allowed:
                    break
                tid = rng.choice(sorted(allowed))
                for c in vocab.bytes[tid]:
                    st = acc.advance(st, c)
                steps += 1
    assert 'keystr' in kinds and 'str' in kinds and multi, (kinds, multi)

    # a free key's text: tracked while it can still become a declared name, forgotten after
    acc = Acceptor(value_schema=schema)
    st = acc.initial()
    for c in b'{"ci':
        st = acc.advance(st, c)
    assert {stack[-1] for stack in st if stack[-1][0] == 'keystr'} == {('keystr', 'ci')}
    for c in b'r':
        st = acc.advance(st, c)
    assert {stack[-1] for stack in st if stack[-1][0] == 'keystr'} == {('keystr', None)}
    after = st
    for c in b'cus':
        st = acc.advance(st, c)
    assert st == after  # more key characters: the same state

    def value_ok(a: Acceptor, text: str) -> bool:  # (a JSON-mode value is done when it can end, not at a closing tag)
        s = a.initial()
        for c in text.encode():
            s = a.advance(s, c)
            if not s:
                return False
        return a.can_end(s)

    assert value_ok(acc, '{"city": "x", "circus": 1}')
    assert value_ok(acc, '{"city": "x", "cit": 1, "cityy": 2}')
    assert not value_ok(acc, '{"city": "x", "city": "y"}')  # a declared name twice: not through the free branch
    assert not value_ok(acc, '{"n": 1}')  # (required)
    assert value_ok(Acceptor(value_schema={}), '{"any key at all": {"k": [1, "v"]}}')


def vocab_ids(vocab: Vocab) -> ta.AbstractSet[int]:
    """The token ids the grammar's trie holds (special tokens are not in it, save the ones a tool call needs)."""

    got = getattr(vocab, '_test_ids', None)
    if got is None:
        ids: set[int] = set()

        def walk(node: dict) -> None:
            for b, child in node.items():
                if b == -1:
                    ids.add(child)
                else:
                    walk(child)

        walk(vocab.root)
        got = vocab._test_ids = frozenset(ids)  # type: ignore[attr-defined]  # noqa
    return got


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

    from ..serve.serving import Engine
    from ..serve.serving import Request
    from ..serve.serving import SamplingDefaults
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    tok = Tokenizer.from_spec(src.tokenizer_spec)

    model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
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
            ManualGenerationRunner(model, spec=spec, capacity=512),
            tok,
            defaults=defaults,
            model_name='tiny',
            log=lambda s: None,
        ).start()
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

    from ..constrain.grammar import JsonConstraint
    from ..serve.serving import Engine
    from ..serve.serving import Request
    from ..serve.serving import SamplingDefaults
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
    model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
    defaults = SamplingDefaults(temperature=1.0, top_k=0, top_p=1.0, max_tokens=120)
    cons = JsonConstraint(tok, schema, thinking=False)
    end = next(iter(cons.end_ids))
    assert end not in cons.allowed()  # type: ignore  # nothing to end yet
    for spec in (0, 3):
        engine = Engine(
            ManualGenerationRunner(model, spec=spec, capacity=512),
            tok,
            defaults=defaults,
            model_name='tiny',
            log=lambda s: None,
        ).start()
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
    from ..serve.serving import Engine
    from ..serve.serving import SamplingDefaults
    from ..serve.serving import serve
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
    engine = Engine(
        ManualGenerationRunner(model, spec=2, capacity=512),
        tok,
        model_name='tiny',
        log=lambda s: None,
        defaults=SamplingDefaults(
            temperature=1.0,
            top_k=0,
            top_p=1.0,
            max_tokens=250,
        ),
    ).start()
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


FUNCTION_TOOLS = [
    {'type': 'function', 'function': {'name': 'read_file', 'parameters': {
        'type': 'object',
        'properties': {
            'path': {'type': 'string'},
            'limit': {'type': 'integer'},
            'mode': {'type': 'string', 'enum': ['text', 'binary']},
            'follow': {'type': 'boolean'},
            'opts': {'type': 'object', 'properties': {'x': {'type': 'array', 'items': {'type': 'integer'}}}},
            'note': {'type': ['string', 'null']},
        },
        'required': ['path'],
        'additionalProperties': False,
    }}},
    {'type': 'function', 'function': {'name': 'read', 'parameters': {'type': 'object', 'properties': {}}}},
    {'type': 'function', 'function': {'name': 'anything', 'parameters': {'type': 'object'}}},
    {'type': 'function', 'function': {'name': 'pick', 'parameters': {
        'type': 'object',
        'properties': {'n': {'type': 'integer'}, 'on': {'type': 'boolean'}, 'kind': {'enum': ['a', 'bc', 3]}},
        'required': ['n', 'kind'],
        'additionalProperties': False,
    }}},
]


def _function_body(name: str, args: dict, fmt: ta.Any = None) -> str:
    """A call as the acceptor sees it: what follows `<tool_call>`, as the chat format renders it."""

    from ..serve.chat import QWEN38
    from ..serve.chat import render_function_call

    return render_function_call({'name': name, 'arguments': args}, fmt or QWEN38)[len('<tool_call>'):]


def test_function_syntax_acceptor():
    """
    The checkpoints' call syntax -- <function=name>, a <parameter=key> block per argument -- under the acceptor: what
    the chat format renders for valid arguments is accepted, and a call that names no declared function, a parameter
    not declared, a required one missing, one twice, or a value not of its schema is not.
    """

    from ..serve.chat import QWEN35
    from ..serve.chat import QWEN38
    from ..serve.chat import parse_output

    acc = Acceptor(FUNCTION_TOOLS, syntax='function')
    good: list[tuple[str, dict]] = [
        ('read_file', {'path': 'a/b.py'}),
        ('read_file', {'path': 'two\nlines <b> "q" \\ </param', 'limit': 3, 'mode': 'binary', 'follow': True}),
        ('read_file', {'limit': -12, 'path': '', 'opts': {'x': [1, 2]}, 'note': None, 'follow': False}),
        ('read_file', {'path': 'ends with a newline\n', 'note': 'free text'}),
        ('read', {}),
        ('anything', {}),
        ('anything', {'foo': 'bar', 'n-1.x_y': 'free text, not JSON', 'j': {'k': [1]}}),
        ('pick', {'kind': 3, 'n': 0}),
        ('pick', {'n': 7, 'on': True, 'kind': 'bc'}),
    ]
    for name, args in good:
        for fmt in (QWEN38, QWEN35):  # (True / False / None in the second: both spellings are grammatical)
            body = _function_body(name, args, fmt)
            assert _accepts(acc, body), (name, args, fmt.name)
            got = parse_output('<tool_call>' + body, fmt=fmt, tools=FUNCTION_TOOLS).tool_calls
            assert [(c['function']['name'], json.loads(c['function']['arguments'])) for c in got] == [(name, args)]

    def raw(name: str, *params: str, close: str = '</function>\n</tool_call>') -> str:
        return f'\n<function={name}>\n' + ''.join(params) + close

    def param(key: str, value: str) -> str:
        return f'<parameter={key}>\n{value}\n</parameter>\n'

    bad = [
        raw('nope'),  # an undeclared function
        raw('read_file'),  # the required parameter missing
        raw('read_file', param('path', 'x'), param('zzz', '1')),  # an undeclared parameter, none allowed
        raw('read_file', param('path', 'x'), param('path', 'y')),  # a parameter twice
        raw('read_file', param('path', 'x'), param('limit', 'three')),  # not an integer
        raw('read_file', param('path', 'x'), param('limit', '1.5')),
        raw('read_file', param('path', 'x'), param('mode', 'hex')),  # not in the enum
        raw('read_file', param('path', 'x'), param('follow', 'yes')),  # not a boolean
        raw('read_file', param('path', 'x'), param('opts', '{"x": ["a"]}')),  # the object's own schema
        raw('read', param('path', 'x')),  # a function without parameters
        raw('anything', param('two words', 'x')),  # a free name is identifier characters
        raw('anything', param('', 'x')),
        raw('pick', param('n', '1')),  # `kind` is required too
        raw('pick', param('n', '1'), param('kind', 'b')),
        raw('read_file', param('path', 'x'), close='</function></tool_call>'),  # the newline before the close
        '<function=read>\n</function>\n</tool_call>',  # the newline after <tool_call>
    ]
    alive = [_accepts(acc, t) for t in bad]
    assert not any(alive), alive
    assert _accepts(acc, raw('read_file', param('path', 'x'), param('follow', 'True'), param('note', 'None')))
    assert _accepts(acc, raw('read_file', param('path', 'x'), param('follow', 'false'), param('note', 'null')))

    only = Acceptor(FUNCTION_TOOLS, only='read', syntax='function')
    assert _accepts(only, raw('read')) and not _accepts(only, raw('anything'))
    # one function's name a prefix of another's: both stay open until the '>'
    assert _accepts(acc, raw('read')) and _accepts(acc, raw('read_file', param('path', 'p')))


def test_function_syntax_masks():
    """
    The token masks of the function syntax equal a brute-force walk of the vocabulary in every state random walks
    reach (the text-parameter and free-name shortcuts among them), the walks end in calls that parse to arguments of
    the declared types, and the controller follows a call rendered by the chat format token by token.
    """

    from ..serve.chat import QWEN38
    from ..serve.chat import parse_output

    tok = _tokenizer()
    vocab = Vocab.for_tokenizer(tok)
    acc = Acceptor(FUNCTION_TOOLS, syntax='function')
    masks = TokenMasks(acc, vocab)
    rng = random.Random(3)

    def survives(a: Acceptor, state, bs: bytes) -> bool:
        for c in bs:
            state = a.advance(state, c)
            if not state:
                return False
        return True
    kinds: set[str] = set()
    done = 0
    for _ in range(60):
        st = acc.initial()
        text = b''
        steps = 0
        while not acc.is_complete(st) and steps < 80:
            allowed = masks.allowed(st)
            brute = {i for i in vocab_ids(vocab) if survives(acc, st, vocab.bytes[i])}
            assert allowed == brute, (sorted(allowed ^ brute)[:5], st)
            kinds |= {stack[-1][0] for stack in st if stack}
            assert allowed, st
            # (lean towards the tokens that close things, or a walk inside a text parameter never ends)
            closing = [i for i in allowed if any(c in vocab.bytes[i] for c in b'<>\n')]
            tid = rng.choice(sorted(closing)) if closing and rng.random() < 0.7 else rng.choice(sorted(allowed))
            for c in vocab.bytes[tid]:
                st = acc.advance(st, c)
            text += vocab.bytes[tid]
            steps += 1
        if not acc.is_complete(st):
            continue
        done += 1
        whole = '<tool_call>' + text.decode(errors='replace')
        (call,) = parse_output(whole, fmt=QWEN38, tools=FUNCTION_TOOLS).tool_calls
        name = call['function']['name']
        args = json.loads(call['function']['arguments'])
        if name == 'read_file':
            assert isinstance(args['path'], str) and set(args) <= {'path', 'limit', 'mode', 'follow', 'opts', 'note'}
            assert isinstance(args.get('limit', 0), int) and args.get('mode', 'text') in ('text', 'binary')
            assert isinstance(args.get('follow', False), bool) and isinstance(args.get('opts', {}), dict)
        elif name == 'pick':
            assert isinstance(args['n'], int) and args['kind'] in ('a', 'bc', 3) and set(args) <= {'n', 'on', 'kind'}
        elif name == 'read':
            assert args == {}
        else:
            assert name == 'anything'
    assert done >= 20, done
    assert {'ptext', 'pkey', 'params', 'lit', 'name'} <= kinds, kinds

    # the controller, fed a rendered call: free until the tag, inside the grammar until the call closes
    for choice in ('auto', 'required'):
        ctl = ToolConstraint(tok, FUNCTION_TOOLS, choice, thinking=False, syntax='function')
        sent = {'path': 'src/main.py', 'limit': 20, 'mode': 'text', 'follow': True}
        for t in tok.encode('<tool_call>' + _function_body('read_file', sent)):
            al = ctl.allowed()
            assert al is None or t in al, (choice, tok.decode([t]))
            ctl.feed(t)
        assert ctl.mode == 'free' and ctl.calls == 1 and ctl.violations == 0, (choice, ctl.mode, ctl.calls)
    # and the JSON syntax is refused by it, as the function syntax is by the JSON controller
    ctl = ToolConstraint(tok, FUNCTION_TOOLS, 'auto', thinking=False, syntax='function')
    for t in tok.encode('<tool_call>\n{"name": "read", "arguments": {}}\n</tool_call>'):
        ctl.feed(t)
    assert ctl.calls == 0 and ctl.violations == 1


def test_engine_function_format():
    """
    An engine in a checkpoint's own chat format: with the random model a forced call comes out in the function syntax,
    parses to arguments of the declared types (plain and speculative, streamed or not), and the turn carrying it back
    with its result still extends the stored state.
    """

    try:
        from ..backends.torch import TorchOps
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..prefix.cache import PrefixCache
    from ..serve.chat import QWEN35
    from ..serve.chat import QWEN38
    from ..serve.serving import Engine
    from ..serve.serving import Request
    from ..serve.serving import SamplingDefaults
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
    defaults = SamplingDefaults(temperature=1.0, top_k=0, top_p=1.0, max_tokens=200)
    # (no text parameters: a random model inside one would not find its closing tag)
    tools = [FUNCTION_TOOLS[3], FUNCTION_TOOLS[1]]
    for fmt, spec in ((QWEN38, 0), (QWEN38, 3), (QWEN35, 0)):
        pc = PrefixCache(ops, 1 << 30, 1 << 30)
        engine = Engine(
            ManualGenerationRunner(model, spec=spec, capacity=512, prefix_cache=pc),
            tok,
            prefix_cache=pc,
            defaults=defaults,
            chat_format=fmt,
            log=None,
        ).start()
        assert engine.format is fmt and engine.open_think
        for stream in (False, True):
            body = {
                'messages': [{'role': 'user', 'content': 'pick one'}],
                'tools': tools,
                'tool_choice': 'required',
                'stream': stream,
                'seed': 11,
                'enable_thinking': False,
            }
            req = Request.from_json(body, defaults, True)
            assert '<function=example_function_name>' in engine.render(req)
            res = engine.run_sync(req)
            assert res.finish_reason == 'tool_calls' and res.tool_calls, (fmt.name, spec, stream, res.text)
            assert '<function=' in res.text and '"arguments"' not in res.text
            for tc in res.tool_calls:
                args = json.loads(tc['function']['arguments'])
                if tc['function']['name'] == 'pick':
                    assert isinstance(args['n'], int) and args['kind'] in ('a', 'bc', 3), args
                    assert isinstance(args.get('on', True), bool) and set(args) <= {'n', 'on', 'kind'}
                else:
                    assert tc['function']['name'] == 'read' and args == {}

        # the call comes back with its result: the stored state is extended, not rebuilt
        history = [
            *body['messages'],  # type: ignore[misc]
            {'role': 'assistant', 'content': res.content, 'reasoning_content': res.reasoning or '',
             'tool_calls': res.tool_calls},
            *[{'role': 'tool', 'content': 'ok', 'tool_call_id': tc['id']} for tc in res.tool_calls],
        ]
        follow = {**body, 'messages': history, 'tool_choice': 'none', 'max_tokens': 8}
        again = engine.run_sync(Request.from_json(follow, defaults, True))
        reused = again.prompt_reused
        assert reused >= res.prompt_tokens + res.completion_tokens - 1, (fmt.name, spec, reused)


def test_agent_file_tools():
    """
    What the agent's file tools hand the model: a whole file exactly as it is (so that what is written back is what
    was read), a range of it numbered the way `cat -n` numbers, and a write that stores its text unchanged.
    """

    from ..entrypoints import agent

    with tempfile.TemporaryDirectory() as tmp:
        tools = agent.Tools(pathlib.Path(tmp))
        text = 'def f(x):\n    return x  \n\n\ttabbed "quoted" \\ line\n'
        assert tools.run('write_file', {'path': 'a/b.py', 'content': text}).startswith('wrote ')
        assert (pathlib.Path(tmp) / 'a' / 'b.py').read_text() == text

        assert tools.run('read_file', {'path': 'a/b.py'}) == text
        assert tools.run('read_file', {'path': 'a/b.py', 'start': 2, 'end': 3}) == '     2\t    return x  \n     3\t'
        assert tools.run('read_file', {'path': 'a/b.py', 'start': 4}).startswith('     4\t\ttabbed "quoted"')
        assert tools.run('read_file', {'path': 'missing.py'}).startswith('error: ')
        assert tools.run('read_file', {'path': '../outside'}).startswith('error: ')
