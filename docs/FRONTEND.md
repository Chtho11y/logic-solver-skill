# 前端布局

对照 [Penpa+](https://github.com/swaroopg92/penpa-edit)（MIT：Opt-Pan / Swaroop Guggilam，见仓库根目录 `NOTICE`）。

```
顶栏（题型 / 尺寸 / 后端 / 样例 / 导入 / 求解）
┌──────────┬──────────────────────────┬──────────────┐
│ 图层     │  Mode / Sub / Style      │ 规则 DSL     │
│ 仅列出   │  棋盘（Penpa 网格）      │              │
│ 盘上有值 │                          │              │
│ 的变量   │                          │              │
└──────────┴──────────────────────────┴──────────────┘
```

- **左侧**：VS Code 资源管理器那样的一行一层。层 = 一个求解变量（或尚未绑定的绘制工具）。只显示盘面上已经有元素的层；眼睛切换显隐，点击切到对应画笔。
- **中间**：Penpa+ Classic 的 Mode / Sub / Style 工具条 + 黑框网格。Surface 色号仍是 Penpa `1/8/3/4`。没有把 penpa-edit 的整页 jQuery 画布嵌进来（那样无法绑 DSL）；工具排列和标签对齐 Penpa+。
- **右侧**：`GET /api/puzzles/<key>` 的 `source`。求解把当前文本作为 `source` 交给 `/api/solve`。

未选择题型也可以画；导入 Penpa+ / puzz.link 写入通用画布。换题型不清空盘面。点「样例」才用该题 sample 覆盖。
