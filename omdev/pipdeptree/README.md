# Vendored pipdeptree

This is an internal fork of [pipdeptree](https://github.com/tox-dev/pipdeptree) at commit
`c0a7570ebcef4d0c818533c6382c10c8a4f16510` (version 3.1.1). The upstream license is in [LICENSE](LICENSE).

The runtime uses the standard library and this repository's `omcore` and `omdev.packaging` modules. It does not
require the upstream package or its optional Python dependencies.

From the repository root, run `./python -m <package-name>` to inspect the active Python environment. The `from-lock`
subcommand reads a PEP 751 `pylock.toml` offline. Both commands support text, freeze, JSON, JSON tree, Mermaid, and
Graphviz DOT output. Graphviz source (`-o graphviz-dot`) needs no Graphviz installation. Other Graphviz formats
(`-o graphviz-svg`, `-o graphviz-png`, and so on) use the `dot` executable when requested. The `--summary` report
supports text and JSON.

The index resolver and Rich renderer from the vendored snapshot were removed because they required external Python
packages. The Python API remains available through this package's `render(...)` function.
