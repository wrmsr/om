import enum


##


class Precedence(enum.IntEnum):
    """
    Expression precedence levels, lowest to highest. A subexpression printed in a context requiring precedence `p` must
    be parenthesized if its own precedence is lower than `p`.
    """

    NAMED_EXPR = enum.auto()  # x := y
    YIELD = enum.auto()  # yield x, yield from x - bare only as a statement or on the right of an assignment
    TUPLE = enum.auto()  # x, y
    TEST = enum.auto()  # x if y else z, lambda: x
    OR = enum.auto()  # x or y
    AND = enum.auto()  # x and y
    NOT = enum.auto()  # not x
    CMP = enum.auto()  # x < y, x in y, x is y, ...
    EXPR = enum.auto()  # x | y
    BXOR = enum.auto()  # x ^ y
    BAND = enum.auto()  # x & y
    SHIFT = enum.auto()  # x << y
    ARITH = enum.auto()  # x + y
    TERM = enum.auto()  # x * y, x @ y, x / y, x // y, x % y
    FACTOR = enum.auto()  # -x, +x, ~x
    POWER = enum.auto()  # x ** y
    AWAIT = enum.auto()  # await x
    ATOM = enum.auto()

    def next(self) -> Precedence:
        try:
            return Precedence(self + 1)
        except ValueError:
            return self
