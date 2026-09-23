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

Requests are handled in a task each, so handlers run concurrently. Notifications may instead be handled inline: an
`RpcHandler` that overrides `handle_notification_inline` applies a notification synchronously on the receive loop, which
makes the stream's order the delivery order - anything the other side sent after it, such as the reply to a later call,
is seen only once it has been applied. This is how the remote agent streams process output. Replies to calls or pings
the local side has already given up on (cancelled, timed out) are recognized by their id and dropped; a reply for an id
that was never issued is a protocol error. Replies the receive loop itself owes (pongs, `busy` rejections) go out from a
short-lived task so a backpressured writer can never stall reading.

Teardown runs to completion however it is entered - a local `aclose`, the other side closing, a transport failure, or
the receive task being cancelled before it ever ran - and always fails every pending call, then runs the callbacks
registered with `add_close_callback`, then releases `wait_closed`.

The package owns only JSON-compatible RPC values. Agent-specific request and result shapes, including any encoding of
byte strings, belong to the agent protocol layered above it.
