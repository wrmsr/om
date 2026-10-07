# dev 13 — the remote subpackage (2026-10-07)

The remote process manager and its target-side service moved here from `omllm/agent/remote`, which had grown both
concerns' client, server and protocol code in one place. The remote agent is now a composition of per-concern `remote`
subpackages, each a `protocol` / `server` / `client` triple, and `omllm/agent/remote` keeps only the amalgamation root,
the docker transport, the composed `RemoteAgentClient` / `RemoteAgentRpcHandler`, and the injector bindings. The
filesystem half is `omllm/agent/fs/remote`; `omllm/core` stays oblivious of it, and of tools in general.

## What is here

- `protocol.py` (lite): the `RemoteProcess*` request / result / event dataclasses and the `REMOTE_PROCESS_*` method
  names, including `REMOTE_PROCESS_EVENT_METHODS` - the agent's unprompted notifications.
- `server.py` (lite): `RemoteProcessService` (was `_RemoteProcessService`), unchanged in behavior, now exposing its
  method table through `methods()` for the agent's composition root to merge.
- `client.py` (standard): `RemoteProcess` / `RemoteProcessManager`. The manager now wires itself: given the peer and an
  `RpcNotificationRouter` (new in `omllm.core.rpc`) it routes its own event methods and registers its connection-lost
  handling on the peer. Builtin-error translation moved to `omllm.core.rpc.translate`.
- `tests/`: the scripted stand-in agent (`support.py`, which also carries the TERM-trapping helper child), the
  manager's own tests, the service's in-process tests, and the protocol round-trips. The amalgam-level integration
  test stays in `omllm/agent/remote/tests`, where the payload is.

## Lite-ness

`server.py` and `protocol.py` are in the amalgam and must stay Python 3.8 compatible, importing nothing but the
standard library, `omcore.lite` and the rpc package. The lite precheck does not know them (they are not marked lite,
as their parent package cannot be imported on 3.8); the amalgam integration test under `.venvs/8` is the guard.
