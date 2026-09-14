# 前端布局与已知问题

对照 [penpa-edit](https://github.com/swaroopg92/penpa-edit)：左侧工具画题面，中间棋盘，右侧编辑规则。

## 已对齐的部分

```
顶栏（题型 / 尺寸 / 后端 / 样例 / 求解）
┌──────────┬─────────────────┬──────────────────┐
│ 图层轨道 │     棋盘 SVG    │  规则 DSL 文本   │
│ 画笔     │                 │  重置 / 行号     │
└──────────┴─────────────────┴──────────────────┘
规则说明
```

- 左侧竖向图层列表 + 当前图层画笔，对应 penpa 的 Surface / Number / Line 工具条。
- 中间只放棋盘，不再用 `max-width: 92vw` 占满整页。
- 右侧载入 `GET /api/puzzles/<key>` 返回的 `source`。求解会把当前文本作为 `source` 交给 `/api/solve`。
- 编译错误会用 `errorLine` 跳到对应行。焦点在 textarea 时，盘面快捷键不会抢数字输入。
- 顶栏可粘贴 **Penpa+** 或 **puzz.link** 链接（`POST /api/import`）。Penpa+ 先按 Surface / Number / Symbol / Line / LineE 分层解码，**不依赖题型**；能从 genre 标签、puzz.link pid 或当前选题猜到规则时再绑定到 `impls/`。无题型时前端仍用解码图层预览盘面。puzz.link 经 pzprjs 解成同一套图层。

## 仍然存在的问题（相对 penpa，有意未做）

1. **不是 penpa 的绘制模型。** 图层来自各题 JSON（shade / number / arrow / edgeline…），没有 Surface 子模式、符号表、边框墙、cage、复合描画。Penpa 导入是「解码再绑定」，不是在编辑器里复刻 Penpa 工具。
2. **没有撤销 / 平移缩放 / 网格样式。** 棋盘是固定 viewBox 的 SVG。
3. **没有 URL 导出。** 可以导入 Penpa+ / puzz.link，还不能把当前盘面再编码回去。
4. **题型选择仍是一个 130 项的 `<select>`。** penpa 用新盘 + 题型面板。
5. **DSL 编辑器是 textarea，不是 Monaco。** 没有语法高亮、补全；仓库已有 LSP，但 Web 未接上。
6. **求解结果不会写回 DSL。** 输出图层画在棋盘上；规则文本只在你改它时参与求解。
7. **改 DSL 不会改图层。** 编辑器改约束，不能增删变量或画笔。新题仍要写 `impls/*.json`。
8. **窄屏只是简单折行。** 没有 penpa 那种移动端工具抽屉。

这些缺口不影响「左画题、右写规则」这条主路径。下一步若继续贴近 penpa，优先撤销栈，而不是先上 Monaco。
