# Puzzle DSL — VS Code extension

Language support for `puzzle/lib/*.dsl` and `impls/*.dsl`: **syntax highlighting**, **hover**, **go to definition**, plus diagnostics, completion, and a symbol outline.

## Requirements

- **Python 3.10+** on your PATH (or set `puzzleDsl.pythonPath`).
- **No required pip packages.** The server is stdlib-only (`python -m puzzle.lsp`). `cspuz` is optional and only used for semantic (T2) diagnostics on `impls/` files that have a matching JSON spec and sample.
- Open the **repository root** (the folder that contains `puzzle/dsl/`) as the VS Code workspace.

## Install

```
cd editors/vscode
npm install
npx vsce package
```

Then in VS Code: **Extensions → … → Install from VSIX** and pick the generated `.vsix`.

For local development, **Run → Start Debugging** from this folder (or `npm run compile` and copy the folder into `.vscode/extensions`).

## Diagnostics

| Level (`puzzleDsl.diagnostics.level`) | What you get |
|---|---|
| `off` | Nothing |
| `syntax` | Lexer / parser errors on every `.dsl` file (T1) |
| `semantic` (default) | T1, plus compile-time errors on `impls/<key>.dsl` when `impls/<key>.json` **and** `impls/samples/<key>.json` exist (T2) |

`puzzle/lib/*.dsl` has no companion JSON, so it **only ever gets T1**. That is expected.

T2 also needs `cspuz` installed; without it, semantic checks are skipped silently.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `puzzleDsl.enable` | `true` | Start the language server |
| `puzzleDsl.pythonPath` | `""` | Interpreter; empty tries `python3` then `python` |
| `puzzleDsl.diagnostics.level` | `semantic` | `off` / `syntax` / `semantic` |
| `puzzleDsl.trace.server` | `off` | LSP trace in the **Puzzle DSL** output channel |

If Python is missing, TextMate highlighting still works; a popup points you at `puzzleDsl.pythonPath`.
