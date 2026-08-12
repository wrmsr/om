"""
Replay-based ('thermometer continuation') multi-shot do-notation.

Monadic programs are written as async function bodies whose binds are awaits. The driver never resumes a suspended
frame: to invoke a continuation it re-executes the whole body from scratch, fast-forwarding through a recorded trace of
previously bound values, and forks at the frontier. Continuations may therefore be invoked zero, one, or many times, at
the cost of O(paths) re-execution - and bodies must be deterministic, with all effects confined to the monad.
"""
import functools
import typing as ta


P = ta.ParamSpec('P')
R = ta.TypeVar('R')
T = ta.TypeVar('T')
U = ta.TypeVar('U')


##


def run_do(
        pure: ta.Callable[[ta.Any], ta.Any],
        fn: ta.Callable[..., ta.Coroutine[ta.Any, ta.Any, ta.Any]],
        /,
        *args: ta.Any,
        **kwargs: ta.Any,
) -> ta.Any:
    def step(trace: tuple[ta.Any, ...]) -> ta.Any:
        c = fn(*args, **kwargs)

        try:
            m = c.send(None)
            for v in trace:  # replaying history demands fn be deterministic up to its awaits
                m = c.send(v)
        except StopIteration as s:
            return pure(s.value)

        c.close()  # this frame is never resumed - each continuation invocation replays from scratch
        return m.bind(lambda x: step((*trace, x)))

    return step(())


## Lists


class ListM(ta.Generic[T]):
    """The nondeterminism monad: a bind forks the rest of the body once per element."""

    def __init__(self, xs: ta.Iterable[T]) -> None:
        super().__init__()

        self._xs = tuple(xs)

    @property
    def xs(self) -> ta.Sequence[T]:
        return self._xs

    @staticmethod
    def pure(x: U) -> ListM[U]:
        return ListM((x,))

    def bind(self, f: ta.Callable[[T], ListM[U]]) -> ListM[U]:
        return ListM(y for x in self._xs for y in f(x)._xs)

    def __await__(self) -> ta.Generator[ListM[T], ta.Any, T]:
        return ta.cast(T, (yield self))  # the single point where the untyped send channel is laundered into T


def choose(xs: ta.Iterable[T]) -> ListM[T]:
    return ListM(xs)


def guard(ok: bool) -> ListM[None]:
    return ListM((None,) if ok else ())


def list_do(fn: ta.Callable[P, ta.Coroutine[ta.Any, ta.Any, R]]) -> ta.Callable[P, ListM[R]]:
    @functools.wraps(fn)
    def inner(*args: P.args, **kwargs: P.kwargs) -> ListM[R]:
        return ta.cast('ListM[R]', run_do(ListM.pure, fn, *args, **kwargs))

    return inner


## Distributions


class DistM(ta.Generic[T]):
    """A finitely-supported weighted distribution monad: a bind multiplies weights down each branch."""

    def __init__(self, ws: ta.Mapping[T, float]) -> None:
        super().__init__()

        self._ws = dict(ws)

    @property
    def ws(self) -> ta.Mapping[T, float]:
        return self._ws

    @staticmethod
    def pure(x: U) -> DistM[U]:
        return DistM({x: 1.})

    def bind(self, f: ta.Callable[[T], DistM[U]]) -> DistM[U]:
        out: dict[U, float] = {}
        for x, p in self._ws.items():
            for y, q in f(x)._ws.items():
                out[y] = out.get(y, 0.) + p * q
        return DistM(out)

    def norm(self) -> DistM[T]:
        z = sum(self._ws.values())
        return DistM({x: w / z for x, w in self._ws.items()})

    def __await__(self) -> ta.Generator[DistM[T], ta.Any, T]:
        return ta.cast(T, (yield self))  # the single point where the untyped send channel is laundered into T


def flip(p: float) -> DistM[bool]:
    return DistM({True: p, False: 1. - p})


def condition(ok: bool) -> DistM[None]:
    return DistM({None: 1.} if ok else {})


def dist_do(fn: ta.Callable[P, ta.Coroutine[ta.Any, ta.Any, R]]) -> ta.Callable[P, DistM[R]]:
    @functools.wraps(fn)
    def inner(*args: P.args, **kwargs: P.kwargs) -> DistM[R]:
        return ta.cast('DistM[R]', run_do(DistM.pure, fn, *args, **kwargs))

    return inner


## Demos


@list_do
async def queens(n: int) -> tuple[int, ...]:
    cols: list[int] = []
    for row in range(n):
        c = await choose(range(n))

        await guard(all(
            c != c2 and abs(c - c2) != row - r2
            for r2, c2 in enumerate(cols)
        ))

        cols.append(c)

    return tuple(cols)


@dist_do
async def diagnosis() -> tuple[bool, bool]:
    flu = await flip(.1)
    covid = await flip(.05)

    fever = await flip(.9 if flu or covid else .05)
    cough = await flip(.8 if covid else .6 if flu else .1)

    await condition(fever and cough)

    return (flu, covid)


##


def _main() -> None:
    qs = queens(8)
    print(f'{len(qs.xs)} solutions, first: {qs.xs[0]}')

    post = diagnosis().norm()
    for (flu, covid), w in sorted(post.ws.items(), key=lambda kv: -kv[1]):
        print(f'flu={flu!s:<5} covid={covid!s:<5} {w:.3f}')


if __name__ == '__main__':
    _main()
