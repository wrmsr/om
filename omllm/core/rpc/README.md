# RPC

This package is the transport-neutral control protocol for a live `omllm` remote agent. It is deliberately small,
stdlib-only apart from `omcore.lite`, and Python 3.8-compatible so it can be included in the agent amalgam. Like the
process launch shim, it is intentionally not marked `@om-lite`: its non-lite `omllm.core` parent cannot itself be
imported on Python 3.8, while an amalgam does not import that parent.

The protocol runs over one ordered, full-duplex byte stream. Frames are a four-byte, network-order payload length
followed by compact JSON. There is no handshake or protocol-version negotiation: the harness launches the remote
process with the exact same code, and a disconnected process is not reattached later.

`RpcPeer` is symmetric. Either endpoint can make concurrent calls, receive calls, send notifications, cancel an
outstanding call, or ping the other endpoint. Request IDs are scoped to their direction, so the same integer can be in
flight independently in both directions. Handler exceptions are returned as structured remote errors without closing
the connection; malformed wire data and transport failures close it and fail every pending call.

The package owns only JSON-compatible RPC values. Agent-specific request and result shapes, including any encoding of
byte strings, belong to the agent protocol layered above it.
