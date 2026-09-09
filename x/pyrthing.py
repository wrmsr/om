import inspect
import json
import subprocess

from omcore import check
from omcore.os.pyremote.bestpython import get_best_python_sh
from omcore.os.pyremote.core import pyremote
from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec
from omdev.home import secretinject
from omdev.home.secretinject import inject_secrets


##


def _remote_main() -> None:
    prt = pyremote.bootstrap_finalize()  # noqa

    #

    import json

    args = json.loads(prt.input.read().decode('utf-8'))

    inject_secrets(
        args['file'],
        args['updates'],
    )

    import time
    time.sleep(10)

    raise SystemExit(0)


##


def _main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('container_id', metavar='container-id')

    args = parser.parse_args(argv)

    #

    payload_src = '\n\n'.join([
        inspect.getsource(secretinject),
        check.not_none(pyremote.get_core_source()),
        inspect.getsource(_remote_main),
        '_remote_main()',
    ])

    proc = subprocess.Popen(
        subprocess_maybe_shell_wrap_exec(
            'docker',
            'exec',
            '-i',
            args.container_id,
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

    pbr = pyremote.make_driver(  # noqa
        payload_src,
    ).run(stdout, stdin)

    stdin.write(json.dumps({
        'file': 'foo.json',
        'updates': {
            'foo': True,
        },
    }).encode('utf-8'))
    stdin.close()

    proc.wait()


if __name__ == '__main__':
    _main()
