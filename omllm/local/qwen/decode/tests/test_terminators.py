import typing as ta

from ...tokenizer import Tokenizer
from ..generation import Generation
from ..terminators import StopStringTerminator


##


class _Bytes:
    """Just enough of a Tokenizer for decoding: token i is TABLE[i]."""

    TABLE: ta.ClassVar[list[bytes]] = [b'a', b'b', b'\n', b'<eot>', 'é'.encode()[:1], 'é'.encode()[1:], b'xy']

    def token_bytes(self, i: int) -> bytes:
        return self.TABLE[i]


A, B, NL, EOT, E1, E2, XY = range(7)


def _stop(*stops: str) -> StopStringTerminator:
    return StopStringTerminator(ta.cast(Tokenizer, _Bytes()), stops, end_ids=[EOT])


def test_stop_strings():
    gen = Generation(prompt=[0], capacity=64)

    # the cut keeps the token completing the stop string; stopped_at is where it starts
    st = _stop('ba')
    assert st.cut(gen, (A, A)) is None
    assert st.cut(gen, (B, B, A, A)) == 3
    assert st.stopped_at == 3  # 'aa' committed, then 'bba': 'ba' starts at 3

    # a stop string across rounds, and across a multi-byte character split between tokens
    st = _stop('aé')
    assert st.cut(gen, (B, A)) is None
    assert st.cut(gen, (E1,)) is None
    assert st.cut(gen, (E2, B)) == 1
    assert st.stopped_at == 1

    # a stop string starting inside one token's text and completed in a later round
    st = _stop('xyb')
    assert st.cut(gen, (XY,)) is None
    assert st.cut(gen, (B,)) == 1
    assert st.stopped_at == 0

    # nothing at or after the end of turn is scanned: no match across it (a template newline after the end of turn)
    st = _stop('\n\n')
    assert st.cut(gen, (A, NL, EOT, NL)) is None
    assert st.stopped_at is None

    # no stop strings: never cuts
    assert _stop().cut(gen, (A, B, NL)) is None
