# x.curl

A small HTTP/1.1 command line client built on `omcore.http.clients.pipelines` and `omcore.io.pipelines`.
It uses the repository's synchronous or asyncio pipeline client, selected with `--asyncio`. It does not use an
`httpx` or `urllib` HTTP client. `urllib.parse` is used only to construct URLs and form data.

Run it from the repository root with `./python -m x.curl`:

```sh
./python -m x.curl https://example.com/
./python -m x.curl --asyncio -i -q 'page=2' -H 'Accept: application/json' https://example.com/items
./python -m x.curl --json '{"name":"Ada"}' --pretty https://example.com/items
./python -m x.curl -F 'name=Ada' -F 'role=admin' https://example.com/form
./python -m x.curl --data-file large.bin -o reply.bin https://example.com/upload
cat large.bin | ./python -m x.curl --asyncio --data-file - --trailer 'X-Done: yes' https://example.com/upload
```

The default output is the response body, copied in bounded chunks to stdout or `-o/--output`. `-i/--include`
prepends status and response headers. `-I/--head` sends HEAD and prints headers. `--show-status` prints the status
to stderr. `--fail` returns exit code 22 for an HTTP error status while still writing its response. Network and
input errors return exit code 2.

`-d/--data` sends UTF-8 text, `--json` validates and sends JSON, and repeated `-F/--form` fields send URL encoded
form data. These options prepare the request body in memory. `--data-file` streams a file or stdin in chunked
transfer encoding, without reading the whole input first. `--trailer` adds trailing headers to that request.
The client always reads response bodies incrementally unless `--pretty` is selected; `--pretty` buffers the full
response to format JSON.

Other options include repeated request headers (`-H`), query parameters (`-q`), Basic or Bearer authorization,
custom Accept and Content-Type headers, gzip negotiation (`--compressed`), raw compressed output (`--raw`),
connection and request timeouts, custom CA bundle (`--ca-file`), and disabled certificate verification (`-k`).

Each invocation sends one request on one connection. Redirect following, proxies, HTTP/2, multipart forms, and
upload resumption are not yet implemented. Streaming uploads exercise the existing HTTP request head, body,
chunk, trailer, and flush messages directly. The high level `HttpClientRequest` currently accepts only complete
`bytes` or `str` bodies, which is why this path uses a small bridge into the pipeline.
