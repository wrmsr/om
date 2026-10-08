"""
Run arg processing per concern, against an injected host. Options are compared as a multiset: their order is not part of
what a run means, the image and command after them are.
"""
import functools
import re
import tempfile
import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.secrets import all as sec

from ..config import Config
from ..run import ID_LABEL
from ..run import RunArgs
from ..run import RunHost
from ..run import RunSecretsUnavailableError
from ..run import process_run_args


##


_SHA = 'sha256:' + '0' * 64
_RUN_ID = uuid.UUID('01234567-89ab-7cde-8f01-23456789abcd')
_LABEL = f'--label={ID_LABEL}={_RUN_ID}'
_HOST_PLATFORM = '--env=DOCKER_HOST_PLATFORM=linux'

_CACHE_MOUNTS = {
    'pip': '/om/.cache/pip',
    'uv': '/om/.cache/uv',
}


@dc.dataclass(frozen=True, kw_only=True)
class _Run:
    options: list[str]
    image_and_command: list[str]
    env: dict[str, str] | None
    staged: dict[str, str]
    staging_dir: str | None


def _process(
        tmp_path,
        args: RunArgs | None = None,
        *,
        cfg: Config | None = None,
        sys_platform: str = 'linux',
        home: str | None = '/home/tester',
        with_git: bool = True,
        load_secrets=None,
) -> _Run:
    cwd = tmp_path / 'cwd'
    cwd.mkdir()
    if with_git:
        (cwd / '.git').mkdir()

    staging_dirs: list[str] = []

    def mkdtemp() -> str:
        d = tempfile.mkdtemp(dir=tmp_path)
        staging_dirs.append(d)
        return d

    p = process_run_args(
        cfg if cfg is not None else Config('ubuntu:24.04', cache_mounts=_CACHE_MOUNTS),
        args if args is not None else RunArgs(id=_RUN_ID),
        _SHA,
        host=RunHost(
            platform_system='Linux',
            sys_platform=sys_platform,
            home=home,
            cwd=str(cwd),
            load_secrets=load_secrets,
            mkdtemp=mkdtemp,
        ),
    )

    assert len(staging_dirs) <= 1
    staged: dict[str, str] = {}
    for d in staging_dirs:
        for name in ('autoexec.sh', 'shift-uid.sh'):
            try:
                staged[name] = (tmp_path / d / name).read_text()
            except FileNotFoundError:
                pass

    i = p.args.index(_SHA)
    return _Run(
        options=sorted(p.args[:i]),
        image_and_command=p.args[i:],
        env={k: v.reveal() if isinstance(v, sec.Secret) else v for k, v in p.env.items()} if p.env else None,
        staged=staged,
        staging_dir=staging_dirs[0] if staging_dirs else None,
    )


def _staging_mount(run: _Run) -> str:
    return f'--mount=type=bind,src={run.staging_dir},dst=/dockerdev,readonly'


##


def test_defaults(tmp_path):
    run = _process(tmp_path)
    assert run.options == sorted(['--rm', '-it', _HOST_PLATFORM, _LABEL])
    assert run.image_and_command == [_SHA, 'bash']
    assert run.env is None
    assert run.staging_dir is None


def test_unknown_args_replace_the_defaults(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, unknown_args=['--name=x', '-d']))
    assert run.options == sorted(['--name=x', '-d', _HOST_PLATFORM, _LABEL])


def test_simple_options(tmp_path):
    run = _process(tmp_path, RunArgs(
        id=_RUN_ID,
        privileged=True,
        offline=True,
        mounts=['type=bind,src=/a,dst=/b', 'type=volume,src=v,dst=/c'],
        mount_docker_sock=True,
        no_host_platform=True,
        no_id_label=True,
    ))
    assert run.options == sorted([
        '--rm',
        '-it',
        '--privileged',
        '--pull=never',
        '--mount=type=bind,src=/a,dst=/b',
        '--mount=type=volume,src=v,dst=/c',
        '--mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock',
    ])


def test_extra_args_replace_the_command(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, extra_args=['python3', '-c', 'x']))
    assert run.image_and_command == [_SHA, 'python3', '-c', 'x']


def test_run_id_is_generated(tmp_path):
    p = process_run_args(
        Config('ubuntu:24.04'),
        RunArgs(),
        _SHA,
        host=RunHost(platform_system='Linux', sys_platform='linux', cwd=str(tmp_path)),
    )
    assert p.id.version == 7
    assert f'--label={ID_LABEL}={p.id}' in p.args


##


def test_cache_mounts(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, mount_caches=True))
    assert run.options == sorted([
        '--rm',
        '-it',
        '--mount=type=volume,src=om-dockerdev-cache,dst=/cache',
        _HOST_PLATFORM,
        _staging_mount(run),
        '--entrypoint=/dockerdev/autoexec.sh',
        _LABEL,
    ])
    assert run.staged == {'autoexec.sh': '\n'.join([
        '#!/bin/sh',
        'set -e',
        'sudo chown om:om /cache',
        'if ! [ -d /cache/pip ] ; then mkdir -p /cache/pip ; fi',
        'rm -rf /om/.cache/pip || true',
        'ln -s /cache/pip /om/.cache/pip',
        'if ! [ -d /cache/uv ] ; then mkdir -p /cache/uv ; fi',
        'rm -rf /om/.cache/uv || true',
        'ln -s /cache/uv /om/.cache/uv',
        'UV_LINK_MODE=symlink exec "$@"',
    ])}


def test_cache_mounts_need_configured_caches(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, mount_caches=True), cfg=Config('ubuntu:24.04'))
    assert run.options == sorted(['--rm', '-it', _HOST_PLATFORM, _LABEL])
    assert run.staging_dir is None


def test_git_mounts(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, mount_git=True))
    git_mount = f'--mount=type=bind,src={tmp_path}/cwd/.git,dst=/git,ro'
    assert run.options == sorted(['--rm', '-it', git_mount, _HOST_PLATFORM, _LABEL])


def test_git_clone(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, clone_mount_git=True))
    assert f'--mount=type=bind,src={tmp_path}/cwd/.git,dst=/git,ro' in run.options
    assert '--entrypoint=/dockerdev/autoexec.sh' in run.options
    assert run.staged['autoexec.sh'].splitlines()[2:] == [
        'git config --global --add safe.directory /git',
        'git clone -q /git /work/git',
        'exec "$@"',
    ]


def test_git_mount_needs_a_git_dir(tmp_path):
    with pytest.raises(RuntimeError):
        _process(tmp_path, RunArgs(id=_RUN_ID, mount_git=True), with_git=False)


def test_autoexecs_follow_the_steps_lines(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, clone_mount_git=True, autoexecs=['echo one', 'echo "two"']))
    assert run.staged['autoexec.sh'].splitlines()[2:] == [
        'git config --global --add safe.directory /git',
        'git clone -q /git /work/git',
        'echo one',
        'echo "two"',
        'exec "$@"',
    ]


##


def _shift_uid_src() -> str:
    return lang.get_relative_resources('..resources', globals=globals())['shift-uid.sh'].read_text()


def _shift_uid_options(inner_entrypoint: str) -> list[str]:
    return [
        '--user=0:0',
        '--env=SHIFTUID_EXTERNAL_UID=1000',
        '--env=SHIFTUID_EXTERNAL_GID=1001',
        '--env=SHIFTUID_INTERNAL_USER=om',
        f'--env=SHIFTUID_INTERNAL_ENTRYPOINT={inner_entrypoint}',
        '--entrypoint=/dockerdev/shift-uid.sh',
    ]


def test_shift_uid(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, shift_uid=(1000, 1001)))
    assert run.options == sorted([
        '--rm',
        '-it',
        _HOST_PLATFORM,
        _staging_mount(run),
        *_shift_uid_options(''),
        _LABEL,
    ])
    assert run.staged == {'shift-uid.sh': _shift_uid_src()}


def test_shift_uid_wraps_the_autoexec_entrypoint(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, shift_uid=(1000, 1001), autoexecs=['echo hi']))

    # One staging dir and mount for both scripts, and only the outer entrypoint given to docker.
    assert run.options == sorted([
        '--rm',
        '-it',
        _HOST_PLATFORM,
        _staging_mount(run),
        *_shift_uid_options('/dockerdev/autoexec.sh'),
        _LABEL,
    ])
    assert run.staged == {
        'autoexec.sh': '#!/bin/sh\nset -e\necho hi\nexec "$@"',
        'shift-uid.sh': _shift_uid_src(),
    }


##


def test_x11_linux(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, x11=True))
    assert run.options == sorted([
        '--rm',
        '-it',
        _HOST_PLATFORM,
        '--env=DISPLAY',
        '--volume=/tmp/.X11-unix:/tmp/.X11-unix:rw',
        '--volume=/home/tester/.Xauthority:/tmp/.Xauthority:ro',
        '--env=XAUTHORITY=/tmp/.Xauthority',
        _LABEL,
    ])


def test_x11_darwin(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, x11=True), sys_platform='darwin')
    assert run.options == sorted(['--rm', '-it', _HOST_PLATFORM, '--env=DISPLAY=host.docker.internal:0', _LABEL])


def test_x11_needs_a_supported_host(tmp_path):
    with pytest.raises(OSError):  # noqa: PT011
        _process(tmp_path, RunArgs(id=_RUN_ID, x11=True), sys_platform='win32')


##


_SECRETS = {
    'foo_key': 'foo-value',
    'bar_key': 'bar-value',
    'other': 'other-value',
}


def _load_secrets() -> sec.Secrets:
    return sec.MappingSecrets(_SECRETS)


def test_secrets_inject_every_match(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, inject_secrets_pats=['.*_key']), load_secrets=_load_secrets)

    # Passed through by name only: the values are in the docker client's environment, never its argv.
    assert run.options == sorted(['--rm', '-it', _HOST_PLATFORM, _LABEL, '--env=FOO_KEY', '--env=BAR_KEY'])
    assert run.env == {'FOO_KEY': 'foo-value', 'BAR_KEY': 'bar-value'}


def test_secrets_patterns_may_be_compiled(tmp_path):
    run = _process(tmp_path, RunArgs(id=_RUN_ID, inject_secrets_pats=[re.compile('oth.*')]), load_secrets=_load_secrets)
    assert '--env=OTHER' in run.options
    assert run.env == {'OTHER': 'other-value'}


def test_secrets_need_a_source(tmp_path):
    with pytest.raises(RunSecretsUnavailableError):
        _process(tmp_path, RunArgs(id=_RUN_ID, inject_secrets_pats=['.*']))


def test_secrets_are_not_loaded_unless_asked_for(tmp_path):
    def load_secrets():
        raise AssertionError('should not have been called')

    run = _process(tmp_path, load_secrets=load_secrets)
    assert run.env is None


##


def test_kitchen_sink(tmp_path):
    run = _process(
        tmp_path,
        RunArgs(
            id=_RUN_ID,
            unknown_args=['--name=sink'],
            privileged=True,
            mount_caches=True,
            clone_mount_git=True,
            autoexecs=['echo hi'],
            shift_uid=(1000, 1001),
            x11=True,
            inject_secrets_pats=['foo.*'],
            extra_args=['python3'],
        ),
        load_secrets=functools.partial(sec.MappingSecrets, _SECRETS),
    )

    assert run.options == sorted([
        '--name=sink',
        '--privileged',
        '--mount=type=volume,src=om-dockerdev-cache,dst=/cache',
        f'--mount=type=bind,src={tmp_path}/cwd/.git,dst=/git,ro',
        _HOST_PLATFORM,
        _staging_mount(run),
        *_shift_uid_options('/dockerdev/autoexec.sh'),
        '--env=DISPLAY',
        '--volume=/tmp/.X11-unix:/tmp/.X11-unix:rw',
        '--volume=/home/tester/.Xauthority:/tmp/.Xauthority:ro',
        '--env=XAUTHORITY=/tmp/.Xauthority',
        _LABEL,
        '--env=FOO_KEY',
    ])
    assert run.image_and_command == [_SHA, 'python3']
    assert run.env == {'FOO_KEY': 'foo-value'}
    assert sorted(run.staged) == ['autoexec.sh', 'shift-uid.sh']
    assert run.staged['autoexec.sh'].splitlines()[-1] == 'UV_LINK_MODE=symlink exec "$@"'
