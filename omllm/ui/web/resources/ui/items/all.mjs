// @ts-check


import {ASK_ITEM_RENDERERS} from './asks.mjs'

import {
  DISPLAY_ITEM_RENDERERS,
  MESSAGE_ITEM_RENDERERS,
} from './messages.mjs'

import {RUN_ITEM_RENDERERS} from './runs.mjs'

import {TOOL_ITEM_RENDERERS} from './tools.mjs'


////


/**
 * @typedef {import('../transcript.mjs').ItemRenderer} ItemRenderer
 */


/** A renderer for every kind of item `FeedModel` makes. */
export const ITEM_RENDERERS = /** @type {Record<string, ItemRenderer>} */ (Object.freeze({
  ...MESSAGE_ITEM_RENDERERS,
  ...DISPLAY_ITEM_RENDERERS,
  ...RUN_ITEM_RENDERERS,
  ...TOOL_ITEM_RENDERERS,
  ...ASK_ITEM_RENDERERS,
}))
