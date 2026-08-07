import abc
import functools
import os
import typing as ta

from .. import check
from .. import dataclasses as dc
from .. import lang


if ta.TYPE_CHECKING:
    import runpy

    from . import services

else:
    runpy = lang.proxy_import('runpy')

    services = lang.proxy_import('.services', __package__)


##


class Target(dc.Case):
    @classmethod
    def of(cls, obj: ta.Any) -> Target:
        if isinstance(obj, Target):
            return obj

        elif isinstance(obj, str):
            return NameTarget(obj)

        elif callable(obj):
            return FnTarget(obj)

        elif isinstance(obj, services.Service):
            return services.ServiceTarget(obj)

        elif isinstance(obj, services.Service.Config):
            return services.ServiceConfigTarget(obj)

        else:
            raise TypeError(obj)


class TargetRunner(lang.Abstract):
    @abc.abstractmethod
    def run(self) -> None:
        raise NotImplementedError


@functools.singledispatch
def target_runner_for(target: Target) -> TargetRunner:
    raise TypeError(target)


##


class FnTarget(Target):
    fn: ta.Callable[[], ta.Any]


class FnTargetRunner(TargetRunner, dc.Frozen):
    target: FnTarget

    def run(self) -> None:
        obj = self.target.fn()
        if obj is not None:
            tgt = Target.of(obj)
            tr = target_runner_for(tgt)
            tr.run()


@target_runner_for.register
def _(target: FnTarget) -> FnTargetRunner:
    return FnTargetRunner(target)


##


class NameTarget(Target):
    name: str

    @classmethod
    def for_obj(
            cls,
            obj: ta.Any,
            *,
            globals: ta.Mapping[str, ta.Any] | None = None,  # noqa
            no_module_name_lookup: bool = False,
    ) -> NameTarget:
        if globals is None:
            globals = obj.__globals__  # noqa
        if not no_module_name_lookup:
            mn = lang.get_real_module_name(globals)
        else:
            mn = globals['__name__']
        qn = obj.__qualname__
        return NameTarget('.'.join([mn, qn]))


class NameTargetRunner(TargetRunner, dc.Frozen):
    target: NameTarget

    def run(self) -> None:
        name = self.target.name
        if lang.can_import(name):
            runpy._run_module_as_main(name)  # type: ignore  # noqa
        else:
            obj = lang.import_attr(self.target.name)
            tgt = Target.of(obj)
            tr = target_runner_for(tgt)
            tr.run()


@target_runner_for.register
def _(target: NameTarget) -> NameTargetRunner:
    return NameTargetRunner(target)


##


class ExecTarget(Target):
    cmd: ta.Sequence[str] = dc.xfield(coerce=check.of_not_isinstance(str))

    _: dc.KW_ONLY

    cwd: str | None = None

    env: ta.Mapping[str, str | None] | None = dc.xfield(None, repr_fn=lambda env: (
        repr({k: lang.LiteralRepr('...') if v is not None else None for k, v in env.items()}) if env is not None else None  # noqa
    ))


class ExecTargetRunner(TargetRunner, dc.Frozen):
    target: ExecTarget

    def run(self) -> None:
        if (cwd := self.target.cwd) is not None:
            os.chdir(os.path.expanduser(cwd))

        env = dict(os.environ)
        if (tgt_env := self.target.env):
            env = {k: v for k, v in {**env, **tgt_env}.items() if v is not None}

        os.execle(*self.target.cmd, env)


@target_runner_for.register
def _(target: ExecTarget) -> ExecTargetRunner:
    return ExecTargetRunner(target)
