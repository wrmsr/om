// @ts-check


import {renderMarkdown} from '../markdown.mjs'

import {el} from '../texts.mjs'


////


/**
 * @typedef {import('../transcript.mjs').ItemRenderer} ItemRenderer
 */


const RUN_END_NOTES = /** @type {Record<string, string>} */ ({
  cancelled: 'cancelled',
  failed: 'failed',
  length: 'cut off by the token limit',
  context_length: 'stopped at the context-window limit',
  max_turns: 'turn limit reached',
})


/** A run of the agent, and the model's text and thinking inside it. */
export const RUN_ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ ({
  run: {
    create() {
      const children = el('div', 'run-body')
      return {box: el('section', 'item run', el('div', 'who who-ai', 'ai'), children), children}
    },

    draw(item, {box}) {
      box.classList.toggle('running', item.status === 'running')

      box.querySelector(':scope > .run-end')?.remove()

      const note = RUN_END_NOTES[item.status]
      if (note) {
        const end = el('div', `run-end run-end-${item.status}`, `(${note})`)
        if (item.error) {
          end.title = item.error
        }
        box.append(end)
      }
    },
  },

  ai: {
    draw(item, {box}) {
      box.classList.add('md')
      box.classList.toggle('streaming', !item.done)
      box.innerHTML = renderMarkdown(item.text)
    },
  },

  thinking: {
    create() {
      return {box: el('details', 'item thinking', el('summary', null), el('div', 'thinking-body'))}
    },

    draw(item, {box}) {
      box.classList.toggle('streaming', !item.done)

      const summary = /** @type {HTMLElement} */ (box.querySelector(':scope > summary'))
      summary.textContent = item.done ? 'thought' : 'thinking…'

      const body = /** @type {HTMLElement} */ (box.querySelector(':scope > .thinking-body'))
      body.textContent = item.text
    },
  },
})
