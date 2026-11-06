// @ts-check


import {readSse} from './sse.mjs'


////


/**
 * A feed entry as the server sends it: a feed event, tagged by `type`, with its `seq` merged in.
 *
 * @typedef {{seq: number, type: string, [key: string]: any}} FeedEntry
 */


/**
 * @typedef {object} CommandInfo
 * @property {string} name
 * @property {string} [description]
 * @property {boolean} [can_run_while_busy]
 */


/**
 * @typedef {object} SessionInfo
 * @property {string} [session_id]
 * @property {string} [model]
 * @property {string} [cwd]
 * @property {CommandInfo[]} commands
 * @property {boolean} busy
 * @property {{id: string, kind: string, text: string}} [current]
 * @property {number} last_seq
 */


export class ApiError extends Error {
  constructor(
    /** @type {number} */ status,
    /** @type {string} */ error,
    /** @type {string | undefined} */ message,
  ) {
    super(message ?? `${status} ${error}`)
    this.status = status
    this.error = error
  }
}


/** @returns {AsyncGenerator<FeedEntry, void, void>} */
async function* readFeedEntries(/** @type {Response} */ resp) {
  if (!resp.body) {
    return
  }
  for await (const msg of readSse(resp.body)) {
    if (msg.event === 'feed') {
      yield /** @type {FeedEntry} */ (JSON.parse(msg.data))
    }
  }
}


/** The server's api, one method per endpoint. Every request carries the session's token. */
export class Api {
  constructor(
    /** @type {string} */ token,
    /** @type {string} */ base = '',
  ) {
    this.token = token
    this.base = base
  }

  /** @returns {Promise<Response>} */
  async request(
    /** @type {string} */ method,
    /** @type {string} */ path,
    /** @type {any} */ body = undefined,
    /** @type {AbortSignal | undefined} */ signal = undefined,
  ) {
    /** @type {Record<string, string>} */ const headers = {'x-omllm-web-token': this.token}
    if (body !== undefined) {
      headers['content-type'] = 'application/json'
    }

    const resp = await fetch(this.base + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      cache: 'no-store',
    })

    if (!resp.ok) {
      /** @type {any} */ let err = {}
      try {
        err = await resp.json()
      } catch {
        // Not every failure has a json body - a proxy's, say.
      }
      throw new ApiError(resp.status, err.error ?? 'error', err.message)
    }

    return resp
  }

  /** @returns {Promise<SessionInfo>} */
  async info() {
    return (await this.request('GET', '/api/info')).json()
  }

  /** @returns {Promise<{entries: FeedEntry[], last_seq: number}>} */
  async feed(/** @type {number} */ after) {
    return (await this.request('GET', `/api/feed?after=${after}`)).json()
  }

  /**
   * Everything after the cursor, then everything after that as it comes, until the signal aborts.
   *
   * @returns {AsyncGenerator<FeedEntry, void, void>}
   */
  async* follow(
    /** @type {number} */ after,
    /** @type {AbortSignal | undefined} */ signal = undefined,
  ) {
    yield* readFeedEntries(await this.request('GET', `/api/feed/stream?after=${after}`, undefined, signal))
  }

  /**
   * Submits a line, then streams the feed from the cursor through the submission's end. Rejects before yielding
   * anything - with a 409 ApiError if the session is busy - if the submission could not start.
   *
   * @returns {Promise<AsyncGenerator<FeedEntry, void, void>>}
   */
  async submit(
    /** @type {string} */ text,
    /** @type {number} */ after,
    /** @type {AbortSignal | undefined} */ signal = undefined,
  ) {
    return readFeedEntries(await this.request('POST', '/api/submit', {text, after}, signal))
  }

  /** @returns {Promise<boolean>} */
  async cancel() {
    return (await (await this.request('POST', '/api/cancel', {})).json()).cancelled
  }

  /** @returns {Promise<void>} */
  async answerPermission(
    /** @type {string} */ id,
    /** @type {boolean} */ allow,
  ) {
    await this.request('POST', '/api/permissions', {id, allow})
  }
}
