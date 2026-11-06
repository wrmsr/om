// @ts-check


import {
  el,
  renderText,
} from '../texts.mjs'


////


/**
 * @typedef {import('../transcript.mjs').ItemRenderer} ItemRenderer
 */


/** What the user said: a prompt, or a command line. */
export const MESSAGE_ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ ({
  user: {
    draw(item, {box}) {
      box.replaceChildren(el('div', 'who who-you', 'you'), el('div', 'user-text', item.text))
    },
  },

  command: {
    draw(item, {box}) {
      box.replaceChildren(item.text)
    },
  },
})


/** What was displayed - command output, in the main - and what the harness had to say. */
export const DISPLAY_ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ ({
  text: {
    draw(item, {box}) {
      box.replaceChildren(renderText(item.text))
    },
  },

  notice: {
    draw(item, {box}) {
      box.className = `item notice notice-${item.level}`
      box.replaceChildren(item.text)
    },
  },
})
