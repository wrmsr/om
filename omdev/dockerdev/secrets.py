import inspect
import json
import os.path
import subprocess
import typing as ta

from omcore import check
from omcore import lang
from omcore.os.pyremote.bestpython import get_best_python_sh
from omcore.os.pyremote.core import pyremote
from omcore.secrets import all as sec
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from ..home import secretinject
from ..home.paths import DEFAULT_HOME_DIR
from ..home.paths import HomePaths
from ..home.secretinject import inject_secrets
from ..home.secrets import DEFAULT_INJECTED_SECRETS_FILE_NAME
from ..home.secrets import load_secrets
from .run import LABEL_PREFIX


##


def _remote_main() -> None:
    prt = pyremote.bootstrap_finalize()  # noqa

    #

    import json

    args = json.loads(prt.input.read().decode('utf-8'))

    #

    inject_secrets(
        os.path.expanduser(args['file_path']),
        args['update'],
        make_dirs=True,
    )

    #

    raise SystemExit(0)


def _check_container_id(container_id: str) -> None:
    out = subprocess.check_output([
        'docker',
        'ps',
        f'--filter=id={container_id}',
        f'--filter=label={LABEL_PREFIX}',
        '--format=json',
    ]).decode('utf-8')

    lines = out.strip().splitlines()
    line = check.single(lines)

    dct = json.loads(line)

    check.equal(dct['ID'], container_id)


def _inject_update(
        container_id: str,
        secrets_file: str,
        update: ta.Mapping[str, ta.Any],
) -> None:
    _check_container_id(container_id)

    #

    args_dct = {
        'file_path': secrets_file,
        'update': update,
    }

    args_bytes = json.dumps(args_dct).encode('utf-8')

    #

    payload_src = '\n\n'.join([
        inspect.getsource(secretinject),
        check.not_none(pyremote.get_core_source()),
        inspect.getsource(_remote_main),
        '_remote_main()',
    ])

    #

    proc = subprocess.Popen(
        subprocess_maybe_shell_wrap_exec(
            'docker',
            'exec',
            '-i',
            container_id,
            'sh',
            '-c',
            get_best_python_sh(),
            '--',
            '-c',
            pyremote.build_bootstrap_source('pyrthing'),
        ),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    stdin = check.not_none(proc.stdin)
    stdout = check.not_none(proc.stdout)

    #

    pbr = pyremote.make_driver(  # noqa
        payload_src,
    ).run(stdout, stdin)

    stdin.write(args_bytes)
    stdin.close()

    proc.wait()


def inject_dockerdev_secrets(
        container_id: str,
        secrets: lang.SequenceNotStr[str | tuple[str, ta.Any]],
        *,
        secrets_file: str | None = None,
) -> None:
    if secrets_file is None:
        secrets_file = os.path.join(
            DEFAULT_HOME_DIR,
            HomePaths.config_subdir,
            DEFAULT_INJECTED_SECRETS_FILE_NAME,
        )

    #

    loaded_secrets: sec.Secrets | None = None

    update: dict[str, ta.Any] = {}

    for o in secrets:
        if isinstance(o, str):
            if loaded_secrets is None:
                loaded_secrets = load_secrets()

            update[o] = loaded_secrets.get(o).reveal()

        else:
            k, v = o
            update[k] = v

    #

    _inject_update(
        container_id,
        secrets_file,
        update,
    )
