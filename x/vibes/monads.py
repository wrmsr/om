"""
Replay-based ('thermometer continuation') multi-shot do-notation.

Monadic programs are written as async function bodies whose binds are awaits. The driver never resumes a suspended
frame: to invoke a continuation it re-executes the whole body from scratch, fast-forwarding through a recorded trace of
previously bound values, and forks at the frontier. Continuations may therefore be invoked zero, one, or many times, at
the cost of O(paths) re-execution - and bodies must be deterministic, with all effects confined to the monad.

Monads whose extra type parameters are erased by the coroutine type (an error type E, a state type S) get their do
fronts and effect vocabularies as generic classes pinned by explicit specialization - ResultDo[str](), SearchOps[str]()
- since without higher-kinded types those parameters cannot be inferred from the decorated body.
"""
import dataclasses as dc
import functools
import typing as ta


E = ta.TypeVar('E')
P = ta.ParamSpec('P')
R = ta.TypeVar('R')
S = ta.TypeVar('S')
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


## Maybes


class MaybeM(ta.Generic[T]):
    """Zero-or-one: absence short-circuits the remainder of the body."""

    def __init__(self, xs: ta.Iterable[T] = ()) -> None:
        super().__init__()

        self._xs = tuple(xs)
        if len(self._xs) > 1:
            raise ValueError(self._xs)

    @property
    def xs(self) -> ta.Sequence[T]:
        return self._xs

    @staticmethod
    def pure(x: U) -> MaybeM[U]:
        return MaybeM((x,))

    def bind(self, f: ta.Callable[[T], MaybeM[U]]) -> MaybeM[U]:
        if self._xs:
            return f(self._xs[0])
        return MaybeM(())

    def __await__(self) -> ta.Generator[MaybeM[T], ta.Any, T]:
        return ta.cast(T, (yield self))


def just(x: T) -> MaybeM[T]:
    return MaybeM((x,))


def nothing() -> MaybeM[ta.Any]:
    return MaybeM(())


def lookup(m: ta.Mapping[T, U], k: T) -> MaybeM[U]:
    return just(m[k]) if k in m else nothing()


def maybe_do(fn: ta.Callable[P, ta.Coroutine[ta.Any, ta.Any, R]]) -> ta.Callable[P, MaybeM[R]]:
    @functools.wraps(fn)
    def inner(*args: P.args, **kwargs: P.kwargs) -> MaybeM[R]:
        return ta.cast('MaybeM[R]', run_do(MaybeM.pure, fn, *args, **kwargs))

    return inner


## Results


class ResultM(ta.Generic[E, T]):
    """Ok-or-err: the first error short-circuits the remainder of the body ('railway' style)."""

    def __init__(self, *, oks: ta.Iterable[T] = (), errs: ta.Iterable[E] = ()) -> None:
        super().__init__()

        self._oks = tuple(oks)
        self._errs = tuple(errs)
        if len(self._oks) + len(self._errs) != 1:
            raise ValueError((self._oks, self._errs))

    @property
    def oks(self) -> ta.Sequence[T]:
        return self._oks

    @property
    def errs(self) -> ta.Sequence[E]:
        return self._errs

    @staticmethod
    def pure(x: U) -> ResultM[ta.Any, U]:
        return ResultM(oks=(x,))

    def bind(self, f: ta.Callable[[T], ResultM[E, U]]) -> ResultM[E, U]:
        if self._oks:
            return f(self._oks[0])
        return ResultM(errs=self._errs)

    def __await__(self) -> ta.Generator[ResultM[E, T], ta.Any, T]:
        return ta.cast(T, (yield self))


def err(e: E) -> ResultM[E, ta.Any]:
    return ResultM(errs=(e,))


class ResultDo(ta.Generic[E]):
    """
    A typed do front for ResultM. E is erased from the decorated body's Coroutine type, so it cannot be inferred - it is
    pinned instead by explicit specialization: @ResultDo[str]().
    """

    def __call__(self, fn: ta.Callable[P, ta.Coroutine[ta.Any, ta.Any, R]]) -> ta.Callable[P, ResultM[E, R]]:
        @functools.wraps(fn)
        def inner(*args: P.args, **kwargs: P.kwargs) -> ResultM[E, R]:
            return ta.cast('ResultM[E, R]', run_do(ResultM.pure, fn, *args, **kwargs))

        return inner


## Searches


class SearchM(ta.Generic[S, T]):
    """
    StateT over ListM, fused: a stateful nondeterministic computation S -> [(T, S)]. Each alternative evolves its own
    copy of the state. Specialized to S=str this is the classic combinator-parser monad.
    """

    def __init__(self, run: ta.Callable[[S], ta.Iterable[tuple[T, S]]]) -> None:
        super().__init__()

        self._run = run

    def run(self, s: S) -> ta.Sequence[tuple[T, S]]:
        return tuple(self._run(s))

    @staticmethod
    def pure(x: U) -> SearchM[ta.Any, U]:
        return SearchM(lambda s: ((x, s),))

    def bind(self, f: ta.Callable[[T], SearchM[S, U]]) -> SearchM[S, U]:
        return SearchM(lambda s: [r for x, s2 in self._run(s) for r in f(x)._run(s2)])

    def __await__(self) -> ta.Generator[SearchM[S, T], ta.Any, T]:
        return ta.cast(T, (yield self))


class SearchOps(ta.Generic[S]):
    """
    A typed effect vocabulary for a SearchM stack with S pinned by explicit specialization - the role mtl type classes
    play in Haskell. Methods pin S through self, letting call sites infer types a free function could not (a bare get()
    would solve S to Never).
    """

    def do(self, fn: ta.Callable[P, ta.Coroutine[ta.Any, ta.Any, R]]) -> ta.Callable[P, SearchM[S, R]]:
        @functools.wraps(fn)
        def inner(*args: P.args, **kwargs: P.kwargs) -> SearchM[S, R]:
            return ta.cast('SearchM[S, R]', run_do(SearchM.pure, fn, *args, **kwargs))

        return inner

    def get(self) -> SearchM[S, S]:
        return SearchM(lambda s: ((s, s),))

    def put(self, s2: S) -> SearchM[S, None]:
        return SearchM(lambda s: ((None, s2),))

    def choose(self, xs: ta.Iterable[T]) -> SearchM[S, T]:
        xt = tuple(xs)
        return SearchM(lambda s: tuple((x, s) for x in xt))

    def guard(self, ok: bool) -> SearchM[S, None]:
        return SearchM(lambda s: ((None, s),) if ok else ())

    def alt(self, *ms: SearchM[S, T]) -> SearchM[S, T]:
        return SearchM(lambda s: [r for m in ms for r in m._run(s)])  # noqa: SLF001


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


#


@dist_do
async def diagnosis() -> tuple[bool, bool]:
    flu = await flip(.1)
    covid = await flip(.05)

    fever = await flip(.9 if flu or covid else .05)
    cough = await flip(.8 if covid else .6 if flu else .1)

    await condition(fever and cough)

    return (flu, covid)


#


@maybe_do
async def grandboss(reports_to: ta.Mapping[str, str], who: str) -> str:
    boss = await lookup(reports_to, who)
    return await lookup(reports_to, boss)


#


@dc.dataclass(frozen=True)
class Server:
    host: str
    port: int


@ResultDo[str]()
async def parse_port(s: str) -> int:
    if not s.isdigit():
        await err(f'bad port: {s!r}')
    return int(s)


@ResultDo[str]()
async def parse_server(spec: str) -> Server:
    host, _, port_s = spec.partition(':')
    if not host:
        await err(f'missing host: {spec!r}')

    port = await parse_port(port_s)
    if not 0 < port < 65536:
        await err(f'port out of range: {port}')

    return Server(host, port)


#


ps = SearchOps[str]()


def item() -> SearchM[str, str]:
    return SearchM(lambda s: ((s[0], s[1:]),) if s else ())


@ps.do
async def sat(pred: ta.Callable[[str], bool]) -> str:
    c = await item()
    await ps.guard(pred(c))
    return c


def char(c: str) -> SearchM[str, str]:
    return sat(lambda c2: c2 == c)


@ps.do
async def number() -> int:
    return int(await sat(str.isdigit))


@ps.do
async def parens() -> int:
    await char('(')
    v = await expr()
    await char(')')
    return v


@ps.do
async def factor() -> int:
    return await ps.alt(number(), parens())


@ps.do
async def term() -> int:
    v = await factor()
    while await ps.choose((True, False)):  # nondeterministically extend or stop
        await char('*')
        v *= await factor()
    return v


@ps.do
async def expr() -> int:
    v = await term()
    while await ps.choose((True, False)):
        await char('+')
        v += await term()
    return v


def parse(src: str) -> ta.Sequence[int]:
    return [v for v, rest in expr().run(src) if not rest]


##


def _main() -> None:
    qs = queens(8)
    print(f'{len(qs.xs)} queens solutions, first: {qs.xs[0]}')

    post = diagnosis().norm()
    for (flu, covid), w in sorted(post.ws.items(), key=lambda kv: -kv[1]):
        print(f'flu={flu!s:<5} covid={covid!s:<5} {w:.3f}')

    rt = {'ann': 'bob', 'bob': 'cat'}
    print(f'grandboss: {grandboss(rt, "ann").xs} {grandboss(rt, "bob").xs}')

    for spec in ('db.internal:5432', 'db.internal:x', ':80'):
        r = parse_server(spec)
        print(f'{spec!r} -> {r.oks or r.errs}')

    for src in ('2*3+4', '(1+2)*3', '2*3+'):
        print(f'{src!r} -> {parse(src)}')


if __name__ == '__main__':
    _main()
