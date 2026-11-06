// @ts-check


import {
  renderMarkdown,
  safeHref,
} from '../../resources/ui/markdown.mjs'

import {
  assert,
  test,
} from './runner.mjs'


////


test('markdown: renders', () => {
  const html = renderMarkdown('# Hi\n\nsome **bold** and `code`\n\n```py\nprint(1)\n```\n')
  assert.match(html, /<h1>Hi<\/h1>/)
  assert.match(html, /<strong>bold<\/strong>/)
  assert.match(html, /<code class="language-py">print\(1\)/)
})


test('markdown: raw html is text', () => {
  const html = renderMarkdown('<script>alert(1)</script>\n\nhello <b onclick="x()">x</b>')
  assert.doesNotMatch(html, /<script/)
  assert.doesNotMatch(html, /<b /)
  assert.match(html, /&lt;script&gt;/)
  assert.match(html, /&lt;b onclick=&quot;x\(\)&quot;&gt;/)
})


test('markdown: only safe links survive', () => {
  const html = renderMarkdown([
    '[ok](https://example.com)',
    '[js](javascript:alert(1))',
    '[rel](/api/cancel)',
    '[data](data:text/html,x)',
  ].join(' '))
  assert.match(html, /<a href="https:\/\/example\.com\/" target="_blank" rel="noopener noreferrer">ok<\/a>/)
  assert.doesNotMatch(html, /javascript:/)
  assert.doesNotMatch(html, /\/api\/cancel/)
  assert.doesNotMatch(html, /data:/)
})


test('markdown: images are never loaded', () => {
  const html = renderMarkdown('![pic](https://evil.example/x.png?d=secret)')
  assert.doesNotMatch(html, /<img/)
  assert.match(html, /<a class="md-image" href="https:\/\/evil\.example\/x\.png\?d=secret"/)
})


test('markdown: safeHref', () => {
  assert.equal(safeHref('https://a.example/b'), 'https://a.example/b')
  assert.equal(safeHref('mailto:x@y.example'), 'mailto:x@y.example')
  assert.equal(safeHref('JAVASCRIPT:alert(1)'), null)
  assert.equal(safeHref('/relative'), null)
})
