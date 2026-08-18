# Release and artifact checklist

## Required checks

Run from the repository root:

```text
./python -m omdev.amalg gen -m omcore x/systevisor
./python -mruff check x/systevisor
./python -m mypy x/systevisor
./python -m pytest -q x/systevisor/tests
VENV=8 ./python -m unittest discover -s x/systevisor/tests -t .
make fix gen check
```

Regenerate the Systevisor artifact again after a repository-wide `make gen`, because the generic source discovery does
not always select the `x/systevisor/__main__.py` amalgamation root during a narrow iteration. The checked generation
test must compare byte-for-byte.

## Artifact properties

- `_bin/systevisor.py` starts with the generated/amalgamation markers required by self-update.
- Its top-level imports remain in the standard-library allowlist.
- It loads and executes from an unrelated directory under isolated CPython 3.8.
- `config-check`, `--help`, and service-template rendering work without the checkout on `PYTHONPATH`.
- Production globals pass the collision guard; no non-prefixed definition may silently overwrite another module when
  flattened.
- `kill`, `killpg`, and `wait*` remain confined to `runtime/processes.py`; production code contains no subprocess use.

## Optional platform gates

With an explicitly available Docker daemon, run:

```text
SYSTEVISOR_DOCKER_TESTS=1 ./python -m pytest -q x/systevisor/tests/test_docker.py
```

This proves Python 3.8 PID-1 collection execution plus successful self-update and injected candidate-resume rollback
inside separate automatically cleaned containers. Linux cgroup/namespace tests requiring a delegated root and Darwin
libproc/launchd host checks remain explicit host gates; an unsupported environment must skip or reject clearly rather
than weakening the contract.

## Publishing

Publish by copying the generated artifact to a new immutable/versioned path, checking its digest, and then atomically
updating the deployment's selected path or invoking the running manager's `self-update` with the versioned path. Keep
the previous artifact readable until the update operation reaches a terminal state so rollback remains possible.
