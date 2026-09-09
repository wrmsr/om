# import inspect
# import json
# import os.path
# import subprocess
#
# from omcore import check
# from omcore import lang
# from omcore.os.pyremote.bestpython import get_best_python_sh
# from omcore.os.pyremote.core import pyremote
# from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec
#
# from ..home import secretinject
# from ..home.secretinject import inject_secrets
# from ..home.secrets import DEFAULT_INJECTED_SECRETS_FILE_NAME
# from ..home.secrets import load_secrets
#
#
# ##
#
#
# def _remote_main() -> None:
#     prt = pyremote.bootstrap_finalize()  # noqa
#
#     #
#
#     import json
#
#     args = json.loads(prt.input.read().decode('utf-8'))
#
#     #
#
#     inject_secrets(
#         os.path.expanduser(args['file_path']),
#         args['update'],
#     )
#
#     raise SystemExit(0)
#
#
# ##
#
#
# def inject_dockerdev_secrets(
#         container_id: str,
#         secret_keys: lang.SequenceNotStr[str],
#         *,
#         secrets_file: str | None = None,
# ) -> None:
#     if secrets_file is None:
#         secrets_file =
#
#     args_dct = {
#         'file_path': 'foo.json',
#         'update': {
#             'foo': True,
#         },
#     }
#
#     payload_src = '\n\n'.join([
#         inspect.getsource(secretinject),
#         check.not_none(pyremote.get_core_source()),
#         inspect.getsource(_remote_main),
#         '_remote_main()',
#     ])
#
#     proc = subprocess.Popen(
#         subprocess_maybe_shell_wrap_exec(
#             'docker',
#             'exec',
#             '-i',
#             container_id,
#             'sh',
#             '-c',
#             get_best_python_sh(),
#             '--',
#             '-c',
#             pyremote.build_bootstrap_source('pyrthing'),
#         ),
#         stdin=subprocess.PIPE,
#         stdout=subprocess.PIPE,
#     )
#
#     stdin = check.not_none(proc.stdin)
#     stdout = check.not_none(proc.stdout)
#
#     pbr = pyremote.make_driver(  # noqa
#         payload_src,
#     ).run(stdout, stdin)
#
#     stdin.write(json.dumps().encode('utf-8'))
#     stdin.close()
#
#     proc.wait()
#
#
# if __name__ == '__main__':
#     _main()
