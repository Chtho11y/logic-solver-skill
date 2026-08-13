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

## 4. D. 尚未实现

| 分类 | 条数 | keys |
|---|---:|---|
| 放置 | 8 | `pentatouch kissing pentopia statuepark pencils tren kinkonkan moonlight` |
| 填写 | 30 | `bosanowa gokigen simplegako blind fuzuli doppelblock renban goishi kakuro easyasabc hanare r roma toichika japanesesums wagiri makaro yajirushi cojun tateyoko arrowflow scrabble kropki-pairs skyscrapers consecutiveq snail magic kropki hebi ubahn` |
| 分区 | 15 | `pentominous tetrominous cbblock heteromino slashpack symmarea subomino mirrorbk nikoji dbchoco sendai lohkous narrow voxas heavydots` |
| 回路I | 15 | `lineofsight waterwalk firewalk disloop icewalk orbital wbloop reflect slalom kouchoku crossstitch bhaibahan tapaloop angleloop nagare` |
| 路径I | 14 | `wblink walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly icebarn herugolf` |
| 回路II | 9 | `ringring pipelink maxi trainstations barns vertigo doubleornothing railpool nagenawa` |
| 路径II | 7 | `haisu rassi keywest mintonette curvedata icelom anglers` |

涂黑II 的 `binairo`、涂黑III 11 条、回路I 中较易的 10 条已实现（见第 8 节）。

### 4.1 暂缓（过难，仅标注）

这些规则需要非正交几何、沿回路走访、自交/多回路或给定形状目录，当前库没有合适原语；硬编码容易写错，故本轮不做。

| key | 难点 |
|---|---|
| `lineofsight` | 最近回路**线段长度**（非整段距离） |
| `waterwalk` / `firewalk` / `icewalk` | 沿回路的颜色段长；火格可走两次；冰格可自交 |
| `disloop` | 前方 N 段长度的**无序**多重集匹配 |
| `orbital` / `ringring` / `nagenawa` | 多条矩形回路且允许交叉 |
| `wbloop` / `bhaibahan` | 沿回路在相邻圆圈之间计转弯 |
| `reflect` / `pipelink` | 指定格自交 |
| `slalom` / `nagare` | 有向回路 + 关卡次序 / 风向 |
| `kouchoku` / `angleloop` / `crossstitch` | 非正交线段、夹角、双顶点回路 |
| `tapaloop` | 八邻域多段无序（同 tapa） |
| `maxi` | 区域内单次经过的最长段（多次进出） |
| `trainstations` | 仅十字格自交；按数字顺序走访且数字格不转弯 |
| `barns` | 冰格自交且不转弯；粗线墙 |
| `vertigo` | 任意自交 + 全程同向转弯 |
| `doubleornothing` | 双回路；加号格交叉或都不经过 |
| `railpool` | 区域内直线段长度的无序集合 |
| `pentatouch` / `kissing` / `pentopia` / `statuepark` | 给定多连块目录 + 旋转翻转放置 |
| `pencils` / `tren` / `kinkonkan` / `moonlight` | 复合放置（笔迹、滑动车、镜面反射、星云照明） |
| `hashi` | 岛屿间 1/2 桥、禁止交叉、全图连通；无“互相看见的岛屿”原语 |
| `pentominous` / `tetrominous` / `heteromino` / `subomino` | 多连块形状目录 / 平移全等 / 一形能否放入另一形 |
| `slashpack` | 格内对角线把盘面剖成区域 |
| `symmarea` | 码牌 + 每区 180° 对称但中心未知（需枚举格心/边心/顶点） |
| `mirrorbk` | 镜子轴对称的两区 |
| `cbblock` | 每区两个虚线块、非矩形、邻区不全等 |
| `nikoji` | 同字母区域平移全等（含字母相对位置） |
| `dbchoco` | 灰白两块相邻且全等 |
| `sendai` | 市内再分且与同形同向市相邻 |
| `lohkous` | 区域内横纵段长的无序集合 |
| `narrow` | 非矩形 + 同符号不同形 + 禁止同符 2×2 |
| `voxas` | 面积 2/3 的矩形 + 区界圆点表示面积/朝向关系 |
| `heavydots` | 顶点伸出 3/4 条界，且与已标点相邻的未标点有额外禁止 |

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

- 部分实现的条目**不具备唯一解**，作为出题器会有多解；作为解题器不会漏解。
- `verify.py` 只验证"样例可满足"，**尚未**验证"解唯一"或"已知真题得到已知解"。

---

## 7. 后续建议顺序

1. **填写 30 条** —— 先补摩天楼可见性、Kakuro 和式、Kropki。
2. **路径I** 其余条目（`hashi` 见 §4.1；滑动/反射类更难）。
3. **分区** 剩余形状目录 / 镜像 / 全等（见 §4.1）。
4. **放置** 中带形状目录的（`pentatouch` 等）等全等原语后再做。

---

## 8. 本轮补全（涂黑III + binairo + 回路I 易项）

测试已改为 `tests/cases/*.json` 的盘面+答案；`unique` 默认关闭，只做 **accept**（钉入答案仍 SAT）。

### 8.1 涂黑III（11 条，此前一轮）

完整：`batten tawa cocktail martini stostone interbd`  
部分（全等未编码）：`mrtile ququ chainedb kuroclone evolmino`

### 8.2 本轮新实现

| key | 分类 | 机制 |
|---|---|---|
| `binairo` | 涂黑II | 无三连 + 行列各半 + 行列图案互异 + 圈色 |
| `myopia` | 回路I | 数回 + 箭头=最近回路边方向（位掩码 `a`） |
| `swslither` | 回路I | 数回 + `inside_flag` 羊内狼外 |
| `midloop` | 回路I | 直穿黑点且两臂等长 |
| `geradeweg` | 回路I | 过圈；直线段长=数字 |
| `dotchi` | 回路I | 过白圈不过黑圈；区内白圈全直或全弯 |
| `dotchi2` | 回路I | 每区择一色走遍；黑弯白直 |
| `balance` | 回路I | 白圈两臂等长、黑圈不等；数字=两臂和 |
| `nanameguri` | 回路I | 每区一次；对角线格不穿过对角 |
| `moonsun` | 回路I | 每区一次；区内日月二择；跨区切换 |
| `castle` | 回路I | 提示格不在回路上；白内黑外；箭头方向回路格数 |

### 8.3 库追加

- `loops.dsl`：`nearest_loop_dist` / `arm_used_len` / `full_straight_len`
- `shading.dsl`：`half_filled_lines` / `lines_all_unique`
- `drop_covers`（垒石刚体下落；与全等无关）

### 8.4 回路II 易项 + Hidato

完整：`yajilin-regions` `koburin` `nuriloop` `nothing` `kurarin` `mukkonn` `hidato`  
部分：`alternate`（仅回路边直接相连的圆圈异色；沿回路隔格的连续同色圆圈未编码）

| key | 机制 |
|---|---|
| `yajilin-regions` | `loop_visits_all_but` + `no_adjacent` + `region_black_count` |
| `koburin` | 数字格不涂黑、不在回路上；其余格回路 xor 涂黑；`n_adj4` |
| `nuriloop` | `cloop`；辅助 `y`=不在回路上（声明于 variables、不进 layers）；岛大小同数墙 |
| `nothing` | 区域全经过或全不经过；进出 0 或 2；未经过区域不相邻 |
| `kurarin` | 留白单回路（连通 + 每格恰 2 个留白邻 + `cc_count==1`）；格点 `c` 1/2/3 用 `cell_of` 多数。不用 `cycle_shape`（`no2x2` 会禁掉合法 4 循环）。角键 `"1,1"` 表示顶点 (r,c) |
| `mukkonn` | 每格至多一个三角形；`link_dir => arm_len == n` |
| `hidato` | 填 1..N 各一次（N=`rows.size * cols.size`）；`distinct(x)`；相邻数字八邻域 |
| `alternate` | `link_between(e,p,q)==1 =>` 圆圈异色（非“所有正交相邻圆圈异色”） |

暂缓（自交 / 多矩形回路 / 无序段长 / 有向转弯）：`ringring` `pipelink` `maxi` `trainstations` `barns` `vertigo` `doubleornothing` `railpool` `nagenawa`。

### 8.5 放置易项

完整：`magnets` `gaps` `dosufuwa`

| key | 机制 |
|---|---|
| `magnets` | 骨牌区域空或一对 `+/-`；正交相邻不能同号；left/top=正号数，right/bottom=负号数 |
| `gaps` | 每行每列两星；八邻不相接；盘外数字=两星之间空格数（不含星本身） |
| `dosufuwa` | 每区一气球(1)一铅球(2)；铅球在盘底/黑格上/铅球上；气球在盘顶/黑格下/气球下 |

暂缓：带多连块目录或复合机关的放置（见 §4.1）。

### 8.6 路径I：数连

完整：`numlin` — 端点 `cdeg==1` 且 `x=n`；其余格要么不经过（x=0, 度 0）要么度 2；邻接边推出同号；`cc_count(x, n)==1`。盘外边强制为 0。

`hashi` 暂缓（见 §4.1）。

### 8.7 分区易项

完整：`fourcells` `fivecells` `meadows` `squarejam` `tatamibari` `tentaisho` `kramma` `aho` `domino-search` `lapaz` `compass` `sashigane` `snakepit` `wafusuma` `bdblock`

| key | 机制 |
|---|---|
| `fourcells` / `fivecells` | `all_regions_size` + `c.border` 四边计数 |
| `meadows` | 正方形 + 每区一黑圈 |
| `squarejam` | 正方形 + 禁止四区共顶点 + 数字=边长 |
| `tatamibari` | 长方形 + 每区一符号 + 禁止四区共顶点；`s` 1=宽>高 2=高>宽 3=正方形 |
| `tentaisho` | 每区一圆点；绕该格心 180°。圆点只写在格子中心 |
| `kramma` | 贯通横竖切割；每区至少一圈且同色 |
| `aho` | 每区一数字=面积；`size%3==0` 则恰一个 2×2 缺一角（L），否则长方形 |
| `domino-search` | 全区骨牌；`param("tiles")` 的每个无序数对恰出现一次 |
| `lapaz` | 黑不相邻；白格骨牌；横向数字=该行黑数，竖向=该列黑数 |
| `compass` | 每区一叉；`nu/nd/nl/nr` = 区内严格更上/下/左/右的格数 |
| `sashigane` | 宽 1、恰两端点、恰一转弯；圈在转弯、箭在端点指向转弯 |
| `snakepit` | 码牌邻区面积不同 + 蛇（宽 1、≥2 格、恰两端、无 2×2）；圈=端、灰≠端 |
| `wafusuma` | 邻区面积不同；格线数字=两侧面积和且必须跨区 |
| `bdblock` | 同数字同区、异数字异区、每区至少一数字；黑点顶点恰 3 条界且全部给出 |

库追加（`regions.dsl`）：`region_width` / `region_height` / `regions_are_squares` / `no_four_meet` / `region_border_clue` / `region_deg` / `same_reg_dir` / `region_notch_count` / `region_end_count` / `region_above` 等方向计数。

暂缓：形状目录、镜像、两色巧克力全等、斜线剖分等（见 §4.1）。
