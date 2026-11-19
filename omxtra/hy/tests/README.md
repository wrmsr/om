# Hy test isolation audit

Run the suite with `./python -m pytest omxtra/hy/tests`, optionally with `-n auto`. The ordinary pytest interpreter
must not call `globalruntime.install()`. Installation adds `sys.path_hooks` (rather than a `meta_path` finder), patches
source inspection, and wraps multiprocessing bootstrap functions.

## In-process tests

- `test_annotations.py`, `test_highlights.py`, `test_positions.py`, and `test_completer.py` check reader, model, or text
  behavior. The readline history case is quarantined separately.
- `test_ast.py`, `test_compiler.py`, `test_hyloader.py`, `test_hy2py.py`, `test_models.py`, and `test_reader.py` use
  private runtimes or explicit loaders. A few preamble assertions call `get_global_runtime()` without installing it.
  The AST, compiler, model, and reader files retain one private runtime per module, so their tests share that runtime.
- `test_macros.py` declares a macro on its test module and uses one runtime for all its tests.
- `native_tests/*.hy` are collected with one private runtime per Hy module, except for the cases listed below.
- `test_runtime.py` tests private runtimes and finders. Its clean-import test uses a fresh interpreter to compare
  process state before and after importing Hy and its CLI.

## Subprocess tests

- `test_bin.py` runs the `hy`, `hyc`, and `hy2py` command entrypoints, interpreter flags, stdio, and multiprocessing in
  child processes. Bytecode and generated files used for assertions are written under each test's `tmp_path`.
- `test_relocation.py` uses fresh interpreters to test alternate package names. Existing module caches cannot represent
  a clean relocation.
- `test_globalruntime.py` runs the quarantined cases below in one child pytest interpreter. The parent checks that Hy
  remains uninstalled.

## Quarantined cases

These cases need or currently change Python process state. Their source remains at its original location where
practical. The child runner selects them explicitly. These are audit notes, not pytest marks.

- `globalruntime_cases.py` and `runtime_global_cases.py` import `.hy` through Python, exercise `runpy` and zip import,
  or install and uninstall the global runtime. Several still use `monkeypatch` to alter `sys.path` or `sys.modules` in
  the child. Explicit paths and cleanup would make their state changes easier to inspect.
- `native_tests/hy_inspect.hy` needs the process-wide `inspect` integration and imports an empty `.hy` file through
  Python.
- `native_tests/repl.hy` replaces `sys.stdin` in its fixture. An injectable input stream would let it run in the
  main suite.
- `native_tests/hy_misc.hy::test_hyI_mangle_chain`, `native_tests/import.hy::test_no_surprise_shadow`, and
  `native_tests/other.hy::test_pydoc` create temporary `.hy` modules and import them through Python's global importer.
- `readline_cases.py` uses process-wide readline completion, key binding, and history state.

## CLI state audit

Importing `omxtra.hy.cli` and its modules does not install Hy or alter Python's search paths. The command entrypoints
`hy_main`, `hyc_main`, and `hy2py_main` call `globalruntime.install()` directly or through `run_hy_cli`. They also alter
`sys.path`, `sys.argv`, environment variables, or stdio according to command options. Helpers in `cli/running.py` alter
`sys.path` or `sys.modules['__main__']` when used to execute files. Those calls belong in command entrypoint processes.
`hy2py_convert` and `hy2py_convert_file` can now be called with an explicit runtime without changing `sys.path`;
`hy2py_main` sets its command search path before conversion.
