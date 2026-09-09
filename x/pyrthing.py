import inspect
import subprocess

from omcore import check

from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec
from omcore.os.pyremote.core import pyremote_get_core_source
from omcore.os.pyremote.core import pyremote_bootstrap_finalize
from omcore.os.pyremote.core import pyremote_build_bootstrap_source
from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.bestpython import get_best_python_sh


##


def _remote_main() -> None:
    prt = pyremote_bootstrap_finalize()

    prt.output.write(b'hi!\n')

    raise SystemExit(0)


##


def _main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('container_id', metavar='container-id')

    args = parser.parse_args(argv)

    #

    payload_src = '\n\n'.join([
        check.not_none(pyremote_get_core_source()),
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
            pyremote_build_bootstrap_source('pyrthing'),
        ),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    stdin = check.not_none(proc.stdin)
    stdout = check.not_none(proc.stdout)

    res = PyremoteBootstrapDriver(
        payload_src,
    ).run(stdout, stdin)

    print(res)
    print(stdout.read())


if __name__ == '__main__':
    _main()
