# 前端与数据契约

新增变量、绘制类型或可复现交付时阅读。当前画布是真正的 Penpa+，不是自绘 React 棋盘。

## 三个文件形成一个前端预设

| 文件 | 内容 |
| --- | --- |
| `impls/<key>.json` | `key/en/zh/rule`、默认尺寸、`variables`、`layers`、`usesRegions`、参数默认值及缺口说明 |
| `impls/<key>.dsl` | 可调用规则函数及主调用；约束只表达规则，不放某一道题的数据 |
| `impls/samples/<key>.json` | `puzzle/rows/cols/clues/regions/params/title`；非空的可操作样例 |

`/api/puzzles` 扫描实现文件。通常不需要维护注册表、修改 React 或向题规目录加一行。
没有常量线索的题型也应给出有意义的区域、尺寸或待解条件，说明样例是否多解。

## 变量不是 Penpa 的工具模式

| 数据 | spec 配置 |
| --- | --- |
| 黑白待解格 | `kind: cell, type: normal, domain: [0,1]` |
| 整数填数 | `kind: cell, type: normal, domain: [下界,上界]` |
| 已给数字/符号 | `type: constant`，每种独立含义各用一个变量；全盘都有值的常量可标记 `dense: true` |
| 待解分区 | `kind: cell, type: cc`；region 输出绑定该变量 |
| 格线或格间连线 | `kind: edge, type: normal, domain: [0,1]` |
| 预先给定房间 | `usesRegions: true`，region 输入绑定 `__regions`；实例 `regions` 填满全部格子 |

变量名用合法标识符，不占用 `__` 开头的框架名字。辅助变量不需要输出图层。
多个变量可以使用相同绘制工具、占据同一个格子；各自拥有文档和历史。“绘制到”决定新笔画归属。

每个 layer 用唯一 `id`，以 `var` 绑定变量。例如：

```json
{"id":"clue_n","label":"相邻黑格数","element":"number","target":"cell","role":"input","var":"n","options":{"min":0,"max":4}}
```

`role: input` 是题目输入，`role: output` 是求解显示，不是 Penpa Problem/Solution 模式的同义词。
导入预设时 `editableSpec` 会为输出增加同类输入绑定，因此用户可以给待解变量画已知值；一般无需手工重复添加。
`options.min/max` 是编辑提示，不能代替待解变量的 `domain` 或 DSL 中的合法性约束。

常用配对：`number → cell`、`shade → cell`、`link → edge`、`edgeline → edge`、`region → cell`。
`H,r,c` 是格子上边，`V,r,c` 是左边；`link` 中 H 对应上下格的竖向连接，V 对应左右格的横向连接。
不要把 link 输出当成 edgeline 回填。

多数字线索的 number layer 设置 `options.mode: "list"`，常量值使用整数列表；`-1` 为问号。
当前这条格内列表输入通路面向 Tapa：最多四项、单项 0..8、0 单独使用。不要将其误当作任意整数数组编辑器。
盘外提示使用 `target: outside` 和 `options.sides/mode`，绑定结果是 `params.top/bottom/left/right`；不要假定 `layer.param` 会创建任意参数名。
标量可调参数放 `params.defaults`；现有参数控件主要展示数字，数组等通过样例和绘制绑定传递。

## 求解 API 的两条路径

持久化预设已在 `impls/` 时：

```json
{"instance":{"puzzle":"room-shade","rows":2,"cols":3,"clues":{},"regions":{},"params":{"k":1}},"backend":"z3","timeoutMs":10000}
```

临时规则、不落入注册目录时，必须同时提供完整定义：

```text
{
  spec: <完整 spec 对象>,
  source: <DSL 字符串>,
  instance: <实例对象，puzzle 与 spec.key 一致>,
  backend: "z3",
  timeoutMs: 10000
}
```

后一个块是结构说明，不是可直接提交的 JSON。不要只提交未知 `puzzle` 与 `source`：缺少 spec 时后端仍会尝试读取磁盘上的题型。

前端还有 `documents: [{id: "n", url: "<Penpa URL>"}, ...]`：

- 每个变量独立一份，区域为 `__regions`，盘外为 `__outside`，尺寸必须相同。
- **只要带 `documents`，后端就会清空 instance 的 clues/regions 并从文档重建。** 不要一半线索放 instance、一半放 documents；`documents: []` 也不会保留原线索。
- 浏览器当前就走这条路径，所以直接调用 `solve_instance` 无法证明 Penpa 绑定正确。
- 后端会拒绝未绑定笔画及明确不支持的绘制。原生工具能画不代表该元素已能参与求解。

## 缺少绘制能力时查哪里

按“输入或输出在哪一步丢失”定位，不重建画布：

| 路径 | 责任 |
| --- | --- |
| `puzzle/importing/penpa.py` / `puzzlink.py` | 解码原生图形与链接 |
| `puzzle/importing/board.py` | 通用标记中间表示与导出层 |
| `puzzle/importing/bind.py` | 按 layer 绑定线索与参数 |
| `web/src/bind.ts`、`drawing.ts` | 样例/通用层与前端数据转换 |
| `web/public/penpa-edit/studio-bridge.js` | 变量文档、选中/显隐、原生笔画、答案叠加 |
| `web/src/PenpaPane.tsx` | Penpa 桥接与 portal 宿主 |
| `web/src/App.tsx`、`VariablePanel.tsx`、`DslEditor.tsx` | 工作区编排、变量总览及规则编辑器 |
| `puzzle/elements.py` | 元素目录；列在目录里不代表完整输入/输出链路均支持 |

修改通用元素要核对解码、绑定、样例装载、答案回填，而不是只让一个图标显示。
保留左侧变量总览、中间 Penpa、右侧 DSL。清空、求解、导入等继续在 Penpa 原生工具区，绘制目标继续水平排列。
除非用户要求布局变更，不添加新的题型操作侧栏。

## 保存和交付边界

导入预设会替换工作区，不是叠加规则。显隐只影响显示，不取消约束。求解答案是叠加层，不能覆盖手工答案和撤销历史。
原生分享 URL 仅携带当前变量及手工答案，不含完整 spec、全部变量、DSL 或自动求解结果；目前没有完整工作区保存/加载入口。
因此交付至少保留 spec、DSL 和样例；用户要求“一个链接恢复所有内容”时，这是待实现能力，不能以原生 Share 链接冒充。
