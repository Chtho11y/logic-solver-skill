---
name: puzzle-rules
description: >-
  Look up grid-puzzle rules (中文/English/pzplus key), implement a solver in the
  puzzle DSL, compose mixed/custom rules from generic layers + DSL, and export
  the board/answer (SVG/PNG/JSON). Use whenever the user names a logic puzzle,
  asks to add/fix impls/, invents a custom rule, wants a specialized editor
  look, or wants a board/answer screenshot or file dump.
---

# Puzzle rules — fastest path

Speed first. **Do not grep `rules.txt`.** Start with:

```bash
python -m tools.puzzle_rules find <name>          # 中文 / English / key
python -m tools.puzzle_rules identify "规则原文"  # paraphrase → candidates
python -m tools.puzzle_rules show <key>           # rule + spec + layers + DSL
python -m tools.puzzle_rules elements             # drawing primitives
python -m tools.puzzle_rules lib                  # shading/loops/fill/…
python -m tools.puzzle_rules builtins
```

`--json` on every command. A leading `✓` means a solver file already exists.

**Never add puzzle-specific React.** The UI draws **layers**, not puzzle types.
A mixed or custom rule is a new spec (variables + layers) plus a DSL file.

---

## 0. Pick a recipe (do not invent a fourth)

| Goal | Recipe |
| --- | --- |
| Look up / explain a named puzzle | `find` / `show` only |
| New catalogue rule (in `rules.txt`) | **A** clone closest implemented key |
| Mix two existing rules | **B** union of layers + one DSL |
| User-invented rule | **C** custom spec + DSL, reuse elements |
| New picture that no element covers | **D** one generic element, then C |
| Board / answer dump | **E** UI export or JSON pack (no new renderer) |

Coverage and leftover gaps: `IMPLEMENTATION_STATUS.md`. Tests: `tests/cases/<key>.json` (accept-only unless `"unique": true`).

---

## A. Catalogue rule (clone, don’t start from zero)

```bash
python -m tools.puzzle_rules show <closest-key> --json
python -m tools.scaffold new <key> --rows 8 --cols 8   # stubs; en/zh/rule from rules.txt
```

1. Copy **variables + layers** from the closest `impls/<close>.json` (Yajilin-like → `yajilin` / `simpleloop`; shading → `nurikabe`; fill → `sudoku` / `fillomino`; regions → `shikaku` / `country`).
2. Write `impls/<key>.dsl`. `import` a lib; don’t re-derive `loop`/`cc_count`.
3. Small sample via `write_sample` / `impls/samples/<key>.json` (4×4).
4. `python -u -m tools.check compile <key>` then `solve <key> --timeout 120000`.
5. Dump SAT answer into `tests/cases/<key>.json` (`unique` unset; answer = decision vars only).

Circles: **1=white, 2=black**. Directions: UP=0 DOWN=1 LEFT=2 RIGHT=3.
`x[p]` is a list — use `at(x, p)` for a scalar.

---

## B. Mixed rules (two puzzles on one board)

No frontend composer. One spec, many layers.

1. `show` both keys. Union **variables** (rename clashes: `n` vs `n2`). Union **layers** (unique `id`s).
2. One shade / one loop variable if both rules paint the same thing — don’t stack two `shade` output layers on two vars.
3. DSL: `import` both libs, concatenate constraints. Shared cells (e.g. Yajilin black + Nurikabe island) are **one** `x`.
4. Same compile/solve/fixture path as A.

The UI already stacks any layer list. Mixed look = mixed spec.

---

## C. Custom / invented rule (elements + DSL)

Skip `rules.txt`. `tools.scaffold new <key>` still works (warns). Put `en`/`zh`/`rule` on the spec yourself.

**Reuse an existing element.** Check `python -m tools.puzzle_rules elements` before drawing anything.

Layer JSON:

```json
{ "id": "clue", "label": "数字", "element": "number",
  "target": "cell", "role": "input", "var": "n" }
```

`role`: `input` = statement (editable), `output` = solution (filled after SAT).
Unknown `element` ids render as a numbered disc; set `options.cycle` and/or
`options.editor` (`cycle`/`int`/`paint`/`toggle`/`direction`/`text`) so they are editable.

**Try without writing files:** UI footer “DSL” textarea + 求解. API:

```http
POST /api/solve
{ "instance": { "puzzle": "<key>", "rows": 4, "cols": 4, "clues": {}, "regions": {}, "params": {} },
  "spec": { "key": "<key>", "variables": [...], "layers": [...], "source": "import \"shading\"\n..." },
  "source": "..." }
```

`spec` in the body means **no `impls/` file required**. Persist to `impls/<key>.json` + `.dsl` once it SAT-solves.

---

## D. New visual primitive (only if C’s fallback is wrong)

Four files, in this order — still **generic**, never `if (puzzle === …)`:

1. `puzzle/elements.py` — `ElementType` (id, targets, values, editor)
2. `web/src/glyphs.tsx` — `glyph()` case (cell markers)
3. `web/src/editors.ts` — `EDITOR_OF` + `DEFAULT_CYCLE` (if not `options.editor`)
4. `web/src/render.tsx` — only if it is not a per-point marker (shade/region/link/edgeline)

Then C. Do not touch `App.tsx` / `Board.tsx` for a single puzzle.

---

## E. Board export, answer, screenshot

Answers already draw on `role: "output"` layers after 求解 (layer chips tagged **解**; hide with 👁).

In the UI toolbar:

| Button | File |
| --- | --- |
| 导出 SVG | vector of **currently visible** layers (clues + answer if solved) |
| 导出 PNG | same, raster screenshot |
| 导出 JSON | `{ spec, instance, answer, status }` pack |

Hide output layers before export to dump the **empty puzzle**; leave them on for the **solved** picture.

Agent-side pack (no browser):

```text
impls/<key>.json          spec (layers)
impls/<key>.dsl           solver
impls/samples/<key>.json  board
tests/cases/<key>.json    board + answer values
```

`POST /api/solve` → `values` is the answer map (same shape as `clues`).

---

## Verify (do not claim success early)

```bash
python -u -m tools.check compile <key>
python -u -m tools.check solve <key> --timeout 120000
python -m unittest tests.test_solve
```

SAT on a sample means satisfiable, not “matches the rule”. Eyeball the exported PNG against the wording from `show`. Constraints must be a **sound** relaxation (never exclude a true solution). Partial encodings: `notes` + `unencodedClues`.

---

## Architecture (when you need a path)

| Path | Role |
| --- | --- |
| `rules.txt` | Names / wording (8-column catalogue) |
| `puzzle/dsl/` | Lexer → z3. Grammar: `puzzle/dsl/GRAMMAR.md` |
| `puzzle/lib/*.dsl` | Templates (`shading` `loops` `fill` `regions` `outside` + `fill2` `loops2` `paths2` `place2`) |
| `puzzle/elements.py` | Generic drawing elements |
| `impls/<key>.json` `.dsl` | One rule |
| `web/src/` | Layer renderer; puzzle-agnostic |
| `puzzle/server.py` | JSON API (`/api/solve` accepts `spec` + `source`) |

Edge `("H", r, c)` is **above** cell `(r,c)`; `("V", r, c)` is **left**. On the cell lattice that edge is the link between the two cells, so `"H"` is a vertical link.

```bash
python -m puzzle.server --port 8000
cd web && npm install && npm run dev
```
