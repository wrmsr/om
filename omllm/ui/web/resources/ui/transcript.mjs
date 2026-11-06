// @ts-check


import {el} from './texts.mjs'


////


/**
 * @typedef {import('../core/feed.mjs').Item} Item
 * @typedef {import('../core/feed.mjs').Changes} Changes
 */


/**
 * @typedef {object} TranscriptActions
 * @property {(askId: string, allow: boolean) => Promise<boolean>} answer - whether the answer went through
 */


/**
 * An item's elements, plus whatever its renderer keeps beside them - what the user has opened or closed, say, which a
 * redraw must not undo.
 *
 * @typedef {{box: HTMLElement, children?: HTMLElement, [key: string]: any}} ItemElements
 */


/**
 * How the view shows one kind of item: `create` builds its elements once, as it is added - among them, for an item
 * other items are shown inside, the element they go in - and `draw` brings them up to date with the item, after every
 * change. Without a `create`, an item gets a plain div.
 *
 * @typedef {object} ItemRenderer
 * @property {(item: Item, view: TranscriptView) => ItemElements} [create]
 * @property {(item: Item, els: ItemElements, view: TranscriptView) => void} draw
 */


/**
 * The transcript, as DOM: one element per model item, put inside its parent's as it is added, and redrawn when it
 * changes - once per animation frame however many times that is, which is what keeps a fast stream cheap. What each
 * kind of item looks like is up to its renderer; an item of a kind with none is not shown.
 */
export class TranscriptView {
  constructor(
    /** @type {HTMLElement} */ root,
    /** @type {HTMLElement} */ scroller,
    /** @type {Record<string, ItemRenderer>} */ renderers,
    /** @type {TranscriptActions} */ actions,
  ) {
    this.root = root
    this.scroller = scroller
    this.renderers = renderers
    this.actions = actions

    /** @type {Map<string, ItemElements>} */ this.els = new Map()
    /** @type {Set<Item>} */ this.dirty = new Set()
    /** @type {number | null} */ this.frame = null

    // Whether the next frame is to end scrolled to the bottom, as it was when its changes came in.
    this.stick = false
  }

  /** @returns {boolean} */
  isAtBottom() {
    const s = this.scroller
    return s.scrollHeight - s.scrollTop - s.clientHeight < 48
  }

  scrollToBottom() {
    this.scroller.scrollTop = this.scroller.scrollHeight
  }

  apply(/** @type {Changes} */ changes) {
    const stick = this.isAtBottom()

    for (const item of changes.added) {
      const renderer = this.renderers[item.kind]
      if (!renderer) {
        continue
      }

      const els = renderer.create ? renderer.create(item, this) : {box: el('div', `item ${item.kind}`)}
      this.els.set(item.id, els)

      const parent = item.parent !== null ? this.els.get(item.parent) : undefined
      ;(parent?.children ?? this.root).append(els.box)

      this.dirty.add(item)
    }

    for (const item of changes.updated) {
      this.dirty.add(item)
    }

    this.schedule(stick)
  }

  schedule(/** @type {boolean} */ stick) {
    if (stick) {
      this.stick = true
    }
    if (this.frame === null) {
      this.frame = requestAnimationFrame(() => this.flush())
    }
  }

  flush() {
    this.frame = null

    const stick = this.stick || this.isAtBottom()
    this.stick = false

    const dirty = [...this.dirty]
    this.dirty.clear()
    for (const item of dirty) {
      this.draw(item)
    }

    if (stick) {
      this.scrollToBottom()
    }
  }

  /** Redraws the item now - for a change the user made, which should not wait on a frame. */
  draw(/** @type {Item} */ item) {
    const els = this.els.get(item.id)
    const renderer = this.renderers[item.kind]
    if (els && renderer) {
      renderer.draw(item, els, this)
    }
  }
}
