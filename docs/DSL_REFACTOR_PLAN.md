# Puzzle DSL 重构计划（P1–P6）

目标：在**不破坏现有 234 个 `impls/*.dsl`** 的前提下，消除库与实现中的系统性冗余，并补齐 B 类「部分实现」集中缺失的原语。

本计划基于对 `puzzle/dsl/*.py`、`puzzle/lib/*.dsl`、234 个 `impls/*.dsl` 的实地勘察撰写，所有文件名、行号、函数名、字段名均已核对。

第 7 项（连通性与单回路的编码方式更换 / 求解后端决策）**不在本文件内**，见 `docs/SOLVER_BACKEND_DISCUSSION.md`。

---

## 0. 现状诊断（量化）

| 现象 | 实测数据 | 根因 |
|---|---|---|
| 手写累加器 `let t = t + b2i(...)` | **48 个 impls 文件 106 处 + 8 个库文件 59 处 = 165 处** | 无匿名函数/闭包，谓词无法作为值传入 |
| 手写 `let ok = ok or/and ...` | **29 个文件 57 处** | 同上（`any`/`all` 的手写替代） |
| 越界判空 `shift(...).size == 0` | **16 个文件** | 无「安全取值」原语 |
| 全盘扫描 `for q in cells()` | **21 个 impls 文件 32 处 + 库 24 处** | 区域几何量在 DSL 层手写，未复用 builtins |
| 行/列成对复制 | `outside.dsl` 8 函数 4 对；`fill2.dsl` 6 函数；`ubahn.dsl:19-63` 逐字重复 20 行 | 无「有序线族」抽象 |
| 方向 if 链 | `core.step`、`loops.link_dir`、`paths2.opposite_dir`、`place2.tr_r`/`tr_c`（16 分支） | 有方向常量但无方向代数 |

集中区（重构收益最高的文件）：`crossstitch` 10 处、`pencils` 8、`tateyoko` 8、`ubahn` 8、`railpool` 11（or 累加）、`place2.dsl` 16、`regions.dsl` 13。

### 关键代码事实（决定方案可行性）

| 事实 | 位置 | 影响 |
|---|---|---|
| 变量**无条件**建成 `z3.Int`，即使 `domain == (0,1)` | `compiler.py:151` | P1 的全部依据 |
| `domain` 以 `And(q>=lo, q<=hi)` 注入，不受 guard 影响 | `compiler.py:228-251` | P1 需在此处分叉 |
| 用户函数**已是一等值**（`_eval_name` 返回 `UserFunction`） | `compiler.py:493-494` | P2 只差「匿名 + 闭包」两件事 |
| 调用时整个作用域栈被替换为 `[frame]`，**无闭包** | `compiler.py:327` | P2 的核心障碍 |
| `_build_value_cc` 的 memo key 是 `("valuecc", name, len(deltas))`，与 CC 变量自身的 `_cc_z3[name]` **完全独立** | `builtins.py:756-763` vs `compiler.py:610-648` | P4：对 CC 变量调 `cc_size` 会**重复生成**一套 id/dist 见证 |
| `->` 在全仓库仅出现于 `impls/lits.dsl` 的注释中；`fn` / `where` 未作标识符使用 | 已 grep 确认 | P2 可安全引入 `->` 与 `fn` |
| 内置函数接收 `args` 列表，天然支持可变元数；用户函数 `def` **强制精确元数** | `compiler.py:318-322`、`737` | 带默认值的新 API 必须做成 builtin |
| `verify.py` 的 bite 检查只断言「约束数增长」 | `verify.py:50-76` | 现有回归网**不足以**保护重构，P0 必须先补 |

---

## 1. 总体原则

1. **纯增量**：P1–P4 不改变任何现有 DSL 语法的语义，旧写法继续可用。库函数只新增、不删除；旧函数改为新原语的薄包装（保留名字与签名）。
2. **先建网，再动刀**：P0 建立全量回归基线，之后每个阶段都以「基线 diff」为验收依据。
3. **每阶段独立可交付、可回滚**：阶段之间只有单向依赖（见 §2），任一阶段失败不影响已合并的前序阶段。
4. **迁移与重构分离**：新原语落地（改 `puzzle/`）与 `impls/` 的改写是两个独立提交。前者必须做到「不改 impls 也全绿」。
5. **不为了简洁牺牲正确性**：`IMPLEMENTATION_STATUS.md:23` 记录的「137 条错误编码」教训 —— 任何改写后的规则若无法通过 accept 检查，一律回退为原写法，不做「看起来更对」的猜测。

---

## 2. 阶段依赖与排序

```
P0 回归基线 ──┬─> P1 布尔变量降型        (独立，收益立即可测)
              ├─> P2 匿名函数 + 闭包 ──┬─> P3 安全取值/方向代数/线族
              │                        └─> P4 CC 派生量统一
              └─> P5 回路走访序/定向    (独立于 P2-P4，但建议在 P0 之后)
                                        └─> P6 形状目录 + 全等
```

- P1 与 P2 可并行（触碰文件不重叠：P1 改 `compiler.py` 变量构造与 `builtins.py` 的数值化辅助；P2 改 `lexer/tokens/parser/ast_nodes/compiler` 的作用域）。
- P3、P4 依赖 P2（新库函数要用谓词参数才写得干净）。
- P6 依赖 P5 的「候选枚举」基础设施复用，但不依赖其回路语义，必要时可提前。

**建议顺序：P0 → P1 → P2 → P3 → P4 → P5 → P6。** 理由：P1 收益最大且零语义风险，适合作为「重构机制本身是否可靠」的验证；P2 是 P3/P4 的前提；P5/P6 是功能补齐，风险最高，放最后。

---

## 3. P0 — 回归基线（前置，必做）

### 3.1 问题

现有验证有三层，但都不足以保护重构：

- `verify.py`：compile + sample-sat + bite。bite 只看约束数是否增长，**不看语义**。
- `tests/test_solve.py`：accept（钉答案后仍 SAT）+ match（自由求解复现答案），但 match 要求 case 声明 `"unique": true`，实测该字段普遍未开。
- 无任何性能基线。

重构会改变约束数（P1 会大幅改变），因此**必须先有语义级基线**，否则无法区分「优化生效」与「编码被改坏」。

### 3.2 任务

| 编号 | 任务 | 产物 |
|---|---|---|
| P0-1 | 新增 `tools/baseline.py`：对全部 236 个 key 跑「compile + accept + free-solve」，记录 `{key, 约束数, accept 状态, free-solve 状态, 求解耗时ms, 模型指纹}` | `docs/baseline/<git-sha>.json` |
| P0-2 | 模型指纹定义为：对每个 NORMAL/CC 变量，按 `sort_points` 序拼接取值后取 SHA-256 前 16 位。用于「同一编码在同一 z3 版本下是否产生同一模型」的弱一致性检查 | 同上 |
| P0-3 | 新增 `tools/baseline_diff.py`：比对两份基线，按 `accept 状态翻转` / `约束数变化率` / `耗时变化率` 三个维度出表 | 终端表格 |
| P0-4 | 为 `tests/cases/*.json` 补 `"unique": true`：**仅**对已人工确认唯一解的 case 开启。逐条确认，不批量猜测 | 更新后的 case 文件 |
| P0-5 | 新增「负向检查」：把答案**故意改错一格**后钉入，断言必须 UNSAT。这是唯一能捕获「约束过松」的自动检查 | `tests/test_solve.py` 新增 reject 检查 |

### 3.3 验收

- P0-1 能在单机一次跑完 236 条并落盘（超时 key 单独标记，不阻塞）。
- P0-5 对基线 46 条中抽样的 12 条（`nurikabe / hitori / slither / sudoku / fillomino / masyu / akari / starbattle / yajilin / kurodoko / context / shikaku`）全部生效并通过。

### 3.4 风险

- reject 检查对「部分实现」（B 类 48 条）会**误报**：约束过松是已知且已声明的状态。处置：reject 检查读取 `impls/<key>.json` 的 `unencodedClues`，非空则降级为 warning 而非 failure。

---

## 4. P1 — 布尔变量降型（`z3.Int` → `z3.Bool`）

### 4.1 现状与依据

`compiler.py:151` 对所有非 CONSTANT 变量无条件执行：

```
quantities = {p: z3.Int(f"{var.name}#{_point_label(p)}") for p in order}
```

随后 `compiler.py:243-247` 用 `And(q >= lo, q <= hi)` 注入 domain。对 `domain == (0,1)` 的变量（涂黑家族的核心变量、所有 edge 型回路变量），这意味着：

- 每个格/边多出 2 条算术边界约束；
- 所有 `num_eq` / `b2i` / `count_true` 走 `If(q == v, 1, 0)`（`builtins.py:672-681`），生成整数比较项而非直接的布尔文字；
- z3 在整数理论上求解本可以纯 SAT 解决的问题。

涂黑 I/II/III 共 60 条 + 回路/路径 60 余条的核心变量都是 0/1，覆盖面超过全部规则的一半。

### 4.2 方案

引入**内部表示分叉**，对 DSL 表面语义零影响：

1. 在 `Variable` 上新增派生属性判定 `is_boolean`（`var_type is NORMAL and domain == (0, 1)`）。不改 `models.py` 的 JSON 契约，只加计算属性。
2. `compiler.py` 变量构造分叉：`is_boolean` 时建 `z3.Bool`，否则保持 `z3.Int`。
3. 新增**取值适配层**：`VarValue` 增加 `bool_backed: bool` 字段。所有消费点统一经过两个新函数：
   - `as_int(q)`：布尔量 → `If(q, 1, 0)`；整数量 → 原样。
   - `as_bool(q, v)`：布尔量与 `v` 比较 → `q`（v==1）/ `Not(q)`（v==0）/ `BoolVal(False)`（其他）；整数量 → `q == v`。
4. 改造消费点（清单见 §4.3），使 `at(x,p) == 1`、`num_eq(list, 1)`、`sum(x[reg])` 在布尔量上生成布尔/PB 形式而非整数比较。
5. `_apply_variable_presets`：布尔变量跳过 domain 注入（值域由类型保证），givens 变成 `q` / `Not(q)`。
6. `solver.py` 读模型（`solver.py:123-137`）：布尔量用 `is_true(evaluated)` 转 0/1 回写，保证前端与 JSON 输出格式**完全不变**。

### 4.3 需改造的消费点清单

| 位置 | 现状 | 改后 |
|---|---|---|
| `compiler.py:151` | 无条件 `z3.Int` | 按 `is_boolean` 分叉 |
| `compiler.py:240-251` | domain + givens 注入 | 布尔变量跳过 domain，givens 转布尔 |
| `builtins.py:_fn_num_eq` (672) | `If(item == value, 1, 0)` | 经 `as_bool` 后 `If(b,1,0)` |
| `builtins.py:_fn_sum` (74) | `z3.Sum(items)` | 布尔项经 `as_int` 提升 |
| `builtins.py:_fn_b2i` (657) | `If(value,1,0)` | 布尔量直接 `If`，整数量保持 |
| `builtins.py:_fn_distinct` (81) | `z3.Distinct` | 布尔量报错（Distinct 对 0/1 无意义，且现无此用法） |
| `builtins.py:_build_value_cc` (714) | `var.quantities[n] == xp` | 同值判定改为 `as_same(a, b)`（布尔用 `==` 于 Bool 亦合法，需显式处理） |
| `builtins.py:_seq_run_slots` (1062) | 已按 `item == 1` 归一 | 增加布尔分支 |
| `builtins.py` loop 系列 (1261-1362) | `z3.Sum([var.quantities[e] ...])` | edge 变量降型后必须经 `as_int` |
| `values.py:to_numeric` (69) | 直接返回 quantities | 布尔量在算术上下文自动 `as_int` |
| `solver.py:123-137` | `evaluated.as_long()` | 布尔分支用 `is_true` |

### 4.4 迁移步骤

1. 先只做「适配层 + 全部消费点改造」，但把 `is_boolean` 恒返回 `False`。跑 P0 基线 → 必须**逐字节相同**。这一步证明适配层无副作用。
2. 打开 `is_boolean`，跑基线 diff。预期：约束数下降、accept 全绿、耗时下降。
3. 若某 key 出现 UNSAT 或耗时反而上升，用变量级白名单（按 key 关闭降型）隔离，单独分析。

### 4.5 验收标准

- 步骤 1：基线**完全一致**（约束数、模型指纹逐条相同）。
- 步骤 2：accept 状态**零翻转**；涂黑家族 60 条的约束数中位数下降 ≥ 20%；总求解耗时下降（具体幅度不预设，以实测为准）。
- 前端与 `solve_instance` 的输出 JSON 格式无变化。

### 4.6 风险与回滚

| 风险 | 处置 |
|---|---|
| edge 变量降型后 `deg`/`cdeg` 的 `Sum` 语义改变 | 这是最容易出错的一处；`deg`/`cdeg` 的返回值被大量比较（`== 2`、`== 0`），必须保证 `as_int` 提升后类型仍是整数项。步骤 1 的「逐字节相同」检查覆盖此项 |
| 某些规则依赖「变量可取 domain 外的值再被约束」 | 不存在此用法（domain 是无条件注入的硬约束），但需 grep 确认无 `at(x,p) == 2` 之类对 0/1 变量的越界比较 |
| z3 混合 Bool/Int 后 `QF_FD` 等 logic 预设失效 | `SOLVER_LOGICS` 只是 UI 下拉项，默认 `AUTO`。若某 logic 失效，从预设列表移除即可 |
| 回滚 | `is_boolean` 恒 `False` 即回到步骤 1 状态；适配层本身无害，可长期保留 |

### 4.7 工作量

改动集中在 3 个文件（`compiler.py`、`builtins.py`、`values.py`）加 `solver.py` 一处。无 `impls/` 改动。

---

## 5. P2 — 匿名函数与闭包

### 5.1 现状与依据

用户函数**已经是一等值**：`_eval_name`（`compiler.py:493-494`）会返回 `UserFunction`，`_eval_call`（`compiler.py:719-720`）会调用它。`regions.dsl:29` 的 `cross_region_pairs(f)` 与 `regions.dsl:83` 的 `count_in_region(f, reg)` 已经在用这个能力。

但它用不起来，因为两个缺口：

1. **无匿名函数**：每个谓词都要在文件顶层 `def` 一个具名函数，反而比手写循环更长。
2. **无闭包**：`compiler.py:327` 调用时 `saved_scopes, self._scopes = self._scopes, [frame]` —— 函数体只能看到自己的参数、全局变量/区域/常量/函数。所以谓词无法引用调用点的 `x`、`p`、`reg`，只能把所有依赖都塞进参数表。这就是 `count_in_region(f, reg)` 在全仓库**几乎无人使用**的原因。

### 5.2 语法设计

新增 token `->`（加入 `tokens.py:_TWO_CHAR_OPS`）与关键字 `fn`（加入 `KEYWORDS`）。已 grep 确认：`->` 全仓库仅出现在 `impls/lits.dsl` 的注释里，`fn` 未被用作标识符，两者引入无冲突。

```
lambda_expr := 'fn' '(' [name_list] ')' '->' expr
```

放在 `_primary()` 中（`parser.py:317`），不影响任何现有产生式：`fn` 是关键字，`_primary` 里现有的 `T_KEYWORD` 分支只接受 `true`/`false`，新增一支即可。

新增 AST 节点 `Lambda(params, body_expr)`（`ast_nodes.py`）。

选择 `->` 而非 `:` 的理由：`:` 会与 `if cond: stmt` 的行内套件产生歧义（`if fn(p): ...`）。选择表达式体（而非语句块）的理由：谓词只需返回值，不需要断言约束；这也让 lambda 天然无副作用，避免与 guard 语义（`compiler.py:419-423`）纠缠。

### 5.3 闭包实现

新增 `Closure` 值类型：`Closure(params, body_expr, captured_scopes)`。

- 求值 `Lambda` 时，把**当前 `self._scopes` 的浅拷贝列表**存入 `captured_scopes`。因为 `_set_local`（`compiler.py:340`）会就地改写字典，浅拷贝需逐层 `dict(scope)` 复制，否则会捕获到后续迭代的值。这一点是正确性关键。
- 调用 `Closure` 时：`self._scopes = captured_scopes + [frame]`，而非 `[frame]`。
- 保留 `UserFunction` 的现有行为**完全不变**（仍替换为 `[frame]`），避免 234 个实现的行为漂移。这意味着 `def` 与 `fn` 的作用域规则不同 —— 需在 `GRAMMAR.md` 明确写出。

递归深度沿用 `_call_depth > 64` 的现有上限（`compiler.py:324`）。

### 5.4 配套聚合内置

新增 4 个 builtin（放在 `AGGREGATE_BUILTINS`）：

| 签名 | 语义 | 替代 |
|---|---|---|
| `count_where(iterable, pred)` | `Sum(If(pred(e),1,0))` | 165 处 `let t = t + b2i(...)` |
| `sum_where(iterable, pred, val)` | `Sum(If(pred(e), val(e), 0))` | 加权求和（`outside.weighted_col_sum` 等） |
| `any_where(iterable, pred)` | `Or([pred(e)])` | 57 处 `let ok = ok or ...` |
| `all_where(iterable, pred)` | `And([pred(e)])` | 同上的 `and` 变体 |

`iterable` 接受 RegionValue / list / VarValue（复用 `_iter_items` 的语义）。`pred` 接受 `Closure` 或 `UserFunction`（后者为兼容 `cross_region_pairs` 的既有调用风格）。

由于 builtin 拿到的是**已求值的实参**，而 `pred` 需要在 builtin 内部被反复调用，需给 `ctx` 暴露一个 `ctx.call(callable, args, pos)` 方法（内部转发到 `_call_user_function` / 新的 `_call_closure`）。这是 P2 对 `Compiler` 公开面的唯一新增。

### 5.5 迁移步骤

1. 语法 + 闭包 + 4 个 builtin 落地，**不改任何 `.dsl`**。跑基线 → 必须逐字节相同。
2. 改写 `puzzle/lib/*.dsl` 的 59 处库内累加器。每改一个库函数，跑一次全量基线（库函数被大量共用，影响面广）。
3. 改写 `impls/` 的 106 处。按收益排序：`crossstitch`(10) → `pencils`(8) → `tateyoko`(8) → `ubahn`(8) → `railpool`(11 处 or 累加) → 其余。每文件单独提交，单独跑该 key 的 accept + reject。

### 5.6 验收标准

- 步骤 1：基线逐字节相同。
- 步骤 2/3：每次改写后该 key 的**约束数应当不变或仅有常量级差异**（累加顺序变化可能影响 z3 的 AST 结构但不影响约束条数）。若约束数显著变化，说明语义被改变，必须回退。
- `impls/` 总行数下降（预期 300–500 行量级，以实测为准）。

### 5.7 风险

| 风险 | 处置 |
|---|---|
| 捕获时机错误导致闭包看到循环的最终值 | §5.3 已指出必须逐层 `dict(scope)` 深拷贝一层。必须为此写专门单测：`for` 体内创建的 lambda 在循环后调用，应看到创建时的值 |
| `let` 就地重绑外层作用域（`compiler.py:349-356`）与闭包捕获交互 | 捕获的是拷贝，因此闭包**不会**观察到捕获后的重绑。这与 Python 语义相反，必须在 `GRAMMAR.md` 显式说明并写单测固定行为 |
| 改写累加器时误改语义（如 `or` 短路顺序、`ite` 嵌套顺序） | 严格逐文件提交 + accept/reject 双检查；`nearest_*` 系列（`place2.dsl:342-371`、`loops.dsl:175-189`）依赖**顺序敏感**的 `seen` 状态机，**不属于**可用 `count_where` 替代的模式，明确列入禁改清单 |

### 5.8 禁改清单（顺序敏感，不得用聚合替代）

`shading.see_count`、`loops.seg_len`/`arm_len`/`nearest_loop_dist`、`loops2.nearest_seg_len`、`place2.nearest_eq_dist`/`nearest_nonzero_dist`/`nearest_nonzero_val`/`h_run_len`/`v_run_len`、`fill2.first_nonzero`/`vis_count`/`magic_line_value`/`apply_run_sums`、`regions.span_stops_at_3`。

这些是沿射线的**前缀状态机**（`alive` / `seen` / `mx` / `blocked`），语义依赖迭代顺序，`count_where` 无法表达。它们应保留手写形式，但可在 P3 中通过「有序线族」减少方向重复。

---

## 6. P3 — 安全取值、方向代数、有序线族

依赖 P2。

### 6.1 安全取值

**现状**：`shift(p,dr,dc)` 越界返回空区域（`builtins.py:529-541`），调用方必须 `if q.size == 0` 判空。全仓库 16 个文件在做这件事，库内更是有 5 个同构副本：`shading.nb_bit(65)`、`loops2.nb_on(224)`、`loops.straight_beside(87)`、`regions.same_reg_dir(182)`、`place2.region_sym_shift(271)`。

**新增 builtin**（可变元数，因此必须是 builtin 而非 `def`）：

| 签名 | 语义 |
|---|---|
| `at_or(var, point, default)` | 点在盘内且变量有值 → 该量；否则 → `default` |
| `nb(var, point, d [, default])` | `at_or(var, step(point,d), default)`，`default` 缺省 0 |
| `nb_at(var, point, dr, dc [, default])` | 偏移版本 |
| `in_grid(point [, dr, dc])` | 编译期布尔，替代 `.size == 0` 判空 |

`at_or` 的 `default` 允许是任意值（包括 `false`），因此不能简单复用 `_fn_at`（`builtins.py:1009`，越界时抛 `CompileError`）。

**迁移**：库内 5 个副本改为 `nb` 的包装并保留原名；`impls/` 的判空样板逐文件替换。

### 6.2 方向代数

**现状**：方向常量已存在（`builtins.py:1677-1686`，`UP=0 … DOWN_RIGHT=7`）与 `DIRECTIONS` 偏移表（`builtins.py:361-370`），但没有任何函数把它们暴露给 DSL。于是每处都手写 if 链。

**新增 builtin / 常量**：

| 名称 | 语义 | 替代 |
|---|---|---|
| `dirs4` / `dirs8` | 方向常量列表 | `for d in [UP, DOWN, LEFT, RIGHT]` 的字面量重复 |
| `dr_of(d)` / `dc_of(d)` | 编译期偏移（读 `DIRECTIONS`） | `core.step` 的 4 分支 |
| `opp(d)` | 反向 | `paths2.opposite_dir`（4 分支） |
| `rot90(d, k)` | 顺时针转 90°×k（仅 4 向） | `vertigo` / `nagare` 未来所需 |
| `is_horizontal(d)` / `is_vertical(d)` | 编译期布尔 | `loops2.edge_seg_len` 的分支 |
| `tr(dr, dc, t)` | 8 元二面体变换，返回 `[dr', dc']` | `place2.tr_r` + `tr_c` 的 16 分支 |

`step(p, d)` 已存在于 `core.dsl:107`，改为基于 `dr_of`/`dc_of` 的单行实现，签名不变。

`link_dir`（`loops.dsl:68`）、`edge_seg_len`（`loops2.dsl:85`）改为查表实现，签名不变。

### 6.3 有序线族

**现状**：三类「线」概念并存且互不通用 —— `row(i)`/`col(j)`（`builtins.py:220-237`，排序后的区域）、`dir(p,d)`（`builtins.py:373-389`，**保持射线顺序不排序**）、`spiral()`（`builtins.py:451`，保持螺旋顺序）。因为没有统一抽象，产生了大量成对复制：

- `outside.dsl`：`col_count`/`row_count`、`col_runs`/`row_runs`、`col_runs_set`/`row_runs_set`、`row_index_sum`/`col_index_sum` —— 8 个函数 4 对，每对只差 `rows`↔`cols`。
- `fill2.dsl`：`vis_count`/`vis_count_row_rev`/`vis_count_col_rev` 与 `first_nonzero`/`first_nonzero_row_rev`/`first_nonzero_col_rev` —— 6 个函数 = 2 个 × 3 个遍历方向，且 `reverse_row_cell`/`reverse_col_cell` 是纯坐标翻转辅助。
- `impls/ubahn.dsl:19-63`：行与列两段 20 行逐字相同。
- `impls/tateyoko.dsl:13-35`：`hlen`/`vlen` 同构，各自内部又把左/右抄一遍。

**新增 builtin**：

| 签名 | 语义 |
|---|---|
| `line(axis, i)` | `axis == 0` → `row(i)`；`axis == 1` → `col(i)`。返回**保持遍历顺序**的区域 |
| `lines(axis)` | 该轴的全部线（列表），等价于 `rows` / `cols` |
| `rev(region)` | 逆序的同类区域（不排序）。用于「从另一端看」 |
| `line_from(p, d)` | `= dir(p, d)`，但语义上归入线族，便于统一书写 |
| `side_of(axis, near)` | 返回该轴该端对应的盘外线索边名（`"top"`/`"bottom"`/`"left"`/`"right"`） |

`rev` 是关键：现有 `RegionValue.of` 会强制 `sort_points`（`values.py:48`），因此 `rev` 必须走 `RegionValue(kind=..., points=...)` 直接构造（`dir` / `spiral` 已经这样做）。

**迁移**：
- `outside.dsl` 的 4 对函数合成 4 个 `axis` 参数版，旧名保留为包装（`row_count(x,v,side)` → `line_count(x,v,0,side)`）。
- `fill2.dsl` 的 6 个函数合成 2 个（`vis_count(x, line)` / `first_nonzero(x, line)`），调用方传 `rev(line(...))` 即可，`reverse_row_cell`/`reverse_col_cell` 删除（改为包装保留）。
- `ubahn.dsl` 的两段合并为 `for axis in [0, 1]`。
- `tateyoko.dsl` 的 `hlen`/`vlen` 合成一个 `run_len(x, p, axis)`。

### 6.4 验收标准

- 每个新 builtin 落地后基线逐字节相同（纯新增）。
- 迁移后：`outside.dsl` 与 `fill2.dsl` 行数下降 ≥ 30%；库内 5 个 `nb_*` 副本收敛为 1；方向 if 链在 `puzzle/lib/` 内清零（`place2.tr_r`/`tr_c` 删除）。
- 每个被改写的库函数：所有依赖它的 key 全部 accept 通过（需先建立「库函数 → 依赖 key」的反向索引，可由 `import` 图 + 函数名 grep 生成，作为 P3 的子任务）。

### 6.5 风险

| 风险 | 处置 |
|---|---|
| `rev` 与 `sort_points` 的交互：把 `rev(...)` 的结果传给 `x[region]` 时，`_do_index`（`compiler.py:529`）按 `index.points` 顺序取量，因此顺序会被保留 —— 但若中间经过任何 `RegionValue.of` 就会被重新排序 | 必须为 `rev` 写单测固定「顺序在索引、迭代、`and` 合并三条路径上的行为」。注意 `_merge`（`compiler.py:790`）用的是 `RegionValue.of`，**会破坏顺序** —— 这是必须在文档中警示的陷阱 |
| `outside.dsl` 被基线 46 条大量使用 | `outside` 的改动只做「新增 axis 版 + 旧名包装」，旧名的实现体一行不改，直接转调新版；先验证包装等价再谈删除 |

---

## 7. P4 — CC 派生量统一

依赖 P2。

### 7.1 现状与依据

存在**两套并行且互不复用**的连通分量派生量：

**A 套（Python builtin，作用于普通 cell 变量）**：`cc_id` / `cc_size` / `cc_count` / `cc_root` / `cc_width` / `cc_height` / `cc_is_rect` / `cc_*_in` / `cc8_*`（`builtins.py:771-941`）。

**B 套（DSL 手写，作用于 CC 变量）**：`regions.dsl` 的 `region_width` / `region_height` / `region_deg` / `region_notch_count` / `region_end_count` / `region_above` / `region_below` / `region_left_of` / `region_right_of`，`place2.dsl` 的 `region_bbox_h` / `region_bbox_w` / `region_bbox_corners` / `region_full2x2` / `region_deg_count` —— 共 **14 个函数**，每个都是 `for q in cells()` 全盘扫描。

更严重的是：**对 CC 变量调用 A 套会重复生成一整套连通性见证**。`_build_value_cc` 的 memo key 是 `("valuecc", var.name, len(deltas))`（`builtins.py:758`），而 CC 变量自身的 id/dist 存在 `Compiler._cc_z3[name]`（`compiler.py:648`）。两者完全独立，于是同一个 CC 变量会有两套 `id` + 两套 `dist`，且必须靠约束互相绑定 —— 变量数与约束数双倍。

### 7.2 方案

1. **统一见证来源**：`_build_value_cc` 增加分支 —— 当目标变量是 CC 变量（`ctx` 需暴露 `is_cc_var(name)`）时，直接复用 `Compiler._cc_z3[name]["id"]` 与 `["_dist"]`，不新建。这一步单独提交，可立即消除重复编码。
2. **补齐 CC 成员**：把 B 套的几何量提升为 CC 变量成员或统一 builtin，实现移到 Python（复用已有的 `_ensure_cc_bbox` 折叠链，`builtins.py:884-908`）：

| 新成员/内置 | 替代的 DSL 函数 |
|---|---|
| `c.bbox_w` / `c.bbox_h` | `region_bbox_w` / `region_bbox_h` / `region_width` / `region_height` |
| `c.deg[cell]` | `region_deg` |
| `cc_corner_count(c, cell)` | `region_bbox_corners` |
| `cc_notch_count(c, cell)` | `region_notch_count` |
| `cc_deg_count(c, cell, d)` | `region_deg_count` / `region_end_count` |
| `cc_half_count(c, cell, axis, side)` | `region_above` / `region_below` / `region_left_of` / `region_right_of` |

3. **旧名全部保留为包装**，实现体转调新成员。`regions.dsl` / `place2.dsl` 的手写体删除。

注意 `region_width` / `region_height`（`regions.dsl:140-153`）语义是「同行/同列的同区格数」，在**矩形区域**前提下等于 bbox 宽高，但对非矩形区域**不等价**。迁移时必须逐调用点确认前提（`regions_are_squares` 里有 `regions_are_rectangles` 前置，是安全的；其他调用点需逐一核对）。这是 P4 最容易出错的地方。

### 7.3 验收标准

- 步骤 1（见证复用）：对使用 CC 变量的 key，约束数与辅助变量数**显著下降**，accept 零翻转。这是 P4 的主要收益。
- 步骤 2/3：`place2.dsl` 与 `regions.dsl` 中 `for q in cells()` 的出现次数从 21 降至 0；O(N²) 编码从 DSL 层移入 Python 层（复杂度不变，但可在 Python 内做 memo 与剪枝）。
- `region_width` 的每一个调用点都有书面的「矩形前提成立」记录。

### 7.4 风险

| 风险 | 处置 |
|---|---|
| `region_width` ≠ `bbox_w` 的语义差 | 见 §7.2 末段；无法确认前提的调用点**保留手写版**，不迁移 |
| 见证复用后 `cc_count` 对 CC 变量的语义 | CC 变量的 id 已保证「同 id ⟺ 连通」，`cc_count(c, v)` 会退化为「id 恰为 v 的分量数」，语义与普通变量不同。方案：对 CC 变量**禁用** `cc_count`（编译报错并提示用 `.size`），避免误用 |
| `_cc_z3[name]["_dist"]` 是私有字段 | 提升为正式内部 API 并加注释，否则跨模块依赖私有键 |

---

## 8. P5 — 回路走访序与定向

不依赖 P2–P4，但依赖 P0。这是**功能补齐**阶段，风险高于前四阶段。

### 8.1 目标规则（14 条）

| 缺口 | 规则 |
|---|---|
| 沿回路的连续段长 / 走访序 | `waterwalk` `firewalk` `icewalk` `bhaibahan` `icelom` `trainstations` `disloop` `maxi` `wbloop` `alternate` |
| 有向回路 | `slalom` `nagare` `vertigo` `icebarn` |

这 14 条在 `IMPLEMENTATION_STATUS.md` §4.1 中的「未实现原因」几乎逐字相同：都是「用连通块面积/邻域计数代替沿回路量」或「无向回路无法定义方向」。

### 8.2 关键设计决策：序号放在**弧**上而非格上

`icewalk` / `icelom` / `firewalk` / `trainstations` / `icebarn` 都允许**同一格被走两次**（度 4 的自交）。因此「每格一个访问序号」从根本上不成立 —— `IMPLEMENTATION_STATUS.md` 对这几条的说明正是「首次访问序不够用」。

方案：在**有向弧**上建序。对 `cloop` 的 cell 图（`builtins.py:1238`），每条无向 edge `e` 拆成两条弧，各配一个布尔 `arc[e,→]` / `arc[e,←]`，约束 `arc→ + arc← == e`（P1 之后 `e` 是布尔，需 `as_int`）。

- **度约束转流守恒**：每格「入弧数 == 出弧数」。deg-2 格 → 各 1；deg-4 格 → 各 2。这自动排除了度 4 处「两条线互相掉头」的非法接法（需额外的直行配对约束，见下）。
- **deg-4 的配对**：自交格必须是「上下直行 + 左右直行」两条独立通道，不能是两个拐弯。约束为「入弧与出弧按对轴配对」：从上入必从下出，从左入必从右出。
- **弧序号**：为每条弧配整数 `ord`，选取一个规范起点（复用 `_link_connect` 的 `dist == 0` 根，`builtins.py:1302`），`ord[start_arc] == 0`，其余 `Implies(arc a 后继 b, ord[b] == ord[a] + 1)`，起点弧除外（环闭合）。`ord` 上界 = 弧总数。

### 8.3 新增内置

| 签名 | 语义 | 服务规则 |
|---|---|---|
| `orient(e)` | 为 `cloop`/`cross_loop` 的边生成弧变量 + 流守恒 + deg-4 配对。返回弧句柄 | 全部 14 条的基础 |
| `arc(e, p, q)` | 从 `p` 到 `q` 的弧是否被使用 | `nagare`（禁逆风）、`slalom` |
| `visit_ord(e, p)` | 格 `p` 的（首次）访问序号 | `trainstations` `hidato` 类顺序 |
| `arc_ord(e, p, q)` | 弧序号（自交格用此，不用 `visit_ord`） | `icelom` `icewalk` |
| `along_run_len(e, x, p, v)` | 沿回路包含 `p` 的、`x == v` 的极大连续段长 | `waterwalk` `firewalk` `icewalk` `bhaibahan` `maxi` |
| `along_next_marked(e, c, p)` | 沿回路从 `p` 出发遇到的下一个带标记格 | `wbloop` `alternate`（「沿回路连续两圈」） |
| `turn_side(e, p)` | 在 `p` 处相对行进方向是左转/直行/右转（`-1/0/1`） | `vertigo` `nagare` |

### 8.4 `along_run_len` 的编码与环绕问题

递推：对每格 `p` 设 `acc[p]`（「到 `p` 为止的同色连续长度」），
`Implies(arc(q,p) and same_colour(q,p), acc[p] == acc[q] + 1)`、
`Implies(arc(q,p) and not same_colour(q,p), acc[p] == 1)`。
段长 = 该段末格的 `acc`。

**环绕问题**：若规范起点恰好落在某个同色段的中间，该段会被错误地切成两截。

处置：起点是**我们自己选的**，因此可以附加约束「起点的前驱与起点不同色」。仅当整个回路同色时无解 —— 此时段长 = 回路总长，单独处理为特例。这个论证是严格的（存在性即可，不影响任何合法解）。

必须为此写专门的单测：构造一个「同色段跨越规范起点」的实例，断言 `along_run_len` 给出正确值。

### 8.5 分步交付

| 步 | 内容 | 验收 |
|---|---|---|
| P5-1 | `orient` + `arc` + 流守恒 + deg-4 配对 | 对现有所有回路 key（约 50 条）**加上 `orient` 但不加任何新约束**，accept 必须零翻转（证明定向本身不排除解） |
| P5-2 | `arc_ord` / `visit_ord` | 同上零翻转；另加单测验证序号在小盘面上确实沿回路递增 |
| P5-3 | `along_run_len` + 环绕特例 | 单测 + `waterwalk` `firewalk` `icewalk` 从 B 转 A |
| P5-4 | `turn_side` | `vertigo` `nagare` 从 B 转 A |
| P5-5 | `along_next_marked` | `wbloop` `alternate` 从 B 转 A |
| P5-6 | `slalom` `icebarn` `disloop` `maxi` `trainstations` `bhaibahan` `icelom` 逐条收紧 | 逐条 accept + reject |

### 8.6 风险

| 风险 | 处置 |
|---|---|
| 定向使变量数翻倍、约束数上升，求解变慢 | `orient` 必须**按需生成**（memo，仅在被调用时才建弧变量），不能像 `cloop` 那样无条件注入。P5-1 的零翻转检查同时记录耗时，若某 key 劣化超过阈值，该 key 不迁移 |
| deg-4 配对约束写错，排除合法自交 | P5-1 的零翻转检查专门覆盖现有允许自交的 key（`icewalk` `icebarn` `trainstations` `vertigo` `cross_loop` 使用者） |
| `vertigo` 的「全左或全右」在**无向**回路上本就有两个镜像解 | 规则语义是「沿某一方向走完整圈时转弯全同向」，定向后是「存在一个定向使 `turn_side` 全同号」。由于我们只需存在性，且 `orient` 给出的定向是求解器自由选择的，这正好正确。需在实现说明中写清此论证 |
| 环绕特例的正确性 | §8.4 已给出严格论证 + 强制单测 |

---

## 9. P6 — 形状目录与全等

依赖 P5 的候选枚举基础设施（可复用但非强依赖）。

### 9.1 目标规则（14 条）

| 缺口 | 规则 |
|---|---|
| 题面给定的多连块目录（可旋转/翻转） | `statuepark` `pentopia` `pentatouch` `kissing` `curvedata` |
| 组间全等比较（8 变换） | `mrtile` `ququ` `kuroclone` `evolmino` `chainedb` `tetrochain` `tetrochaink` `hinge` `dbchoco` |

### 9.2 现状：指纹 hack 与 O(8N⁴) 展开

**指纹 hack**：`place2.dsl:83-118` 的 `pent_type` / `tet_type` 用「凹角数 + 2×2 满窗数 + 度数分布 + bbox 角点数」凑出 12 个五连块的判别式。每个指纹项内部是一次全盘扫描，一次 `pent_type` 调用展开成 6 次 O(N²) 扫描。不可读、不可验证。

**全等展开**：`place2.dsl:199-204` 的 `freely_congruent` 是 `for t in 0..7: for b in cells(): region_match_tr(...)`，而 `region_match_tr`（`place2.dsl:188`）内部又是 `for s in cells()` —— 合计 O(8·N⁴) 个约束项。在实际盘面上不可用，这就是这 9 条被记为部分实现的真正原因（不是"太难"，是"编码方式不可行"）。

`place2.dsl:239-245` 的 `parts_congruent` 更是 `N² × 8 × N²`。

### 9.3 方案 A：形状目录 → 精确覆盖（服务前 5 条）

题面新增 param 约定：`param("shapes")` = 形状列表，每个形状是 `[[dr,dc], ...]` 的归一化偏移集。

新增 builtin `place_shapes(x, catalogue, opts)`：

1. **编译期**枚举全部候选放置：对每个形状 × 每个允许的变换（由 `opts` 控制 rot/flip）× 每个锚点，检查是否完全落在盘内 → 得到候选集 `P`（纯 Python 计算，无 z3）。
2. 每个候选一个布尔 `use[i]`。
3. 覆盖约束：每格 `Sum(use[i] for i 覆盖该格) == b2i(x[cell] != 0)`（不重叠 + 与涂色变量绑定）。
4. 用量约束：由 `opts` 指定「每形状恰用一次 / 至多一次 / 不限」。

这是经典精确覆盖编码，规模 O(|catalogue| × 8 × N)，远小于现状。

副产品：`pent_type` / `tet_type` / `tromino_type` 三个指纹 hack 可整体删除 —— 形状身份成为显式变量，`pentominous` / `tetrominous` / `lits` 等既有实现也可迁移（但**不强制迁移**，它们目前是 A 类完全实现，属于「能跑就别动」范畴，迁移仅在有明确收益时进行）。

### 9.4 方案 B：有界形状 id → 全等（服务后 9 条）

关键观察：这 9 条里，除 `dbchoco`（灰白两大块）外，**组的大小都有上界**（`mrtile`/`ququ`/`kuroclone`/`chainedb` 由线索给出，`tetrochain`/`tetrochaink` 恰 4，`evolmino` 逐步 +1，`hinge` 由区域大小界定）。

因此：**枚举所有大小 ≤ k 的自由多连块**（k=5 时 12 个，k=6 时 35 个，k=7 时 108 个，编译期纯 Python 生成），给每个格配一个「形状类 id」变量 + 「组内锚点偏移」变量。

新增 builtin：

| 签名 | 语义 |
|---|---|
| `shape_class(var, value, max_size)` | 返回每格「所在同值分量的自由多连块类 id」（分量大小 > `max_size` 时为 0，需配合大小约束保证不出现） |
| `congruent_class(var, value, max_size, mode)` | `mode` 选 `free`（8 变换）/ `translation`（仅平移）/ `rotation`（仅旋转） |

于是「两组全等」 ⟺ 「两组 `shape_class` 相等」，从 O(8N⁴) 降到 O(1) 的比较。

`dbchoco`（两块可能很大）不在此方案覆盖范围内，**明确保留为部分实现**，并在文档中写明原因（形状类枚举随 k 指数增长，大块不适用）。这是诚实的边界，不做勉强。

### 9.5 分步交付

| 步 | 内容 | 验收 |
|---|---|---|
| P6-1 | 编译期多连块枚举器（纯 Python，含 8 变换归一化与自由类判定） | 单测：k=1..7 的自由多连块计数必须等于已知序列 `1,1,2,5,12,35,108` |
| P6-2 | `place_shapes` | `statuepark` `pentopia` `pentatouch` `kissing` 从 B 转 A |
| P6-3 | `shape_class` / `congruent_class` | 单测 + `mrtile` `ququ` `kuroclone` `chainedb` `tetrochain` `tetrochaink` `evolmino` 从 B 转 A |
| P6-4 | 删除 `place2.dsl` 的 `pent_type` / `tet_type` / `tromino_type` / `freely_congruent` / `region_match_tr` / `parts_congruent` / `subset_match_tr` / `tr_r` / `tr_c` | 依赖这些函数的 key 全部 accept 通过 |
| P6-5 | `curvedata`（折线骨架可伸缩匹配） | 单独评估：它需要「形状的拓扑骨架 + 各段长可变」，是 `place_shapes` 的推广而非直接应用。若成本过高，保留为部分实现 |

### 9.6 风险

| 风险 | 处置 |
|---|---|
| 候选枚举爆炸（大目录 × 大盘面） | P6-2 前先统计各 key 的实际候选数；超过阈值的 key 不迁移。枚举是编译期的，可以先测量再决定 |
| `shape_class` 的 `max_size` 选错导致合法解被排除（大分量映射到 id 0） | 必须与「分量大小上界」约束成对使用，并在 builtin 内部强制：若某分量大小可能 > `max_size` 而调用方未约束，编译期报错而非静默放过 |
| `hinge` 的缺口其实是「跨区界 + 沿界轴对称」，全等只是其中一半 | `hinge` 不列入 P6 承诺范围，仅作为 `congruent_class` 的潜在受益者 |
| 删除 `place2` 函数破坏既有 A 类实现 | P6-4 前先生成「函数 → 依赖 key」反向索引（P3 已建），逐 key 验证后才删除；无法迁移的调用点保留旧函数 |

---

## 10. 交付物汇总

| 阶段 | 改动范围 | 新增 `impls/` 能力 | 主要收益 |
|---|---|---|---|
| P0 | `tools/`、`tests/` | — | 建立语义级回归网（含 reject 负向检查） |
| P1 | `compiler.py` `builtins.py` `values.py` `solver.py` | — | 求解性能（覆盖过半规则），零语义变化 |
| P2 | `lexer/tokens/parser/ast_nodes/compiler` + 4 builtin | — | 消除 165 处累加器 + 57 处布尔累加 |
| P3 | `builtins.py` + `core/loops/outside/fill2/regions/place2` | — | 消除 16 文件判空样板、全部方向 if 链、行列成对复制 |
| P4 | `builtins.py` `compiler.py` + `regions/place2` | — | 消除 CC 变量的重复连通性见证；14 个手写 O(N²) 函数下沉 |
| P5 | `builtins.py` + 14 个 impls | **14 条 B → A** | 沿回路段长、走访序、有向回路 |
| P6 | `builtins.py` + 11 个 impls | **11 条 B → A** | 形状目录、全等比较；删除指纹 hack |

预期 B 类「部分实现」从 48 条降至约 23 条。剩余的 23 条缺口类型：非正交几何（`kouchoku` `angleloop`，需独立设计）、半格三角 lattice（`shakashaka` `wagiri` `slashpack` `crossstitch` `kinkonkan`）、按颜色可达计数（`oasis` `go` `teri`）、双层区域（`parquet`）、通配段（`cts`）、照明/反射（`moonlight` `kinkonkan`）、大块全等（`dbchoco`）等。这些留待后续规划，本文件不承诺。

---

## 11. 文档同步义务

每个阶段合并时必须同步更新：

- `puzzle/dsl/GRAMMAR.md`：§2 语法（P2 的 `fn`/`->`）、§6 内置函数表（P2–P6 全部新增）、§8 变量类型（P1 的布尔降型说明）、§13「常见陷阱」（P2 的闭包捕获语义、P3 的 `rev` 与 `_merge` 顺序陷阱、P4 的 `region_width` ≠ `bbox_w`）。
- `builtins.py` 的 `function_table()`：新 builtin 必须带 `signature` + `doc`，否则 UI 函数浏览器与 LSP 悬浮提示会缺项。
- `IMPLEMENTATION_STATUS.md`：P5/P6 每条 B → A 的转换都要更新分类表与 §4.1 的逐条说明，并清空对应 JSON 的 `unencodedClues`。
