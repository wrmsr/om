from .. import pairs as fpa


def test_simple():
    fp = fpa.of(lambda s: s.encode('utf-8'), lambda b: b.decode('utf-8'))
    assert fp.forward('hi') == b'hi'
    assert fp.backward(b'hi') == 'hi'


def test_compose():
    fp0 = fpa.of(
        lambda v: v + 1,
        lambda v: v - 1,
    )

    fp1 = fpa.of(
        lambda v: v * 3,
        lambda v: v // 3,
    )

    fp2 = fpa.compose(fp0, fp1)

    assert fp2.forward(10) == 33
    assert fp2.backward(33) == 10


def test_compose_types():
    fp0 = fpa.of[float, int](int, float)
    fp1 = fpa.of[int, str](str, int)
    fp2 = fpa.of[str, list[str]](list, ''.join)

    cfp = fpa.compose(fp0, fp1, fp2)
    assert cfp(13.1) == ['1', '3']
    assert cfp.backward(['2', '4']) == 24.


def test_invert():
    fp = fpa.of(lambda value: value + 1, lambda value: value - 1)

    inverted = fp.invert()
    assert inverted.forward(3) == 2
    assert inverted.backward(3) == 4
    assert inverted.invert() is fp


def test_compose_zero_or_one():
    fp = fpa.of(lambda value: value + 1, lambda value: value - 1)

    assert fpa.compose() is fpa.NOP
    assert fpa.compose(fp) is fp


def test_optional():
    fp = fpa.Optional(fpa.of(lambda value: value + 1, lambda value: value - 1))

    assert fp.forward(None) is None
    assert fp.backward(None) is None
    assert fp.forward(1) == 2
    assert fp.backward(2) == 1


def test_lines():
    fp = fpa.Lines()

    assert fp.forward(['first', 'second']) == 'first\nsecond'
    assert fp.backward('first\nsecond') == ['first', 'second']


def test_struct():
    fp = fpa.Struct('>IH')

    encoded = fp.forward((0x12345678, 0xABCD))
    assert encoded == b'\x12\x34\x56\x78\xab\xcd'
    assert fp.backward(encoded) == (0x12345678, 0xABCD)
