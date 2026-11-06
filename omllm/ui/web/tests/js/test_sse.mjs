// @ts-check


import {SseParser} from '../../resources/core/sse.mjs'

import {
  assert,
  test,
} from './runner.mjs'


////


test('sse: whole messages', () => {
  const p = new SseParser()
  assert.deepEqual(p.feed('id: 1\nevent: feed\ndata: {"a":1}\n\n'), [{id: '1', event: 'feed', data: '{"a":1}'}])
})


test('sse: messages split anywhere', () => {
  const src = 'id: 1\nevent: feed\ndata: one\n\n: keepalive\n\nid: 2\ndata: two\ndata: lines\n\n'
  for (let i = 0; i <= src.length; i++) {
    const p = new SseParser()
    const got = [...p.feed(src.slice(0, i)), ...p.feed(src.slice(i))]
    assert.deepEqual(got, [
      {id: '1', event: 'feed', data: 'one'},
      {id: '2', event: 'message', data: 'two\nlines'},
    ], `split at ${i}`)
  }
})


test('sse: crlf and cr line endings, a crlf split between pieces', () => {
  const p = new SseParser()
  const got = [...p.feed('data: a\r'), ...p.feed('\n\r\ndata: b\r\r')]
  assert.deepEqual(got, [{id: null, event: 'message', data: 'a'}])

  // The last '\r' could yet be the start of a '\r\n', so its message waits on what follows.
  assert.deepEqual(p.feed('data: c\n\n'), [
    {id: null, event: 'message', data: 'b'},
    {id: null, event: 'message', data: 'c'},
  ])
})


test('sse: comments and blank lines alone make no messages', () => {
  const p = new SseParser()
  assert.deepEqual(p.feed(': hello\n\n\n\n'), [])
})
