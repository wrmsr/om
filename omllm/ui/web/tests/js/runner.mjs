// @ts-check


// @ts-ignore -- Node's own types are not installed: there is nothing to install them with.
import assert from 'node:assert/strict'


////


/** @type {{name: string, fn: () => void | Promise<void>}[]} */
const tests = []

const nodeProcess = /** @type {any} */ (globalThis).process


export {assert}


/** @returns {void} */
export function test(
  /** @type {string} */ name,
  /** @type {() => void | Promise<void>} */ fn,
) {
  tests.push({name, fn})
}


/** @returns {Promise<void>} */
export async function run() {
  let failed = 0
  for (const item of tests) {
    try {
      await item.fn()
      nodeProcess.stdout.write(`ok - ${item.name}\n`)
    } catch (error) {
      failed += 1
      const details = error instanceof Error ? error.stack ?? error.message : String(error)
      nodeProcess.stderr.write(`not ok - ${item.name}\n${details}\n`)
    }
  }
  nodeProcess.stdout.write(`${tests.length - failed}/${tests.length} JavaScript tests passed\n`)
  if (failed) {
    nodeProcess.exitCode = 1
  }
}
