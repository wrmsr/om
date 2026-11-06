// @ts-check


import {
  el,
  renderText,
} from '../texts.mjs'


////


/**
 * @typedef {import('../transcript.mjs').ItemRenderer} ItemRenderer
 */


const ASK_OUTCOMES = /** @type {Record<string, string>} */ ({
  allow: 'allowed',
  deny: 'denied',
  aborted: 'withdrawn',
})


/**
 * A permission ask: what is asking to do what - with the change it would make, where it says - and the buttons which
 * answer it. Once answered it shrinks to a line, as what it showed is what the call's result shows by then.
 */
export const ASK_ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ ({
  ask: {
    draw(item, {box}, view) {
      box.className = `item ask is-${item.outcome}`

      if (item.outcome !== 'pending') {
        const line = el(
          'div',
          'ask-line',
          el('span', 'ask-outcome', ASK_OUTCOMES[item.outcome] ?? item.outcome),
          el('b', null, item.tool),
          el('span', 'ask-target', item.target),
        )
        line.title = item.rule
        box.replaceChildren(line)
        return
      }

      const head = el('div', 'ask-head', 'Permission: ', el('b', null, item.tool))
      head.title = item.rule

      const parts = [
        head,
        el('div', 'ask-target', item.target),
      ]

      if (item.preview !== null) {
        parts.push(el('div', 'ask-preview', renderText(item.preview)))
      }

      const allow = el('button', 'ask-allow', 'Allow')
      const deny = el('button', 'ask-deny', 'Deny')
      for (const [button, allowed] of /** @type {[HTMLElement, boolean][]} */ ([[allow, true], [deny, false]])) {
        button.addEventListener('click', async () => {
          allow.setAttribute('disabled', '')
          deny.setAttribute('disabled', '')

          // Answered, the ask's outcome redraws it. Not, it can be answered again.
          if (!await view.actions.answer(item.askId, allowed)) {
            allow.removeAttribute('disabled')
            deny.removeAttribute('disabled')
          }
        })
      }
      parts.push(el('div', 'ask-actions', allow, deny))

      box.replaceChildren(...parts)
    },
  },
})
