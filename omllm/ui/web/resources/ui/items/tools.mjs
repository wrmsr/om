// @ts-check


import {
  el,
  renderText,
} from '../texts.mjs'


////


/**
 * @typedef {import('../transcript.mjs').ItemRenderer} ItemRenderer
 * @typedef {import('../transcript.mjs').ItemElements} ItemElements
 * @typedef {import('../../core/feed.mjs').Item} Item
 */


const TOOL_ICONS = /** @type {Record<string, string>} */ ({
  running: '◌',
  ok: '✓',
  error: '✗',
  aborted: '–',
})


/** @returns {string} */
function compactJson(/** @type {any} */ v) {
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}


/** @returns {string} */
function prettyJson(/** @type {any} */ v) {
  try {
    return JSON.stringify(v, null, 2)
  } catch {
    return String(v)
  }
}


/** @returns {string} */
function tail(
  /** @type {string} */ s,
  /** @type {number} */ n,
) {
  return s.length <= n ? s : '…' + s.slice(s.length - n)
}


/** @returns {HTMLElement} */
function drawArgs(
  /** @type {Item} */ item,
  /** @type {ItemElements} */ els,
) {
  const args = /** @type {HTMLDetailsElement} */ (
    el('details', 'tool-args', el('summary', null, 'arguments'), el('pre', null, prettyJson(item.args)))
  )
  args.open = !!els.argsOpen
  args.addEventListener('toggle', () => {
    els.argsOpen = args.open
  })
  return args
}


/**
 * A tool call's card: a header line saying what was called, and - opened, by the user or by what it has to show - its
 * arguments, its live output, and its result. The calls a subagent it spawned makes, and the permission asks it makes,
 * are shown inside it.
 */
export const TOOL_ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ ({
  tool: {
    create(item, view) {
      const head = el('div', 'tool-head')
      const children = el('div', 'tool-children')
      const els = {box: el('div', 'item tool', head, el('div', 'tool-body'), children), children}

      // Opened or closed by hand, a card stays that way, whatever its state would show by itself.
      head.addEventListener('click', () => {
        /** @type {ItemElements} */ (els).open = !els.box.classList.contains('open')
        view.draw(item)
      })

      return els
    },

    draw(item, els) {
      const box = els.box
      box.className = `item tool tool-${item.status}`

      // Open is what the user chose, if they did, and otherwise whatever the card has to show: what the tool is
      // printing while it runs, or a result it says the user should see.
      const open = els.open ?? ((item.status === 'running' && !!item.output) || item.show)
      box.classList.toggle('open', open)

      const head = /** @type {HTMLElement} */ (box.querySelector(':scope > .tool-head'))
      head.replaceChildren(
        el('span', 'tool-icon', TOOL_ICONS[item.status] ?? '?'),
        el('span', 'tool-name', item.name),
      )

      if (item.summary !== null) {
        head.append(el('span', 'tool-summary', renderText(item.summary)))
      } else if (item.args !== null) {
        head.append(el('span', 'tool-summary tool-args-inline', tail(compactJson(item.args), 200)))
      }

      if (item.via) {
        head.append(el('span', 'tool-via', item.via))
      }

      const body = /** @type {HTMLElement} */ (box.querySelector(':scope > .tool-body'))
      if (!open) {
        body.replaceChildren()
        return
      }

      const parts = []

      if (item.args !== null) {
        parts.push(drawArgs(item, els))
      }

      if (item.status === 'running' && item.output) {
        parts.push(el('pre', 'tool-output', tail(item.output, 4000)))
      }

      if (item.note) {
        parts.push(el('div', 'tool-note', item.note))
      }

      if (item.result !== null) {
        const result = el('div', 'tool-result', renderText(item.result))
        if (typeof item.result === 'string') {
          result.classList.add('pre')
        }
        parts.push(result)
      }

      body.replaceChildren(...parts)
    },
  },
})
