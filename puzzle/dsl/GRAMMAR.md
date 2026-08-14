# Puzzle DSL 语法文档

本文件描述 `decoders/puzzle/dsl` 中实现的网格谜题约束 DSL。该语言用于
描述网格谜题（数独、连线等）的约束，最终被编译（lower）为 [z3](https://github.com/Z3Prover/z3)
布尔表达式求解。语言本身与 UI 解耦，不依赖 PyQt；z3 仅在求解时按需导入。

整条管线：`源码 → 词法 lexer → 语法 parser（AST）→ 编译 compiler（z3 约束）→ 求解 solver`。

---

## 1. 词法（Lexical）

### 注释
- 以 `#` 开头到行尾的内容为注释，被忽略。
- 整行空白或仅含注释的行不产生任何 token。

### 缩进与换行
- 采用 **Python 风格的显著缩进**：缩进产生 `INDENT`，回退产生 `DEDENT`，逻辑行以 `NEWLINE` 结束。
- 同级缩进必须一致，否则报 `inconsistent indentation`。
- 括号 `(` / `[` 内的换行视为续行，不做缩进处理（可跨行书写长表达式）。
- 换行符 `\r\n`、`\r` 会被归一化为 `\n`。

### 关键字（KEYWORDS）
```
if  elif  else  for  in  let  and  or  not  true  false  def  return  import  meta  scope  fn
```

### 运算符
- 双字符（优先匹配）：`==` `!=` `<=` `>=` `&&` `||` `=>` `->`
- 单字符：`+ - * / % < > = ( ) [ ] , : ^ ! .`
- `&&` / `||` 是 `and` / `or` 的符号别名；`^` 是 xor；`!` 是 not；`=>` 是 implies；`->` 用于 `fn (...) -> expr`；`.` 是成员访问。

### 字面量与标识符
- 整数：连续数字组成（仅非负整数；负数由一元 `-` 得到）。
- 布尔：`true` / `false`。
- 字符串：`"..."` 或 `'...'`，单行，支持 `\` 转义。用于 `import`、`edge("H", r, c)`、`param("top")`。
- 标识符（NAME）：字母或 `_` 开头，后接字母/数字/`_`。

> 注意：语言**没有**浮点字面量。

---

## 2. 语法（Grammar，非形式 EBNF）

```ebnf
program     := { NEWLINE } { statement }
statement   := simple NEWLINE | compound
compound    := if_stmt | for_stmt | def_stmt | meta_stmt | scope_stmt
if_stmt     := 'if' expr ':' suite { 'elif' expr ':' suite } [ 'else' ':' suite ]
for_stmt    := 'for' name_list 'in' expr ':' suite
def_stmt    := 'def' NAME '(' [ name_list ] ')' ':' suite
meta_stmt   := 'meta' ':' suite
scope_stmt  := 'scope' ':' suite
suite       := simple NEWLINE | NEWLINE INDENT statement+ DEDENT
simple      := 'let' name_list '=' expr | 'return' [ expr ] | 'import' STR | expr
name_list   := NAME { ',' NAME }
expr        := implies_expr
implies_expr:= or_expr ['=>' implies_expr]          # 右结合
or_expr     := xor_expr {('or'|'||') xor_expr}
xor_expr    := and_expr {'^' and_expr}
and_expr    := not_expr {('and'|'&&') not_expr}
not_expr    := ('not'|'!') not_expr | comparison
comparison  := arith {('=='|'!='|'<'|'<='|'>'|'>=') arith}
arith       := term {('+'|'-') term}
term        := factor {('*'|'/'|'%') factor}
factor      := ('+'|'-') factor | postfix
postfix     := primary {'[' expr ']' | '(' [args] ')' | '.' NAME}
primary     := INT | STR | 'true' | 'false' | NAME | '(' expr ')' | '[' [items] ']' | lambda_expr
lambda_expr := 'fn' '(' [name_list] ')' '->' expr
```

`fn` 的体是**单个表达式**（不是语句块）。跨行时把体放在括号里：`fn (p) -> (a or b)`。

### 语句
- **顶层表达式语句**：将其（广播后的）布尔值作为约束断言。整数/区域等非布尔会报错。
- **`let NAME = expr`**：绑定。若该名字已存在于某个外层作用域，则**就地重绑定**该作用域中的绑定；否则在当前作用域新建。这样 `for` 循环体内的累加惯用法 `let total = total + …` 才能跨迭代生效。循环变量始终绑定在循环自身的（每次迭代新建的）作用域里。
- **`if cond: body [elif …] [else: body2]`**：
  - 若 `cond` 在编译期可求值为**纯 Python 布尔常量**，则进行**常量折叠**：直接编译被选中的分支，既不生成条件约束，也不为该分支添加守卫。`not` / `and` / `or` / `^` / `=>` 在两侧都是编译期布尔时同样折叠，因此 `if not same_region(p, q):` 之类写法可以安全地包裹 `let` 累加。
  - 否则把 `body` 内每条约束包装为 `Implies(cond, c)`，`else` 分支包装为 `Implies(Not(cond), c)`。守卫（guard）会累积。**注意**：守卫只作用于被断言的约束，不会阻止 `let` 执行——需要条件性累加时请确保条件是编译期常量。
- **`for v in iterable: body`**：在编译期**展开**循环，每次迭代把 `v` 绑定到一个元素。
- **`def name(a, b): body`**：定义编译期内联的辅助函数。函数体内的约束按调用点的守卫被断言；`return expr` 返回一个值（可以是布尔表达式、区域、列表……），没有 `return` 时返回空列表。同一块内的 `def` 会被**提升**，因此可以先用后定义。调用时作用域栈被替换为**仅** `[参数帧]`（只能看到自己的参数与全局的变量/区域/常量/函数），**不捕获**外层 `let`。
- **`fn (a, b) -> expr`**：匿名函数，表达式体，无副作用。求值时把当前 `self._scopes` **逐层 `dict(scope)` 拷贝**进闭包。调用时作用域为 `captured + [参数帧]`，因此能看见捕获时的外层绑定。捕获的是拷贝，之后的 `let` 就地重绑定**不可见**（与 Python 相反）。`def` 与 `fn` 的作用域规则不同，不要混用预期。
- **`import "module"`**：把另一个 DSL 模块的定义引入当前程序（同名模块只加载一次）。解析顺序为 `puzzle/lib/` 然后 `impls/`，扩展名 `.dsl` 可省略。
- **`meta:` 块**：编译期求解。`solve` / `exclude` / `scope` / `require` / `emit_witness` **只能**写在这里。块必须出现在守卫为空的位置（不能包在符号 `if` 里），不能嵌套，块内不能 `def`。`meta:` 可以写在 `def` 体内，但调用点的守卫仍须为空。默认不执行：`compile_source` / `solve` / `solve_instance` 的 `run_meta` 默认为 `False`；`compile_only` 恒为 `False`。关闭时整块跳过并记一条 debug。
- **`scope:` 块**：只能写在 `meta:` 内。对应求解器 `push`/`pop`、截断本次加入的约束、回滚 `_memo` 与 `_cc_z3`。**不** push DSL 变量作用域，因此 `let s2 = solve()` 可以在退出后继续读取。不回滚 `_aux_counter`。

### 结构化绑定（解包）
- `let a, b, c = expr` 与 `for a, b, c in expr:` 把 `expr`（或每个循环元素）按位解包到多个目标名。
- 元素数量必须与目标数量**严格相等**，否则编译报错 `cannot unpack N value(s) into M targets`。
- 单目标 `let x = expr` / `for x in expr` 保持原语义（不做解包）。

### 套件（suite）
- 行内单语句：`if cond: stmt`（`else` 同样支持行内：`if cond: a else: b`）
- 块：换行 + 缩进的多条语句。空块报错。`else` 须与对应 `if` 同级缩进。

---

## 3. 值类型（运行期）

编译期流动的值是以下之一：

| 类型 | 说明 |
|------|------|
| **标量 scalar** | Python `int` / `bool`，或 z3 表达式 |
| **列表 list** | 可嵌套的值列表；支持 `.size` / `.append(x)` / `[i]` |
| **RegionValue** | 单一种类（cell/corner/edge）的有序点集，可作索引或被迭代；支持 `.size` |
| **VarValue** | 一个变量在其全部点上的量集合；直接使用时等价于其所有量组成的列表；支持 `.size`。区域划分（cc）变量的 `.id` / `.size` / `.border` 也以 `VarValue` 形式返回 |
| **Closure** | `fn (...) -> expr` 的值：参数、表达式体、捕获的作用域拷贝。可传入 `count_where` 等聚合 |
| **UserFunction** | `def` 定义的函数值。调用时**不**捕获外层 `let`（作用域仅为参数帧） |
| **_BoundMethod** | 由成员访问产生的可调用方法（如 `list.append`），仅用于随后立即调用 |

### 点（Point）表示
- cell / corner：`(r, c)`
- edge：`(orient, r, c)`，`orient` 为 `"H"`（水平）或 `"V"`（竖直）
- 排序：cell/corner 先于 edge，整体确定性排序。

### 数值化规则（`to_numeric`）
- `VarValue` → 其量列表；
- 列表 → 递归数值化；
- `RegionValue` 用作数字 → 报错（区域不能直接当数字）。

### 成员访问 `.size` / `.append`
- `list.size` / `RegionValue.size` / `VarValue.size` → 元素个数（编译期具体 `int`）。
- `list.append(x)` → 返回**追加 x 后的新列表**（不就地修改原列表，避免副作用），常配合 `let` 累积：`let xs = xs.append(v)`。
- `list[i]` 下标访问、`[a, b, c]` 列表构造一并支持。

---

## 4. 运算符与优先级

从低到高（同栏内从左到右结合，除特别说明）：

| 优先级 | 运算符 | 含义 | 备注 |
|--------|--------|------|------|
| 1（最低） | `=>` | 蕴含 implies | **右结合**：`a => b => c` 即 `a => (b => c)` |
| 2 | `or` / `\|\|` | 逻辑或 | |
| 3 | `^` | 逻辑异或 xor | |
| 4 | `and` / `&&` | 逻辑与 | 两个集合相与时表示**合并**（见下） |
| 5 | `not` / `!` | 逻辑非 | 一元 |
| 6 | `== != < <= > >=` | 比较 | 元素级广播 |
| 7 | `+ -` | 加减 | |
| 8 | `* / %` | 乘 / 除 / 取模 | 双方为具体整数时按整数除法/取模 |
| 9（最高） | 一元 `+ -` | 取正 / 取负 | |
| postfix | `[]` `()` `.` | 索引 / 调用 / 成员 | |

### `and` 的集合合并语义
当 `and` 两侧都是「可合并」值（list / RegionValue / VarValue）时，结果是**合并**而非逻辑与：
- 两个同种 `RegionValue` → 合并点集为新区域；不同种类报错。**合并走 `RegionValue.of`，会按 `sort_points` 重排**，因此 `rev(...) and ...` 会丢掉逆序。
- 否则各自展平为元素列表后拼接。

`and` / `or` / `^` / `=>` **两侧都会求值**，没有短路。`in_grid(p, dr, dc) and at(x, shift(p, dr, dc))` 仍会执行 `shift`/`at`，越界时照样报错。越界请用 `if not in_grid(...):` 守卫，或改用 `at_or` / `nb`（缺省值）。

这样可写 `row(0) and row(1)` 把两行合成一个区域再传给函数。

---

## 5. 索引与广播

### 索引 `base[index]`
- `index` 为列表时，对每个元素分别索引并返回列表。
- **VarValue[RegionValue]**：取变量在该区域各点上的量列表；区域种类须与变量种类一致，且点须在网格内。
- **VarValue[int]**：按 `order` 取第 i 个量。
- **RegionValue[int]**：取第 i 个点（返回单点区域）。
- **list[int]**：取第 i 个元素。

### 广播（broadcast）
二元运算遵循广播规则（递归作用于嵌套列表）：
- 标量 + 标量 → 直接运算；
- 列表 + 标量 → 元素级；
- 两个列表：长度相等按位运算；其中一个长度为 1 时拉伸；否则报 `cannot broadcast`。

逐元素函数（如 `abs`）、一元运算同样按元素映射。

### 函数入参广播（function-argument broadcast）
部分接受**单个点 / 单个 cell** 的函数被标记为可广播（`broadcast`）：当其唯一实参是一个**列表**时，对列表中每个元素分别调用一次并收集结果为列表。

当前启用广播的函数：`adj4` / `adj8` / `cell_of` / `corner_of` / `edge_of`。

例如 `adj4(row(0))` 等价于对第 0 行每个 cell 分别取 `adj4`，得到「区域列表」。聚合函数（`sum` / `distinct` 等）不广播，仍消费整个列表。

---

## 6. 内置函数（Builtins）

调用上下文 `ctx` 提供 `ctx.z3`（z3 模块）与 `ctx.grid`（网格）。

### 6.1 聚合函数（Aggregate）— 消费整个列表

| 签名 | 说明 |
|------|------|
| `sum(list)` | 列表/区域中所有量之和 |
| `distinct(list)` | 所有量两两不同（`z3.Distinct`） |
| `all(list)` | 列表中所有布尔同时成立 |
| `any(list)` | 至少一个布尔成立 |
| `count(list)` | 元素个数（具体整数，编译期可得） |
| `max(list)` | 最大量（z3 If 链）；空列表报错 |
| `min(list)` | 最小量（z3 If 链）；空列表报错 |
| `count_where(iterable, pred)` | `Sum(If(pred(e), 1, 0))`。`pred` 为 `fn` 或 `def` |
| `sum_where(iterable, pred, val)` | `Sum(If(pred(e), val(e), 0))`。`val` 同样是可调用 |
| `any_where(iterable, pred)` | 至少一个 `pred(e)` 成立 |
| `all_where(iterable, pred)` | 全部 `pred(e)` 成立 |

`iterable` 接受 RegionValue / list / VarValue。空列表时 `count_where`/`sum_where` 为 0，`any_where` 为 false，`all_where` 为 true。
沿射线的前缀状态机（`see_count`、`seg_len`/`arm_len`、`vis_count`/`first_nonzero`、`h_run_len` 等）**不能**改写成这些聚合：它们依赖迭代顺序上的 `alive`/`seen`/`mx`。

### 6.2 逐元素函数（Element-wise）

| 签名 | 说明 |
|------|------|
| `abs(x)` | 绝对值，对列表逐元素映射 |

### 6.3 区域生成器（Region producers）

| 签名 | 说明 |
|------|------|
| `row(i)` | 第 i 行的 cell 区域 |
| `col(j)` | 第 j 列的 cell 区域 |
| `cell(r, c)` | 坐标 (r,c) 的单个 cell |
| `corner(r, c)` | 坐标 (r,c) 的单个 corner |
| `edge("H"\|"V", r, c)` | 单条 edge：`"H"` 在 cell (r,c) 上方，`"V"` 在其左侧 |
| `cells()` / `corners()` / `edges()` | 整个 lattice |
| `boundary()` | 位于盘面外圈的 cell |
| `rect(r, c, h, w)` | 以 (r,c) 为左上角的 h×w 矩形（越界裁剪） |
| `shift(point, dr, dc)` | 平移后的 cell/corner；越界时返回空区域 |
| `in_grid(point [, dr, dc])` | 点（加可选偏移）是否在盘内；编译期布尔，替代 `.size == 0` |
| `diag()` | 主对角线 cell：(0,0),(1,1),… |
| `ct_diag()` | 反对角线 cell：(0,cols-1),(1,cols-2),… |
| `adj4(cell)` | 正交相邻的 4 个 cell（越界裁剪） |
| `adj8(cell)` | 周围 8 个 cell（越界裁剪） |
| `diag4(cell)` | 对角相邻的 4 个 cell |
| `cell_of(point)` | 与某 cell/corner/edge 直接相连的 cell |
| `corner_of(point)` | 与某 cell/corner/edge 直接相连的 corner |
| `edge_of(point)` | 与某 cell/corner/edge 直接相连的 edge |
| `dir(cell, value)` | 从某 cell 沿方向 value(0-7) 的所有 cell（不含起点，保持射线顺序） |
| `line_from(p, d)` | 与 `dir(p, d)` 相同，线族写法 |
| `line(axis, i)` | `axis==0` → `row(i)`；`axis==1` → `col(i)`。保持从左到右 / 从上到下的顺序 |
| `lines(axis)` | 该轴全部线，等价于 `rows` / `cols` |
| `rev(region)` | 逆序的同类区域或列表。**直接构造，不经过 `RegionValue.of`，因此不排序** |
| `side_of(axis, near)` | 盘外线索边名。`axis==0`（行）：`near==0` → `"left"`，否则 `"right"`；`axis==1`（列）：`near==0` → `"top"`，否则 `"bottom"`。`near` 须为具体整数 0/1 |
| `dr_of(d)` / `dc_of(d)` | 方向 `d` 的行列偏移（编译期整数，读方向表） |
| `opp(d)` | 反向（4 向与 8 向都支持） |
| `rot90(d [, k])` | 4 向顺时针转 90°×k（`k` 缺省 1） |
| `is_horizontal(d)` / `is_vertical(d)` | 编译期布尔：LEFT/RIGHT vs UP/DOWN |
| `tr(dr, dc, t)` | 8 元二面体变换，返回 `[dr', dc']` |
| `spiral()` | 从左上角起顺时针螺旋走过每个 cell（保持访问顺序，不排序） |
| `grid(w, h)` | 把棋盘划分为不重叠的 w×h tile（区域列表，仅完整 tile） |
| `slide(w, h)` | 所有重叠的 w×h 滑动窗口（步长 1，区域列表） |
| `row_of(point)` / `col_of(point)` | 点的行/列号（编译期整数） |

> `dir` 的 `value` 取值见下方方向常量；`grid` / `slide` 中 `w` 跨列、`h` 跨行。

### 6.4 题面数据与取值（Instance data）

| 签名 | 说明 |
|------|------|
| `at(var, point)` | 变量在**单个点**上的量（标量）。`x[p]` 返回长度 1 的列表，需要标量时一律用 `at` |
| `at_or(var, point, default)` | 点在盘内且变量有值 → 该量；否则 → `default`（`default` 可以是任意值，包括 `false`） |
| `nb(var, point, d [, default])` | `at_or(var, step(point, d), default)`，`default` 缺省 0 |
| `nb_at(var, point, dr, dc [, default])` | 偏移版本。缺省 0 在「值为 0 也合法」时**不能**当越界哨兵（例如数相邻的 0-格对） |
| `defined(var)` | 常量变量实际有值的点组成的区域 |
| `has_value(var, point)` | 该点是否有值（编译期布尔） |
| `param("name")` | 实例参数（整数或嵌套列表），如盘外提示 `param("top")[c]` |
| `has_param("name")` | 实例是否定义了该参数 |
| `regions` | 题面预先画好的区域列表（常量） |
| `region_of(point)` | 包含该点的题面区域 |
| `region_id(point)` | 该区域的序号（编译期整数，无区域时 -1） |
| `same_region(a, b)` | 两点是否同区域（编译期布尔） |

### 6.5 逻辑与计数（Logic & counting）

| 签名 | 说明 |
|------|------|
| `ite(cond, a, b)` | if-then-else 表达式 |
| `b2i(x)` | 布尔转 0/1（逐元素） |
| `count_true(list)` | 列表中成立的布尔个数 |
| `num_eq(list, value)` | 列表中等于 value 的量的个数 |
| `at_most(list, k)` / `at_least(list, k)` / `exactly(list, k)` | 计数约束 |
| `runs(list, lengths)` | 0/1 序列的极大连续 1 段长度**依次**等于 `lengths`；`-1` 表示 `?`（任一段长 ≥1） |
| `runs_set(list, lengths[, extra])` | 段长作为**多重集**等于 `lengths`（二分图匹配，不是排序后 zip）。`-1` = `?`；`extra=true` 允许未被线索匹配的剩余段（`*`） |
| `runs_cycle(list, lengths[, extra])` | 把 `list` 当成环做无序段长匹配（Tapa 八邻域）；全 1 视为一段长度为 n |
| `values_set(list, lengths[, extra])` | `list` 中的正值作为多重集等于 `lengths`（忽略 0）；`-1` = `?` |

### 6.6 同值连通分量（Connectivity）

作用于 **cell 变量**，把「取值相同且相邻」的格子归为一组。按语义强度分层：

| 层 | 签名 | 说明 |
|----|------|------|
| **L1** | `is_connected(var, value)` | 取值为 value 的格**至多一个** 4-连通分量。**空集算连通**。单流编码，**不建 id**。`connected(x, v)` 转调此函数。只适合作为约束断言；`not is_connected` 不是「存在两个分量」的见证 |
| **L1** | `is_connected8(var, value)` | 8-连通版本；`connected8` 转调它 |
| **L2** | `component_count(var, value)` | 取值为 value 的 4-连通分量个数。别名 `cc_count` |
| **L3** | `same_component(var, p, q)` | 两点是否同 4-连通同值分量（依赖 canonical id） |
| **L4** | `component_size(var)` | 每格所在分量格数（O(N²)）。别名 `cc_size` |
| **L5** | `component_id(var)` | **low-level** canonical id = 分量内最小 `r*cols+c`。别名 `cc_id` |
| | `cc_root(var, cell)` | 该格是否为其分量的代表元 |
| | `cc_count_in` / `cc_size_in` | 区域外当墙后的 4-连通版本 |
| | `cc_width` / `cc_height` / `cc_is_rect` | 外接框派生量（O(N²)） |
| | `cc8_*` | 上述的 8-连通版本 |

**L5 硬约束**：`component_id` / CC 变量自身的值必须是 canonical id（分量内最小线性下标）。唯一性判定依赖「一个分区 ↔ 一组 id 赋值」的双射。费用流等非 canonical 编码**只允许**用于不暴露 id 的 L1。

`group_count(x, v, n)` 仍是 `cc_count(x, v) == n`（L2）。

### 6.7 回路与路径（Loops）

作用于 **edge 变量**（值域 0/1）。两套 lattice：

* `loop(e)` —— 线段画在**格线**上，度数在 corner 处统计（数回家族）；
* `cloop(e)` —— 线段连接**相邻格中心**，度数在 cell 处统计（珍珠家族）。
  此时一条 edge 代表它所分隔的两个 cell 之间的连线，故 `"H"` edge 是一条竖直连线。

| 签名 | 说明 |
|------|------|
| `loop(var)` | corner lattice 上恰好形成一个闭合回路 |
| `cloop(var)` | 经过格中心恰好形成一个闭合回路（盘面外沿的 edge 强制为 0） |
| `deg(var, corner)` | corner 处被选中的格线条数 |
| `cdeg(var, cell)` | cell 处引出的连线条数 |
| `connect_edges(var)` | corner lattice 上被选中的边连通成一个整体（不限度数） |
| `connect_links(var)` | 格中心连线连通成一个整体（不限度数） |

### 6.8 调试函数（Debug）

| 签名 | 说明 |
|------|------|
| `print(expr, ...)` | **编译期**打印每个参数所代表的变量 / 区域 / 列表描述 |

`print` 不产生任何约束（返回空列表），仅把描述记录到编译/求解结果的 `debug` 中，
并在输出面板末尾以 `print():` 块展示。配合工具栏的 **Compile** 按钮可只编译不求解，
方便检查某个表达式实际指向哪些点。

示例：
```
print(row(0))        # 打印第 0 行的 cell 列表
print(x[row(0)])     # 打印变量 x 在第 0 行的量列表
```

### 6.9 元求解（Meta）

只在 `meta:` 块内可用（`domain_of` 除外，它是纯编译期查询）。`require` / `unique_over` / `emit_witness` 返回空列表，用作表达式语句时不产生 `BoolVal(True)`。

| 签名 | 说明 |
|------|------|
| `solve([timeout_ms])` | 对**当前已生成的全部约束**求解。返回快照：`.sat`（编译期布尔）、`.status`（`"sat"` / `"unsat"`）、`.<变量名>`（CONSTANT 风格的取值表，可用 `at(s.x, p)`） |
| `exclude(s [, vars...])` | 约束：决定性变量（NORMAL / CC，或 `unique_over` / 额外参数列出的子集）与快照 `s` 至少有一处不同。不纳入 aux / `cc.size` / `cc.border` |
| `unique_over(v1, v2, ...)` | 声明后续 `exclude()` 的判定范围。不声明时 `exclude(s)` 覆盖全部决定性变量；辅助建模变量上的 `model_completion` 会造成虚假多解 |
| `require(cond, msg)` | 编译期断言。`cond` 必须是 Python 布尔，否则报错（不会静默变成约束） |
| `fail(msg)` | 无条件终止编译 |
| `domain_of(var)` | 编译期整数列表，展开 `Variable.domain` 的闭区间 |
| `emit_witness(tag, value)` | 记录一条 `(tag, int)` 见证到 `SolveResult.witnesses` |
| `solve_count()` | 本 `meta:` 块内已调用 `solve()` 的次数 |

库函数 `import "meta"` 提供 `assert_unique(v)`：求一解 → `exclude` → 再求，期望第二次 UNSAT。

---

## 7. 常量（Constants）

| 名称 | 含义 |
|------|------|
| `rows` | 所有行区域组成的列表 |
| `cols` | 所有列区域组成的列表 |
| `UP` = 0 | 方向：上 |
| `DOWN` = 1 | 方向：下 |
| `LEFT` = 2 | 方向：左 |
| `RIGHT` = 3 | 方向：右 |
| `UP_LEFT` = 4 | 方向：左上 |
| `UP_RIGHT` = 5 | 方向：右上 |
| `DOWN_LEFT` = 6 | 方向：左下 |
| `DOWN_RIGHT` = 7 | 方向：右下 |
| `dirs4` | `[UP, DOWN, LEFT, RIGHT]` |
| `dirs8` | 四个正交方向后接四个对角方向 |

方向常量用于 `dir(cell, value)` / `nb` / `dr_of`。`dirs4`/`dirs8` 是可迭代的方向列表。

---

## 8. 变量类型（VarType）

每个变量有一个类型，决定其如何被求解与渲染：

| 类型 | 说明 |
|------|------|
| **NORMAL（普通）** | 每点一个待求解的量（最常见）。可设值域 `domain` 与预设 givens。 |
| **CC（区域划分）** | 一类**独立**的区域划分变量，自身在每个 cell 上的值即该 cell 的**区域 id**，内置 4-连通约束，不依赖任何其他变量。始终定义于 cell。无预设。暴露成员 `.id` / `.size` / `.border`。 |
| **CONSTANT（常量）** | 不参与求解；仅在**填写了预设值**的点上存在该常量值，可被表达式引用。 |

### 8.1 区域划分变量（CC）

设变量 `c` 为 CC 类型（cell），4-连通，按需惰性生成成员：

| 表达式 | 说明 |
|--------|------|
| `c` | 直接使用即每个 cell 的区域 id 量集合（等价 `c.id`） |
| `c.id[cell(r,c)]` | 每个 cell 的区域 id；id 相等 ⟺ 连通；id = 区域内最小线性下标 `r*cols+c` |
| `c.size[cell(r,c)]` | 每个 cell 所在区域的 cell 数；O(N²)，谨慎使用 |
| `c.border[edge(...)]` | 每条 edge 的 0/1 整数：当且仅当该 edge 位于**网格边界**、或其两侧 cell 属于**不同区域**（cc id 不等）时为 1 |

编码方式：在 4-连通网格上，每个区域的 `id` 等于其所有 cell 中最小的线性下标
`r*cols+c`（即其唯一根，亦即 CC 变量自身的 z3 量），并通过生成树距离见证
（distance witness）保证同 id 的 cell 必然连通。`.size` / `.border` 仅在被引用时
才生成（`.size` 为每个 cell 一个 If 求和；`.border` 为每条 edge 一个 0/1 量）。

> 注意：旧版本通过普通 cell 变量的 `x.cc` 派生连通分量的写法**已移除**。请改为新建一个 CC 类型变量并引用 `c.id` / `c.size` / `c.border`。

### 8.2 常量变量（CONSTANT）

常量变量不生成 z3 量，仅在其**预设点**上以 Python 整数存在。被 `x[region]` 索引或
迭代时返回这些常量；若索引到**未预设的点**，编译报错
`constant 'x' has no value at the indexed point(s)`。

---

## 9. 变量预设（编译器自动注入）

在执行用户程序前，编译器会为每个 **NORMAL** 变量无条件注入以下约束（不受 `if` 守卫影响）：
- **值域 domain**：若变量带有 `domain = (lo, hi)`，则每个量满足 `lo <= q <= hi`。
- **预填 givens**：若某点有预设值 `g`，则 `q == g`。

CC 变量自身编码连通约束（id/size/border），不接受 domain；若实例把 CC 取值钉成 givens（例如负向检查），则按 `id[p] == given` 注入。CONSTANT 变量
直接携带其预设值，不注入额外约束。求解后：CC 变量回显其区域 id（可「按区域染色」），
`.border` 回显每条 edge 的 0/1，CONSTANT 变量回显其预设值。

---

## 10. 编译与求解 API

包 `decoders.puzzle.dsl` 对外导出：

| 名称 | 说明 |
|------|------|
| `parse(source)` | 解析为 AST `Program` |
| `solve(grid, variables, regions, source, logic="AUTO", params=None, loader=None, timeout_ms=None, run_meta=False)` | 编译并用 z3 求解，返回 `SolveResult`。`run_meta=True` 时执行 `meta:` 块 |
| `compile_only(grid, variables, regions, source, params=None, loader=None)` | **仅编译**：报告约束数与 `print()` 输出，不求解；`run_meta` 恒为 `False` |
| `compile_source(..., run_meta=False)` | 编译入口。默认跳过 `meta:`。`session is None` 且 `run_meta=True` 时报错 |
| `format_model(result)` | 把结果渲染为输出面板可读文本（末尾附 `print():` 块） |
| `is_available()` | z3 是否已安装 |
| `function_table()` | 供 UI 浏览的内置函数/常量/运算符/cc 文档表 |
| `SOLVER_LOGICS` | UI 可选的求解器后端预设元组 |

`params` 将实例数据暴露给 `param("name")`；`loader(name) -> source` 解析 `import`。
上层封装见 `puzzle.runner.solve_instance(spec, instance, run_meta=False)`，它会从 `PuzzleSpec` /
`Instance` 构造好网格、变量、区域与参数。`SolveResult.witnesses` 保存 `emit_witness` 记录。

### 求解器后端（`logic`）
`solve` 的 `logic` 参数选择 z3 后端：
- `"AUTO"`（默认）使用通用 `z3.Solver()`；
- 其他值传入 `z3.SolverFor(logic)` 选择专用逻辑引擎。

`SOLVER_LOGICS` 提供 UI 下拉的固定预设：`AUTO` / `QF_LIA` / `QF_FD` / `QF_IDL` /
`LIA` / `QF_NIA`。无效 logic 会返回 `STATUS_ERROR`。

### SolveResult 状态
| 常量 | 含义 |
|------|------|
| `STATUS_SAT` | 可满足，已找到模型 |
| `STATUS_UNSAT` | 不可满足 |
| `STATUS_UNKNOWN` | 求解器返回 unknown |
| `STATUS_ERROR` | 编译/内部错误（带 `error_line`） |
| `STATUS_COMPILED` | 仅编译成功（`compile_only` 返回） |

z3 未安装时，`solve` / `compile_only` 会返回 `STATUS_ERROR` 并提示安装
`pip install z3-solver`。

---

## 11. 完整示例

```text
# 每行、每列数字 1-4 互不相同（变量 x 已设 domain = 1..4）
for r in rows:
    distinct(r)
for c in cols:
    distinct(c)

# 主对角线之和为 10
sum(x[diag()]) == 10

# 若 (0,0) 为 1，则其右邻不能为 1
x[cell(0,0)] == 1 => x[cell(0,1)] != 1

# 用 let 复用区域
let topleft = grid(2, 2)[0]
distinct(x[topleft])

# 常量 if 折叠 + else（条件在编译期可求值时直接选分支）
let n = count(rows)
if n == 9:
    sum(x[diag()]) == sum(x[ct_diag()])
else:
    true

# 结构化绑定：把一行的前两个 cell 分别绑定
# （此处仅示意；实际可解包任意等长列表）

# 区域划分变量 c（CC 类型，cell）：让每个区域恰好 4 个 cell，且相邻区域颜色不同
for cell0 in row(0):
    c.size[cell0] == 4

# c.border 为 1 表示该 edge 是区域边界（或网格边界）
sum(c.border[col(0)]) >= 1

# 调试：打印第 0 行实际包含的点（点 Compile 即可查看）
print(row(0))
```

---

## 12. 错误类型

| 异常 | 触发阶段 |
|------|----------|
| `LexError` | 词法（非法字符、缩进不一致） |
| `ParseError` | 语法（意外 token、缺少块等） |
| `CompileError` | 编译（类型/越界/不可广播/未知名等） |
| `DSLError` | 上述三者的基类 |

所有错误都带 `line` / `col` 定位信息，便于在编辑器中高亮。

---

## 13. 公共模板库（`puzzle/lib/*.dsl`）

用 `import "模块名"` 引入。运行 `python -m tools.puzzle_rules lib` 可列出全部辅助函数。

| 模块 | 内容 |
|------|------|
| `core` | `eq` / `is_black` / `is_white`、`n_adj4` / `n_adj8` / `n_diag4` / `n_around`、`no2x2` / `no_run` / `no_adjacent`、`connected` / `connected8` / `group_count`、`is_rect_group`、`clue_cells` / `before` / `step` |
| `shading` | 涂黑家族骨架：`island_rule`（黑格不相邻 + 白格连通）、`wall_rule`（黑格连通 + 无全黑 2x2）、`no_mono_2x2`、`adj_black_clue` / `around_black_clue` / `adj8_black_clue`、`region_black_count`、`see_count` / `see4`、`group_touches_border`、`clues_in_distinct_groups` |
| `regions` | `for_each_region_count`、`region_uniform`、`cross_region_pairs`、`in_region_count` / `ordered_pairs_in` / `region_cells_in`、`no_white_crossing_3_regions`、`neighbour_sizes_differ`、`region_size_clue`、`one_clue_per_region`、`regions_are_rectangles` |
| `loops` | `up_edge`/`down_edge`/`left_edge`/`right_edge` 与 `link_*`、`on_loop` / `off_loop` / `turns` / `goes_straight` / `goes_horizontal` / `goes_vertical`、`full_loop` / `loop_visits_all_but`、`arm_len` / `seg_len`、`cell_edge_count` / `inside_flag`、`region_crossings` / `region_visited_cells` / `region_turns` |
| `fill` | `latin`、`boxes`、`region_1_to_n`、`touching_differ` / `adjacent_differ`、`region_consecutive`、箭头辅助 |
| `outside` | `line_count` / `line_runs` / `line_runs_set`（`axis` 0=行 1=列）；旧名 `row_count` / `col_count` 等保留为包装；`row_index_sum` / `col_index_sum` |
| `meta` | `assert_unique(v)`：编译期唯一性判定（须 `run_meta=True`） |

### 常见陷阱

1. `x[p]` 是**列表**，而 `and` 在两个列表上是**合并**而非逻辑与。需要标量时用 `at(x, p)`。
2. 守卫不阻止 `let` 执行。想要“条件性累加”时，条件必须是编译期常量
   （`region_id` / `row_of` / `has_value` / 常量变量的值 / `.size` 都是）。
3. `cc_size` / `cc_width` / `cc_height` 是 O(N²) 编码，大盘面谨慎；`cc_count` 便宜得多。
4. `runs` 是**有序**段长；无序用 `runs_set`，环形用 `runs_cycle`。长度 `-1` 表示 `?`；`runs_set(..., extra=true)` 才允许多余未匹配段（`*`）。`*` 插在有序 `runs` 中间仍未编码。
5. `loop` / `cloop` 会为每个节点生成 id/距离辅助量，同一变量多次调用会复用缓存。
6. `scope:` **不**引入 DSL 变量作用域（与 `for` 不同）。`let s2 = solve()` 写在 `scope:` 内、在块外读 `s2` 是故意支持的写法。
7. 若在 `scope:` 内**首次**触发 `cloop` / `cc.size` 等重型编码，退出时会回滚 `_memo` 与 `_cc_z3`，否则块外再次调用会命中缓存但约束已被丢弃。
8. `exclude` 默认覆盖全部 NORMAL/CC 变量。辅助建模变量在 `model_completion=True` 下可能取任意值，造成虚假多解；用 `unique_over(v1, …)` 限制判定范围。
9. `fn` 捕获的是作用域**拷贝**，之后的 `let` 重绑定看不见；`def` 完全不捕获外层 `let`。不要按 Python 闭包来想。
10. `rev(region)` 保序；把它交给 `and` 合并或任何走 `RegionValue.of` 的路径会**重新排序**。索引 `x[rev(line)]` 与 `for p in rev(line)` 保留逆序。
11. `and`/`or` 不短路。越界取值用 `if not in_grid` 或 `at_or`/`nb`，不要写 `in_grid(...) and at(...)`。`nb` 缺省 0：当 0 是合法值时，越界与「值为 0」无法区分。
