# 谜题规则实现状态报告

生成时间：2026-08-13　　目录总数：**236** 条（`rules.txt`）

> 本报告数据由脚本从 `rules.txt` + `impls/*.json` 直接统计，非人工记录。

---

## 1. 总览

| 分组 | 条数 | 占比 | 说明 |
|---|---:|---:|---|
| **A. 本次完全实现** | **12** | 5% | 规则的全部决定性约束均已编码 |
| **B. 本次部分实现** | **31** | 13% | 约束为真解的**合法松弛**，不排除任何正确答案 |
| **C. 原有实现（基线）** | 46 | 19% | 本次任务之前已存在，**未在本次审计范围内** |
| **D. 尚未实现** | **147** | 62% | 无 `impls/` 文件 |
| 合计 | 236 | 100% | |

本次会话产出 **43** 条（A+B），全部通过三重验证：编译、样例可满足、**线索非空洞**。

### 关于上一轮的纠正

上一轮我曾声称"190 条全部补全"，那是**过度宣称**：当时的 `compile`+`solve` 只证明"能编译且空盘可满足"，未校验与规则的一致性；复审发现 137 条存在**错误编码**（写了真解不满足的约束）。该批产物已按你的要求 `git clean` 全部回滚，当前 43 条是重做结果。

---

## 2. A. 完全实现（12 条）

| key | 中文名 | 分类 | 已编码的关键机制 |
|---|---|---|---|
| `nothree` | 等隔无三 | 涂黑I | island_rule + 圆圈恰触1黑 + **同行列等距三连黑禁止**（全间距枚举） |
| `sumiwake` | 圆角房间 | 涂黑I | island_rule + 留白段跨区限制 + 白圈触1黑/黑圈触2黑 |
| `usoone` | 单一谎言 | 涂黑I | island_rule + 邻黑计数 + **每区域恰好一个错误数字** |
| `yajikazu` | 真假仙人 | 涂黑I | island_rule + **提示仅在其格留白时生效**（涂黑则失效） |
| `ayeheya` | 对称数间 | 涂黑I | island_rule + 跨区限制 + 区域黑数 + **区域180°旋转对称** |
| `bosnianroad` | 波斯尼亚路 | 涂黑II | **闭环**（每黑格恰2黑邻+连通+无2x2）+ 八邻计数 + 数字格留白 |
| `sansaroad` | 三叉路口 | 涂黑II | 留白连通 + 无全白2x2 + **三叉度3/其余度2** + 点提示 |
| `snake` | 数蛇 | 涂黑II | **蛇形**（连通/宽1/恰2端点）+ 端点·蛇身圆圈 + 盘外行列计数 |
| `dominion` | 多米诺分区 | 涂黑II | **骨牌配对且互不相邻** + 字母格留白 + 同字母同区/异字母异区 |
| `norinuri` | 海苔墙 | 涂黑II | 骨牌涂黑 + **每留白组恰一数字**（组数=数字数）+ 组格数 |
| `isowatari` | 渡池石块 | 涂黑II | **每黑组恰 N 格** + 留白连通 + 无全白2x2 + 圆圈颜色 |
| `aquarium` | 水族馆 | 涂黑II | **区域内水往下沉 + 同区同行水位相同**（水面平）+ 盘外计数 |

> 少数条目带解释性附注（如 `bosnianroad` 的"环不与自身对角接触"由无 2x2 部分保证），已写入各自 `notes`。

---

## 3. B. 部分实现（31 条）

约束均为真解的**合法松弛**：可作为正确起点，但当前不足以唯一确定解。`unencoded` 列出"已声明可录入、但尚未参与约束"的线索变量（已在 JSON 的 `unencodedClues` 中标记，验证器据此豁免）。

### 涂黑I（13 条）

| key | 中文名 | 已编码 | 未编码（缺口） |
|---|---|---|---|
| `disco` | disco | 涂黑连通+无2x2+每区≥2黑 | 每区域**恰好两组**连通 |
| `parquet` | 拼花地板 | 涂黑连通且**无环（树）** | 粗线/细线**两级区域**模型缺失 |
| `teri` | 矩形领土 | island_rule + 白圈留白 | 含此格的**最大留白矩形面积** |
| `akichi` | 数间(空地) | island_rule + 跨区限制 | 区域内**最大**留白连通组面积（`n`） |
| `nuritwin` | 涂黑成对 | 涂黑连通+无2x2+区黑数为偶且=2×数字 | 恰两组、两组**等面积且不相邻** |
| `guidearrow` | 指引箭头 | 黑不相邻 + 留白**无环（树）** | 箭头指向星星的**唯一路径方向**（`d,s`） |
| `oasis` | 绿洲 | island_rule+无全白2x2+白圈留白 | 沿留白**可达白圈计数** |
| `sashikabe` | 曲尺数墙 | 涂黑连通+无2x2+留白宽度为一 | **恰L形**（仅一次转弯）、圆圈/箭头定位（`n,d`） |
| `oneroom` | 单房门 | island_rule+区黑数+**相邻区至多一门** | 每区域**内部**留白连通 |
| `cts` | 过河 | 涂黑连通+无2x2+盘外**有序段长** | `?` / `*` 通配提示 |
| `coral` | 珊瑚 | 涂黑连通+无2x2+**留白连通到边界** | 盘外**无序**段长集合匹配 |
| `tapa` | 土派艺术 | 涂黑连通+无2x2+提示格留白 | **环形八邻域多段长度**（无序、含?） |
| `nurimaze` | 迷宫地图 | 无单色2x2+区域单色+留白**树** | 圆圈/三角相对 S–G 唯一路径的位置（`m`） |

### 涂黑II（18 条）

| key | 中文名 | 已编码 | 未编码（缺口） |
|---|---|---|---|
| `hinge` | 合页 | 区域黑格数 | 每黑组跨一条区界且**沿其轴对称** |
| `snakeegg` | 蛇蛋 | 蛇形 + 端点圆圈 + 留白组格数 | 盘外留白组格数**多重集一一对应** |
| `shakashaka` | 摇啊摇 | 黑格数字=相邻被涂格数 | **三角形四朝向**变量 + 含对角矩形判定 |
| `circlesquare` | 方圆 | 涂黑连通+无2x2+圆圈+留白组为**矩形** | 矩形须为**正方形**（长=宽） |
| `tetrochain` | 四格骨牌链(指) | 每黑组恰4格+对角连通+方向计数 | 对角相邻骨牌**不全等** |
| `tetrochaink` | 四格骨牌链(暗) | 每黑组恰4格+对角连通+点提示 | 对角相邻骨牌**不全等** |
| `go` | 围棋 | 圆圈颜色固定 | **「气」**=连通组相邻异色格去重计数（`n`） |
| `diamond` | 钻石链 | 涂黑对角连通 | **◇菱形**（2x2斜正方形）放置模型（`w,n`） |
| `wittgen` | 三格长桌 | 每黑组恰3格且宽1+邻接计数+留白连通 | 三格须**成直线**（排除 L 形） |
| `nuribou` | 数壁 | 黑组宽1+无2x2+每留白组恰一数字+组格数 | 黑组**成直线**、相接触黑组**面积不同** |
| `cornerch` | cornerch | 留白对角连通+数字格留白+组面积 | 偶面积**必为**矩形 / 奇面积**必不为**矩形 |
| `tasquare` | 正方放置 | 黑组为矩形+留白连通+提示格邻黑 | 长=宽、**相邻正方形面积之和** |
| `antmill` | 蚂蚁怪圈 | 骨牌配对+互不正交邻+对角连通 | 每骨牌**恰与两块接触**（成环）、□/× 提示 |
| `mochinyoro` | 藕断丝弯 | 无2x2+留白对角连通+留白组矩形+组格数 | 任意黑组**都不是**矩形 |
| `scrin` | 方形回路 | 涂色组矩形+对角连通+圆圈在色内+组面积 | 每矩形**恰与两块接触**（成环） |
| `lookair` | 观云 | 黑组为矩形+含自身五格计数 | 长=宽、同行列**视线内无全等正方形** |
| `clouds` | 云团 | 黑组矩形+每黑格≥2黑邻+盘外计数 | 云团**互不接触**、圆角/× 预给提示 |
| `shugaku` | 修学旅行 | 涂黑连通+无2x2+留白成床骨牌+每床邻黑 | **枕头**变量、枕头计数、竖床不朝北（`n`） |

---

## 4. D. 尚未实现（147 条）

| 分类 | 条数 | keys |
|---|---:|---|
| 涂黑II | 1 | `binairo` |
| 涂黑III | 11 | `batten mrtile ququ kuroclone cocktail tawa stostone evolmino interbd chainedb martini` |
| 放置 | 11 | `pentatouch kissing magnets gaps pentopia dosufuwa statuepark pencils tren kinkonkan moonlight` |
| 填写 | 30 | `bosanowa gokigen simplegako blind fuzuli doppelblock renban goishi kakuro easyasabc hanare r roma toichika japanesesums wagiri makaro yajirushi cojun tateyoko arrowflow scrabble kropki-pairs skyscrapers consecutiveq snail magic kropki hebi ubahn` |
| 分区 | 30 | `meadows fivecells fourcells pentominous tetrominous domino-search squarejam cbblock heteromino slashpack symmarea subomino wafusuma kramma tentaisho sashigane mirrorbk bdblock nikoji dbchoco sendai lohkous lapaz tatamibari narrow snakepit compass aho voxas heavydots` |
| 回路I | 25 | `myopia swslither midloop geradeweg lineofsight nanameguri waterwalk dotchi castle firewalk disloop icewalk orbital wbloop reflect slalom dotchi2 kouchoku balance crossstitch moonsun bhaibahan tapaloop angleloop nagare` |
| 路径I | 15 | `wblink numlin walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly icebarn herugolf` |
| 回路II | 16 | `alternate ringring yajilin-regions koburin pipelink maxi nuriloop trainstations barns vertigo nothing mukkonn doubleornothing railpool nagenawa kurarin` |
| 路径II | 8 | `haisu rassi hidato keywest mintonette curvedata icelom anglers` |

---

## 5. C. 原有实现（基线 46 条，未审计）

```
akari aqre aquapelago araf battleship box canal cave cbanana chocona context
country creek detour doubleback fillomino heyawake hitori kurodoko kurotto
lightshadow lits masyu meander mines mochikoro nanro nonogram norinori nurikabe
nurimisaki paintarea putteria ripple shikaku shimaguni simpleloop slither
starbattle sudoku suguru sukoro tents tilepaint yajilin yinyang
```

抽样阅读过的 `nurikabe / hitori / slither / sudoku / fillomino / masyu / akari / starbattle / yajilin / kurodoko / context / shikaku` 编码忠实；其余未逐条核对，故不做质量断言。

---

## 6. 本次的工程改动

**新增库函数**（`puzzle/lib/shading.dsl`，纯追加，不影响原有 46 条）：

| 函数 | 用途 |
|---|---|
| `color_count` / `color_adjacent_pairs` | 同色格数、同色相邻对数 |
| `color_is_tree` | 连通且无环（\|V\|−\|E\|=1），同时排除 2x2 |
| `color_is_acyclic` | 无环但不强制连通 |
| `width_one` | 宽度为一（同色邻居 ≤2） |
| `snake_shape` / `cycle_shape` | 蛇（恰2端点）/ 闭环（每格度2） |
| `all_dominoes` | 同色格两两成 1x2 且不同骨牌互不相邻 |
| `groups_of_size` | 每个同色连通组恰 k 格 |
| `group_size_clue` / `group8_size_clue` | 数字=所在连通组格数（4/8 连通） |
| `majority_dot_clue` | 点提示四邻黑白多寡 |

**流程改进**（针对上一轮失误的根因）：

1. **元数据强制取自 `rules.txt`** —— `en/zh/rule/category/subcategory` 不再由我撰写，杜绝上一轮"仙人指路→趋势"这类捏造。
2. **非空洞（bite）测试** —— 逐个给常量线索赋值，断言约束数**必须增长**；这正是能抓出上一轮 `region_visited_cells(e, n)` 死语句的检查。
3. **样例带真实线索且手工核验** —— `nurimaze`（留白梳齿）、`cts`（十字）、`aquarium`（水位阶梯）、`sansaroad`（外框+竖弦）的解均已渲染并逐格对照，不再依赖空盘 sat。
4. **`unencodedClues` 显式声明** —— 部分实现的缺口写进 JSON，而非隐藏在注释里。

### 已知遗留问题

- 部分实现的 31 条**不具备唯一解**，作为出题器会有多解；作为解题器不会漏解。
- `verify.py` 只验证"样例可满足"，**尚未**验证"解唯一"或"已知真题得到已知解"。补齐 147 条前建议先加真题回归集。

---

## 7. 后续建议顺序

1. **回路/路径 64 条**（回路I+II、路径I+II）—— 库中 `loops.dsl` 最完备（`cloop`/`deg`/`seg_len`/`region_crossings` 齐全），单位成本最低。
2. **分区 30 条** —— 依赖 CC 变量的 `.size`/`.border`，`shikaku`/`fillomino` 已有可直接套用的范式。
3. **填写 30 条** —— 需先补 `outside.dsl` 的可见性（摩天楼）、和式（kakuro/日本和）辅助。
4. **涂黑III 11 条 + 放置 11 条** —— 多数需要"形状全等/克隆"判定，建议先在库中实现通用的**多连块同构比较**再动手。
