# 规则能力缺口

覆盖数字、部分实现和未实现名单统一见 [自动状态报告](../IMPLEMENTATION_STATUS.md)。
这里维护能力层面的待办，具体规则遗漏以 `impls/<key>.json` 的 notes / unencodedClues 为准。

“存在实现”“样例 SAT”“完整符合原规则”是不同验收层次。先补真实题、非法解反例和第二解检查，
再扩大覆盖范围，避免将合法松弛当作完整求解器。

## 共用能力优先级

已补齐 Tapa 的环形数字规则、CircleSquare 的正方形规则和 OneRoom 的区域内白格连通，
并增加合法盘面、非法解反例以及图约束的小盘面穷举测试。它们不再标注部分实现，仍不代表已完成所有题目的验收。
预设列表与工作区展示部分实现状态；求解结果只表示满足当前编码，不自动声明唯一性。

1. **多连块全等与克隆**：tetrochain、kuroclone、mrtile、ququ、evolmino。
   新增 `same_shape`，可控制旋转和镜像；当前使用有限变换枚举，适合小盘面，接入各题型前须评估规模。
   LITS 已有 I/L/S/T 分类及跨区域同形禁邻，应补验证，不应重复列为缺失实现。Evolmino 的增长仍需专门约束。
2. **区域内部的连通组统计**：disco、nuritwin。
   `connected_in` 已用于 OneRoom，只统计指定区域内的路径；精确多组统计仍待补齐。
   库中已有 one / at_most_one / two_black_groups_per_region，但会禁止跨区域黑格相邻，
   不能直接用于允许跨界连接、只统计区域内部组数的题型。
3. **单路径与路径上的提示**：路径类题、guidearrow 和 nurimaze；
   区分普通连通、树、闭环、单路径及指定端点路径。
4. **无序段长和通配提示**：coral、cts。
   `cyclic_runs` 已用于 Tapa，支持多数字、问号和边界补零；`unordered_runs` 提供线性无序匹配。
   当前枚举方法限制 12 个位置，较长盘外线索需要新的计数/自动机编码，不能直接去除 coral、cts 的缺口标记。
5. **最大面积、形状与接触关系**：teri、akichi、tasquare、scrin、antmill、lookair。
   `square_groups` 与 `cc_contacts` 已提供正方形、去重接触组数基础；最大矩形、接触成环等仍需题型级反例。
6. **专用几何模型**：shakashaka 的三角朝向、diamond 的菱形、parquet 的两级区域，
   以及 go 的气、hinge 的轴对称、wittgen / nuribou 的直线限制。

## 验收与工具限制

- 连通、分区大小、不分割和原生单环适配已复用 cspuz 公共图函数，不再维护其算法副本。
- Z3 的 DSL 回路/边连通布尔实现保留：`not cloop(e)` 等需要完整布尔语义，不能用“取反上游约束及辅助变量”代替。
  已有反例测试覆盖此区别。原生算子仍按后端能力选择；本机没有 cspuz_core 时，原生求解测试会跳过。

- `tools.check compile` 使用合成盘面；全格数字要在 VarSpec 声明 dense。
- `tools.check solve` 只测试已有随附样例，不能覆盖没有样例的实现。
- `verify.py` 的 bite 比较约束数量，且可能同时添加伴随线索。这只是启发式检查，
  不证明每个线索独立有效，更不证明规则完整。partial 标识参考元数据，其余只称 sample-checked。
- 答案比对可以发现回归，但求出一次预期答案不证明唯一；仍需排除已知答案后再次求解。
- 修改生成器管理的实现时同步修改 gen*.py；覆盖统计由 tools.status 重新生成。
