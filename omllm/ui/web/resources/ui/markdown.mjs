// @ts-check


// @ts-ignore -- Vendored, and untyped: marked's own types are typescript, which is not vendored.
import {Marked} from '../vendor/packages/marked/index.js'


////


/**
 * Markdown to html, for model output - which is untrusted, and headed into the page. Raw html is shown as text - an
 * html block as a code block, as the terminal frontends show it - links are kept only to schemes which go nowhere
 * unexpected, and images are never loaded: an image is a request made on the reader's behalf the moment it is shown,
 * which is a way out for whatever the model was talked into putting in its url. The page's content security policy
 * stands behind all of this.
 */


/** @returns {string} */
export function escapeHtml(/** @type {string} */ s) {
  return s
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}


const SAFE_LINK_PROTOCOLS = new Set(['http:', 'https:', 'mailto:'])


/** @returns {string | null} */
export function safeHref(/** @type {string} */ href) {
  let url
  try {
    url = new URL(href)
  } catch {
    // Relative, and so pointing back into this server - nothing a model has any business linking to.
    return null
  }
  return SAFE_LINK_PROTOCOLS.has(url.protocol) ? url.href : null
}


const MARKED = new Marked({
  gfm: true,
  breaks: false,
  renderer: {
    /**
     * @param {any} token
     * @returns {string}
     */
    html(token) {
      if (token.block) {
        return `<pre class="md-html"><code>${escapeHtml(token.text)}</code></pre>\n`
      }
      return escapeHtml(token.text)
    },

    /**
     * @param {any} token
     * @returns {string}
     */
    link(token) {
      // @ts-ignore -- marked binds renderer methods to its renderer, which has a parser.
      const inner = this.parser.parseInline(token.tokens)
      const href = safeHref(token.href)
      if (href === null) {
        return inner
      }
      const title = token.title ? ` title="${escapeHtml(token.title)}"` : ''
      return `<a href="${escapeHtml(href)}"${title} target="_blank" rel="noopener noreferrer">${inner}</a>`
    },

    /**
     * @param {any} token
     * @returns {string}
     */
    image(token) {
      const alt = token.text ? escapeHtml(token.text) : 'image'
      const href = safeHref(token.href)
      if (href === null) {
        return `[${alt}]`
      }
      return `<a class="md-image" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">[${alt}]</a>`
    },
  },
})


/** @returns {string} */
export function renderMarkdown(/** @type {string} */ src) {
  return /** @type {string} */ (MARKED.parse(src, {async: false}))
}
