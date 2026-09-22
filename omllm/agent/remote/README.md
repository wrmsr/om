# Remote agent

This package is the agent-side capability service used when the harness itself stays on the host. The generated
`_amalg.py` payload is bootstrapped into a target Python 3.8+ interpreter and serves filesystem and process operations
over `omllm.core.rpc` until that one connection closes. There is no reconnect or protocol negotiation.

On the host, `RemoteFsOps` implements the ordinary `FsOps` interface. `RemoteProcessManager` implements the ordinary
`ProcessManager` / `ProcessScope` contracts with local proxy handles and output spools, so `ProcessesExecOps` and the
existing foreground and background process tools need no remote-specific variants. Target-side children run in owned
process groups, retain an unreaped leader until teardown, and are terminated when the RPC connection closes. PTY
children use a small target-side bootstrap to acquire a controlling terminal before executing the requested argv.

`main.py` is the amalgamation root and `payload.py` loads its generated sibling for a connector. Docker attachment and
harness injector / CLI selection intentionally live in the next wiring layer, outside this package.
