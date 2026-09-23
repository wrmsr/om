# Remote agent

This package is the agent-side capability service used when the harness itself stays on the host. The generated
`_amalg.py` payload is bootstrapped into a target Python 3.8+ interpreter and serves filesystem and process operations
over `omllm.core.rpc` until that one connection closes. There is no reconnect or protocol negotiation.

On the host, `RemoteFsOps` implements the ordinary `FsOps` interface. `RemoteProcessManager` implements the ordinary
`ProcessManager` / `ProcessScope` contracts with local proxy handles and output spools, so `ProcessesExecOps` and the
existing foreground and background process tools need no remote-specific variants. Target-side children run in owned
process groups, retain an unreaped leader until teardown, and are terminated when the RPC connection closes. PTY
children use a small target-side bootstrap to acquire a controlling terminal before executing the requested argv.

Output chunks, end-of-output and exit reach the host as notifications, which it applies inline in the RPC receive loop,
in wire order. The reply to a `process.close` is therefore an ordering barrier: every chunk sent before it is in the
spool by the time the host sees it, without a round trip per chunk. Exits are observed by one SIGCHLD handler that
probes every unexited child with a non-blocking, non-reaping `waitid` - no thread or task per child, and nothing to
saturate - which requires the agent's event loop to run in its main thread, as `remote_agent_main` does. Per child the
agent runs only its pipe (or pty) reader tasks and, on demand, a close. Process events on the host are delivered in the
order they happened, from one drain, exactly like the local manager's. A spawn the caller cancels still closes the child
the agent forked for it as soon as its id is known.

`RemoteAgentClient.aclose(timeout_s=...)` bounds the graceful teardown: an agent that has not finished closing its
processes by then - or has stopped answering entirely - has its connection severed, which fails every pending call and
lets the process manager finish on its own.

`main.py` is the amalgamation root and `payload.py` loads its generated sibling. `DockerRemoteAgentConnection` starts
that payload through `docker exec -i`, owns the resulting RPC client, and tears the Docker process down with the
connection. `bind_docker_remote_agent` exposes its filesystem and process implementations under the ordinary agent
interfaces.

The TUI's `--container CONTAINER` option selects these bindings. `--cwd` is interpreted entirely in the target
namespace; when omitted, the running container's configured working directory is resolved by the remote filesystem.
Filesystem, process, bash, and ripgrep tools use the remote capabilities. Session storage, model access, permissions,
eval and web tools, and the rest of the harness remain on the host.
