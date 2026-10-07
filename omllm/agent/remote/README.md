# Remote agent

This package is the composition root of the remote agent: the capability service used when the harness itself stays on
the host and its tools run somewhere else. The generated `_amalg.py` payload is bootstrapped into a target Python 3.8+
interpreter and serves filesystem and process operations over `omllm.core.rpc` until that one connection closes. There
is no reconnect or protocol negotiation. The target needs nothing but that interpreter: no `om` install, and not
necessarily an `om` dev container.

The concerns themselves live with their owners, each as a `remote` subpackage of three modules: a `protocol` of
lite-marshaled wire shapes, a lite `server` that runs inside the payload, and a standard `client` that runs on the host
and implements the concern's ordinary interface:

- `omllm/agent/fs/remote` - `RemoteFsOps` implements `FsOps` over a `RemoteFsService`, sharing the lite primitives in
  `omllm/agent/fs/common.py` with `LocalFsOps`.
- `omllm/core/processes/remote` - `RemoteProcessManager` implements `ProcessManager` / `ProcessScope` over a
  `RemoteProcessService`, with local proxy handles and output spools. See its README for the process semantics.

Nothing below those knows the others exist; only this package does. `server.py` merges the services' method tables into
the payload's one `RpcHandler`, and `client.py`'s `RemoteAgentClient` builds each concern's client on the one host-side
peer, with an `RpcNotificationRouter` through which a concern routes the notifications it alone understands. Adding a
remotable concern is a new such subpackage, plus one import and one line in each of those two modules and the injector
bindings in `inject.py`.

Everything reachable from `main.py` is included in the amalgam, so the protocol and server modules, and anything they
import, must stay Python 3.8 compatible and import nothing but the standard library, `omcore.lite`, and the rpc
package. The lite precheck does not know these files; the integration test in `tests/test_remote.py` runs the payload
under the `.venvs/8` interpreter when present and is the guard.

`RemoteAgentClient.aclose(timeout_s=...)` bounds the graceful teardown: an agent that has not finished closing its
processes by then - or has stopped answering entirely - has its connection severed, which fails every pending call and
lets the process manager finish on its own.

`main.py` is the amalgamation root and `payload.py` loads its generated sibling. `DockerRemoteAgentConnection` starts
that payload through `docker exec -i` (given a container id or name), owns the resulting RPC client, and tears the
Docker process down with the connection. `bind_docker_remote_agent` exposes its filesystem and process implementations
under the ordinary agent interfaces, along with the root process scope the ui hands to tools.

The TUI's `--container CONTAINER` option selects these bindings. `--cwd` is interpreted entirely in the target
namespace; when omitted, the running container's configured working directory is resolved by the remote filesystem.
Filesystem, process, bash, and ripgrep tools use the remote capabilities, the ripgrep tool without its host-only
sandbox. Session storage, model access, permissions, eval and web tools, and the rest of the harness remain on the
host.

The connection is one `docker exec` stream, with no reconnect: should it drop, every live remote process is poisoned
and further calls fail until the harness restarts. Reconnecting by respawning a fresh agent into the same container -
losing background processes, restoring everything else - is the intended follow-up.
