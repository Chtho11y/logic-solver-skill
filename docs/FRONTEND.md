# 前端布局

对照 [Penpa+](https://github.com/swaroopg92/penpa-edit)（MIT：Opt-Pan / Swaroop Guggilam，见仓库根目录 `NOTICE` 与 `web/public/penpa-edit/`）。

```
顶栏（题型 / 尺寸 / 后端 / 样例 / 导入 / 求解）
┌──────────┬──────────────────────────┬──────────────┐
│ 图层     │  Penpa+ 原版编辑器       │ 规则 DSL     │
│ 仅列出   │  （Mode / Sub / Style /  │              │
│ 盘上有值 │   棋盘，vendored iframe）│              │
│ 的变量   │                          │              │
└──────────┴──────────────────────────┴──────────────┘
```

- **左侧**：VS Code 资源管理器那样的一行一层。层 = 一个求解变量（或尚未绑定的绘制工具）。只显示盘面上已经有元素的层；眼睛切换显隐，点击切到对应 Penpa 模式。
- **中间**：vendored Penpa+（`web/public/penpa-edit/`）。画布是 Penpa 的 canvas，不是自家 SVG。样例 / 导入把图层 stamp 到 `create_newboard()` 建出的棋盘上（不走会清空内线的 URL `load()`）。求解时用 `pu.maketext()` 导出 URL，走 `/api/import` 绑定 DSL。
- **右侧**：`GET /api/puzzles/<key>` 的 `source`。求解把当前文本作为 `source` 交给 `/api/solve`。

未选择题型也可以画；导入 Penpa+ / puzz.link 解码后 stamp 到画布。换题型不清空盘面。点「样例」才用该题 sample 覆盖。`/api/encode` 仍可用于把图层编成 Penpa URL，前端加载盘面不再经过它。
