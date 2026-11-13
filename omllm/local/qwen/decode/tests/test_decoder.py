import numpy as np

from ...arch.qwen35 import load_qwen35
from ...backends.torch import TorchOps
from ...core.cache import Cache
from ...tests.test_parity import synthetic_source
from ..decoder import Decoder


##


def test_decoder_consumes_its_cache():
    """
    A decoder built with `consume` takes the cache's state layer by layer (a long context's KV is then never held
    twice) and decodes exactly as one built from a cache it leaves alone.
    """

    cfg, _, src = synthetic_source()
    ids = np.random.default_rng(3).integers(0, cfg.vocab_size, (1, 12))
    for kv_dtype in ('bf16', 'fp8'):
        ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', verbose=False)

        kept = Cache(cfg)
        model.forward(ids[:, :8], kept)
        given = Cache(cfg)
        model.forward(ids[:, :8], given)

        a = Decoder(model, kept, capacity=32)
        b = Decoder(model, given, capacity=32, consume=True)
        assert all(st is not None for st in kept.layers)
        assert all(st is None for st in given.layers)

        for t in ids[0, 8:]:
            la = ops.numpy(a.step(int(t)))
            lb = ops.numpy(b.step(int(t)))
            assert np.array_equal(la, lb), kv_dtype
