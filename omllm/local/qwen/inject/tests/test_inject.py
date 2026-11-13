"""
The injector assembles the same engine `api.generate` assembles by hand: same tokens, plain and speculative; requests
get their own generation scope; the prefix store is shared across requests; an injector-built Engine serves.
"""
import json

import numpy as np

from omcore import inject as inj

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...backends.inject import BackendConfig
from ...backends.torch import TorchOps
from ...decode.inject import DecodeConfig
from ...decode.runners import GenerationParams
from ...decode.runners import GenerationRunner
from ...decode.sampling import Sampler
from ...load.inject import LoadConfig
from ...prefix.cache import PrefixCache
from ...prefix.inject import PrefixConfig
from ...serve.inject import ServeConfig
from ...serve.serving import Request
from ...serve.serving import SamplingDefaults
from ...spec.inject import LookupConfig
from ...spec.inject import SpecConfig
from ...tests.test_parity import synthetic_source
from ..inject import bind_qwen
from ..inject import create_engine


##


def _configs(src, spec, lookup=0):
    return dict(
        backend=BackendConfig(backend='torch', device='cpu'),
        load=LoadConfig(model=str(src.path), dtype='f32', mtp=True),
        decode=DecodeConfig(capacity=256),
        spec=SpecConfig(k=spec),
        prefix=PrefixConfig(enabled=True, device_mib=1024, host_mib=0),
        lookup=LookupConfig(ngram=lookup) if lookup else None,
    )


def test_injected_generation_equals_hand_assembled():
    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(4).integers(0, cfg.vocab_size, 9).tolist()

    ops = TorchOps('cpu')
    ref_model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)

    for spec, lookup in ((0, 0), (3, 0), (0, 1), (3, 1)):  # (unigram lookup: any repeated token is a match)
        injector = inj.create_injector(bind_qwen(**_configs(src, spec, lookup)))
        runner = injector[GenerationRunner]

        res = runner.run(GenerationParams(prompt=prompt, max_new_tokens=12))
        ref = generate(ref_model, prompt, max_new_tokens=12, spec=spec, lookup_ngram=lookup, capacity=256)
        assert list(res.tokens) == list(ref.tokens), (spec, lookup, res.tokens, ref.tokens)
        assert (res.rounds, res.drafted, res.accepted) == (ref.rounds, ref.drafted, ref.accepted), (spec, lookup)
        assert res.reused == 0 and (res.drafted > 0) == bool(spec or lookup), (spec, lookup, res)

        # a follow-up in a new request scope resumes from the singleton store
        res2 = runner.run(GenerationParams(prompt=[*prompt, *res.tokens, 5], max_new_tokens=4))
        assert res2.reused == len(prompt) + len(res.tokens), (spec, res2.reused)

        # sampled with penalties: same seed, same tokens as the hand-assembled path
        params = GenerationParams(
            prompt=prompt,
            max_new_tokens=10,
            temperature=1.0,
            top_k=20,
            seed=7,
            presence_penalty=1.5,
        )
        got = runner.run(params)
        ref_s = generate(
            ref_model,
            prompt,
            max_new_tokens=10,
            spec=spec,
            lookup_ngram=lookup,
            capacity=256,
            sampler=Sampler(temperature=1.0, top_k=20, seed=7),
            presence_penalty=1.5,
        )
        assert list(got.tokens) == list(ref_s.tokens), (spec, lookup, got.tokens, ref_s.tokens)

        # the model and the store are singletons; the store is the prefix cache
        assert injector[PrefixCache] is injector[PrefixCache]


def test_injected_engine_serves_json_mode():
    cfg, hf, src = synthetic_source()
    engine = create_engine(
        serve=ServeConfig(
            defaults=SamplingDefaults(temperature=1.0, top_k=0, top_p=1.0, max_tokens=200),
            model_name='tiny',
        ),
        **_configs(src, 2),
    )
    engine.log = None
    assert engine.prefix_cache is not None  # bound (prefix caching is on), so /health reports it
    engine.start()

    res = engine.run_sync(Request.from_json({
        'messages': [{'role': 'user', 'content': 'json please'}],
        'response_format': {'type': 'json_object'},
        'chat_template_kwargs': {'enable_thinking': False},
        # a fixed seed: the grammar makes every output a valid JSON prefix, but an unlucky draw from the clock-seeded
        # default can still run into max_tokens mid-string (this one is an 82-token document)
        'seed': 0,
    }, engine.defaults, engine.enable_thinking))
    json.loads(res.content)  # grammar-constrained: valid JSON when it stops
    assert res.finish_reason == 'stop', res.finish_reason
