// @ts-check


////


/**
 * @typedef {object} SseMessage
 * @property {string | null} id
 * @property {string} event
 * @property {string} data
 */


/**
 * An incremental `text/event-stream` parser: fed decoded text in whatever pieces it arrives in, it returns each message
 * as soon as the blank line ending it has been seen. Comments are dropped. `fetch` is used rather than `EventSource`
 * because the streams here are as often POST responses as not.
 */
export class SseParser {
  constructor() {
    this.buf = ''
    /** @type {string | null} */ this.id = null
    /** @type {string | null} */ this.event = null
    /** @type {string[]} */ this.data = []
  }

  /** @returns {SseMessage | null} */
  line(/** @type {string} */ line) {
    if (!line) {
      if (!this.data.length && this.event === null) {
        return null
      }
      const msg = {id: this.id, event: this.event ?? 'message', data: this.data.join('\n')}
      this.event = null
      this.data = []
      return msg
    }

    if (line.startsWith(':')) {
      return null
    }

    const colon = line.indexOf(':')
    const name = colon < 0 ? line : line.slice(0, colon)
    let value = colon < 0 ? '' : line.slice(colon + 1)
    if (value.startsWith(' ')) {
      value = value.slice(1)
    }

    if (name === 'data') {
      this.data.push(value)
    } else if (name === 'event') {
      this.event = value
    } else if (name === 'id') {
      this.id = value
    }

    return null
  }

  /** @returns {SseMessage[]} */
  feed(/** @type {string} */ chunk) {
    this.buf += chunk

    /** @type {SseMessage[]} */ const out = []
    for (;;) {
      const m = /\r\n|\r|\n/.exec(this.buf)

      // A lone '\r' at the very end may be the first half of a '\r\n' whose second half has yet to arrive.
      if (!m || (m[0] === '\r' && m.index === this.buf.length - 1)) {
        break
      }

      const line = this.buf.slice(0, m.index)
      this.buf = this.buf.slice(m.index + m[0].length)

      const msg = this.line(line)
      if (msg) {
        out.push(msg)
      }
    }
    return out
  }
}


/** @returns {AsyncGenerator<SseMessage, void, void>} */
export async function* readSse(/** @type {ReadableStream<Uint8Array>} */ body) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  const parser = new SseParser()

  try {
    for (;;) {
      const {done, value} = await reader.read()
      if (done) {
        break
      }
      yield* parser.feed(decoder.decode(value, {stream: true}))
    }
    yield* parser.feed(decoder.decode() + '\n\n')
  } finally {
    reader.releaseLock()
  }
}
