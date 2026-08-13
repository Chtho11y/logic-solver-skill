# 谜题规则实现状态报告

生成时间：2026-08-13　　目录总数：**236** 条（`rules.txt`）

> 本报告数据由 `rules.txt` + `impls/*.dsl` + `impls/*.json` 的 `notes` / `unencodedClues` 直接统计，非凭记忆。完全/部分以 JSON 为准：含「部分实现」「未编码」「松弛」或非空 `unencodedClues` 记为 B。

---

## 1. 总览

| 分组 | 条数 | 占比 | 说明 |
|---|---:|---:|---|
| **A. 完全实现** | **140** | 59% | 规则的全部决定性约束均已编码（不含基线） |
| **B. 部分实现** | **48** | 20% | 约束为真解的**合法松弛**，不排除任何正确答案 |
| **C. 原有实现（基线）** | 46 | 19% | 本次任务之前已存在，**未在本次审计范围内** |
| **D. 尚未实现** | **2** | 1% | 无 `impls/` 文件：`kouchoku`、`angleloop` |
| 合计 | 236 | 100% | |

累计产出 **188** 条（A+B）。`impls/*.dsl` 共 234 个，与 `rules.txt` 236 键相减，缺口仅为上述 2 条。

### 关于上一轮的纠正

上一轮我曾声称「190 条全部补全」，那是**过度宣称**：当时的 `compile`+`solve` 只证明「能编译且空盘可满足」，未校验与规则的一致性；复审发现 137 条存在**错误编码**（写了真解不满足的约束）。该批产物已按你的要求 `git clean` 全部回滚。其后各轮按「合法松弛、宁缺毋错」重做；本文件是剩余规则全部处理完后的终稿。en/zh/rule 仍取自 `rules.txt`，不另撰。

---

## 2. A. 完全实现（140 条）

按分类列出全部完全实现的 key（机制见各自 `impls/*.json` 的 `notes`）。首轮涂黑 12 条的机制表保留在文末历史节，此处不重复。

| 分类 | 条数 | keys |
|---|---:|---|
| 涂黑I | 11 | `nothree sumiwake usoone yajikazu ayeheya disco akichi nuritwin oneroom coral tapa` |
| 涂黑II | 16 | `bosnianroad dominion snake norinuri isowatari binairo aquarium sansaroad snakeegg circlesquare wittgen nuribou cornerch tasquare mochinyoro lookair` |
| 涂黑III | 6 | `batten cocktail tawa stostone interbd martini` |
| 填写 | 29 | `bosanowa gokigen simplegako blind fuzuli doppelblock renban goishi kakuro easyasabc hanare r roma toichika japanesesums makaro yajirushi cojun tateyoko arrowflow scrabble kropki-pairs skyscrapers consecutiveq snail magic kropki hebi ubahn` |
| 放置 | 5 | `magnets gaps dosufuwa pencils tren` |
| 分区 | 28 | `meadows fivecells fourcells pentominous tetrominous domino-search squarejam cbblock heteromino symmarea subomino wafusuma kramma tentaisho sashigane mirrorbk bdblock nikoji sendai lohkous lapaz tatamibari narrow snakepit compass aho voxas heavydots` |
| 回路I | 14 | `myopia swslither midloop geradeweg lineofsight nanameguri dotchi castle orbital reflect dotchi2 balance moonsun tapaloop` |
| 回路II | 11 | `ringring yajilin-regions koburin pipelink nuriloop barns nothing mukkonn doubleornothing nagenawa kurarin` |
| 路径I | 14 | `wblink numlin walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly herugolf` |
| 路径II | 6 | `haisu rassi hidato keywest mintonette anglers` |

---

## 3. B. 部分实现（48 条）

约束均为真解的**合法松弛**：可作为正确起点，但当前不足以唯一确定解。缺口写在 JSON 的 `notes` / `unencodedClues`。**逐条说明见 §4.1**（含已编码内容与未实现原因）。

| 分类 | 条数 | keys |
|---|---:|---|
| 涂黑I | 7 | `parquet teri guidearrow oasis sashikabe cts nurimaze` |
| 涂黑II | 10 | `hinge shakashaka tetrochain go diamond antmill scrin tetrochaink clouds shugaku` |
| 涂黑III | 5 | `mrtile ququ kuroclone evolmino chainedb` |
| 填写 | 1 | `wagiri` |
| 放置 | 6 | `pentatouch kissing pentopia statuepark kinkonkan moonlight` |
| 分区 | 2 | `slashpack dbchoco` |
| 回路I | 9 | `waterwalk firewalk disloop icewalk wbloop slalom crossstitch bhaibahan nagare` |
| 回路II | 5 | `alternate maxi trainstations vertigo railpool` |
| 路径I | 1 | `icebarn` |
| 路径II | 2 | `curvedata icelom` |

---

## 4. D. 尚未实现（2 条）

无 `impls/<key>.dsl` 的 key **仅有**：

| 分类 | 条数 | keys |
|---|---:|---|
| 回路I | 2 | `kouchoku` `angleloop` |

其余 234 条均有编码文件。曾列在旧稿「尚未实现」里的填写 / 路径 / 放置 / 分区 / 其余回路，本轮均已落入 A 或 B，不再出现在本节。

### 4.1 因困难未实现（逐条）

含全部 **D（跳过）** 与 **B（部分）**。硬编码缺失约束时，若会把合法真解判 UNSAT，本轮一律不写该约束。

#### 尚未编码（D，2）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `kouchoku` | 交直 | 回路I | 无文件 | 线段可非正交，仅垂直才可交叉；同字母须沿回路连续。现有原语只有横竖格心连线。若改成正交哈密顿回路，会排除全部合法斜线解。 |
| `angleloop` | 角度回路 | 回路I | 无文件 | 必须在符号顶点转弯，夹角可为锐/直/钝，线段不必正交。正交格线只能 90°。硬套数回式格线回路会排除锐角、钝角真解。 |

#### 填写（1）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `wagiri` | 斜线(环和切) | 填写 | 每格一条对角线；顶点数字=引出的斜线数 | 「輪/切」要求判定一条斜线是否落在某个圈上。库没有「边是否属于圈」的原语。若把整盘收成单圈或禁止分叉，会排除合法的非环斜线配置。`unencodedClues: ["m"]` |

#### 路径（3）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `icebarn` | 冰宫游弋 | 路径I | IN/OUT；冰格直行或十字自交；白格不自交；冰区必经；箭头沿该轴穿过 | 冰面允许自交时，箭头的**方向感**无法用「该轴有边」表达。强制单向穿过会排除冰上十字折返仍合法穿过箭头的解。 |
| `curvedata` | 曲线数据 | 路径II | 每格属于某图形；每图恰好一个提示 | 提示是禁止旋转/翻转的折线骨架，只允许伸缩各段。没有「指定折线的相似匹配」原语。按格数硬套形状会排除可伸缩的真解；放任自由路径则过宽。 |
| `icelom` | 冰宫巡游 | 路径II | IN→OUT；走遍白格；冰可交叉且不转弯 | 数字须按 1..k **访问顺序**经过。冰面自交时同一格可走两次，单次访问序不够用。用首次访问序号强制顺序会排除「后一次交叉才碰到该数字」的真解。`unencodedClues: ["n"]` |

#### 放置（6）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `statuepark` | 雕像公园 | 放置 | 五格连通块、块间正交不相邻、余白连通、黑/白圈 | 题面给出的是**具体形状目录**（可旋转翻转）。库不能把「给定多连块列表」实例化为放置变量。若只允许某几种固定五格，会排除目录里其它形状的真解。`unencodedClues: ["shapes"]` |
| `pentopia` | 近视五格 | 放置 | 五格块、互不八邻接触、近视箭头 | 同上，目录未编码；当前允许任意五格骨牌。收紧成标准 12 种或某固定子集，会排除目录外/目录内与子集不一致的真解。`unencodedClues: ["shapes"]` |
| `pentatouch` | pentatouch | 放置 | 五格块；仅在标记格点对角相接 | 形状目录未编码。硬写标准五格全集或题面以外的集合，都会排除「目录与全集不同」的真解。`unencodedClues: ["shapes"]` |
| `kissing` | kissing | 放置 | 仅在标记边上正交相接；× 不覆盖 | 形状目录未编码（块大小也不固定为 5）。假定某种骨牌集将排除其它多连块真解。`unencodedClues: ["shapes"]` |
| `kinkonkan` | 金刚镜 | 放置 | 每区恰好一条对角线镜子（m 1=主对角 2=副对角） | 字母光束须配对结束，数字=反射次数，每镜至少用一次。没有「沿镜面反射的射线」原语。若禁止镜子或改成无反射直行，会排除所有合法反射解。unencodedClues: letters, bounces |
| `moonlight` | 星光 | 放置 | 行列星/云个数；行星与 × 不放图 | 「星照亮行星、受照象限变白」是视线+象限着色，现有放置原语没有照明模型。若忽略照明只排个数，题面仍 SAT，但白象限线索完全空转。`unencodedClues: ["light"]` |

#### 分区（2）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `slashpack` | 斜线分区 | 分区 | 格内对角线；共享边上三角形编号一致；每个编号含 1..N 各一次 | 区域须由三角形沿邻边连通成块。当前只对齐了编号，未强制三角形图连通。若再要求「编号相同即四连通格连通」，斜线切开后同号不相连的合法剖分会被误杀。`unencodedClues: ["connectivity"]` |
| `dbchoco` | 双巧克力 | 分区 | 灰白面积相等、各自连通、两色正交相邻、数字=半区面积 | 灰白两块须在旋转/翻转下全等。8 种变换的格对格匹配在 DSL 里过重，且易把「全等」写成「同外接框」而排除旋转全等真解。`unencodedClues: ["congruence"]` |

#### 回路I（9）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `waterwalk` | 水面行者 | 回路I | 单回路；必经数字格；水段沿回路 ≤2；n=1 | n>1 要的是「沿回路的连续白段长度」。没有按走访顺序切颜色段的原语。用正交白连通块面积代替，会把弯出回路的白格算进去，从而排除/误杀真解。 |
| `firewalk` | 烈焰行者 | 回路I | 连通回路；火格必转弯、允许度 4；必经数字；n=1 | 同上，n>1 的沿回路白段长未编码。火格可走两次，更不能用普通连通块长冒充段长。 |
| `icewalk` | 冰宫行者 | 回路I | 冰不转弯可自交；陆地不交叉；必经数字；n=1 | 同上，n>1 白段长未编码。冰上自交时「沿回路下一段白」与格的首次访问不一致。 |
| `disloop` | 乱序回路 | 回路I | 提示格不在回路上；单个数字=前方格的直线段长 | 多个数字是前方 N 段长度的**无序多重集**。有序匹配会排除段长对、但顺序不同的真解。 |
| `wbloop` | 黑白回路 | 回路I | 经过所有圆圈；同一横/竖直线段上的圆圈同色 | 规则比的是沿回路**连续**两圈之间的转弯次数（同色 0 次 / 异色 1 次）。共线同色只是必要条件。用「所有正交相邻圈异色」会排除隔格同色的真解。 |
| `slalom` | 巡行通关 | 回路I | 不经黑格；过圆圈；关卡直行；圈内数字=关卡数 | 回路有向，且黑格箭头给出关卡次序。无向回路无法谈「第 k 个关卡」。强行给边定向又容易把反向走访的真解排除。`unencodedClues: ["d"]` |
| `crossstitch` | 十字绣 | 回路I | 对角线空/单斜/交叉；格点度 0 或 2；交叉不相邻；圆圈/箭头数字 | 必须恰好两条回路（两种顶点各一条）。强制单圈会排除双回路真解；不限制条数则可能出现更多圈。 |
| `bhaibahan` | 同胞回路 | 回路I | 过所有圈；相邻圈一直行一转弯；直行 n=直线段内部格数 | 转弯数字是沿回路的连续转弯段长，仅 n=1 已写。n>1 需要走访序列。用「邻域转弯格数」代替会把非沿回路的弯算进去。 |
| `nagare` | 吹风机回路 | 回路I | 不经黑格；白箭头格沿轴直行；下风格若在回路上则含顺风边 | 「不得逆风、进入风区必须转向顺风至少一格」是有向约束。无向回路写「禁止某向边」会排除反向吹风仍合法的走法。 |

#### 回路II（5）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `alternate` | 交替回路 | 回路II | 被回路边直接相连的圆圈异色 | 规则是沿回路连续经过的两圈异色（中间可隔空格）。只约束边相邻会漏掉隔格同色；改成「所有圆圈两两异色」又排除不相邻同色真解。 |
| `maxi` | 极大回路 | 回路II | 哈密顿回路；进出次数与最长段的鸽笼不等式 | 「最大值必须在某次经过时达到」需要枚举每一次进出。不等式只给上界，不强迫某次等于 n；若改成「整个区域经过格数=n」会排除多次进出的真解。 |
| `trainstations` | 铁轨 | 回路II | 走遍全盘；仅数字格可自交；数字格不转弯 | 须按 1..k 顺序走访车站。哈密顿自交回路上没有可靠的全局访问序变量。按坐标远近或首次访问编号排序会排除绕行真解。 |
| `vertigo` | 晕头转向 | 回路II | 走遍全盘；允许自交 | 沿一个方向走完整圈时，转弯须全左或全右。无向自交回路无法定义「左转」。任意指定一个环定向，会把另一手方向的真解排除一半。 |
| `railpool` | 轨道库 | 回路II | 与区域相交的直线段长度做成不重复集合；`?`（-1）可匹配任意段长 | 有问号时多余不同段长仍可能被接受，未强制问号与剩余段长一一对应。 |

#### 涂黑I（7）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `parquet` | 拼花地板 | 涂黑I | 涂黑连通且无环（树） | 粗线/细线两级区域：每个粗线区须整块涂黑恰好一个细线子区。题面只有一层 `regions`。硬用当前区域当细线，会把粗线边界理解错并排除真解。 |
| `teri` | 矩形领土 | 涂黑I | island_rule；白圈留白 | 「含此格的最大留白矩形面积」要对每个候选矩形取 max。枚举不全会漏更大矩形，枚举时误含黑格会排除真解。 |
| `guidearrow` | 指引箭头 | 涂黑I | 黑不相邻；留白无环（树） | 箭头是到星星的**唯一路径方向**。树只保证唯一路径存在，不约束箭头与该方向一致。若强制箭头四向都通往星，会排除只在一格转向的真解。`unencodedClues: ["d","s"]` |
| `oasis` | 绿洲 | 涂黑I | island_rule、无全白 2×2、白圈留白 | 数字是沿留白可达的白圈个数。没有按颜色的可达计数原语。用曼哈顿距离或整盘白圈数代替会排除被黑格隔开的真解。 |
| `sashikabe` | 曲尺数墙 | 涂黑I | 涂黑连通、无 2×2、留白宽度为一 | 「恰 L 形（只转一次）」以及圈/箭定位未编码。宽 1 允许蛇形多弯。若再禁所有转弯，会排除合法 L；若要求每块恰好一弯却用错端点定义，也会误杀。`unencodedClues: ["n","d"]` |
| `cts` | 过河 | 涂黑I | 涂黑连通、无 2×2、盘外**有序**段长；`?` 为 -1 | 星号 `*`（任意个额外段，含 0 个）未编码。有序 `runs` 中间插入 `*` 不是 leftover-runs 能表达的。 |
| `nurimaze` | 迷宫地图 | 涂黑I | 无单色 2×2、区域单色、留白为树 | 圆圈/三角相对 S–G 唯一路径的位置。树保证唯一路径，但不标记哪些格在路径上。用「圈必为端点」之类硬规则会排除路径中段的圈。`unencodedClues: ["m"]` |

#### 涂黑II（10）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `hinge` | 合页 | 涂黑II | 区域黑格数 | 每黑组须跨一条区界并沿该界轴对称。要先定位跨界再镜像匹配。用「区黑数偶数」代替对称，过宽；用区域自身 180° 对称则排除合页轴不是区域中心的真解。 |
| `shakashaka` | 摇啊摇 | 涂黑II | 黑格数字=相邻被涂格数 | 半格三角形有四朝向，留白须成（含对角的）矩形。0/1 涂黑模型表达不了斜边。把半格当成全黑会排除「只涂一角」的真解。 |
| `tetrochain` | 四格骨牌链(指) | 涂黑II | 每黑组恰 4 格、对角连通、方向计数 | 对角相邻骨牌不能全等。全等要 8 变换。若改成「相邻面积不同」对四格无意义；若只禁平移全等会漏镜像对。 |
| `tetrochaink` | 四格骨牌链(暗) | 涂黑II | 每黑组恰 4 格、对角连通、点提示 | 与 `tetrochain` 相同，对角不全等未编码。 |
| `go` | 围棋 | 涂黑II | 圆圈颜色固定 | 「气」= 与整块相连的异色格去重计数。邻格简单求和会重复计数。`unencodedClues: ["n"]` |
| `diamond` | 钻石链 | 涂黑II | 涂黑对角连通 | ◇ 是占 4 格的斜正方形，与 2×2 方块不同。用正交 2×2 放置会排除真正的菱形解。`unencodedClues: ["w","n"]` |
| `antmill` | 蚂蚁怪圈 | 涂黑II | 骨牌配对、互不正交邻、对角连通 | 「每牌恰与两牌接触成环」以及 □/× 成对提示未编码。改成「对角连通即成环」过宽；改成「恰好两骨牌」又排除多牌环。 |
| `scrin` | 方形回路 | 涂黑II | 涂色组矩形、对角连通、圈在色内、组面积 | 「每矩形恰与两块接触成环」未编码。对角连通不等于度 2 环。强制全部矩形边相邻会排除只在角上相接的真解。 |
| `clouds` | 云团 | 涂黑II | 黑组矩形、每黑格 ≥2 黑邻、云团互不对角接触、盘外计数 | 圆角/× 预给未编码。 |
| `shugaku` | 修学旅行 | 涂黑II | 涂黑连通、无 2×2、留白成床骨牌、每床邻黑 | 「枕头」是床的一格，需额外变量；竖床不能床头朝北。把整床当枕头或禁止所有竖床，都会排除合法床位。`unencodedClues: ["n"]` |

#### 涂黑III（5）

| key | 中文名 | 分类 | 已编码 | 未实现原因 |
|---|---|---|---|---|
| `mrtile` | 复制瓦片 | 涂黑III | 数字=黑组面积；每组须对角贴上另一组 | 对角伙伴须与本组全等。面积相同≠全等。按面积配对会排除/放过形状不同的块。 |
| `ququ` | 区区 | 涂黑III | 留白组恰一数字且面积匹配 | 对角接触的黑组不能全等。没有按组的 8 变换比较。禁对角接触会排除形状不同的合法对角对。 |
| `kuroclone` | 黑块克隆 | 涂黑III | 每区恰两组；提示=邻格黑组面积 | 区内两组须全等。两组等面积仍可能不同形。 |
| `evolmino` | 生长方块 | 涂黑III | 每组恰一箭头格；箭上后组比前组多一格 | 后组须为前组的**平移**加一格。只比大小会允许旋转/翻转变形，其中有些不是合法生长。 |
| `chainedb` | 区块链 | 涂黑III | 每黑组恰一数字（问号不限面积）；对角链 | 同一 8-链内两组不能全等。全等比较缺失。把整条链禁同面积会排除不同形同面积的真解。 |

---

## 5. C. 原有实现（基线 46 条，未审计）

```
akari aqre aquapelago araf battleship box canal cave cbanana chocona context
country creek detour doubleback fillomino heyawake hitori kurodoko kurotto
lightshadow lits masyu meander mines mochikoro nanro nonogram norinori nurikabe
nurimisaki paintarea putteria ripple shikaku shimaguni simpleloop slither
starbattle sudoku suguru sukoro tents tilepaint yajilin yinyang
```

抽样阅读过的 `nurikabe / hitori / slither / sudoku / fillomino / masyu / akari / starbattle / yajilin / kurodoko / context / shikaku` 编码忠实；其余未逐条核对，故不做质量断言。本轮**没有**覆盖这些文件。

---

## 6. 本次的工程改动

**库函数（纯追加，不影响基线 46 条）**

| 文件 | 用途 |
|---|---|
| `puzzle/lib/shading.dsl` | `color_count` / `color_is_tree` / `snake_shape` / `cycle_shape` / `all_dominoes` / `groups_of_size` 等 |
| `puzzle/lib/loops.dsl` | `nearest_loop_dist` / `arm_used_len` / `full_straight_len` |
| `puzzle/lib/regions.dsl` | `region_width` / `regions_are_squares` / `no_four_meet` / `region_border_clue` 等 |
| `puzzle/lib/fill2.dsl` | 填写：`spiral()`、`dir()` 射线序、拉丁方/可见性辅助 |
| `puzzle/lib/paths2.dsl` | 路径：滑动、冰面直行/十字、配对路径 |
| `puzzle/lib/place2.dsl` | 放置/分区：多连块大小、镜像、三角编号 |
| `puzzle/lib/loops2.dsl` | 回路：矩形圈、自交、冰/火格、段长松弛；`around8_bits` / `tapaloop_clue` |
| `puzzle/dsl/builtins.py` | `cc_count_in` / `cc_size_in` / `cc8_*_in`、`cc_width` / `cc_height` / `cc_is_rect`、`runs_set` / `runs_cycle` / `values_set`；`runs` 支持 `?`=-1 |

**流程改进**（针对回滚前那一轮失误的根因）：

1. **元数据强制取自 `rules.txt`** —— `en/zh/rule/category/subcategory` 不再撰写。
2. **非空洞（bite）测试** —— 给常量线索赋值，断言约束数必须增长。
3. **样例带真实线索** —— 不再依赖空盘 sat 作为「实现完成」的证据。
4. **`unencodedClues` 显式声明** —— 部分实现的缺口写进 JSON。

### 已知遗留问题

- 部分实现的条目**不具备唯一解**；作为解题器不会漏解，作为出题器会有多解。
- `verify.py` 只验证「样例可满足」，**尚未**验证「解唯一」或「已知真题得到已知解」。
- 基线 46 条仍未纳入本轮审计。

---

## 7. 后续建议

1. **仅剩的完全跳过（D=2）**：为 `kouchoku` / `angleloop` 增加**非正交几何**（任意方向的点对线段、夹角、垂直才可交叉）。在现有正交格线模型上补约束只会排除真解，不建议硬编。
2. **收紧 B 类部分实现**，按缺口类型而不是按分类：
   - **形状目录**：`statuepark` `pentopia` `pentatouch` `kissing` —— 需要把题面给定的多连块列表变成放置变量。
   - **沿回路段长 / 走访序**：`waterwalk` `firewalk` `icewalk` `bhaibahan` `icelom` `trainstations` `disloop` `maxi` —— 需要回路走访序列，而不是连通块面积。
   - **全等 / 8 变换**：`dbchoco` `mrtile` `ququ` `kuroclone` `evolmino` `chainedb` `tetrochain` `tetrochaink` `nikoji` 已做平移、其余未做旋转翻转。
   - **有向回路**：`slalom` `nagare` `vertigo`。
   - **圈/斜线属于环**：`wagiri`；**双回路条数**：`crossstitch`。
   - **通配线索**：`cts` 的 `*`（有序段中间的任意段数）。`?` 已用 -1 编码。`railpool` 的问号仍是「有问号则允许多余段长」的松弛。
   - **复合机关**：`kinkonkan` 反射光束、`moonlight` 照明象限、`curvedata` 折线伸缩、`shakashaka` 半格三角、`icebarn` 自交时的箭头方向。
3. 基线 46 条若要宣称「全部规则已实现」，仍须按同样标准审计（目前明确未做）。

---

## 8. 本轮补全（填写 / 路径 / 放置+分区 / 回路 remaining）

测试为 `tests/cases/*.json` 的盘面+答案；`unique` 默认关闭，只做 **accept**。本轮处理旧稿 §4 中全部剩余 key：**96 条编码，2 条因非正交几何跳过**。

### 8.1 填写（30/30，无跳过）

完整 29：`bosanowa gokigen simplegako blind fuzuli doppelblock renban goishi kakuro easyasabc hanare r roma toichika japanesesums makaro yajirushi cojun tateyoko arrowflow scrabble kropki-pairs skyscrapers consecutiveq snail magic kropki hebi ubahn`

部分 1：`wagiri`（见 §4.1）

库：`puzzle/lib/fill2.dsl`（含 `spiral()`、`dir()` 射线序）。

### 8.2 路径 I+II remaining（21/21，无跳过）

`numlin` / `hidato` 此前已完成，不计入这 21。

完整 18：`wblink walllogic hashi coffeemilk kaero bonsan sato forestwalk yosenabe rectslider pmemory firefly herugolf haisu rassi keywest mintonette anglers`

部分 3：`icebarn` `curvedata` `icelom`（见 §4.1）

库：`puzzle/lib/paths2.dsl`。

### 8.3 放置+分区 remaining（23/23，无跳过）

完整 15：`pencils tren pentominous tetrominous heteromino cbblock symmarea subomino mirrorbk nikoji sendai lohkous narrow voxas heavydots`

部分 8：`statuepark pentopia pentatouch kissing kinkonkan moonlight slashpack dbchoco`（见 §4.1）

库：`puzzle/lib/place2.dsl`。

### 8.4 回路 I+II remaining（22/24 已编码，2 跳过）

完整 9：`lineofsight orbital reflect ringring pipelink barns doubleornothing nagenawa tapaloop`

部分 13：`waterwalk firewalk disloop icewalk wbloop slalom crossstitch bhaibahan nagare maxi trainstations vertigo railpool`

`railpool` 的直线段长集合与 `?` 通配已编码，但有问号时多余段长仍可能被接受，故记 B 而非 A。

跳过 2：`kouchoku` `angleloop`（见 §4.1）

库：`puzzle/lib/loops2.dsl`。

### 8.5 此前各轮（仍计入 A/B 总数，供对照）

这些不是本轮新写，但属于回滚后的重做产物，已计入 §1。

| 批次 | 完整 | 部分 |
|---|---|---|
| 涂黑 I/II 首轮 | `nothree sumiwake usoone yajikazu ayeheya bosnianroad sansaroad snake dominion norinuri isowatari aquarium` | §3 涂黑 I/II 共 17 条 |
| 涂黑III | `batten tawa cocktail martini stostone interbd` | `mrtile ququ chainedb kuroclone evolmino` |
| 涂黑II + 回路I 易项 | `binairo myopia swslither midloop geradeweg dotchi dotchi2 balance nanameguri moonsun castle` | — |
| 回路II 易项 + Hidato | `yajilin-regions koburin nuriloop nothing kurarin mukkonn hidato` | `alternate` |
| 放置易项 | `magnets gaps dosufuwa` | — |
| 路径I 数连 | `numlin` | — |
| 分区易项 | `fourcells fivecells meadows squarejam tatamibari tentaisho kramma aho domino-search lapaz compass sashigane snakepit wafusuma bdblock` | — |

首轮 12 条完全实现的机制（历史记录，与 JSON notes 一致）：

| key | 中文名 | 分类 | 已编码的关键机制 |
|---|---|---|---|
| `nothree` | 等隔无三 | 涂黑I | island_rule + 圆圈恰触1黑 + **同行列等距三连黑禁止** |
| `sumiwake` | 圆角房间 | 涂黑I | island_rule + 留白段跨区限制 + 白圈触1黑/黑圈触2黑 |
| `usoone` | 单一谎言 | 涂黑I | island_rule + 邻黑计数 + **每区域恰好一个错误数字** |
| `yajikazu` | 真假仙人 | 涂黑I | island_rule + **提示仅在其格留白时生效** |
| `ayeheya` | 对称数间 | 涂黑I | island_rule + 跨区限制 + 区域黑数 + **区域180°旋转对称** |
| `bosnianroad` | 波斯尼亚路 | 涂黑II | **闭环** + 八邻计数 + 数字格留白 |
| `sansaroad` | 三叉路口 | 涂黑II | 留白连通 + 无全白2x2 + **三叉度3/其余度2** |
| `snake` | 数蛇 | 涂黑II | **蛇形** + 端点·蛇身圆圈 + 盘外行列计数 |
| `dominion` | 多米诺分区 | 涂黑II | **骨牌配对且互不相邻** + 字母分区 |
| `norinuri` | 海苔墙 | 涂黑II | 骨牌涂黑 + **每留白组恰一数字** |
| `isowatari` | 渡池石块 | 涂黑II | **每黑组恰 N 格** + 留白连通 + 无全白2x2 |
| `aquarium` | 水族馆 | 涂黑II | **区域内水往下沉 + 同区同行水位相同** |
