// @ts-check


////


/**
 * @typedef {import('./api.mjs').FeedEntry} FeedEntry
 */


/**
 * One thing in the transcript. Every item has an id, a kind, and the id of the item it is shown inside - a run, or a
 * tool call's card - or null for the top level. The rest depends on the kind:
 *
 *   - `user`, `command`: `text` - a prompt, a command line
 *   - `text`: `text` - WebText displayed, command output in the main
 *   - `notice`: `text`, `level`
 *   - `run`: `status` - `running`, or how it ended - and `error`
 *   - `ai`, `thinking`: `text`, `done`
 *   - `tool`: `key`, `name`, `summary`, `args`, `via`, `status` - `running`, `ok`, `error`, or `aborted` - and
 *     `output`, `note`, `result`, `show`
 *   - `ask`: `askId`, `key`, `tool`, `target`, `rule`, `preview`, `outcome` - `pending`, `allow`, `deny`, or `aborted`
 *
 * @typedef {{id: string, kind: string, parent: string | null, [key: string]: any}} Item
 */


/**
 * @typedef {object} Changes
 * @property {Item[]} added - in the order to be shown
 * @property {Set<Item>} updated - items changed after being added, never including those added in the same batch
 * @property {boolean} status - whether anything in `FeedModel.status` changed
 * @property {Set<Item>} fresh - `added`, as a set
 */


/**
 * @typedef {object} Usage
 * @property {number} input
 * @property {number} inputCached
 * @property {number} inputCacheWrite
 * @property {number} output
 * @property {number} reasoning
 * @property {number} turns
 */


/**
 * Folds the feed into the transcript the page shows: a flat registry of items, each knowing where it is shown, plus
 * the session's status. Knows nothing of the DOM - `apply` reports what changed, and the view does the rest.
 *
 * Entries are applied in seq order, each once: one already seen - arriving again on a second stream - is ignored.
 */
export class FeedModel {
  constructor() {
    this.lastSeq = 0

    /** @type {Item[]} */ this.items = []
    /** @type {Map<string, Item>} */ this.byId = new Map()
    /** @type {Map<string, Item>} */ this.tools = new Map()
    /** @type {Map<string, Item>} */ this.asks = new Map()

    /** @type {Item | null} */ this.openRun = null
    /** @type {Item | null} */ this.openAi = null
    /** @type {Item | null} */ this.openThinking = null

    this.status = {
      /** @type {Map<string, {kind: string, text: string, exclusive: boolean}>} */ running: new Map(),

      /** @type {Usage} */ usage: {input: 0, inputCached: 0, inputCacheWrite: 0, output: 0, reasoning: 0, turns: 0},
      /** @type {{input: number, limit: number | null, estimated: boolean} | null} */ context: null,

      shutdown: false,
    }

    this.nextId = 1
  }

  /** @returns {boolean} */
  get busy() {
    for (const sub of this.status.running.values()) {
      if (sub.exclusive) {
        return true
      }
    }
    return false
  }

  //

  /** @returns {Item} */
  add(
    /** @type {Changes} */ changes,
    /** @type {string} */ kind,
    /** @type {Record<string, any>} */ fields,
    /** @type {Item | null | undefined} */ parent = undefined,
  ) {
    if (parent === undefined) {
      parent = this.openRun
    }

    const item = {id: `i${this.nextId++}`, kind, parent: parent ? parent.id : null, ...fields}
    this.items.push(item)
    this.byId.set(item.id, item)
    changes.added.push(item)
    changes.fresh.add(item)
    return item
  }

  touch(
    /** @type {Changes} */ changes,
    /** @type {Item} */ item,
  ) {
    if (!changes.fresh.has(item)) {
      changes.updated.add(item)
    }
  }

  /**
   * Ends the streaming blocks in progress: whatever comes next starts a block of its own. Called on what ends a block
   * of the model's output - a new prompt or run, a tool call, a switch between thinking and text - and not on what
   * merely lands beside one, like a notice or a command's output: the stream's next delta, and its end with the whole
   * block's text, belong to the block it was already in.
   */
  closeBlocks(/** @type {Changes} */ changes) {
    for (const item of [this.openAi, this.openThinking]) {
      if (item && !item.done) {
        item.done = true
        this.touch(changes, item)
      }
    }
    this.openAi = null
    this.openThinking = null
  }

  //

  onSubmissionStart(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.status.running.set(e.id, {kind: e.kind, text: e.text, exclusive: e.exclusive ?? true})
    changes.status = true
  }

  onSubmissionEnd(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.status.running.delete(e.id)
    changes.status = true
  }

  onUserMessage(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.closeBlocks(changes)
    this.add(changes, 'user', {text: e.text})
  }

  onCommandEcho(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.add(changes, 'command', {text: e.text})
  }

  onRunStart(/** @type {Changes} */ changes) {
    this.closeBlocks(changes)
    this.openRun = this.add(changes, 'run', {status: 'running', error: null}, null)
  }

  onRunEnd(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.closeBlocks(changes)

    for (const tool of this.tools.values()) {
      if (tool.status === 'running') {
        tool.status = 'aborted'
        this.touch(changes, tool)
      }
    }

    if (this.openRun) {
      this.openRun.status = e.reason
      this.openRun.error = e.error ?? null
      this.touch(changes, this.openRun)
      this.openRun = null
    }
  }

  onAiTextDelta(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    if (this.openThinking) {
      this.closeBlocks(changes)
    }
    if (!this.openAi) {
      this.openAi = this.add(changes, 'ai', {text: '', done: false})
    }
    this.openAi.text += e.text
    this.touch(changes, this.openAi)
  }

  onAiTextEnd(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const item = this.openAi ?? this.add(changes, 'ai', {text: '', done: false})
    item.text = e.text
    this.touch(changes, item)
    this.closeBlocks(changes)
  }

  onAiText(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.closeBlocks(changes)
    this.add(changes, 'ai', {text: e.text, done: true})
  }

  onThinkingStart(/** @type {Changes} */ changes) {
    this.closeBlocks(changes)
    this.openThinking = this.add(changes, 'thinking', {text: '', done: false})
  }

  onThinkingDelta(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    if (!this.openThinking) {
      this.closeBlocks(changes)
      this.openThinking = this.add(changes, 'thinking', {text: '', done: false})
    }
    this.openThinking.text += e.text
    this.touch(changes, this.openThinking)
  }

  onThinkingEnd(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const item = this.openThinking ?? this.add(changes, 'thinking', {text: '', done: false})
    item.text = e.text
    this.touch(changes, item)
    this.closeBlocks(changes)
  }

  onToolStart(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.closeBlocks(changes)

    const parent = e.parent != null ? this.tools.get(e.parent) : undefined
    const item = this.add(changes, 'tool', {
      key: e.key,
      name: e.name,
      summary: e.summary ?? null,
      args: e.args ?? null,
      via: e.via ?? null,
      status: 'running',
      output: '',
      note: null,
      result: null,
      show: false,
    }, parent)
    this.tools.set(e.key, item)
  }

  onToolOutput(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const item = this.tools.get(e.key)
    if (item) {
      item.output += e.text
      this.touch(changes, item)
    }
  }

  onToolEnd(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    // A call never seen starting - its start lost to a feed replayed from a stored transcript, say - gets a card now.
    let item = this.tools.get(e.key)
    if (!item) {
      item = this.add(changes, 'tool', {key: e.key, name: e.key, summary: null, args: null, via: null, output: ''})
      this.tools.set(e.key, item)
    }

    item.status = e.ok ? 'ok' : 'error'
    item.note = e.note ?? null
    item.result = e.result ?? null
    item.show = !!e.show
    this.touch(changes, item)
  }

  onPermissionAsk(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const parent = e.key != null ? this.tools.get(e.key) : undefined
    const item = this.add(changes, 'ask', {
      askId: e.id,
      key: e.key ?? null,
      tool: e.tool,
      target: e.target,
      rule: e.rule,
      preview: e.preview ?? null,
      outcome: 'pending',
    }, parent)
    this.asks.set(e.id, item)

    if (parent) {
      this.touch(changes, parent)
    }
    changes.status = true
  }

  onPermissionAnswer(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const item = this.asks.get(e.id)
    if (item) {
      item.outcome = e.outcome
      this.touch(changes, item)
    }
    changes.status = true
  }

  onUsage(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    const u = this.status.usage
    u.input += e.input ?? 0
    u.inputCached += e.input_cached ?? 0
    u.inputCacheWrite += e.input_cache_write ?? 0
    u.output += e.output ?? 0
    u.reasoning += e.reasoning ?? 0
    u.turns += 1
    changes.status = true
  }

  onContext(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.status.context = {input: e.input, limit: e.limit ?? null, estimated: !!e.estimated}
    changes.status = true
  }

  onNotice(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.add(changes, 'notice', {text: e.text, level: e.level ?? 'info'})
  }

  onText(/** @type {Changes} */ changes, /** @type {FeedEntry} */ e) {
    this.add(changes, 'text', {text: e.text})
  }

  onShutdown(/** @type {Changes} */ changes) {
    this.closeBlocks(changes)
    this.add(changes, 'notice', {text: 'session ended', level: 'info'}, null)
    this.status.shutdown = true
    changes.status = true
  }

  /** @returns {Changes} */
  apply(/** @type {Iterable<FeedEntry>} */ entries) {
    /** @type {Changes} */ const changes = {added: [], updated: new Set(), status: false, fresh: new Set()}

    for (const e of entries) {
      if (e.seq <= this.lastSeq) {
        continue
      }
      this.lastSeq = e.seq

      switch (e.type) {
        case 'submission_start':
          this.onSubmissionStart(changes, e)
          break
        case 'submission_end':
          this.onSubmissionEnd(changes, e)
          break
        case 'user_message':
          this.onUserMessage(changes, e)
          break
        case 'command_echo':
          this.onCommandEcho(changes, e)
          break
        case 'run_start':
          this.onRunStart(changes)
          break
        case 'run_end':
          this.onRunEnd(changes, e)
          break
        case 'ai_text_delta':
          this.onAiTextDelta(changes, e)
          break
        case 'ai_text_end':
          this.onAiTextEnd(changes, e)
          break
        case 'ai_text':
          this.onAiText(changes, e)
          break
        case 'thinking_start':
          this.onThinkingStart(changes)
          break
        case 'thinking_delta':
          this.onThinkingDelta(changes, e)
          break
        case 'thinking_end':
          this.onThinkingEnd(changes, e)
          break
        case 'tool_start':
          this.onToolStart(changes, e)
          break
        case 'tool_output':
          this.onToolOutput(changes, e)
          break
        case 'tool_end':
          this.onToolEnd(changes, e)
          break
        case 'permission_ask':
          this.onPermissionAsk(changes, e)
          break
        case 'permission_answer':
          this.onPermissionAnswer(changes, e)
          break
        case 'usage':
          this.onUsage(changes, e)
          break
        case 'context':
          this.onContext(changes, e)
          break
        case 'notice':
          this.onNotice(changes, e)
          break
        case 'text':
          this.onText(changes, e)
          break
        case 'shutdown':
          this.onShutdown(changes)
          break
        default:
          // An event of a type this page does not know - from a newer server, say - is passed over, not fatal.
          break
      }
    }

    return changes
  }

  /** @returns {Item[]} */
  pendingAsks() {
    return [...this.asks.values()].filter(a => a.outcome === 'pending')
  }

  /** @returns {Item | undefined} */
  get(/** @type {string | null} */ id) {
    return id === null ? undefined : this.byId.get(id)
  }
}
