from ..chain import chain
from ..funcs import of


def test_chain_codec_order_and_pair():
    angle = of(
        lambda s: f'<{s}>',
        lambda s: s.removeprefix('<').removesuffix('>'),
    )
    square = of(
        lambda s: f'[{s}]',
        lambda s: s.removeprefix('[').removesuffix(']'),
    )
    codec = chain(angle, square)

    assert codec.encode('value') == '[<value>]'
    assert codec.decode('[<value>]') == 'value'
    assert codec.as_pair().forward('value') == '[<value>]'
    assert codec.as_pair().backward('[<value>]') == 'value'
