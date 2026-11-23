"""The tokenizer from a GGUF's fields: what a source may say that the fields themselves do not."""
from ..tokenizer import Tokenizer
from ..tokenizer import bytes_to_unicode


##


def test_a_gguf_spec_may_ignore_merges():
    b2u = bytes_to_unicode()
    spec = {
        'kind': 'gguf',
        'model': 'gpt2',
        'pre': 'inkling2',
        'tokens': [*(b2u[i] for i in range(256)), 'ab', 'abc'],
        'token_type': None,
        'merges': ['a b'],
    }

    # by the merges alone 'abc' is never reached: no merge makes it
    plain = Tokenizer.from_spec(spec)
    assert not plain.ignore_merges
    assert plain.encode('abc') == [256, ord('c')] and plain.encode('ab') == [256]

    # a word that is a token as it stands is that token, as tokenizer.json's option of the name has it; any other
    # word is merged as before
    whole = Tokenizer.from_spec({**spec, 'ignore_merges': True})
    assert whole.ignore_merges
    assert whole.encode('abc') == [257]
    assert whole.encode('ab abcd') == plain.encode('ab abcd') == [256, ord(' '), 256, ord('c'), ord('d')]
