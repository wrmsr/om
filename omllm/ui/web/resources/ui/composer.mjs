// @ts-check


import {el} from './texts.mjs'


////


/**
 * @typedef {import('../core/api.mjs').CommandInfo} CommandInfo
 */


/**
 * @typedef {object} ComposerActions
 * @property {(text: string) => Promise<boolean>} submit - whether the submission was taken: the input clears only if so
 * @property {() => void} cancel
 */


const HISTORY_KEY = 'omllm.web.history'
const HISTORY_MAX = 200


/** @returns {string[]} */
function loadHistory() {
  try {
    const v = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]')
    return Array.isArray(v) ? v.filter(s => typeof s === 'string') : []
  } catch {
    return []
  }
}


function saveHistory(/** @type {string[]} */ history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-HISTORY_MAX)))
  } catch {
    // Storage is a convenience: a browser without it just forgets.
  }
}


/**
 * The input along the bottom. Enter submits and shift+enter breaks the line; escape cancels whatever is running; up
 * and down at the edges of the text walk back through what was submitted before. A line starting with a slash is a
 * command, and while one is being typed the commands it could be are listed above.
 */
export class Composer {
  constructor(
    /** @type {HTMLElement} */ root,
    /** @type {ComposerActions} */ actions,
  ) {
    this.actions = actions

    this.hints = el('div', 'composer-hints')
    this.hints.hidden = true

    this.input = /** @type {HTMLTextAreaElement} */ (el('textarea', 'composer-input'))
    this.input.rows = 1
    this.input.placeholder = 'Message, or /command'
    this.input.title = 'Enter sends, shift+enter breaks the line, escape cancels, up and down walk the history'
    this.input.spellcheck = false

    this.send = el('button', 'composer-send', 'Send')
    this.send.addEventListener('click', () => this.submit())

    root.replaceChildren(this.hints, el('div', 'composer-row', this.input, this.send))

    /** @type {CommandInfo[]} */ this.commands = []

    this.history = loadHistory()
    this.historyPos = this.history.length
    this.draft = ''
    this.submitting = false

    this.input.addEventListener('keydown', e => this.onKeyDown(e))
    this.input.addEventListener('input', () => this.onInput())
    window.addEventListener('resize', () => this.resize())
  }

  setCommands(/** @type {CommandInfo[]} */ commands) {
    this.commands = commands
    this.onInput()
  }

  setEnabled(/** @type {boolean} */ enabled) {
    this.input.disabled = !enabled
    this.send.toggleAttribute('disabled', !enabled)
  }

  focus() {
    this.input.focus()
  }

  //

  resize() {
    this.input.style.height = 'auto'
    this.input.style.height = `${Math.min(this.input.scrollHeight, window.innerHeight / 3)}px`
  }

  onInput() {
    this.resize()

    const text = this.input.value
    const m = /^\/(\S*)$/.exec(text.trimEnd() === text ? text : '')
    if (!m) {
      this.hints.hidden = true
      return
    }

    const matches = this.commands.filter(c => c.name.startsWith(m[1]))
    if (!matches.length) {
      this.hints.hidden = true
      return
    }

    this.hints.replaceChildren(...matches.map(c => el(
      'div',
      'composer-hint',
      el('span', 'composer-hint-name', `/${c.name}`),
      el('span', 'composer-hint-desc', c.description ?? ''),
    )))
    this.hints.hidden = false
  }

  setText(/** @type {string} */ text) {
    this.input.value = text
    this.onInput()
    this.input.setSelectionRange(text.length, text.length)
  }

  onKeyDown(/** @type {KeyboardEvent} */ e) {
    if (e.isComposing) {
      return
    }

    if (e.key === 'Enter' && !e.shiftKey && !e.altKey) {
      e.preventDefault()
      this.submit()
      return
    }

    if (e.key === 'Escape') {
      e.preventDefault()
      this.actions.cancel()
      return
    }

    const input = this.input
    const atStart = input.selectionStart === 0 && input.selectionEnd === 0
    const atEnd = input.selectionStart === input.value.length

    if (e.key === 'ArrowUp' && atStart && this.historyPos > 0) {
      e.preventDefault()
      if (this.historyPos === this.history.length) {
        this.draft = input.value
      }
      this.historyPos -= 1
      this.setText(this.history[this.historyPos])
      input.setSelectionRange(0, 0)
      return
    }

    if (e.key === 'ArrowDown' && atEnd && this.historyPos < this.history.length) {
      e.preventDefault()
      this.historyPos += 1
      this.setText(this.historyPos === this.history.length ? this.draft : this.history[this.historyPos])
    }
  }

  async submit() {
    const text = this.input.value
    if (!text.trim() || this.submitting) {
      return
    }

    this.submitting = true
    let taken = false
    try {
      taken = await this.actions.submit(text)
    } finally {
      this.submitting = false
    }

    if (!taken) {
      return
    }

    if (this.history[this.history.length - 1] !== text) {
      this.history.push(text)
      saveHistory(this.history)
    }
    this.historyPos = this.history.length
    this.draft = ''
    this.setText('')
  }
}
