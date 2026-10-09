### interop

- answer heartbeat PINGs with PONGs in the in-house backend. Native peers send PINGs when `ZMQ_HEARTBEAT_IVL` is set,
  even to 3.0 peers; they are read past but never answered, so a native peer which also sets `ZMQ_HEARTBEAT_TIMEOUT`
  likely drops an idle in-house connection and reconnects repeatedly. Confirm with a native heartbeat-timeout test
  first, then answer: PONG echoes the PING's context (about 10 lines in `zmtp/pipelines/handshakes.py`)
- relax the NULL handshake's strictness where libzmq is lenient: it rejects a greeting with as-server set, which libzmq
  does not check, and caps READY metadata at 64 properties with a strict name charset - either could reject a non-libzmq
  peer, or one with heavy `ZMQ_METADATA`

### tests

- tidy the review-written regression tests in `tests/test_regressions.py` to house style (long docstrings, a test
  helper header duplicated from elsewhere)
