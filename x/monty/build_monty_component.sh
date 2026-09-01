#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
usage: build_monty_component.sh MONTY_COMMIT [OUTPUT]

Build the current pydantic/monty WIT component at an exact Git commit. OUTPUT defaults to
./monty-runtime.component.wasm.

Runtime use does not require Node or Rust; they are only build-time tools.
EOF
    exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage

commit=$1
output=${2:-monty-runtime.component.wasm}
output=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$output")

work=$(mktemp -d "${TMPDIR:-/tmp}/monty-component.XXXXXX")
trap 'rm -rf "$work"' EXIT

src=$work/monty
tools=$work/component-tools

# Pin this checkout by immutable commit, not by branch or package version.
git clone --quiet --filter=blob:none https://github.com/pydantic/monty.git "$src"
git -C "$src" checkout --quiet --detach "$commit"

(
    cd "$src"
    rustup target add wasm32-wasip1
    cargo build --locked -p monty-wasm-runtime --target wasm32-wasip1 --release
)

mkdir -p "$tools"
printf '%s\n' '{"private":true,"type":"module"}' > "$tools/package.json"
npm install \
    --silent \
    --prefix "$tools" \
    --save-exact \
    @bytecodealliance/jco@1.25.2

cat > "$tools/build.mjs" <<'JS'
import {readFile, writeFile} from 'node:fs/promises'
import {join, resolve} from 'node:path'
import {
  componentNew,
  preview1AdapterReactorPath,
} from '@bytecodealliance/jco'

const root = resolve(process.argv[2])
const output = resolve(process.argv[3])

const [core, adapter] = await Promise.all([
  readFile(join(root, 'target/wasm32-wasip1/release/monty_wasm_runtime.wasm')),
  readFile(preview1AdapterReactorPath()),
])

const component = await componentNew(core, [
  ['wasi_snapshot_preview1', adapter],
])

await writeFile(output, component)
JS

mkdir -p "$(dirname "$output")"
node "$tools/build.mjs" "$src" "$output"

printf 'monty commit: %s\n' "$(git -C "$src" rev-parse HEAD)"
printf 'component: %s\n' "$output"
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$output"
else
    sha256sum "$output"
fi
