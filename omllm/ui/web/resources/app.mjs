// @ts-check


import {
  Api,
  ApiError,
} from './core/api.mjs'

import {FeedModel} from './core/feed.mjs'

import {Composer} from './ui/composer.mjs'

import {ITEM_RENDERERS} from './ui/items/all.mjs'

import {StatusBar} from './ui/status.mjs'

import {el} from './ui/texts.mjs'

import {TranscriptView} from './ui/transcript.mjs'


////


/**
 * @typedef {import('./core/api.mjs').FeedEntry} FeedEntry
 */


/** @returns {string} */
function errorMessage(/** @type {unknown} */ error) {
  return error instanceof Error ? error.message : String(error)
}


/**
 * The page. Everything shown comes from the session's feed, folded into the model and drawn by the view; the page only
 * decides when to read the feed, and from where:
 *
 *   - when it loads, and when it regains focus: whatever it missed, by a plain fetch;
 *   - while a submission of its own runs: from that submission's own stream, which ends with it;
 *   - while one it did not submit runs - in another tab, say, or from before a reload: by following the feed until the
 *     session is idle again.
 *
 * Streams may overlap - a `/steer` sent mid-prompt has a stream of its own - and the model takes each entry once.
 */
class App {
  constructor(/** @type {string} */ token) {
    this.api = new Api(token)
    this.model = new FeedModel()

    /** @type {string | null} */ this.connection = 'connecting'
    /** @type {number | null} */ this.retryTimer = null
    this.retryDelayMs = 1000
    this.title = 'omllm'
    /** @type {number | null} */ this.toastTimer = null
    /** @type {AbortController | null} */ this.following = null
    this.ownStreams = 0

    this.toast = /** @type {HTMLElement} */ (document.getElementById('toast'))

    this.status = new StatusBar(/** @type {HTMLElement} */ (document.getElementById('status')), {
      cancel: () => this.cancel(),
    })

    this.view = new TranscriptView(
      /** @type {HTMLElement} */ (document.getElementById('transcript')),
      /** @type {HTMLElement} */ (document.getElementById('scroller')),
      ITEM_RENDERERS,
      {answer: (id, allow) => this.answer(id, allow)},
    )

    this.composer = new Composer(/** @type {HTMLElement} */ (document.getElementById('composer')), {
      submit: text => this.submit(text),
      cancel: () => this.cancel(),
    })
  }

  //

  say(
    /** @type {string} */ message,
    /** @type {'info' | 'error'} */ level = 'info',
  ) {
    this.toast.textContent = message
    this.toast.className = `toast toast-${level}`
    this.toast.hidden = false

    if (this.toastTimer !== null) {
      clearTimeout(this.toastTimer)
    }
    this.toastTimer = setTimeout(() => {
      this.toast.hidden = true
      this.toastTimer = null
    }, level === 'error' ? 8000 : 4000)
  }

  setConnection(/** @type {string | null} */ connection) {
    this.connection = connection
    this.updateStatus()
  }

  /** Marks the connection lost for the error, and says so - unless the error is the page's own doing. */
  lost(
    /** @type {unknown} */ error,
    /** @type {string} */ what,
  ) {
    if (error instanceof ApiError && error.status === 403) {
      // The server does not know this page's token: it is not the server which served the page - restarted, say.
      this.setConnection('stale')
      this.say('This page is from a session no longer served here. Reload it.', 'error')
      return
    }

    this.setConnection('disconnected')
    if (!this.retryTimer) {
      this.say(`${what}: ${errorMessage(error)}`, 'error')
    }
    this.retryLater()
  }

  /** Tries to catch up again in a while, waiting longer each time it fails, until it does not. */
  retryLater() {
    if (this.retryTimer !== null || this.model.status.shutdown) {
      return
    }

    const delay = this.retryDelayMs
    this.retryDelayMs = Math.min(delay * 2, 15000)

    this.retryTimer = setTimeout(() => {
      this.retryTimer = null
      void this.catchUp()
    }, delay)
  }

  updateStatus() {
    this.status.update(this.model, this.connection)

    const busy = this.model.busy && !this.model.status.shutdown
    const mark = this.model.pendingAsks().length ? '◆ ' : busy ? '● ' : ''
    document.title = `${mark}${this.title}`
  }

  apply(/** @type {FeedEntry[]} */ entries) {
    const changes = this.model.apply(entries)
    this.view.apply(changes)

    if (changes.status) {
      this.updateStatus()

      if (this.model.status.shutdown) {
        this.composer.setEnabled(false)
        document.body.classList.add('ended')
      }
    }
  }

  //

  /** Fetches whatever has been missed, then, if something is running, follows the feed until it is not. */
  async catchUp() {
    try {
      const {entries} = await this.api.feed(this.model.lastSeq)
      this.apply(entries)
      this.setConnection(null)

      this.retryDelayMs = 1000
      if (this.retryTimer !== null) {
        clearTimeout(this.retryTimer)
        this.retryTimer = null
      }
    } catch (error) {
      this.lost(error, 'Lost the session')
      return
    }

    // A hidden page does not follow: every page following holds a connection, and a browser allows only a handful to
    // each server - enough of them, and the request answering a permission ask would queue behind them for good.
    if (this.model.busy && !this.ownStreams && !document.hidden) {
      void this.follow()
    }
  }

  async follow() {
    if (this.following || this.model.status.shutdown) {
      return
    }

    const ctl = new AbortController()
    this.following = ctl

    try {
      for await (const entry of this.api.follow(this.model.lastSeq, ctl.signal)) {
        this.apply([entry])

        if (!this.model.status.running.size || document.hidden) {
          break
        }
      }
    } catch (error) {
      if (!ctl.signal.aborted) {
        this.lost(error, 'Lost the feed')
      }
    } finally {
      ctl.abort()
      this.following = null
    }
  }

  /** @returns {Promise<boolean>} */
  async submit(/** @type {string} */ text) {
    if (this.model.status.shutdown) {
      return false
    }

    let stream
    try {
      stream = await this.api.submit(text, this.model.lastSeq)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        this.say('Busy - wait for it to finish, cancel it (Esc), or /steer it.')

        // What is running may be something this page has not heard of - another tab's.
        void this.catchUp()
      } else {
        this.lost(error, 'Could not submit')
      }
      return false
    }

    void this.consume(stream)
    return true
  }

  async consume(/** @type {AsyncGenerator<FeedEntry, void, void>} */ stream) {
    this.ownStreams += 1
    this.following?.abort()

    try {
      for await (const entry of stream) {
        this.apply([entry])
      }
      this.setConnection(null)
    } catch (error) {
      this.lost(error, 'Lost the stream')
    } finally {
      this.ownStreams -= 1
    }

    // The submission is over, but what else is running - another tab's - is still worth watching.
    if (!this.ownStreams && !this.model.status.shutdown) {
      await this.catchUp()
    }
  }

  async cancel() {
    if (!this.model.busy) {
      return
    }
    try {
      await this.api.cancel()
    } catch (error) {
      this.say(`Could not cancel: ${errorMessage(error)}`, 'error')
    }
  }

  /** @returns {Promise<boolean>} */
  async answer(
    /** @type {string} */ id,
    /** @type {boolean} */ allow,
  ) {
    try {
      await this.api.answerPermission(id, allow)
      return true
    } catch (error) {
      this.say(`Could not answer: ${errorMessage(error)}`, 'error')
      return false
    }
  }

  //

  async boot() {
    const info = await this.api.info()
    this.status.setInfo(info)
    this.composer.setCommands(info.commands)

    if (info.model) {
      this.title = `omllm · ${info.model}`
    }

    await this.catchUp()
    this.view.scrollToBottom()
    this.composer.focus()

    // Escape cancels from anywhere on the page - the input handles its own.
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && e.target !== this.composer.input) {
        void this.cancel()
      }
    })

    // A page coming back into view catches up on what it missed, and following stops as one goes out of it.
    const wake = () => {
      if (!document.hidden && !this.ownStreams && !this.following && this.connection !== 'stale') {
        void this.catchUp()
      }
    }
    window.addEventListener('focus', wake)
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.following?.abort()
      } else {
        wake()
      }
    })
  }
}


async function main() {
  const meta = /** @type {HTMLMetaElement | null} */ (document.querySelector('meta[name="omllm-web-token"]'))
  const app = new App(meta?.content ?? '')

  try {
    await app.boot()
  } catch (error) {
    app.setConnection('disconnected')
    document.getElementById('transcript')?.append(
      el('div', 'item notice notice-error', `Could not load the session: ${errorMessage(error)}`),
    )
  }
}


void main()
