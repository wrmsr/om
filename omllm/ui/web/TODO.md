# Web UI TODO

What the web frontend works around in the code it is built on, then what it does not do yet.


## Upstream

- **Keep-alive with the asgi handler.** `AsgiIoPipelineHandler` always emits `FinalOutput` once a response is done,
  while `IoPipelineHttpServerKeepAliveHandler` says the handlers behind it must leave closing to it - the two are not
  tested together, and as they stand every response closes its connection. A page load is then a connection per file,
  and every response has to say so (`connection: close`). Wants a decision: a flag on the asgi handler, or it always
  leaving closing to whatever manages the connection.
- **Peer disconnects logged as errors.** `PollAsyncioStreamIoPipelineDriver.loop_until_done` logs a full ERROR
  traceback for a `BrokenPipeError` raised from `wait_closed()` as it closes a connection whose peer has gone - which
  for sse is every page reload. `main.configure_web_logging` filters those records out; the driver could treat a
  connection lost during its graceful close as routine.
- **An asgi app raising once its response is done.** Since the 500 change, an app raising before it starts its response
  is answered and logged, and one raising mid-response still propagates - rightly, as the connection has to drop. But
  one raising after it has *finished* its response propagates too, cutting off a client which got everything.
- **`RouteHandlerApp` and the asgi scope:**
  - It requires `scope['server']` when given no base url. The pipeline asgi handler now supplies it when given the
    connection's addresses, but any server leaving it out, as asgi allows, gets a `KeyError`.
  - The base url it builds from `server` does not bracket an ipv6 host - which is why `server.app.WebApp` passes an
    explicit one.
  - It routes on `scope['raw_path']`, which asgi makes optional, and decodes it as strict utf-8: with raw bytes now
    passed through as received, a request target which is not utf-8 raises rather than missing.


## Frontend

- **Websockets.** Everything is plain requests and sse.
- **Tab completion** of commands: the composer only lists the commands a line could be.
- **Bounding the feed.** It lives as long as the session. Tool results, output, and arguments are clipped going in, but
  a long session is replayed whole by every page load.
- **The repl modes** (`/py`, `/bash`, ...) of the minitui frontend.
