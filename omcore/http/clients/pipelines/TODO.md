- client streaming io lol
- keepalive ffs
- chunked compression ffs
- response body safety policy
  - add a configurable maximum total response body size for the convenience ``request()`` path
  - decide whether the limit applies before or after content decompression (probably expose both wire and decoded bounds)
- decide whether the high-level clients should have a finite default request timeout; connect timeout is finite today,
  but request timeout deliberately defaults to disabled
