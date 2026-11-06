// @ts-check


import {el} from './texts.mjs'


////


/**
 * @typedef {import('../core/api.mjs').SessionInfo} SessionInfo
 * @typedef {import('../core/feed.mjs').FeedModel} FeedModel
 */


/** @returns {string} */
export function formatTokens(/** @type {number} */ n) {
  if (n < 1000) {
    return String(n)
  }
  if (n < 1000000) {
    return `${(n / 1000).toFixed(n < 10000 ? 1 : 0)}k`
  }
  return `${(n / 1000000).toFixed(1)}m`
}


/** The bar along the top: what the session is, what it has cost, and whether it is busy. */
export class StatusBar {
  constructor(
    /** @type {HTMLElement} */ root,
    /** @type {{cancel: () => void}} */ actions,
  ) {
    this.root = root

    this.session = el('span', 'status-session')
    this.usage = el('span', 'status-usage')
    this.state = el('span', 'status-state')

    this.cancel = el('button', 'status-cancel', 'Cancel')
    this.cancel.title = 'Cancel the running prompt (Esc)'
    this.cancel.addEventListener('click', () => actions.cancel())
    this.cancel.hidden = true

    root.replaceChildren(
      el('span', 'status-brand', 'omllm'),
      this.session,
      el('span', 'status-spacer'),
      this.usage,
      this.state,
      this.cancel,
    )
  }

  setInfo(/** @type {SessionInfo} */ info) {
    const parts = []
    if (info.model) {
      parts.push(el('span', 'status-model', info.model))
    }
    if (info.cwd) {
      const cwd = el('span', 'status-cwd', info.cwd.length > 48 ? '…' + info.cwd.slice(-47) : info.cwd)
      cwd.title = info.cwd
      parts.push(cwd)
    }
    if (info.session_id) {
      const sid = el('span', 'status-sid', info.session_id.slice(-8))
      sid.title = `session ${info.session_id}`
      parts.push(sid)
    }
    this.session.replaceChildren(...parts)
  }

  update(
    /** @type {FeedModel} */ model,
    /** @type {string | null} */ connection = null,
  ) {
    const {usage, context, shutdown} = model.status

    const usageParts = []
    if (usage.input || usage.inputCached || usage.output) {
      usageParts.push(`in ${formatTokens(usage.input + usage.inputCached)} out ${formatTokens(usage.output)}`)
    }
    if (context && context.limit) {
      const pct = Math.round(100 * context.input / context.limit)
      usageParts.push(`ctx ${context.estimated ? '~' : ''}${pct}%`)
    }
    this.usage.textContent = usageParts.join(' · ')

    let state = 'idle'
    if (shutdown) {
      state = 'ended'
    } else if (connection) {
      state = connection
    } else if (model.pendingAsks().length) {
      state = 'waiting for you'
    } else if (model.busy) {
      state = 'working'
    }

    this.state.textContent = state
    this.root.dataset.state = state.replaceAll(' ', '-')

    this.cancel.hidden = !model.busy || shutdown
  }
}
