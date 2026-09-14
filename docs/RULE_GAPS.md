# 规则实现缺口（2026-09-14）

对照 `rules.txt`（236 条）和 `impls/`（130 个 `.dsl`）。
`IMPLEMENTATION_STATUS.md` 写于 2026-08-13，当时只有约 89 个实现、147 个未做；
不要再引用那份「D 类 147」数字。

本轮补了 30 条能用现有 DSL **完整编码**的规则（`python gen_easy.py`），
每条都通过 `verify.py` 的编译 / 样例 SAT / 提示非空洞检查。

## 总览

| | 条数 | 说明 |
|---|---:|---|
| 目录 | 236 | `rules.txt` |
| 已有 `impls/` | 130 | 能编译、样例可 SAT |
| 完全未做 | 106 | 无 DSL |
| 部分实现 | 35 | JSON `notes` 写了「部分实现」或 `unencodedClues` |

按分类（已实现 / 目录）：

| 分类 | 已有 | 目录 | 未做 |
|---|---:|---:|---:|
| 涂黑 I | 31 | 31 | 0 |
| 涂黑 II | 34 | 34 | 0 |
| 涂黑 III | 14 | 14 | 0 |
| 放置 | 7 | 16 | 9 |
| 填写 | 18 | 37 | 19 |
| 分区 | 12 | 33 | 21 |
| 回路 I | 5 | 27 | 22 |
| 回路 II | 8 | 21 | 13 |
| 路径 I | 0 | 15 | 15 |
| 路径 II | 1 | 8 | 7 |

涂黑家族文件最齐，但不少是合法松弛：真解仍 SAT，多解/非唯一。
分区在 fillomino / shikaku / araf 之外补了正方形/骨牌/榻榻米等 `type: cc` 题。
路径类仍几乎空白（只有 Hidato 这种「填数当路径」）。

## 本轮新补（30，全完整）

- 涂黑 II: `binairo`
- 放置: `gaps` `magnets`
- 填写: `simplegako` `bosanowa` `fuzuli` `doppelblock` `easyasabc` `skyscrapers` `kropki` `kropki-pairs` `cojun` `hanare` `makaro`
- 分区: `fourcells` `fivecells` `meadows` `squarejam` `tatamibari` `domino-search` `lapaz` `symmarea` `wafusuma`
- 回路 I: `midloop` `geradeweg` `balance`
- 回路 II: `yajilin-regions` `koburin` `nuriloop`
- 路径 II: `hidato`

库函数随之加了 `subset_latin`、`outside_visible`、`used_arm_len`、`regions_are_squares`、`region_180_symmetric` 等。

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
8. **「气」、轴对称、直线 polyomino。** go 的气、hinge 轴对称、wittgen/nuribou 必须成直线。
   （区域 180° 对称已在 `symmarea` 用质心配对编码，轴对称仍缺。）

下一步对规则覆盖帮助最大的仍是 **形状同构**、**区域内的 cc_count** 和 **单路径**。

## 完全未做（106）

- 放置 (9): `pentatouch kissing pentopia dosufuwa statuepark pencils tren kinkonkan moonlight`
- 填写 (19): `gokigen blind renban goishi kakuro r roma toichika japanesesums wagiri yajirushi tateyoko arrowflow scrabble consecutiveq snail magic hebi ubahn`
- 分区 (21): `pentominous tetrominous cbblock heteromino slashpack subomino kramma tentaisho sashigane mirrorbk bdblock nikoji dbchoco sendai lohkous narrow snakepit compass aho voxas heavydots`
- 回路 I (22): `myopia swslither lineofsight nanameguri waterwalk dotchi castle firewalk disloop icewalk orbital wbloop reflect slalom dotchi2 kouchoku crossstitch moonsun bhaibahan tapaloop angleloop nagare`
- 路径 I (15): `wblink numlin walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly icebarn herugolf`
- 回路 II (13): `alternate ringring pipelink maxi trainstations barns vertigo nothing mukkonn doubleornothing railpool nagenawa kurarin`
- 路径 II (7): `haisu rassi keywest mintonette curvedata icelom anglers`

建议顺序：路径（先封装单路径 / Hashi 桥）→ 冰面回路与交叉回路 → 形状同构后再回头收 35 条部分实现。
