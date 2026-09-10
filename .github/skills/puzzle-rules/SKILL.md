---
name: puzzle-rules
description: 'Look up grid-puzzle rules by name (中文/English/pzplus key) or identify a puzzle from a rule description, and implement new rules end-to-end — cspuz-backed solver in the puzzle DSL plus the front-end editor/solution layers. Use whenever the user mentions a logic-puzzle name (数独/数墙/Nurikabe/Masyu/…), asks what a rule means, asks to add or fix a solver under impls/, or asks for a custom/new puzzle rule.'
---

# Puzzle rules: identify, implement, render

This repository solves ~236 grid-puzzle rules (catalogued in `rules.txt`) with a
constraint DSL lowered through cspuz, and renders them with a puzzle-agnostic layer
front-end. **Always start with the `puzzle-rules` tool** — never grep
`rules.txt` by hand and never guess a rule's wording.

All commands run from the repository root and accept `--json`.

## 1. Name ⇄ rule

```bash
python -m tools.puzzle_rules find 数墙            # name (any language) -> rule
python -m tools.puzzle_rules find nurikabe
python -m tools.puzzle_rules identify "涂黑格互不相邻且留白连通"   # rule text -> candidates
python -m tools.puzzle_rules show nurikabe        # rule + spec + variables + layers + DSL
python -m tools.puzzle_rules list --category 回路I
python -m tools.puzzle_rules categories           # coverage per category
python -m tools.puzzle_rules todo                 # rules with no solver yet
```

`find` matches key / English / Chinese and falls back to rule text; `identify`
ranks by shared rule wording, so a paraphrase still resolves. A leading `✓`
means a solver already exists.

## 2. Architecture in one screen

| Path | Role |
| --- | --- |
| `rules.txt` | The rule catalogue (tab separated, 8 columns). Source of truth for names. |
| `puzzle/models.py`, `puzzle/grid.py` | Board geometry: `cell (r,c)`, `corner (r,c)`, `edge ("H"\|"V", r, c)`. |
| `puzzle/dsl/` | Lexer → parser → compiler → cspuz multi-backend solver. Grammar in `puzzle/dsl/GRAMMAR.md`. |
| `puzzle/lib/*.dsl` | Shared templates: `core`, `shading`, `regions`, `loops`, `fill`, `outside`. |
| `puzzle/elements.py` | The generic drawing elements (number/shade/circle/arrow/link/…). |
| `puzzle/spec.py` | `PuzzleSpec` (variables + layers) and `Instance` (board data). |
| `puzzle/runner.py`, `puzzle/server.py` | Solve one instance; JSON HTTP API. |
| `impls/<key>.json` + `<key>.dsl` | One rule: spec + constraints. |
| `impls/samples/<key>.json` | Sample instance used as the regression test. |
| `web/src/` | React + Vite front-end; renders **layers**, never puzzles. |

Edge convention: `("H", r, c)` is the edge **above** cell `(r,c)`; `("V", r, c)`
is the edge **left of** cell `(r,c)`. On the cell lattice an edge stands for the
link between the two cells it separates, so `"H"` is a *vertical* link.

## 3. Implementing a new rule

```bash
python -m tools.puzzle_rules show <key>        # 1. read the exact rule text
python -m tools.puzzle_rules lib               # 2. see which templates already exist
python -m tools.puzzle_rules builtins          #    ... and the DSL builtins
python -m tools.scaffold new <key> --rows 8 --cols 8   # 3. create the three stub files
# 4. edit impls/<key>.json (variables + layers) and impls/<key>.dsl (constraints)
python -m tools.check compile <key>            # 5. fast syntax/shape check
# 6. add a hand-checked board to tools/samples.py, then
python -m tools.samples && python -m tools.check solve <key>
```

### Choosing variables

| Rule shape | Variables |
| --- | --- |
| 涂黑 (shading) | `x` cell normal `domain [0,1]`, 1 = 涂黑 |
| 填数 | `x` cell normal with the value range |
| 提示数字/圆圈/箭头 | a **constant** cell variable per clue kind (`n`, `o`, `d`, …) |
| 分区 (solve a partition) | a `cc` cell variable; use `c.id` / `c.size` / `c.border` |
| 回路 / 路径 | `e` edge normal `domain [0,1]` |
| 已画好的区域 | set `"usesRegions": true`; read them with `regions` / `region_of` |

Auxiliary variables are fine (LITS uses `t` for the tetromino type, Nanro uses a
0/1 `f` "is filled" flag). Mark a constant that must exist on *every* cell with
`"dense": true` (Hitori's printed numbers).

### DSL rules of thumb

* `x[p]` yields a **list**; use `at(x, p)` whenever you need a scalar, because
  `and` between two lists *merges* them instead of conjoining.
* Compile-time values (`region_id`, `row_of`, `has_value`, constants, `.size`)
  are plain Python — `if` over them constant-folds and costs nothing.
* Accumulate with `let total = total + …` inside `for`; `let` rebinds the
  nearest enclosing binding, so accumulators survive loop iterations.
* Connectivity: `cc_count(x, v) <= 1` (one group), `cc_id` / `cc_size` /
  `cc_root`, and the `cc8_*` diagonal variants.
* Loops: `loop(e)` on the corner lattice (Slitherlink), `cloop(e)` through cell
  centres (Masyu); then `on_loop`, `turns`, `goes_straight`, `cdeg`,
  `region_crossings`.
* Outside clues live in `params`: `param("top")[c]`; use the `outside` lib’s
  `row_count` / `col_runs` etc. — they tolerate missing/short lists (−1 = 无提示).
* `import "shading"` etc. pulls in a template module; `def` helpers are hoisted,
  so order does not matter.

### Verify before claiming success

`python -m tools.check compile` must stay at 45/45 (or higher) and
`python -m tools.check solve` at 25/25 (or higher). A sample that solves proves
the encoding is *satisfiable*; also eyeball the printed board against the rule.

## 4. Front-end: layers, not puzzles

A puzzle spec lists **layers**; each layer binds a generic element to a variable:

```json
{ "id": "clue", "label": "岛屿数字", "element": "number",
  "target": "cell", "role": "input", "var": "n" }
```

* `element` — one of `python -m tools.puzzle_rules elements`
  (`number`, `text`, `shade`, `circle`, `square`, `triangle`, `star`, `cross`,
  `dot`, `arrow`, `edgeline`, `link`, `diagonal`, `region`, `outside`, plus the
  special pictures `tree`, `tent`, `ship`, `wave`, `bulb`).
* `target` — `cell` / `corner` / `edge` / `outside`.
* `role` — `input` (part of the statement, editable) or `output` (the solution).
* `palette` maps integer values to colours, so the same element serves many rules.
* Layers toggle independently in the UI, which is how the board is inspected
  layer by layer.

**Never add puzzle-specific code to `web/src`.** To support a new rule, reuse an
existing element; only if a genuinely new visual primitive is needed, add it to
`puzzle/elements.py`, draw it in `web/src/glyphs.tsx` (`glyph()`), and — if it
is not a per-point marker — give it a case in `web/src/render.tsx` and an
editor kind in `web/src/editors.ts` (`EDITOR_OF` / `cycleValues`). Cell-marker
glyphs get board+palette support automatically.

Run the stack with:

```bash
python -m puzzle.server --port 8000     # JSON API (+ web/dist when built)
cd web && npm install && npm run dev    # Vite dev server, proxies /api
```

## 5. Custom rules the user invents

Same flow, with two shortcuts:

* Pick a `key` that is not in `rules.txt`; `tools.scaffold new` warns but works,
  and the spec's own `en` / `zh` / `rule` fields carry the description.
* The API accepts `{"instance": …, "source": "<dsl>"}`, so a rule can be tried
  from the UI without touching `impls/` — copy it into `impls/<key>.dsl` once it
  works.
