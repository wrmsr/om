# import io
# import os
# import pathlib
# import shutil
# import subprocess
# import typing as ta
#
# from omcore import dataclasses as dc
#
# from . import sexp as sx
#
#
# ##
#
#
# def _realpath(p: str | os.PathLike[str]) -> str:
#     return os.path.realpath(os.path.abspath(os.fspath(p)))
#
#
# def _ancestor_dirs(path: str) -> list[str]:
#     p = pathlib.Path(path)
#     # For /Users/me/src/repo -> ["/", "/Users", "/Users/me", "/Users/me/src"]
#     return [str(x) for x in reversed(p.parents)]
#
#
# ##
#
#
# @dc.dataclass(frozen=True, kw_only=True)
# class SandboxProfile:
#     profile: str
#     param_defs: ta.Sequence[str] | None = None
#
#
# def build_rg_sandbox_profile(
#         rg: str,
#         roots_real: ta.Sequence[str],
# ) -> SandboxProfile:
#     # Minimal-ish runtime read set. You can tighten this after seeing sandboxd logs.
#     tool_read_roots = [
#         '/System/Library',
#         '/usr/lib',
#         '/usr/share',
#         os.path.dirname(rg),
#     ]
#
#     if rg.startswith('/opt/homebrew/'):
#         tool_read_roots.append('/opt/homebrew')
#     elif rg.startswith('/usr/local/'):
#         tool_read_roots.extend([
#             '/usr/local/Cellar',
#             '/usr/local/opt',
#             '/usr/local/lib',
#         ])
#     elif rg.startswith('/opt/local/'):
#         tool_read_roots.append('/opt/local')
#
#     profile_lines: list[sx.Sexp] = [
#         ['version', 1],
#         ['deny', 'default'],
#         ['allow', 'process-exec', ['literal', ['param', sx.quote('RG_BIN')]]],
#         ['allow', 'sysctl-read'],
#         ['allow', 'file-read*', 'file-test-existence', ['literal', sx.quote('/')]],
#     ]
#
#     allow_read_lines: list[sx.Sexp] = []
#
#     param_defs: list[str] = [
#         f'RG_BIN={rg}',
#         f'RG_DIR={os.path.dirname(rg)}',
#     ]
#
#     for i, tr in enumerate(dict.fromkeys(tool_read_roots)):
#         if os.path.exists(tr):
#             key = f'TOOL_READ_{i}'
#             param_defs.append(f'{key}={tr}')
#             allow_read_lines.append(['subpath', ['param', sx.quote(key)]])
#
#     profile_lines.append(['allow', 'file-read*', *allow_read_lines])
#
#     # Allow ancestor metadata for path resolution, but not directory contents.
#     ancestor_params: list[str] = []
#     seen_ancestors: set[str] = set()
#     for r in roots_real:
#         for a in _ancestor_dirs(r):
#             if a not in seen_ancestors:
#                 seen_ancestors.add(a)
#                 key = f'ANCESTOR_{len(ancestor_params)}'
#                 ancestor_params.append(key)
#                 param_defs.append(f'{key}={a}')
#
#     if ancestor_params:
#         ancestor_param_lines: list[sx.Sexp] = []
#         for key in ancestor_params:
#             ancestor_param_lines.append(['literal', ['param', sx.quote(key)]])
#         profile_lines.append(['allow', 'file-read-metadata', *ancestor_param_lines])
#
#     # Allow the actual requested roots.
#     for i, r in enumerate(roots_real):
#         key = f'ROOT_{i}'
#         param_defs.append(f'{key}={r}')
#         profile_lines.append(['allow', 'file-read*', ['literal', ['param', sx.quote(key)]]])
#         profile_lines.append(['allow', 'file-read*', ['subpath', ['param', sx.quote(key)]]])
#
#     out = io.StringIO()
#     sx.render_to(out, *profile_lines)
#     out.write('\n')
#     profile = out.getvalue()
#
#     return SandboxProfile(
#         profile=profile,
#         param_defs=param_defs or None,
#     )
#
#
# ##
#
#
# # These are defense-in-depth against rg features that read surprising places or spawn helper programs.
# SAFETY_RG_ARGS: ta.Final[ta.Sequence[str]] = [
#     '--no-config',
#     '--no-pre',
#     '--no-search-zip',
#     '--no-follow',
#     '--no-ignore-parent',
#     '--no-ignore-global',
#     '--color=never',
# ]
#
#
# def sandboxed_rg(
#         *,
#         roots: ta.Sequence[str | os.PathLike[str]],
#         args: ta.Sequence[str] | None = None,
#         timeout: float = 30.0,
# ) -> subprocess.CompletedProcess[str]:
#     """rg_args should be your own allowlisted flags, not arbitrary model-supplied text."""
#
#     if not roots:
#         raise ValueError('at least one allowed root is required')
#
#     rg0 = shutil.which('rg')
#     if rg0 is None:
#         raise FileNotFoundError('rg not found on PATH')
#
#     rg = _realpath(rg0)
#     roots_real = [_realpath(r) for r in roots]
#
#     for r in roots_real:
#         if not os.path.isdir(r):
#             raise NotADirectoryError(r)
#
#     sbp = build_rg_sandbox_profile(
#         rg,
#         roots_real,
#     )
#
#     defs: list[str] = []
#     for d in sbp.param_defs or []:
#         defs.extend(['-D', d])
#
#     cmd = [
#         '/usr/bin/sandbox-exec',
#         *defs,
#         '-p', sbp.profile,
#         rg,
#         *(args or []),
#         *SAFETY_RG_ARGS,
#         '--', *roots_real,
#     ]
#
#     env = {
#         'PATH': '/usr/bin:/bin',
#         'HOME': '/var/empty',
#         'LANG': os.environ.get('LANG', 'C.UTF-8'),
#         'LC_ALL': os.environ.get('LC_ALL', os.environ.get('LANG', 'C.UTF-8')),
#     }
#
#     return subprocess.run(
#         cmd,
#         cwd=roots_real[0],
#         env=env,
#         stdin=subprocess.DEVNULL,
#         capture_output=True,
#         text=True,
#         timeout=timeout,
#         close_fds=True,
#         check=False,
#     )
