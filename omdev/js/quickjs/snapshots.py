"""
Data snapshots of a Context's user-defined globals.

A snapshot captures the own enumerable properties of `globalThis` which are not part of a pristine context - that is,
what user code has defined - and serializes them as one object graph, so shared references between globals survive.
Restoring assigns them onto another (usually fresh) context.

This is a *data* facility. See TODO.md for the limitations it inherits from the engine serializer: prototypes and
class identity are not preserved, unique symbol identity is lost, non-enumerable and symbol-keyed properties are
dropped, accessors are captured as their current value, and mutations to builtins are invisible.
"""
import typing as ta

from omcore import cached
from omcore import dataclasses as dc
from omcore.formats.json import all as json

from ._pyqjsng import Context
from ._pyqjsng import JsError


##


class SnapshotError(Exception):
    pass


class UnsupportedGlobalsError(SnapshotError):
    """Raised when globals which the engine cannot serialize are encountered in strict mode."""

    def __init__(self, reasons: ta.Mapping[str, str]) -> None:
        super().__init__(f'Unsupported globals: {", ".join(sorted(reasons))}')

        self.reasons = reasons


@dc.dataclass(frozen=True, kw_only=True)
class Snapshot:
    data: bytes

    # The globals captured in `data`, and - in skip mode - those left out, by name and engine reason.
    keys: ta.Sequence[str] = ()
    skipped: ta.Mapping[str, str] = dc.field(default_factory=dict)


##


@cached.function
def pristine_global_keys() -> frozenset[str]:
    """The own enumerable globals of a fresh context, which snapshots exclude."""

    return frozenset(_own_global_keys(Context()))


def _own_global_keys(ctx: Context) -> ta.Sequence[str]:
    return json.loads(ctx.eval('JSON.stringify(Object.keys(globalThis))'))


def user_global_keys(ctx: Context) -> ta.Sequence[str]:
    pristine = pristine_global_keys()
    return [k for k in _own_global_keys(ctx) if k not in pristine]


def _globals_object(ctx: Context, keys: ta.Sequence[str]) -> ta.Any:
    # Collected into a plain object so the graph serializes as a unit, preserving references shared between globals.
    return ctx.eval(
        f'(function(ks) {{ var o = {{}}; for (var i = 0; i < ks.length; i++) o[ks[i]] = globalThis[ks[i]]; return o; }})'  # noqa: E501
        f'({json.dumps(list(keys))})',
    )


def _key_error(ctx: Context, key: str) -> str | None:
    try:
        _globals_object(ctx, [key]).serialize()
    except JsError as e:
        return str(e)
    return None


##


def take_snapshot(ctx: Context, *, skip_unsupported: bool = False) -> Snapshot:
    """
    Captures the context's user-defined globals.

    Globals the engine cannot serialize - functions (including Python callables registered via `set`), promises,
    errors, proxies, and other live objects - raise `UnsupportedGlobalsError` naming them, or with
    `skip_unsupported=True` are left out and reported in the result's `skipped`.
    """

    keys = user_global_keys(ctx)

    try:
        data = _globals_object(ctx, keys).serialize()

    except JsError:
        # Diagnose per key only on the failing path - the common case stays a single pass.
        reasons = {k: e for k in keys if (e := _key_error(ctx, k)) is not None}
        if not reasons:
            raise

        if not skip_unsupported:
            raise UnsupportedGlobalsError(reasons) from None

        keys = [k for k in keys if k not in reasons]
        return Snapshot(
            data=_globals_object(ctx, keys).serialize(),
            keys=keys,
            skipped=reasons,
        )

    return Snapshot(
        data=data,
        keys=keys,
    )


def restore_snapshot(ctx: Context, snapshot: Snapshot | bytes) -> ta.Sequence[str]:
    """
    Assigns a snapshot's globals onto the context, returning the names restored.

    Existing globals of the same name are overwritten. Python callables are host objects and are never part of a
    snapshot - re-register them with `set` after restoring.
    """

    data = snapshot.data if isinstance(snapshot, Snapshot) else snapshot

    obj = ctx.deserialize(data)
    keys = obj.keys()
    # Called as a JS function object rather than via eval, so no temporary global is needed.
    ctx.eval('Object.assign')(ctx.global_this, obj)
    return keys
