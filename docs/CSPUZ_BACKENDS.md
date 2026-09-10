# cspuz 多后端与扩展数据结构

项目的 DSL 不再生成 Z3 AST。现在的调用链是：

`DSL AST -> ConstraintModel -> cspuz expressions -> concrete backend`

`puzzle/backends/base.py` 定义编译器所需的最小约束接口，
`puzzle/backends/cspuz.py` 是当前实现，`puzzle/backends/registry.py`
负责发现和选择具体求解器。

## 安装

基础环境（cspuz 建模层和 Z3 回退）：

```text
pip install -r requirements.txt
```

`requirements.txt` 将 cspuz 固定到经过本项目验证的 Git commit
`1d074431984148944dde4c7d5d1636ac9cfe29e2`。cspuz_core
不是 PyPI 的普通预编译依赖；Windows 上需要 Rust、C++ 编译器，并递归拉取其
Git 子模块后执行 `pip install .`：

```text
git clone --recursive https://github.com/semiexp/cspuz_core.git
git -C cspuz_core checkout 0a51e8973b43f5394bce787f93601b9b19776fdf
git -C cspuz_core submodule update --init --recursive
pip install ./cspuz_core
```

## 选择后端

- `auto`：无 timeout 时按 `cspuz_core -> z3` 选择；请求正数 timeout 时会选择
  能落实超时的 Z3，避免 cspuz_core 无限阻塞服务。
- `cspuz_core`：推荐，支持原生图约束但不支持进程内 timeout；显式选择时不会回退。
- `z3`：便于安装的默认回退，并保留毫秒级 timeout/unknown 状态。
- `csugar`：安装 `pycsugar` 后可选，支持原生图约束。
- `sugar` / `sugar_extended`：POSIX/WSL 中设置 `CSPUZ_BACKEND_PATH` 后可选。
  固定版本 cspuz 使用 `/dev/stdin`，因此原生 Windows 会将它们标为不可用。

HTTP 的 `GET /api/health` 返回默认后端以及每个后端的 `available`、`reason`、
`supportsTimeout` 和 `supportsGraphPrimitives`。求解请求可指定：

```json
{
  "instance": {},
  "backend": "z3",
  "timeoutMs": 60000
}
```

显式指定但不可用的后端返回 `status: "error"` 和具体原因。旧请求中的
`logic: "AUTO"` 仍等价于 `backend: "auto"`；其他 Z3 logic 名称不再接受。

## 当前已接入

- 有限域整数标量，以及用整数 `0/1` 表示的现有布尔变量。
- cell、corner、edge 三种点格上的变量与区域。
- 列表广播、条件表达式、计数、all-different、比较和布尔组合。
- 有界线性常数乘法，以及对正整数常数的符号除法/取模。
- 4/8 邻接连通分量、分区 id/size/border、边连通和单回路的兼容编码。
- `find_answer()` 完整模型读取，保持现有前端 `values/kinds` 协议。

这些能力覆盖当前 `impls/` 下的全部 DSL，无需修改题型文件。

## 可新增支持的数据结构

以下结构由 cspuz 提供，但尚未全部暴露为本项目 DSL 类型或 builtin：

- 一维/二维数组：`BoolArray1D`、`BoolArray2D`、`IntArray1D`、
  `IntArray2D`。可用于原生网格切片、逐元素约束和答案键。
- 网格边框：`BoolGridFrame` 和 `BoolInnerGridFrame`，同时保存 horizontal /
  vertical 边，支持 cell/vertex 邻边、内外格对偶和单回路。
- 任意图：`cspuz.graph.Graph`，可表示非矩形棋盘、传送边、岛屿邻接图或
  题目特有网络。
- 连通点集：`active_vertices_connected`，可直接表达黑格、白格或指定值格
  的整体连通。
- 非相邻且不分割点集：`active_vertices_not_adjacent_and_not_segmenting`，
  适合同时要求禁邻接和补集连通的涂黑题。
- 无环边集：`active_edges_acyclic`，可表示树、森林和禁止闭环的线路。
- 单回路：`active_edges_single_cycle`，可配合 `BoolGridFrame` 表示格线回路。
- 单路径：`active_edges_single_path`，可表达给定或可求端点的连续路线；当前
  cspuz 在关闭图原语时尚未实现其普通约束展开，因此只适合
  `cspuz_core`/`csugar`。
- 可交叉线路：`active_edges_single_cycle_crossable` 和
  `active_edges_connected_crossable`，可表达允许十字交叉的单环或连通网。
- 连通分区：`division_connected`，支持网格/任意图、固定分组数和指定根。
- 可变分组与边界：`division_connected_variable_groups` 以及
  `division_connected_variable_groups_with_borders`，可同时求区域编号、
  区域大小和边界边。
- 可判定答案键：`Solver.add_answer_key()` + `Solver.solve()` 可返回
  irrefutable 值；无法由约束唯一确定的位置保留为 `None`。
- 题目生成结构：`ArrayBuilder2D`、`SegmentationBuilder2D` 和
  `generate_problem()`，可在现有求解器之上增加唯一解题目生成。
- 推理分析：`Analyzer` 可用于记录不可否定事实及推理步骤。
- 题目序列化组合器：`Grid`、`OneOf`、`Spaces`、`HexInt` 等，可扩展
  puzz.link / pzpr 风格 URL 的导入导出。

建议下一步优先增加原生布尔变量和二维数组，再将 `loop`、`cloop` 与简单连通
builtin 切换到图原语；这样能减少辅助整数和手写生成树约束，同时保持 DSL
表面语法不变。

## 兼容边界

cspuz 的整数变量必须有有限上下界。项目变量必须声明 spec `domain`，CC 和
内部见证变量由编译器推导可靠边界；无法推导时会在编译期报错，不会套用猜测范围。
真正的非线性乘法（两个符号表达式相乘）不在 cspuz 的约束子集中，也会给出明确
错误；当前内置题型不使用该能力。

cspuz_core 和 csugar 可以使用原生图约束。Z3 与 Sugar 会使用 cspuz 的普通约束
展开（`active_edges_single_path` 除外）。后端配置在编译前确定，并通过进程内
锁保护；每次调用后恢复，避免一个请求改变后续请求的默认行为。

cspuz 只能直接读取变量的 `.sol`。若以后允许把任意派生表达式发布到前端，
适配层必须先将表达式重化为有界辅助变量并添加等式，不能直接读取表达式。
