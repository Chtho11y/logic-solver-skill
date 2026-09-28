# 规则能力缺口

覆盖数字、部分实现和未实现名单统一见 [自动状态报告](../IMPLEMENTATION_STATUS.md)。
这里维护能力层面的待办，具体规则遗漏以 `impls/<key>.json` 的 notes / unencodedClues 为准。

“存在实现”“样例 SAT”“完整符合原规则”是不同验收层次。先补真实题、非法解反例和第二解检查，
再扩大覆盖范围，避免将合法松弛当作完整求解器。

## 共用能力优先级

1. **多连块全等与克隆**：tetrochain、kuroclone、mrtile、ququ、lits、evolmino。
   面积相等不足以证明形状相同，需要明确旋转、反射和平移的允许方式。
2. **区域内部的连通组统计**：disco、nuritwin、oneroom。
   库中已有 one / at_most_one / two_black_groups_per_region，但会禁止跨区域黑格相邻，
   不能直接用于允许跨界连接、只统计区域内部组数的题型。
3. **单路径与路径上的提示**：路径类题、guidearrow 和 nurimaze；
   区分普通连通、树、闭环、单路径及指定端点路径。
4. **无序段长和通配提示**：coral、cts、tapa；现有有序 runs 不能直接代替无序或环形匹配。
5. **最大面积、形状与接触关系**：teri、akichi、tasquare、scrin、antmill、lookair。
   最大矩形、正方形、块间接触次数等应分别建立反例。
6. **专用几何模型**：shakashaka 的三角朝向、diamond 的菱形、parquet 的两级区域，
   以及 go 的气、hinge 的轴对称、wittgen / nuribou 的直线限制。

## 验收与工具限制

- `tools.check compile` 使用合成盘面；全格数字要在 VarSpec 声明 dense。
- `tools.check solve` 只测试已有随附样例，不能覆盖没有样例的实现。
- `verify.py` 的 bite 比较约束数量，且可能同时添加伴随线索。这只是启发式检查，
  不证明每个线索独立有效，更不证明规则完整。partial 标识参考元数据，其余只称 sample-checked。
- 答案比对可以发现回归，但求出一次预期答案不证明唯一；仍需排除已知答案后再次求解。
- 修改生成器管理的实现时同步修改 gen*.py；覆盖统计由 tools.status 重新生成。
