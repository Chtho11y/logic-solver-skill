# 规则实现缺口（2026-09-14）

对照 `rules.txt`（236 条）和 `impls/`（100 个 `.dsl`）。
`IMPLEMENTATION_STATUS.md` 写于 2026-08-13，当时只有约 89 个实现、147 个未做；
涂黑 III 等后来已经补了文件，不要再引用那份「D 类 147」数字。

P3（`graph_division`）只换了 `cc_size` / `groups_of_size` / CC `.size` 的编码，
**不会**补上下面这些规则缺口。

## 总览

| | 条数 | 说明 |
|---|---:|---|
| 目录 | 236 | `rules.txt` |
| 已有 `impls/` | 100 | 能编译、样例可 SAT |
| 完全未做 | 136 | 无 DSL |
| 部分实现 | 35 | JSON `notes` 写了「部分实现」或 `unencodedClues` |

按分类（已实现 / 目录）：

| 分类 | 已有 | 目录 | 未做 |
|---|---:|---:|---:|
| 涂黑 I | 31 | 31 | 0 |
| 涂黑 II | 33 | 34 | 1（`binairo`） |
| 涂黑 III | 14 | 14 | 0 |
| 放置 | 5 | 16 | 11 |
| 填写 | 7 | 37 | 30 |
| 分区 | 3 | 33 | 30 |
| 回路 I | 2 | 27 | 25 |
| 回路 II | 5 | 21 | 16 |
| 路径 I | 0 | 15 | 15 |
| 路径 II | 0 | 8 | 8 |

涂黑家族文件最齐，但不少是合法松弛：真解仍 SAT，多解/非唯一。
分区几乎只有 `fillomino` / `shikaku` / `araf`（`type: cc`）。
路径类全部空白。

## 编码层缺口（已有题也写不出的约束）

这些反复出现在 35 条部分实现的 `notes` 里，也挡住大量未做题：

1. **多连块全等 / 克隆。** tetrochain、kuroclone、mrtile、ququ、lits 相邻全等、evolmino 平移。
   需要把每个连通组的形状归一化后比较，而不是只比面积。
2. **按区域的连通组计数。** disco「每区恰好两组」、nuritwin「每区恰好两组且等面积」、
   oneroom「区内留白连通」。现在的 `cc_count` 只能全盘统计。
3. **无序段长 / 通配提示。** coral 无序 runs、cts 的 `?` `*`、tapa 环形八段。
   `runs()` 只支持有序精确列表。
4. **最大矩形 / 最大区内白组。** teri、akichi、tasquare 的「长=宽」。
5. **路径唯一性。** guidearrow、nurimaze 的 S–G 唯一路径；路径类题本身还没有
   `active_edges_single_path` 的 DSL 封装（cspuz 在 Z3 上也没有展开）。
6. **三角形朝向 / 菱形放置。** shakashaka、diamond：0/1 涂黑不够。
7. **两级区域。** parquet 粗线+细线。
8. **「气」、对称、直线 polyomino。** go 的气、hinge 轴对称、wittgen/nuribou 必须成直线。

P0–P3 已经把连通、回路、岛/墙、分量大小接到图原语；下一步对规则覆盖帮助最大的是
**形状同构** 和 **区域内的 cc_count**，而不是再切一条图算子。

## 完全未做（136）

- 涂黑 II (1): `binairo`
- 放置 (11): `pentatouch kissing magnets gaps pentopia dosufuwa statuepark pencils tren kinkonkan moonlight`
- 填写 (30): `bosanowa gokigen simplegako blind fuzuli doppelblock renban goishi kakuro easyasabc hanare r roma toichika japanesesums wagiri makaro yajirushi cojun tateyoko arrowflow scrabble kropki-pairs skyscrapers consecutiveq snail magic kropki hebi ubahn`
- 分区 (30): `meadows fivecells fourcells pentominous tetrominous domino-search squarejam cbblock heteromino slashpack symmarea subomino wafusuma kramma tentaisho sashigane mirrorbk bdblock nikoji dbchoco sendai lohkous lapaz tatamibari narrow snakepit compass aho voxas heavydots`
- 回路 I (25): `myopia swslither midloop geradeweg lineofsight nanameguri waterwalk dotchi castle firewalk disloop icewalk orbital wbloop reflect slalom dotchi2 kouchoku balance crossstitch moonsun bhaibahan tapaloop angleloop nagare`
- 路径 I (15): `wblink numlin walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly icebarn herugolf`
- 回路 II (16): `alternate ringring yajilin-regions koburin pipelink maxi nuriloop trainstations barns vertigo nothing mukkonn doubleornothing railpool nagenawa kurarin`
- 路径 II (8): `haisu rassi hidato keywest mintonette curvedata icelom anglers`

建议顺序：回路（库里 `loop`/`cloop` 已可用）→ 分区（套 `type: cc` + `.size`/`.border`）→
填写（先补摩天楼/和式）→ 路径（先封装单路径）→ 形状同构后再回头收 35 条部分实现。
