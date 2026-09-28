# 项目实现状态

由 `python -m tools.status --write` 从目录、元数据及测试案例生成；
`python -m tools.status --check` 检查是否过期。这里统计文件覆盖，不代表完整规则验收。

## 覆盖情况

| 项目 | 数量 | 口径 |
|---|---:|---|
| 规则目录 | 236 | rules.txt |
| 已有实现 | 130 | 同时有 JSON 与 DSL，占 55.1% |
| 尚未实现 | 106 | 目录内缺少实现 |
| 标注部分实现 | 35 | notes 或 unencodedClues 声明缺口 |
| 随附样例 | 109 | 已实现题型中有 sample 的数量 |
| 缺少随附样例 | 21 | 不等同于没有任何测试案例 |
| 答案回归案例 | 34 | 覆盖 33 个题型 |
| 启用答案比对 | 13 | 有答案且没有标记 unique=false |

未标注“部分实现”不等于已证明完整。SAT 只证明满足当前编码；
答案比对也不能替代非法解反例和第二解检查。

## 部分实现

`akichi` `antmill` `circlesquare` `clouds` `coral` `cornerch` `cts` `diamond` `disco` `evolmino` `go` `guidearrow` `hinge` `kuroclone` `lookair` `mochinyoro` `mrtile` `nuribou` `nurimaze` `nuritwin` `oasis` `oneroom` `parquet` `ququ` `sashikabe` `scrin` `shakashaka` `shugaku` `snakeegg` `tapa` `tasquare` `teri` `tetrochain` `tetrochaink` `wittgen`

具体缺口以 `impls/<key>.json` 为准，能力规划见 [规则缺口](docs/RULE_GAPS.md)。

## 缺少随附样例

`aquapelago` `araf` `battleship` `canal` `cbanana` `context` `creek` `kurotto` `lightshadow` `lits` `meander` `mochikoro` `nanro` `nurimisaki` `paintarea` `putteria` `shimaguni` `sukoro` `tents` `tilepaint` `yajilin`

## 尚未实现

`aho` `alternate` `angleloop` `anglers` `arrowflow` `barns` `bdblock` `bhaibahan` `blind` `bonsan` `castle` `cbblock` `coffeemilk` `compass` `consecutiveq` `crossstitch` `curvedata` `dbchoco` `disloop` `dosufuwa` `dotchi` `dotchi2` `doubleornothing` `firefly` `firewalk` `forestwalk` `goishi` `gokigen` `haisu` `hashi` `heavydots` `hebi` `herugolf` `heteromino` `icebarn` `icelom` `icewalk` `japanesesums` `kaero` `kakuro` `keywest` `kinkonkan` `kissing` `kouchoku` `kramma` `kurarin` `lineofsight` `lohkous` `magic` `maxi` `mintonette` `mirrorbk` `moonlight` `moonsun` `mukkonn` `myopia` `nagare` `nagenawa` `nanameguri` `narrow` `nikoji` `nothing` `numlin` `orbital` `pencils` `pentatouch` `pentominous` `pentopia` `pipelink` `pmemory` `r` `railpool` `rassi` `rectslider` `reflect` `renban` `ringring` `roma` `sashigane` `sato` `scrabble` `sendai` `slalom` `slashpack` `snail` `snakepit` `statuepark` `subomino` `swslither` `tapaloop` `tateyoko` `tentaisho` `tetrominous` `toichika` `trainstations` `tren` `ubahn` `vertigo` `voxas` `wagiri` `walllogic` `waterwalk` `wblink` `wbloop` `yajirushi` `yosenabe`

## 已具备的工程能力

- DSL 解析、编译、共享规则库及 cspuz 后端适配。
- Penpa+ / puzz.link 图层导入，原生 Penpa+ 画布与题型绑定。
- 中央棋盘工作区包含题型、尺寸、参数、导入、求解及结果；右侧编辑 DSL。
- VS Code 语法高亮、诊断、悬浮、跳转、补全、签名帮助和引用查找。

## 待办顺序

1. 完善 Penpa 标记与答案映射、保护手工答案、细分图层显隐。
2. 为已有规则补充真实题答案、非法解反例和唯一性检查，补齐缺失样例。
3. 将同步 HTTP 求解迁移为可取消的独立进程任务；当前长任务仍阻塞服务。
4. 统一前后端绑定规则与测试案例，再扩展形状、区域内连通和路径能力。
5. 接入 Web 语言服务，扩充尚未实现的题型。

具体实施顺序及验收标准见 [下一步计划](docs/NEXT_STEPS.md)。
运行与测试入口见 [README](README.md)。测试通过数量应引用实际运行结果，
不要将本表当成测试报告。旧阶段报告可通过 Git 历史查阅。
