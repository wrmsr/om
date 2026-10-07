# Remote processes

Process management over an rpc connection to a remote agent, in the three-module shape every remotable concern takes:
`protocol.py` holds the lite-marshaled wire shapes, `server.py` the lite service that runs inside the agent payload, and
`client.py` the standard host side. The remote agent itself - the payload, its transport, and how the concerns are
composed - lives in `omllm/agent/remote`; nothing here knows about any other concern.

On the host, `RemoteProcessManager` implements the ordinary `ProcessManager` / `ProcessScope` contracts with local proxy
handles (`RemoteProcess`) and output spools, so `ProcessesExecOps` and the foreground and background process tools need
no remote-specific variants. It is built on a peer and an `RpcNotificationRouter`, through which it takes the agent's
process notifications, and it poisons its handles when the peer closes.

Target-side, `RemoteProcessService` runs children in owned process groups, retains an unreaped leader until teardown, and
terminates everything when the RPC connection closes. PTY children use a small bootstrap to acquire a controlling
terminal before executing the requested argv. Exits are observed by one SIGCHLD handler that probes every unexited child
with a non-blocking, non-reaping `waitid` - no thread or task per child, and nothing to saturate - which requires the
agent's event loop to run in its main thread. Per child the agent runs only its pipe (or pty) reader tasks and, on
demand, a close.

Output chunks, end-of-output and exit reach the host as notifications, which it applies inline in the RPC receive loop,
in wire order. The reply to a `process.close` is therefore an ordering barrier: every chunk sent before it is in the
spool by the time the host sees it, without a round trip per chunk. Process events on the host are delivered in the
order they happened, from one drain, exactly like the local manager's. A spawn the caller cancels still closes the child
the agent forked for it as soon as its id is known.

The remote manager supports the termination, spool, session (`'session'` only), run-timeout and tag options; the
server spawns with `subprocess.Popen` rather than the local shim, so credentials, rlimits, deathsig, passed fds,
sandboxes and targets are rejected. `server.py` and `protocol.py` are included in the agent amalgam and must stay Python
3.8 compatible, importing nothing but the standard library, `omcore.lite` and the rpc package.
