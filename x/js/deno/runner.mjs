const PROTOCOL_VERSION = 1;
const PROTOCOL_PREFIX = "\x1escript-runner-result-v1:";

const jsonParse = JSON.parse.bind(JSON);
const jsonStringify = JSON.stringify.bind(JSON);
const string = String;
const textEncoder = new TextEncoder();

const workerSource = String.raw`
const arrayPush = Array.prototype.push;
const asyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const jsonParse = JSON.parse.bind(JSON);
const jsonStringify = JSON.stringify.bind(JSON);
const messagePortClose = MessagePort.prototype.close;
const messagePortPostMessage = MessagePort.prototype.postMessage;
const rangeError = RangeError;
const reflectApply = Reflect.apply;
const string = String;
const typeError = TypeError;

function errorString(value, fallback) {
  if (value == null) {
    return fallback;
  }
  try {
    return typeof value === "string" ? value : string(value);
  } catch {
    return fallback;
  }
}

function serializeError(error) {
  let name = "Error";
  let message = "Script execution failed";
  let stack = null;

  try {
    name = errorString(error?.name, name);
  } catch {
    // Retain the fallback.
  }
  try {
    message = errorString(error?.message ?? error, message);
  } catch {
    // Retain the fallback.
  }
  try {
    if (error?.stack != null) {
      stack = errorString(error.stack, null);
    }
  } catch {
    // Retain the fallback.
  }

  return { name, message, stack };
}

function jsonSnapshot(value, description) {
  let encoded;
  try {
    encoded = jsonStringify(value);
  } catch {
    throw new typeError(description + " is not JSON-serializable");
  }
  if (encoded === undefined) {
    throw new typeError(description + " is not JSON-serializable");
  }
  return jsonParse(encoded);
}

self.onmessage = async (event) => {
  const { port, source, input, maxEmissions } = event.data;
  const emitted = [];

  const emit = (value) => {
    if (emitted.length >= maxEmissions) {
      throw new rangeError("Script emitted too many values");
    }
    reflectApply(
      arrayPush,
      emitted,
      [jsonSnapshot(value, "Emitted value")],
    );
  };

  let payload;
  try {
    const fn = new asyncFunction(
      "input",
      "emit",
      '"use strict";\n' + source + '\n//# sourceURL=llm-script.js',
    );
    const value = jsonSnapshot(await fn(input, emit), "Script result");
    payload = { ok: true, value, emitted };
  } catch (error) {
    payload = { ok: false, error: serializeError(error) };
  }

  reflectApply(messagePortPostMessage, port, [payload]);
  reflectApply(messagePortClose, port, []);
};
`;

function requireObject(value, description) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(description + " must be an object");
  }
  return value;
}

function requirePositiveInteger(value, description) {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new TypeError(description + " must be a positive integer");
  }
  return value;
}

function serializeError(error) {
  let name = "Error";
  let message = "Runner execution failed";
  let stack = null;

  try {
    name = typeof error?.name === "string" ? error.name : string(error?.name);
  } catch {
    // Retain the fallback.
  }
  try {
    message = typeof error?.message === "string" ? error.message : string(error);
  } catch {
    // Retain the fallback.
  }
  try {
    if (error?.stack != null) {
      stack = typeof error.stack === "string" ? error.stack : string(error.stack);
    }
  } catch {
    // Retain the fallback.
  }

  return { name, message, stack };
}

async function readRequest() {
  const requestText = await new Response(Deno.stdin.readable).text();
  return requireObject(jsonParse(requestText), "Request");
}

async function execute(request) {
  if (request.version !== PROTOCOL_VERSION) {
    throw new TypeError("Unsupported protocol version");
  }
  if (typeof request.token !== "string" || !/^[0-9a-f]{32}$/.test(request.token)) {
    throw new TypeError("Invalid protocol token");
  }
  if (typeof request.source !== "string") {
    throw new TypeError("Script source must be a string");
  }

  const maxEmissions = requirePositiveInteger(
    request.maxEmissions,
    "maxEmissions",
  );
  const maxResultBytes = requirePositiveInteger(
    request.maxResultBytes,
    "maxResultBytes",
  );

  const workerUrl = URL.createObjectURL(
    new Blob([workerSource], { type: "text/javascript" }),
  );
  const worker = new Worker(workerUrl, {
    type: "module",
    name: "llm-script",
  });
  const channel = new MessageChannel();

  let payload;
  try {
    payload = await new Promise((resolve) => {
      let settled = false;

      const finish = (value) => {
        if (!settled) {
          settled = true;
          resolve(value);
        }
      };

      channel.port1.onmessage = (event) => finish(event.data);
      channel.port1.onmessageerror = () => finish({
        ok: false,
        error: {
          name: "DataCloneError",
          message: "Worker returned an invalid message",
          stack: null,
        },
      });
      worker.onerror = (event) => {
        event.preventDefault();
        finish({
          ok: false,
          error: {
            name: "WorkerError",
            message: event.message || "Script worker failed",
            stack: null,
          },
        });
      };

      worker.postMessage(
        {
          port: channel.port2,
          source: request.source,
          input: request.input,
          maxEmissions,
        },
        [channel.port2],
      );
    });
  } finally {
    channel.port1.close();
    worker.terminate();
    URL.revokeObjectURL(workerUrl);
  }

  let payloadText;
  try {
    payloadText = jsonStringify(payload);
  } catch (error) {
    payloadText = jsonStringify({
      ok: false,
      error: serializeError(error),
    });
  }

  if (textEncoder.encode(payloadText).byteLength > maxResultBytes) {
    payloadText = jsonStringify({
      ok: false,
      error: {
        name: "ResultSizeError",
        message: "Script result exceeded its byte limit",
        stack: null,
      },
    });
  }

  const protocolText =
    PROTOCOL_PREFIX + request.token + ":" + payloadText + "\n";
  await Deno.stdout.write(textEncoder.encode(protocolText));
}

try {
  await execute(await readRequest());
} catch (error) {
  console.error(serializeError(error));
  Deno.exit(1);
}
