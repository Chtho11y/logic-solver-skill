# 元求解（Meta-Solve）执行计划 —— 编译期求解、唯一性判定、唯一化见证

对应审查讨论第 3 点。本文件是**可执行计划**，不是决策材料。

关联文档：
- `docs/DSL_REFACTOR_PLAN.md` —— P0–P6 的重构计划。本计划编号为 **PM**，插在 P1 之后、P2 之前（理由见 §2.3）。
- `docs/SOLVER_BACKEND_DISCUSSION.md` —— 后端决策。本计划的存在**收敛了**该文件的方案选择（§11）。

---

## 1. 目标与动机

### 1.1 当前缺失的能力

| 现状 | 位置 | 后果 |
|---|---|---|
| `verify.py` 只验「样例可满足」 | `verify.py:42-48` | 无法发现「约束过松」 |
| bite 检查只断言约束数增长 | `verify.py:50-76` | 语义无关。`IMPLEMENTATION_STATUS.md:23` 记录的 137 条错误编码正是这样通过验证的 |
| match 检查要求 `"unique": true` | `tests/test_solve.py:75-76` | 实测该字段普遍未开，检查被跳过 |
| 无任何唯一性判定 | — | `IMPLEMENTATION_STATUS.md:219-220` 已列为已知遗留 |

直接后果：**48 条 B 类「部分实现」的共同性质是「作为解题器不漏解，作为出题器会多解」，而现在没有任何自动手段能发现多解。** 收紧一条规则之后，也没有手段确认它真的收紧了。

### 1.2 三个层次的目标

| 层次 | 能力 | 服务对象 |
|---|---|---|
| **M1 唯一性判定** | 求一个解 → 排除它 → 再求 → 期望 UNSAT | 验证（P5/P6 每条 B→A 的验收依据） |
| **M2 编译期反馈** | 拿到模型后据其添加约束、再次求解 | 调试、增量收紧 |
| **M3 唯一化见证** | 「x 有 n 种可能，其中某个取值使其余部分解唯一」 | 出题器 |

M1 是刚需且最简单；M3 是出题器功能，最后做。

---

## 2. 这是范式变化，必须显式隔离

### 2.1 现状是严格单向的

```
compile_source(source, ...) → CompiledProgram(constraints=[...])   [compiler.py:176-193]
                            ↓
solve(...) → z3.Solver() → add all → check()                       [solver.py:96-115]
```

依赖方向：`solver.py:93` 里 `from .compiler import compile_source`，即 **solver → compiler**，compiler 完全不知道求解的存在。

### 2.2 闭环引入的三个语义变化

1. **语句顺序变得关键。** 现在 DSL 语句基本是无序合取（`_exec_block` 顺序执行但结果是合取集合）。有了 `solve()` 之后，「在第几行求解」决定「基于哪些约束求解」。
2. **程序变成非确定的。** `solve()` 返回 z3 任意选择的一个模型。同一份代码两次运行可能走不同分支、产生不同约束。对出题器可接受，对解题器不可接受。
3. **求解次数从 1 变成 n。** 单一 `timeout_ms`（`runner.py:30`，默认 60000）模型失效。

### 2.3 为什么排在 P1 之后、P2 之前

- **必须在 P1 之后**：`exclude()` 要生成「变量取值不等于模型值」，这个表达式的形式取决于变量是 `z3.Int` 还是 `z3.Bool`。P1 引入的 `as_bool` / `as_int` 适配层正是 `exclude` 需要的。在 P1 之前做会写两遍。
- **应当在 P2 之前**：唯一性判定是 P2–P6 全部改写工作的**验收工具**。P2 要改写 165 处累加器、P5/P6 要把 25 条 B 转 A —— 没有唯一性判定，这些改写只能靠 accept（不漏解）验证，无法确认「没有引入过松」。先有工具再动刀。
- 这也**加强了 P0**：P0-5 设计的「改错一格必须 UNSAT」是唯一性判定的弱化替代品，PM 落地后 P0-5 可退化为快速冒烟检查。

---

## 3. 语法设计

### 3.1 `meta:` 块 —— 两种范式的边界

```
# ---- 声明阶段（现状；纯合取，顺序无关；234 个现有实现完全不受影响）----
import "shading"
island_rule(x)
adj_black_clue(x, n)

# ---- 元阶段（顺序执行，可求解）----
meta:
    let s1 = solve()
    require(s1.sat, "no solution")
    scope:
        exclude(s1)
        let s2 = solve()
    require(not s2.sat, "multiple solutions")
```

**硬性限制（编译期强制，违反即报错）**：

| 限制 | 理由 | 检查点 |
|---|---|---|
| `solve` / `exclude` / `scope` / `require` / `emit_witness` **只能**出现在 `meta:` 块内 | 保持声明阶段纯净 | 编译器维护 `_in_meta` 深度计数 |
| `meta:` 块**只能**在顶层，即 `self._guards` 必须为空 | guard 是符号的，编译期不知真假，「在 guard 成立的假设下求解」无法定义 | `_exec_meta` 入口检查 `len(self._guards) == 0` |
| `meta:` 块不能嵌套 | 无意义且使 scope 语义复杂 | 同上计数 |
| `meta:` 块内不能 `def` | 避免函数体内隐藏 solve | `_exec_block` 在 meta 上下文中拒绝 `DefStmt` |

### 3.2 新增关键字与 AST

- `tokens.py:KEYWORDS` 新增 `meta`、`scope`。
  - 已 grep 确认：这两个词未在任何 `.dsl` 中作为标识符使用（与 P2 引入 `fn` 时同一批检查）。
- `parser.py`：`_statement()` 新增两个分支，均复用现有 `_suite()`，语法形状与 `if`/`for` 一致：
  ```
  meta_stmt  := 'meta' ':' suite
  scope_stmt := 'scope' ':' suite
  ```
- `ast_nodes.py` 新增 `MetaStmt(body)`、`ScopeStmt(body)`。

`scope` 设计为**语句块**而非 `push()`/`pop()` 裸函数对，保证配对性由语法保证，无法泄漏。

### 3.3 `scope:` 不引入 DSL 变量作用域 —— 关键设计决定

`scope:` 只管三件事：solver 的 `push`/`pop`、约束列表回滚、派生缓存回滚（§5.3）。**它不 push `self._scopes`。**

理由：唯一性判定的标准写法需要在 scope 内 `let s2 = solve()`，并在 scope 外读 `s2`：

```
scope:
    exclude(s1)
    let s2 = solve()
require(not s2.sat, "multiple solutions")
```

若 `scope:` 引入变量作用域层，`s2` 在退出时消失。而 `s2` 是**编译期 Python 快照**（§4.1），不是 z3 引用，因此在 scope 外读它是安全且有意义的。

这与 `for`（`compiler.py:284-289` 每次迭代 push 一层）行为不同，必须写进 `GRAMMAR.md`。

### 3.4 新增内置一览

| 签名 | 返回 | 语义 |
|---|---|---|
| `solve([timeout_ms])` | Solution | 对「当前已生成的全部约束」求解。同步未 flush 的约束（§5.2）后调用 `session.check()` |
| `s.sat` / `s.status` | 编译期 bool / str | 结果状态 |
| `s.<varname>` | CONSTANT 变量 | 该变量在模型中的取值快照（§4.1） |
| `exclude(s [, vars])` | 约束 | 排除该模型。`vars` 缺省为全部决定性变量（§4.2） |
| `unique_over(v1, v2, ...)` | — | 声明唯一性判定的变量范围（§4.3） |
| `require(cond, msg)` | — | 编译期断言；`cond` 必须是编译期布尔，否则报错 |
| `fail(msg)` | — | 无条件终止编译并报告 |
| `domain_of(var)` | 编译期整数列表 | 读 `Variable.domain`（`models.py:68`）展开为 `[lo..hi]` |
| `emit_witness(tag, value)` | — | 记录一条见证到结果（M3 用，§8） |
| `solve_count()` | 编译期整数 | 已求解次数，供预算诊断 |

`solve` 的可选参数意味着它**必须是 builtin**（用户 `def` 强制精确元数，`compiler.py:318-322`）。

---

## 4. 值模型设计

### 4.1 `Solution` 复用 CONSTANT 变量机制 —— 几乎不需要新类型

`VarType.CONSTANT`（`compiler.py:139-149`）已经就是「编译期具体整数值」的载体：它不生成 z3 量，`quantities` 直接是 `dict[Point, int]`。

因此 `solve()` 返回一个轻量 `SolutionValue`，其 `.<varname>` 成员构造一个 `VarValue(name, kind, {point: int}, order)` —— 与 CONSTANT 变量**完全同构**。

由此免费获得三件事：

1. `at(s.x, p)` 直接返回 Python `int`。
2. **天然参与常量折叠**：`if at(s.x, p) == 1:` 会在 `_try_const_bool`（`compiler.py:400-410`）中被识别为编译期常量，直接选择分支、不产生 guard。这正是「执行静态代码」所需的机制，**已经存在**。
3. `defined(s.x)` / `has_value(s.x, p)` 等既有 CONSTANT 工具链直接可用。

`SolutionValue` 需在 `_eval_member`（`compiler.py:557`）中新增一个分支，返回上述 `VarValue` 或 `.sat` / `.status`。

### 4.2 `exclude` 的正确性 —— 只能对决定性变量生成

排除模型的约束是：

```
Or([ q != model_value(q)  for each point q of each decisive variable ])
```

**若把辅助变量也算进去，唯一性判定会全面失效** —— 同一个解会因辅助变量取值不同而被判成「另一个解」，`exclude` 排掉一种见证后仍能找到同一个解的另一种见证，结果永远是「多解」。

**好消息：现有架构已经天然分好了。** 全部辅助量都经 `ctx.new_int`（`compiler.py:197`）/ `_new_bool`（`builtins.py:1057`）创建并经 `add_aux` 注入，**不进入 `compiled.var_z3`**：

| 辅助量 | 来源 |
|---|---|
| `ids` / `dist` | `_build_value_cc`（`builtins.py:737-738`） |
| loop 的 `id` / `d` | `_link_connect`（`builtins.py:1291-1292`） |
| `run#l` / `run#el` / `run#m` | `_seq_run_slots`、`_match_slots_to_clues` |
| `runs#L` / `runs#s` | `_fn_runs` |
| `drop` | `_fn_drop_covers` |
| cc 的 `_dist` | `_ensure_cc`（`compiler.py:648`） |
| cc 的 `size` / `border` | `_ensure_cc_size` / `_ensure_cc_border` |

而 `solver.py:139-141` 读模型时只遍历 `compiled.variables`。

因此判定规则很干净：**决定性变量 = `var_z3` 中 `var_type in (NORMAL, CC)` 的变量**（CONSTANT 存的是 Python int，无 z3 量，天然排除）。

注意 `cc.size` / `cc.border` 虽然挂在 CC 变量名下，但它们存在 `_cc_z3[name]["size"]` 而非 `var_z3[name]`，所以自动被排除 —— 这是正确的（它们是 id 的函数，不是自由度）。

### 4.3 `model_completion` 陷阱与 `unique_over`

`solver.py:132` 使用 `model_completion=True`。若某变量未被任何约束触及，z3 会任意赋值 —— 于是 `exclude` 之后它可以取另一个值，产生**虚假多解**。

两项处置：

1. **`unique_over(...)` 显式声明范围**，而非默认全部。多数规则只有一两个「答案变量」（如涂黑家族只有 `x`），其余是辅助的建模变量（如 `slashpack` 的三角编号、`pencils` 的 `k`）。
2. **自由变量诊断**：`exclude` 生成时，对每个纳入范围的量用 `model.eval(q, model_completion=False)` 检查是否真被赋值；若返回值仍是该变量自身（未被约束确定），发出 warning 列出这些点。这能在第一次运行时就暴露建模疏漏。

### 4.4 硬约束：CC 变量必须保持 canonical id

唯一性判定依赖「一个解 ↔ 一组变量赋值」的**双射**。

CC 变量当前是 canonical id（分量内最小线性下标 `r*cols+c`，`compiler.py:636-639` 强制 `id <= lin` 且 `(dist==0) == (id==lin)`），因此「一个分区 ↔ 一组 id 赋值」是双射，安全。

**如果连通性改用费用流或任何非 canonical 编码，同一个分区会有多种合法 id 赋值，唯一性判定必然误报多解。**

这条约束必须写入 `DSL_REFACTOR_PLAN.md` 的 P4A（连通性 API 分层）：**L3/L5 层（`cc_id` / `cc_root` / CC 变量）永久保持 canonical 树距离编码，费用流只允许用于不暴露 id 的 L1 层。**

---

## 5. 架构改造

### 5.1 依赖方向：注入而非 import

compiler 不能 `import solver`（会形成循环），也不应直接 `import z3` 的 Solver。

方案：定义协议，由 `solver.py` 注入实现。

```python
# puzzle/dsl/session.py （新文件）
class SolverSession(Protocol):
    def add(self, constraint) -> None: ...
    def push(self) -> None: ...
    def pop(self) -> None: ...
    def check(self, timeout_ms: int | None = None) -> str: ...   # "sat"/"unsat"/"unknown"
    def value_of(self, term) -> int: ...        # 读模型（含 model_completion 开关）
    def is_determined(self, term) -> bool: ...  # §4.3 的自由变量诊断
```

- `Compiler.__init__` 增加可选参数 `session: SolverSession | None = None`。
- `session is None` 时遇到 `meta:` 块 → 按 `run_meta` 策略处理（§5.4）。
- `solver.py` 新增 `_Z3Session` 实现该协议，构造时 `set("random_seed", ...)` 固定种子（缓解 §2.2-2 的非确定性）。

依赖方向仍是 `solver → compiler`，未反转。**这是整个改造中唯一触及架构的部分，且是加法。**

### 5.2 约束同步（flush）机制

现有约束收集不变（`self._constraints.append(...)`）。新增游标 `self._synced_upto = 0`。

`solve()` 执行时：
```
for c in self._constraints[self._synced_upto:]:
    session.add(c)
self._synced_upto = len(self._constraints)
result = session.check(timeout_ms)
```

好处：声明阶段零开销（不 flush 就不产生任何 session 调用），只有 `meta:` 块才触发。

### 5.3 `scope` 的回滚清单 —— 最容易出错的地方

进入 `scope:` 时快照，退出时恢复：

| 状态 | 操作 | 若遗漏的后果 |
|---|---|---|
| `session` | `push()` / `pop()` | 临时约束泄漏到后续求解 |
| `self._constraints` | 记录长度 / 截断 | 临时约束进入最终产物 |
| `self._synced_upto` | 记录 / 恢复（取 `min(saved, len(constraints))`） | flush 游标越界或重复 add |
| **`self._memo`** | 浅拷贝 dict / 整体恢复 | **见下** |
| **`self._cc_z3`** | 浅拷贝（含每个内层 dict 的键集合） | 同上 |
| `self._aux_counter` | **不回滚** | 单调递增仅影响命名，回滚会导致重名 |
| `self._scopes`（DSL 变量） | **不动**（§3.3） | — |

**`memo` 必须回滚的原因**：若在 scope 内首次调用 `cloop(e)`，`ctx.memo`（`compiler.py:208-213`）会缓存编码结果，但其生成的约束在 `pop` 后被丢弃。退出 scope 后再用 `cloop(e)` 时 memo 命中，**约束却已不存在** —— 产生一个静默错误的编码（回路约束凭空消失）。

同理 `_cc_z3`：`_ensure_cc` 用 `if name in self._cc_z3: return` 做幂等（`compiler.py:620-621`），若在 scope 内首次生成，退出后会被认为「已生成」而跳过。

这两项是本计划**最高风险点**，必须有专门单测（§7 的 PM-2 验收）。

### 5.4 `meta:` 默认关闭 —— 保护现有 234 个实现的编译速度

`meta:` 块内每个 `solve()` 都是一次完整求解。若默认执行，`compile_only` 会变慢甚至挂住。

策略：
- `compile_source(..., run_meta: bool = False)`；`compile_only` 恒传 `False`。
- `run_meta=False` 时，`meta:` 块**整块跳过**（不执行、不报错），仅记录一条 debug 说明已跳过。
- `solve_instance(..., run_meta=False)` 默认关闭；`verify.py` / `tests` 显式开启。
- `session is None` 且 `run_meta=True` → 报错（配置错误，应当显式暴露）。

### 5.5 预算与终止

| 设施 | 默认 | 作用 |
|---|---|---|
| 单次 solve 超时 | 继承 `timeout_ms`（`runner.py:30` 的 60000） | 单次卡死 |
| `meta:` 总时间预算 | 需定值（建议 300000ms） | 整块卡死 |
| solve 调用次数上限 | 需定值（建议 200） | 防止 `for v in domain_of(x)` 意外展开成上千次求解 |

超预算 → `CompileError` 并报告已完成次数，**不静默截断**。

---

## 6. 唯一性判定的标准写法（M1）

落地后，`verify.py` 与 `tests` 使用统一模板（放入 `puzzle/lib/meta.dsl` 作为库函数，供各规则 `import`）：

```
# puzzle/lib/meta.dsl
def assert_unique(v):
    meta:
        unique_over(v)
        let s1 = solve()
        require(s1.sat, "UNSAT: encoding rejects the intended answer")
        scope:
            exclude(s1)
            let s2 = solve()
        require(not s2.sat, "MULTIPLE: encoding admits more than one solution")
```

注意：`meta:` 块出现在 `def` 体内是允许的（限制是「meta 块内不能 def」，不是「def 内不能有 meta 块」），但调用点必须 guard 为空 —— `_exec_meta` 的 `_guards` 检查会自动保证这点。

---

## 7. 分步交付

| 步 | 内容 | 验收标准 |
|---|---|---|
| **PM-0** | `session.py` 协议 + `_Z3Session` + 注入 + flush 游标。**无新语法** | 全量基线（P0-1）**逐字节相同**（约束数、模型指纹逐条一致）。证明基础设施无副作用 |
| **PM-1** | `meta:` 语法 + `solve()` + `s.sat` / `s.status` / `s.<var>` + `run_meta` 开关 + `require` / `fail` | 手工样例：在某规则末尾加 `meta:` 块打印模型某格取值，与 `solve_instance` 的输出一致。`run_meta=False` 时基线不变 |
| **PM-2** | `scope:` 语法 + push/pop + §5.3 全部回滚项 | **三个专项单测**：(a) scope 内加约束，退出后失效；(b) scope 内首次触发 `cloop`，退出后再用仍完整；(c) scope 内首次触发 CC 变量的 `.size`，退出后仍正确。(b)(c) 是 §5.3 的静默错误检测 |
| **PM-3** | `exclude()` + `unique_over()` + 自由变量诊断 | 对 `tests/cases/*.json` 中已人工确认唯一的 case，判定为唯一；对 B 类 48 条中抽样的 5 条（已知多解），判定为多解。**两个方向都必须验证**，只验一边说明不了什么 |
| **PM-4** | 接入 `verify.py` 与 `tests/test_solve.py`，唯一性成为正式检查 | 全量跑一遍并**落盘一份「唯一性现状报告」**。预期会大规模发现多解 —— 这是本计划的主要产出，不是失败 |
| **PM-5** | `domain_of` + 预算/次数上限 + seed 固定 + `solve_count` | 预算超限时报错而非挂住；同一输入两次运行产生相同模型 |
| **PM-6** | `emit_witness` + M3 唯一化见证（§8） | 见 §8 |

PM-0 到 PM-4 构成 M1（唯一性判定），是刚需部分。PM-5 是工程化。PM-6 是出题器功能，可延后。

---

## 8. M3：唯一化见证（PM-6）

### 8.1 问题的形式化

需求：*「x 有 n 种可能，其中某个取值可使其余部分解唯一」*

\[
\exists v \in \mathrm{dom}(x):\ \neg \exists s_1, s_2\ \big(\mathrm{sat}(s_1) \land \mathrm{sat}(s_2) \land s_1 \neq s_2 \land x = v\big)
\]

即 ∃∀¬∃。**这不可能作为一条约束交给 z3**（QF 逻辑无量词；引入量词则性能不可控）。唯一实现路径是编译期枚举 + 增量求解 —— 正是 `meta:` 块的用途。

### 8.2 标准写法

```
meta:
    unique_over(x)
    for v in domain_of(x):
        scope:
            at(x, cell(0, 0)) == v
            let s1 = solve()
            if s1.sat:
                scope:
                    exclude(s1)
                    let s2 = solve()
                if not s2.sat:
                    emit_witness("uniquifier", v)
```

注意内层 `scope` 嵌套：外层固定 `x == v`，内层排除 `s1`。嵌套 scope 对应 session 的嵌套 push/pop，需在 PM-2 中就支持任意深度（用栈记录快照）。

### 8.3 交付物

`emit_witness` 的记录进入 `SolveResult`（新增 `witnesses: list[tuple[str, int]]` 字段）并由 `format_model` 渲染。这是出题器读取的接口。

---

## 9. 风险清单

| 风险 | 等级 | 处置 |
|---|---|---|
| `memo` / `_cc_z3` 回滚遗漏 → 约束静默消失 | **最高** | PM-2 的三个专项单测；回滚清单（§5.3）逐项对照实现 |
| `exclude` 误纳辅助变量 → 唯一性判定永远报多解 | 高 | §4.2 已确认 `var_z3` 恰为决定性集合；PM-3 的双向验证（已知唯一 + 已知多解）能捕获 |
| `model_completion` 导致虚假多解 | 高 | `unique_over` 显式范围 + 自由变量诊断（§4.3） |
| 未来把连通性改成非 canonical 编码 → 唯一性判定失效 | 高 | §4.4 写入 P4A 作为硬约束 |
| `meta:` 块使编译变慢 | 中 | `run_meta` 默认关闭（§5.4） |
| solve 次数爆炸（尤其 M3 的枚举） | 中 | 次数与时间双预算（§5.5） |
| 非确定性导致结果不可复现 | 中 | 固定 seed；但 z3 版本升级仍可能改变模型，故基线含版本号 |
| `require` 的 `cond` 意外是符号值 | 低 | 强制编译期布尔，否则报错（不静默转成约束） |

---

## 10. 文档同步义务

- `puzzle/dsl/GRAMMAR.md`：
  - §2 语法：`meta:` / `scope:` 块
  - §6 内置函数表：§3.4 的全部新增（必须带 `signature` + `doc`，否则 UI 函数浏览器与 LSP 悬浮提示缺项）
  - §10 API：`compile_source` / `solve` 的 `run_meta` 参数
  - §13 常见陷阱：新增三条 —— `scope:` 不引入变量作用域（§3.3）；`scope:` 内首次触发重型编码的回滚语义（§5.3）；`unique_over` 不声明范围时 `model_completion` 会造成虚假多解（§4.3）
- `docs/DSL_REFACTOR_PLAN.md`：依赖图与交付物表已含 PM（本次同步完成）。
- `IMPLEMENTATION_STATUS.md`：PM-4 产出的「唯一性现状报告」应作为新的一节，替代目前 §7「已知遗留问题」中关于唯一解的描述。

---

## 11. 本计划对后端决策的影响

**增量求解（`push`/`pop` + 跨 `check()` 复用学习子句）是 SMT 求解器的天生强项，恰恰是 CP-SAT 与 MiniZinc/Chuffed 的弱项**：

| 后端 | 增量支持 | 对本计划的适配 |
|---|---|---|
| **z3**（现有） | 原生 `push`/`pop`，跨 check 复用 lemma | 完全适配，正是为交互式使用设计 |
| OR-Tools CP-SAT | 弱；每次 solve 基本重建 model（仅 solution hint 能传递少量信息） | §8.2 的嵌套枚举代价高 |
| MiniZinc / Chuffed | 无（外部进程） | §8.2 需付 n 次进程启动 + n 次模型文本生成/解析 |

因此本计划的存在使 `SOLVER_BACKEND_DISCUSSION.md` 的方案 C/D 吸引力显著下降，讨论应收敛到「留在 z3 + L2 全局约束抽象 + 惰性割」。该文件已相应更新（见其 §6、§7）。
