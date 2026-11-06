// @ts-check


import {FeedModel} from '../../resources/core/feed.mjs'

import {
  assert,
  test,
} from './runner.mjs'


////


/**
 * @typedef {import('../../resources/core/api.mjs').FeedEntry} FeedEntry
 */


/** @returns {FeedEntry[]} */
function entries(/** @type {Record<string, any>[]} */ ...events) {
  return events.map((e, i) => ({seq: i + 1, type: '', ...e}))
}


/** @returns {any[]} */
function shape(
  /** @type {FeedModel} */ model,
  /** @type {string[]} */ keys = ['text'],
) {
  return model.items.map(item => {
    const parent = item.parent ? model.byId.get(item.parent)?.kind : null
    /** @type {Record<string, any>} */ const out = {kind: item.kind, parent}
    for (const k of keys) {
      if (k in item) {
        out[k] = item[k]
      }
    }
    return out
  })
}


test('feed: a prompt, streamed', () => {
  const m = new FeedModel()
  const changes = m.apply(entries(
    {type: 'submission_start', id: '1', kind: 'prompt', text: 'hi'},
    {type: 'user_message', text: 'hi'},
    {type: 'run_start'},
    {type: 'thinking_start'},
    {type: 'thinking_delta', text: 'hm'},
    {type: 'thinking_end', text: 'hmm'},
    {type: 'ai_text_delta', text: 'Hel'},
    {type: 'ai_text_delta', text: 'lo'},
    {type: 'ai_text_end', text: 'Hello'},
  ))

  assert.equal(m.busy, true)
  assert.deepEqual(shape(m), [
    {kind: 'user', parent: null, text: 'hi'},
    {kind: 'run', parent: null},
    {kind: 'thinking', parent: 'run', text: 'hmm'},
    {kind: 'ai', parent: 'run', text: 'Hello'},
  ])
  assert.equal(changes.added.length, 4)
  assert.equal(changes.updated.size, 0)
  assert.equal(m.items[3].done, true)

  m.apply([
    {seq: 10, type: 'run_end', reason: 'completed'},
    {seq: 11, type: 'submission_end', id: '1', status: 'completed'},
  ])
  assert.equal(m.busy, false)
  assert.equal(m.items[1].status, 'completed')
})


test('feed: entries already seen are ignored', () => {
  const m = new FeedModel()
  const es = entries(
    {type: 'user_message', text: 'one'},
    {type: 'user_message', text: 'two'},
  )
  m.apply(es)
  const changes = m.apply([...es, {seq: 3, type: 'user_message', text: 'three'}])

  assert.deepEqual(m.items.map(i => i.text), ['one', 'two', 'three'])
  assert.equal(changes.added.length, 1)
  assert.equal(m.lastSeq, 3)
})


test('feed: updates to items added in an earlier batch', () => {
  const m = new FeedModel()
  m.apply(entries({type: 'run_start'}, {type: 'ai_text_delta', text: 'a'}))

  const changes = m.apply([{seq: 3, type: 'ai_text_delta', text: 'b'}])
  assert.equal(changes.added.length, 0)
  assert.deepEqual([...changes.updated].map(i => i.text), ['ab'])
})


test('feed: tools, nested calls, and asks', () => {
  const m = new FeedModel()
  m.apply(entries(
    {type: 'run_start'},
    {type: 'tool_start', key: 'k1', name: 'subagent', args: {}},
    {type: 'tool_start', key: 'k2', name: 'ls', parent: 'k1', via: 'explore 1'},
    {type: 'permission_ask', id: 'a1', key: 'k2', tool: 'ls', target: 't', rule: 'r'},
    {type: 'tool_output', key: 'k2', text: 'out'},
  ))

  assert.deepEqual(shape(m, ['name', 'status', 'outcome']), [
    {kind: 'run', parent: null, status: 'running'},
    {kind: 'tool', parent: 'run', name: 'subagent', status: 'running'},
    {kind: 'tool', parent: 'tool', name: 'ls', status: 'running'},
    {kind: 'ask', parent: 'tool', outcome: 'pending'},
  ])
  assert.equal(m.byId.get(m.items[3].parent ?? '')?.name, 'ls')
  assert.equal(m.pendingAsks().length, 1)
  assert.equal(m.tools.get('k2')?.output, 'out')

  m.apply([
    {seq: 6, type: 'permission_answer', id: 'a1', outcome: 'allow'},
    {seq: 7, type: 'tool_end', key: 'k2', ok: true, result: 'a b'},
    {seq: 8, type: 'run_end', reason: 'cancelled'},
  ])

  assert.equal(m.pendingAsks().length, 0)
  assert.equal(m.tools.get('k2')?.status, 'ok')
  // A call the run never finished is finished with it.
  assert.equal(m.tools.get('k1')?.status, 'aborted')
  assert.equal(m.items[0].status, 'cancelled')
})


test('feed: a command allowed while busy does not make the session busy', () => {
  const m = new FeedModel()
  m.apply(entries({type: 'submission_start', id: '1', kind: 'command', text: '/echo x', exclusive: false}))
  assert.equal(m.busy, false)
})


test('feed: usage adds up, context is the latest', () => {
  const m = new FeedModel()
  m.apply(entries(
    {type: 'usage', input: 10, input_cached: 5, output: 3},
    {type: 'usage', input: 1, output: 2},
    {type: 'context', input: 100, limit: 1000},
  ))

  assert.equal(m.status.usage.input, 11)
  assert.equal(m.status.usage.inputCached, 5)
  assert.equal(m.status.usage.output, 5)
  assert.equal(m.status.usage.turns, 2)
  assert.deepEqual(m.status.context, {input: 100, limit: 1000, estimated: false})
})


test('feed: unknown event types are passed over', () => {
  const m = new FeedModel()
  const changes = m.apply(entries({type: 'from_the_future'}, {type: 'user_message', text: 'hi'}))
  assert.equal(changes.added.length, 1)
  assert.equal(m.lastSeq, 2)
})


test('feed: what lands beside a streaming block does not split it', () => {
  const m = new FeedModel()
  m.apply(entries(
    {type: 'run_start'},
    {type: 'ai_text_delta', text: 'Hello '},
    {type: 'command_echo', text: '/steer x'},
    {type: 'text', text: 'Steering queued.'},
    {type: 'notice', text: 'retrying', level: 'warn'},
    {type: 'ai_text_delta', text: 'there.'},
    {type: 'ai_text_end', text: 'Hello there.'},
    {type: 'thinking_delta', text: 'hm'},
    {type: 'notice', text: 'debug', level: 'debug'},
    {type: 'thinking_end', text: 'hmm'},
  ))

  assert.deepEqual(m.items.filter(i => i.kind === 'ai').map(i => i.text), ['Hello there.'])
  assert.deepEqual(m.items.filter(i => i.kind === 'thinking').map(i => i.text), ['hmm'])
  assert.deepEqual(m.items.map(i => i.kind), ['run', 'ai', 'command', 'text', 'notice', 'thinking', 'notice'])
})
