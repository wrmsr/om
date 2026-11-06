# Overview

A web frontend for the agent harness: `om llm --web` (or `python -m omllm.ui.web`) runs one session, just as the
terminal frontends do, and serves it on a local port - `http://127.0.0.1:8077/` by default - to however many browser
tabs open it. It takes the same arguments as the other frontends, plus `--host`, `-p/--port` (`0` for an ephemeral
one), and `-v/--verbose`.

For a look without api keys, `python -m omllm.ui.web.tests.demo` serves a scripted model working through a little
project in a temporary directory: thinking, streaming markdown, tool calls, permission asks with diffs, and a final
answer.

# Architecture

```
agent events --+                        +--> GET  /api/feed          json, after a cursor
command output +--> feed (seq'd log) ---+--> POST /api/submit        sse, through the submission's end
permission asks+                        +--> GET  /api/feed/stream   sse, for as long as it is open
```

Everything the session shows goes into one append-only, sequence-numbered **feed** of display events:

- `output.agents.AgentEventFeeder` translates the agent's events - stream deltas, tool executions, usage, the run's end.
- `output.display.FeedTextDisplayer` is the `ui.TextDisplayer`, so command output lands there too.
- `permissions.FeedPermissionAsker` puts each permission ask there, and parks the asking tool on a future until an
  answer comes in out of band.

Nothing is dropped, so a page loading late, or reloading mid-run, replays the feed and misses nothing. Each page keeps
a cursor - the last seq it has seen - and every read of the feed starts from it.

What the user submits - a prompt, or a slash command - runs as a **submission** (`submissions.Submitter`): a task of its
own, bracketed in the feed by `submission_start` and `submission_end`. Submissions run one at a time under an asyncio
lock which is never waited on: one submitted while another runs is rejected on the spot with a 409. The exception is a
command allowed to run while busy - `/steer`, say - which runs alongside. A submission belongs to no request, so a
browser going away mid-run leaves the run running; `POST /api/cancel` is what stops it.

`POST /api/submit` streams the feed from the page's cursor through the submission's own `submission_end`, which carries
how it ended. A visible page which finds something running it did not submit - on loading, on coming back into view, or
on being turned away with a 409 - follows `GET /api/feed/stream` until the session is idle. Hidden pages do not follow:
each page following holds one of the handful of connections a browser allows a server. A page which loses the server
retries with backoff, and one served by an earlier server - which no longer knows its token - says to reload.

Quitting - `/quit`, or ctrl+c - cancels whatever is running, feeds the ends of what it cancelled, and only then feeds
`shutdown`, the last thing the feed carries. A submission's stream ending while the session quits goes on through it.

## The wire protocol

Feed events are the closed family of dataclasses in `feed/events.py`, marshaled as json objects tagged by a `type`
field, with the entry's `seq` merged in:

```
id: 12
event: feed
data: {"seq":12,"type":"ai_text_delta","text":"Hel"}
```

They are deliberately close to what is displayed rather than to what happened, so that the browser folds them into its
view knowing nothing of agents or tools. Text carried in them - command output, tool results, permission previews - is
`ui.Text` lowered by `texts.WebTextRenderer`: markdown and diffs travel as their sources and are rendered by the
browser.

## The browser

Zero-build `.mjs` modules, type-checked by `tsc` in `checkJs` mode through JSDoc, with no framework:

- `core/sse.mjs` - an incremental sse parser over `fetch`, as the streams here are as often POST responses as not.
- `core/api.mjs` - one method per endpoint.
- `core/feed.mjs` - `FeedModel`, a pure fold of feed entries into transcript items, which reports what changed.
- `ui/transcript.mjs` - draws the items as DOM, redrawing changed ones once per animation frame, each kind of item by
  its renderer in `ui/items/` - a new kind of item is a fold in the model and a renderer here.
- `ui/markdown.mjs` - the vendored `marked`, configured for untrusted model output.
- `ui/composer.mjs`, `ui/status.mjs` - the input and the status bar.

The only dependency is [`marked`](https://github.com/markedjs/marked), vendored under `resources/vendor` by
`omdev.js.vendor` from `vendor.json`:

```bash
./python -m omdev.js.vendor --manifest omllm/ui/web/vendor.json --destination omllm/ui/web/resources/vendor verify
npx --yes --package=typescript@5.9.2 tsc -p omllm/ui/web/tsconfig.json
node omllm/ui/web/tests/js/testall.mjs

# Drives the demo in headless firefox. Marked slow: it runs when selected alone, or with --slow.
./python -m pytest omllm/ui/web/tests/test_browser.py
```

# Security

The agent may run commands, and the server listens on a port any local process - and through a local browser, any web
page - can reach. So:

- The Host header must name the server - by an ip address, which dns rebinding cannot produce, or as `localhost` or
  the name it was bound to - and an Origin header, where sent, must be its own.
- Api requests must carry a per-process token, which only the page the server serves is given.
- Model output is untrusted: raw html in markdown is shown as text, links are kept only to `http`, `https`, and
  `mailto`, and images are shown as links rather than loaded - a loaded image is a request made on the reader's
  behalf, which is a way out for whatever a model was talked into putting in its url. A strict content security
  policy stands behind all of that.

None of this defends against something which can already read the page - another local user, for one, or, bound to
a non-loopback address, anyone who can reach it. Bind to one only knowing that.

# Serving

Http is served by `omcore.io.pipelines` - one pipeline per connection, its asgi handler stepping the app inside the
connection's driver rather than in a task of its own. Responses close their connections, streamed ones chunked and
flushed as they are sent.

# Not yet

- Websockets: everything is plain requests and sse.
- Tab completion of commands: the composer only lists the commands a line could be.
- Bounding the feed: it lives as long as the session. Tool results and output are clipped going in, but a long session
  is replayed whole by every page load.
- The repl modes (`/py`, `/bash`, ...) of the minitui frontend.
