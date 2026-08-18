# dev 06 — sandbox transform (phase 4) (2026-08-18)

General OS-level confinement, applied per-spawn like a Target. `sandboxed_rg`'s intent (confine a search to the tree,
no writes, no network) is now a reusable system, with ripgrep as the first opt-in user.

## What landed (`omllm/core/processes/sandbox/`)

- **`Sandbox`** (`types/options.py`): a `UniqueTypedValue` ProcOption, sibling to `Target`. The manager applies
  `options.get(Sandbox).transform_spec(spec)` right after any Target, so confinement composes with everything (pipes,
  pty, spool, teardown). Absence == unconfined.
- **`SandboxPolicy`**: backend-neutral - `read_roots`, `write_roots`, `system_read_roots` (libs/binaries, missing
  ones skipped), `allow_network`, `allow_dev`, `allow_proc`, `tmpfs_tmp`.
- **`BwrapSandbox`** (Linux): renders the policy to `bwrap --die-with-parent --unshare-pid/ipc/uts/net --new-session
  --ro-bind <sys+read> --bind <write> --dev --proc --tmpfs /tmp --chdir <cwd> -- <cmd>`. `--die-with-parent` +
  `--unshare-pid` make teardown clean (bwrap is the ns init; killing our process group takes the whole sandbox).
- **`SandboxExecSandbox`** (macOS): renders a `(deny default)` sandbox-exec profile with `(allow file-read* (subpath
  ...))` / `(allow file* ...)` per root; `sandbox-exec -p <profile> <cmd>`.
- **`platform_sandbox(policy)`**: picks the backend by `sys.platform`.
- Composes through `ExecOps`: `ExecParams` gained `options: Sequence[ProcOption]`, `ProcessesExecOps` passes them to
  `scope.spawn(spec, *options)`. `RipgrepTool(sandbox=True)` -> `platform_sandbox(SandboxPolicy(read_roots=[cwd]))`
  (opt-in, default off so it runs anywhere).

Usage: `await scope.run(spec, platform_sandbox(SandboxPolicy(read_roots=[cwd])))`.

## Tested

- Rendering: bwrap argv (ro/rw binds, missing-path skip, `--unshare-net` toggle, `--chdir`), sandbox-exec profile
  (deny-default, subpath allows incl. spaces, network toggle), stdio (PtyStdio) preserved through wrapping.
- Passthrough: `ProcessesExecOps` applies `ExecParams.options` end-to-end (a test `Sandbox` that echoes a marker then
  execs - proves the manager applies it and output streams back). `RipgrepTool` passes a `Sandbox` iff `sandbox=True`.
- **Gated live** bwrap confinement test (`test_bwrap_confinement_live`): reads allowed root, cannot read an unbound
  path, no network. **Skipped in this sandbox** - bwrap here can't create unprivileged user namespaces (kernel
  restriction). Run on a box that allows userns to exercise real confinement.

## Notes / follow-ups

- The existing ripgrep-specific `omllm/agent/exec/ripgrep/sandbox/` (an rg-tailored sandbox-exec profile +
  SAFETY_RG_ARGS, a synchronous `subprocess.run` path not wired into the tool) is left in place; it can migrate onto
  this general `SandboxPolicy` later. Its `SAFETY_RG_ARGS` (rg `--no-config` etc.) are rg-specific hardening, separate
  from FS/net confinement, and not folded in here.
- Sandbox is modeled as its own option (not a Target) - Target = *where* it runs, Sandbox = *how confined*; applied
  Target-then-Sandbox. sandbox+docker isn't a meaningful combo (the container already confines) and isn't supported
  usefully.
- `bwrap.py` hardcodes `/tmp` as the tmpfs mount point inside the sandbox (noqa S108) - that's the in-sandbox path,
  not a host temp file.
