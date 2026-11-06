// @ts-check


import {renderMarkdown} from './markdown.mjs'


////


/**
 * Renders the server's WebText - see `omllm.ui.web.texts` - to DOM nodes. Everything is built as nodes or escaped,
 * except markdown, which goes through `renderMarkdown`.
 */


/** @returns {HTMLElement} */
export function el(
  /** @type {string} */ tag,
  /** @type {string | null} */ className = null,
  /** @type {(Node | string)[]} */ ...children
) {
  const e = document.createElement(tag)
  if (className) {
    e.className = className
  }
  e.append(...children)
  return e
}


/** @returns {string} */
function diffLineClass(/** @type {string} */ line) {
  if (line.startsWith('+++') || line.startsWith('---')) {
    return 'd-file'
  }
  if (line.startsWith('@@')) {
    return 'd-hunk'
  }
  if (line.startsWith('+')) {
    return 'd-add'
  }
  if (line.startsWith('-')) {
    return 'd-del'
  }
  if (line.startsWith('\\')) {
    return 'd-meta'
  }
  return 'd-ctx'
}


/** @returns {HTMLElement} */
export function renderDiff(/** @type {{path?: string | null, lines: string[]}} */ diff) {
  const pre = el('pre', 'diff-body')
  for (const line of diff.lines) {
    // File headers say what the block's own header says already.
    if (line.startsWith('+++') || line.startsWith('---')) {
      continue
    }
    pre.append(el('span', diffLineClass(line), line.endsWith('\n') ? line : line + '\n'))
  }

  const box = el('div', 'diff')
  if (diff.path) {
    box.append(el('div', 'diff-path', diff.path))
  }
  box.append(pre)
  return box
}


/** @returns {Node} */
export function renderText(/** @type {any} */ t) {
  if (t === null || t === undefined) {
    return document.createDocumentFragment()
  }

  if (typeof t === 'string') {
    return document.createTextNode(t)
  }

  if (Array.isArray(t)) {
    const frag = document.createDocumentFragment()
    for (const c of t) {
      frag.append(renderText(c))
    }
    return frag
  }

  if ('style' in t) {
    const span = el('span', 't-style')
    const y = t.style ?? {}
    if (y.color) {
      span.classList.add(`t-${y.color}`)
    }
    if (y.bold) {
      span.classList.add('t-bold')
    }
    if (y.italic) {
      span.classList.add('t-italic')
    }
    span.append(renderText(t.c))
    return span
  }

  if ('json' in t) {
    const span = el('span', 't-json')
    for (const [kind, s] of t.json) {
      span.append(kind ? el('span', `j-${kind}`, s) : s)
    }
    return span
  }

  if ('md' in t) {
    const div = el('div', 'md')
    div.innerHTML = renderMarkdown(t.md)
    return div
  }

  if ('diff' in t) {
    return renderDiff(t.diff)
  }

  // A node of a kind this page does not know, from a newer server: shown for what it is rather than dropped.
  return document.createTextNode(JSON.stringify(t))
}


/** @returns {string} */
export function textToString(/** @type {any} */ t) {
  if (t === null || t === undefined) {
    return ''
  }
  if (typeof t === 'string') {
    return t
  }
  if (Array.isArray(t)) {
    return t.map(textToString).join('')
  }
  if ('style' in t) {
    return textToString(t.c)
  }
  if ('json' in t) {
    return t.json.map((/** @type {[string | null, string]} */ [, s]) => s).join('')
  }
  if ('md' in t) {
    return t.md
  }
  if ('diff' in t) {
    return t.diff.lines.join('')
  }
  return JSON.stringify(t)
}
