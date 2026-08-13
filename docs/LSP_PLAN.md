# Puzzle DSL — LSP 服务器与 VSCode 插件实现规划

目标：为 `puzzle/lib/*.dsl` 与 `impls/*.dsl` 提供**语法高亮、悬浮提示、定义跳转**三项核心能力，并顺带获得诊断、补全、符号大纲。

本规划基于对现有代码的实地勘察撰写，所有模块名、函数名、字段名均已核对。

---

## 1. 现有资产盘点

这是本方案能低成本落地的根本原因：**编译器前端已经把 LSP 需要的位置信息全部备好了**。

| 现有资产 | 位置 | 可直接支撑的 LSP 能力 |
|---|---|---|
| `tokenize(src) -> list[Token]`，`Token(type, value, line, col)` | `puzzle/dsl/lexer.py`、`tokens.py` | **Semantic Tokens**（精确高亮） |
| `parse(src) -> Program`，**所有 AST 节点带 `line`/`col`** | `puzzle/dsl/parser.py`、`ast_nodes.py` | 定义跳转、符号大纲、引用查找 |
| `DefStmt(name, params, body)` / `ImportStmt(path)` / `Name(ident)` / `Call(callee)` / `Member(attr)` | `ast_nodes.py` | 符号定义与引用的全部载体 |
| `LexError` / `ParseError` / `CompileError`，均带 `.message` `.line` `.col` | `puzzle/dsl/errors.py` | **Diagnostics** |
| `function_table() -> list[DocEntry]`，`DocEntry(name, signature, doc, category)` | `puzzle/dsl/builtins.py` | 内置函数/常量/运算符的**悬浮提示 + 补全** |
| `BUILTIN_FUNCTIONS` 字典、`DEBUG_BUILTINS` 集合 | `puzzle/dsl/builtins.py` | 区分正式 API 与调试 API |
| `make_loader()`：先查 `LIB_DIR` 再查 `IMPLS_DIR`，带路径逃逸校验 | `puzzle/spec.py` | `import "shading"` → **跳转到文件** |
| `LIB_DIR = puzzle/lib`、`IMPLS_DIR = impls`、`SAMPLES_DIR = impls/samples` | `puzzle/spec.py` | 工作区索引范围 |
| `compile_only(grid, variables, regions, src, params, loader)` | `puzzle/dsl/__init__.py` | 第二档**语义诊断** |
| `load_spec(key)` / `load_sample(key)` / `build_*` | `puzzle/spec.py` | 为 `.dsl` 找到同名 `impls/<key>.json` 上下文 |
| 库函数的中文文档注释（`def` 体内第一行 `#`） | `puzzle/lib/*.dsl` | 用户函数的**悬浮文档** |
| `puzzle/server.py` 全程只用 `http.server`（stdlib） | `puzzle/server.py` | 确立"零三方依赖"工程惯例 |
| `web/` = React 18 + Vite 5 + TS 5.6（npm） | `web/package.json` | 插件端 TS 工具链可复用同一套约定 |

**现状确认**：仓库内不存在任何 `tmLanguage` / TextMate / Monaco / CodeMirror 相关文件 —— 高亮部分是全新开发，无历史包袱。

---

## 2. 关键设计决策

### D1. LSP 服务端：手写 stdlib JSON-RPC，不引入 `pygls`

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| `pygls` / `lsprotocol` | 协议完备、装饰器 API 省事 | 引入两个三方依赖及其传递依赖 | ✗ |
| **stdlib 手写 JSON-RPC over stdio** | 与 `puzzle/server.py` 的零依赖风格一致；`pip install` 无需求；打包进插件极简 | 需自己写约 200 行帧解析与派发 | **✓ 采用** |

理由：`puzzle/server.py` 已证明本项目坚持 stdlib（z3 都是可选依赖）。LSP 的 stdio 传输就是 `Content-Length` 头 + JSON 体，手写成本可控，换来的是"任何有 Python 的机器上开箱即用"。

### D2. 高亮采用**双层**：TextMate 语法 + Semantic Tokens

- **第 1 层 TextMate**（`syntaxes/puzzle-dsl.tmLanguage.json`）：服务器未启动、大文件、或 Python 缺失时的兜底，纯正则，瞬时生效。
- **第 2 层 Semantic Tokens**（服务端 `tokenize` 驱动）：真实词法器输出，能正确区分"内置函数 / 用户函数 / 参数 / 局部变量 / 谜题变量"，这是正则做不到的。

两层叠加是 VSCode 的标准做法（语义层覆盖语法层），既快又准。

### D3. LSP 自建轻量符号索引，**不复用 `Compiler`**

`Compiler._exec_import` 会把导入模块**内联执行**，且 `compile_only` 强制要求 `grid` / `variables` / `regions` —— 它是"求解器前端"，不是"语言服务"。

因此索引层独立实现：对每个 `.dsl` 只做 `parse()`，遍历顶层与嵌套 `DefStmt` 收集符号。代价极低（纯语法分析，无需 z3、无需谜题实例），且天然支持"文件尚有编译错误但仍能跳转"。

### D4. 诊断分两档

| 档位 | 触发条件 | 手段 | 覆盖 |
|---|---|---|---|
| **T1 语法** | 任何 `.dsl`，随敲随算 | `tokenize` + `parse` | 词法/语法错误 |
| **T2 语义** | 存在同名 `impls/<key>.json` **且**有 `samples/<key>.json` | `compile_only` | 未知名称、类型错误、参数数量 |

`puzzle/lib/*.dsl` 是库文件，没有配套 `json`，**只能享受 T1** —— 这是必须向用户说清的行为边界，否则会被误认为 bug。

### D5. 文档注释必须从**原始文本**提取

`lexer.py` 直接丢弃 `#` 注释，不产生 token。而库函数的文档正是 `def` 体内第一行注释：

```
def island_rule(x):
    # "涂黑格互不相邻 + 留白连通" (Hitori / Kurodoko / Heyawake ...)
    blacks_isolated(x)
```

所以悬浮提示的取文档逻辑是：拿到 `DefStmt.line` → 回到**源文件行数组** → 向下扫描连续 `#` 行。不能指望 AST。

### D6. 坐标转换（易错点，单独立项）

- 本项目 `Token.line` / `Token.col` 均为 **1 基**；LSP 的 `Position` 是 **0 基**。转换：`lsp_line = line - 1`，`lsp_char = col - 1`。
- LSP 默认 `positionEncoding` 为 **UTF-16 code unit**，而 Python 的 col 是 **code point**。CJK 在 BMP 内两者相等，但 emoji / CJK 扩展 B 区会错位。
- 处置：`initialize` 时优先协商 `positionEncoding: "utf-32"`（LSP 3.17，等价 code point，零转换）；客户端不支持时回落到 UTF-16 并对含非 BMP 字符的行做一次换算。

---

## 3. 架构

```
┌──────────────────── VSCode ────────────────────┐
│  editors/vscode  (TypeScript)                  │
│   ├─ package.json     语言注册 / 激活事件      │
│   ├─ syntaxes/*.tmLanguage.json   第1层高亮    │
│   ├─ language-configuration.json  注释/括号/缩进│
│   └─ src/extension.ts  启动并管理服务器进程    │
└───────────────┬────────────────────────────────┘
                │  stdio: Content-Length + JSON-RPC 2.0
                ▼
┌──────────── python -m puzzle.lsp ──────────────┐
│  puzzle/lsp/                                   │
│   ├─ __main__.py   入口                        │
│   ├─ rpc.py        帧读写 + 请求派发           │
│   ├─ server.py     能力声明 + 各 handler       │
│   ├─ workspace.py  文档缓存（增量同步）        │
│   ├─ index.py      跨文件符号索引              │
│   ├─ docs.py       文档聚合(内置表 + # 注释)   │
│   └─ convert.py    位置/区间换算               │
└───────────────┬────────────────────────────────┘
                │  仅调用现有稳定 API，不改其行为
                ▼
  puzzle.dsl.tokenize / parse / compile_only
  puzzle.dsl.builtins.function_table / BUILTIN_FUNCTIONS
  puzzle.spec.make_loader / load_spec / load_sample / LIB_DIR / IMPLS_DIR
```

---

## 4. 新增文件清单

```
puzzle/lsp/                       ← 新增，纯 stdlib
    __init__.py
    __main__.py
    rpc.py
    server.py
    workspace.py
    index.py
    docs.py
    convert.py

editors/vscode/                   ← 新增，TS
    package.json
    tsconfig.json
    language-configuration.json
    syntaxes/puzzle-dsl.tmLanguage.json
    src/extension.ts
    README.md
    .vscodeignore

tests/lsp/                        ← 新增
    test_rpc.py
    test_index.py
    test_hover.py
    test_definition.py
    test_semantic_tokens.py
```

对既有代码的改动：**默认为零**。第 8 节列出的上游微调均为可选增强项。

---

## 5. 分期实施

### M0 — 骨架贯通（约 0.5 天）
- `rpc.py`：`Content-Length` 帧读写、JSON-RPC 请求/通知/响应、`initialize` / `initialized` / `shutdown` / `exit`。
- `workspace.py`：`didOpen` / `didChange`（先做全量 `TextDocumentSyncKind.Full`）/ `didClose`。
- **验收**：VSCode 打开 `.dsl` 时状态栏显示服务器 running，输出面板无异常；`shutdown` 能干净退出。

### M1 — 语法高亮（约 1 天）
- TextMate 语法：关键字 `if elif else for in let and or not true false def return import`；运算符 `== != <= >= && || =>` 与 `+-*/%<>=()[],:^!.`；`#` 行注释；`"..."` 字符串；十进制整数；`def` 后名字识别为 `entity.name.function`。
- `textDocument/semanticTokens/full`：由 `tokenize` 驱动，映射见下表。
- **验收**：`puzzle/lib/shading.dsl`、`impls/nurikabe.dsl` 高亮正确；故意写错语法时高亮不崩（词法器抛错则回落到 TextMate 层）。

**Token → Semantic Token 映射**

| 本项目 token | 判定 | LSP semantic type | modifiers |
|---|---|---|---|
| `T_KEYWORD` | 在 `KEYWORDS` 内 | `keyword` | — |
| `T_KEYWORD` | `true` / `false` | `keyword` | — |
| `T_INT` | — | `number` | — |
| `T_STR` | — | `string` | — |
| `T_OP` | — | `operator` | — |
| `T_NAME` | 紧跟 `def` 之后 | `function` | `declaration` |
| `T_NAME` | 在 `BUILTIN_FUNCTIONS` 且下一 token 为 `(` | `function` | `defaultLibrary` |
| `T_NAME` | 在 `DEBUG_BUILTINS` | `function` | `defaultLibrary deprecated` |
| `T_NAME` | 命中索引中的用户 `def` 且下一 token 为 `(` | `function` | — |
| `T_NAME` | 当前 `def` 的形参名 | `parameter` | — |
| `T_NAME` | `let` / `for` 绑定的名字 | `variable` | `definition` |
| `T_NAME` | 同名 `impls/<key>.json` 的 `variables[].name` | `variable` | `readonly` |
| `T_NAME` | 其余 | `variable` | — |
| `T_NEWLINE` `T_INDENT` `T_DEDENT` `T_EOF` | — | 不发出 | — |

### M2 — 诊断（约 0.5 天，为 M3/M4 提供索引基础）
- T1：`tokenize` + `parse`，异常 → 一条 `Diagnostic`（`severity=Error`，range 取 `line/col` 到行尾）。
- T2：文件位于 `impls/` 且存在同名 json + sample → `compile_only`，`CompileError` 转诊断。
- 去抖 200ms；`didSave` 强制全量重算。
- **验收**：删掉 `nurikabe.dsl` 里一个右括号 → 立刻红波浪线且位置正确；把 `wall_rule` 改名 → T2 报"unknown name"。

> **已知限制**：`parser.py` 与 `Compiler` 都是遇错即抛（fail-fast），故一次只能报**首个**错误。多错并报需要错误恢复，属独立课题（见第 8 节 U3）。

### M3 — 悬浮提示（约 1 天）
按优先级依次命中：

1. **内置函数 / 常量 / 运算符** → `function_table()` 的 `DocEntry`，渲染为：
   ```
   (builtin) no2x2(x, v) -> constraint          ← signature
   ─────────────────────────────────────
   {doc}                                        ← doc
   Category: Shading                            ← category
   ```
   `DEBUG_BUILTINS` 额外标注"⚠ 调试用，勿用于正式规则"。
2. **用户函数**（本文件或已导入模块）→ 签名由 `DefStmt.name` + `params` 重建，文档由 D5 的注释扫描取得，并附来源 `puzzle/lib/shading.dsl:59`。
3. **谜题变量**（`x` / `n` / `e` / `c` 等）→ 读同名 `impls/<key>.json`，展示该变量的 `kind` / `type` / `domain` / `doc`。这一项对本 DSL 尤其有价值，因为变量语义完全由 spec 定义。
4. **`import "name"`** → 展示解析到的绝对路径 + 该模块导出的 `def` 列表。
5. 未命中 → 返回 `null`（不要返回空 Hover，否则 VSCode 会闪一个空气泡）。

- **验收**：悬停 `island_rule` 显示其中文文档与 `puzzle/lib/shading.dsl` 出处；悬停 `no2x2` 显示内置签名；在 `nurikabe.dsl` 悬停 `x` 显示 `cell / normal / domain [0,1]`。

### M4 — 定义跳转（约 1 天）

| 光标所在 | 跳转目标 | 数据来源 |
|---|---|---|
| 用户函数调用 `island_rule(x)` | 其 `DefStmt` 所在文件与行 | 符号索引 |
| `import "shading"` 的字符串 | `puzzle/lib/shading.dsl` 首行 | 复用 `make_loader` 的解析规则 |
| 形参 / `let` / `for` 绑定 | 其绑定处 | 见下方限制 |
| 谜题变量 `x` | `impls/<key>.json` 中该变量的定义位置 | JSON 内文本搜索定位 |
| 内置函数 | 不跳转，返回 `null`（由 Hover 承担说明职责） | — |

解析顺序遵循编译器的名称查找链（`_eval_name`：局部作用域 → 区域值 → 常量 → 用户函数 → 内置），保证跳转结果与实际求解语义一致。

- 同时实现 `textDocument/documentSymbol`（大纲，列出全部 `def`）与 `workspace/symbol`（全局按名搜函数），二者与跳转共用索引，几乎零边际成本。
- **验收**：在 `impls/nurikabe.dsl` 的 `wall_rule` 上 F12 → 跳到 `puzzle/lib/shading.dsl` 对应 `def`；在 `import "shading"` 上 F12 → 打开该库文件。

### M5 — 打包与体验（约 0.5 天）
- `python` 解释器发现顺序：设置项 `puzzleDsl.pythonPath` → `python3` → `python`；失败时弹出可操作的错误提示而非静默。
- 设置项：`puzzleDsl.enable`、`puzzleDsl.diagnostics.level`（`off|syntax|semantic`）、`puzzleDsl.trace.server`。
- `vsce package` 产出 `.vsix`；README 写明"需本机 Python 3.10+，无需 pip 安装任何包"。
- **验收**：全新克隆仓库 → 装 `.vsix` → 打开 `.dsl` 三项功能可用。

**合计约 4.5–5 人日**（估算，不含 M2 之外的诊断增强与第 8 节可选项）。

---

## 6. 顺带获得的能力（低成本，建议一并做）

- **补全** `textDocument/completion`：`function_table()` 全量 + 索引内用户函数 + 当前作用域变量。约 0.5 天。
- **签名帮助** `signatureHelp`：`DocEntry.signature` 已是现成字符串。约 0.3 天。
- **引用查找** `references`：索引已含调用点，遍历即可。约 0.3 天。
- **格式化**：**不建议**。DSL 是缩进敏感语言，实现一个不破坏 `INDENT`/`DEDENT` 语义的 formatter 风险收益比很差。

---

## 7. 符号索引设计

```
index.py
  build(root)                      启动时扫描 puzzle/lib/*.dsl 与 impls/*.dsl
  symbols: dict[str, list[Symbol]] 函数名 → 定义（可能同名多处）
  imports: dict[uri, list[str]]    文件 → 其 import 的模块名
  Symbol(name, params, uri, line, col, module, doc)
```

- **构建**：仅 `parse()`，递归遍历语句树收集 `DefStmt`（注意嵌套 `def` —— `gen_shade1.py` 生成的 `nothree.dsl` 就在顶层语句之后才写 `def`，编译器靠 `_exec_block` 的声明提升支持"先用后定义"，索引必须同样不依赖出现顺序）。
- **可见性**：解析引用时，候选集 = 本文件符号 ∪ 所有**递归** import 到的模块符号。因为 `_exec_import` 是在全局作用域执行的，导入是传递可见的，索引须与此一致。
- **失效策略**：`didChange` 只重建当前文件；`didSave` 若该文件被他人 import，则重建其反向依赖。
- **鲁棒性**：单个文件 parse 失败不得中断整体索引 —— 捕获异常、跳过该文件、保留上一次成功结果。

---

## 8. 建议的上游微调（全部可选、向后兼容）

| 编号 | 改动 | 解锁能力 | 风险 |
|---|---|---|---|
| **U1** | `DefStmt` 增加 `name_line` / `name_col` | 跳转/高亮精确落在**函数名**而非 `def` 关键字 | 极低：新增可选字段，`parser.py` 一处赋值 |
| **U2** | `params` / `LetStmt.targets` / `ForStmt.vars` 由 `list[str]` 改为带位置的结构 | 形参与局部变量的**精确跳转、重命名、作用域高亮** | 中：`compiler.py` 多处消费这些字段，需同步适配 |
| **U3** | 解析器错误恢复（跳到下一行继续） | **一次报出多个**语法错误 | 中高：触及 `parser.py` 主循环 |
| **U4** | `lexer.py` 可选保留注释 token | 免去 D5 的"回读源文本"变通 | 低：加开关，默认关闭 |

**当前限制的诚实说明**：不做 U2 的话，形参与 `let`/`for` 局部变量**无法精确跳转**（只能定位到其所属 `def` 的行）。M1–M5 全部功能不依赖任何上游改动即可交付，U1 建议顺手做（一行赋值），U2/U3 视后续需求再评估。

---

## 9. 协议消息清单

**服务端声明的 capabilities**
```
textDocumentSync            : Full（M0）→ Incremental（可选优化）
semanticTokensProvider      : { legend, full: true }
hoverProvider               : true
definitionProvider          : true
documentSymbolProvider      : true
workspaceSymbolProvider     : true
completionProvider          : { triggerCharacters: ["(", ",", "\""] }   ← 若做第6节
diagnosticProvider          : 采用 push 模式（publishDiagnostics）
positionEncoding            : 优先 "utf-32"，回落 "utf-16"
```

**实现的请求/通知**：`initialize`、`initialized`、`shutdown`、`exit`、`textDocument/didOpen|didChange|didSave|didClose`、`textDocument/semanticTokens/full`、`textDocument/hover`、`textDocument/definition`、`textDocument/documentSymbol`、`workspace/symbol`、`textDocument/publishDiagnostics`（出）。

---

## 10. 测试策略

**天然优势：仓库已有 52 个 `.dsl` 文件（6 个库 + 46 个实现）可直接充当测试语料。**

| 层级 | 做法 |
|---|---|
| 单元 | `rpc.py` 帧解析（含分包、UTF-8 多字节、超长头）；`convert.py` 的 1基↔0基与 UTF-16 换算 |
| 索引 | 对全部 52 个 `.dsl` 建索引，断言 `puzzle/lib/shading.dsl` 中每个 `def` 都被收录且行号正确 |
| 快照 | 对 `shading.dsl` / `nurikabe.dsl` 的 semantic tokens、hover、definition 结果做 golden 对比 |
| 端到端 | 起子进程，按真实 LSP 时序发 `initialize → didOpen → hover → definition → shutdown`，断言响应；**不依赖 VSCode** |
| 回归 | 断言"对 52 个文件逐一 didOpen，服务器不抛未捕获异常、不产生 T1 诊断"——这同时也是 DSL 语料的健康检查 |

最后一条尤其有价值：它能顺带发现库文件里的语法退化。

---

## 11. 风险与规避

| 风险 | 影响 | 规避 |
|---|---|---|
| 用户机器无 Python / 版本过低 | 服务器起不来 | TextMate 层仍保证基础高亮；明确弹窗提示并给出设置项 |
| `puzzle` 包不在 `sys.path` | import 失败 | 以工作区根为 `cwd` 启动 `python -m puzzle.lsp`；启动前探测 `puzzle/dsl/__init__.py` 是否存在 |
| `compile_only` 在大盘面上偏慢 | 输入卡顿 | T2 仅在 `didSave` 触发（不随敲字跑）；加超时与去抖 |
| 库文件无 json 上下文，用户误以为诊断失灵 | 认知困惑 | 状态栏标注当前档位；README 明确 T1/T2 边界 |
| `.dsl` 扩展名与他人插件冲突 | 高亮被抢 | 语言 id 用 `puzzle-dsl`；仅在工作区含 `puzzle/lib/` 时激活 |
| 索引随文件增长变慢 | 启动延迟 | 52 文件量级下纯 parse 是毫秒级；必要时按 mtime 缓存 |

---

## 12. 验收标准

1. 打开 `puzzle/lib/shading.dsl`：关键字、字符串、注释、`def` 名、内置函数各具区分色。
2. 悬停 `no2x2` → 显示内置签名 + 文档 + 分类；悬停 `island_rule` → 显示其中文注释文档 + 定义出处。
3. 在 `impls/nurikabe.dsl` 的 `wall_rule` 上 F12 → 跳转至 `puzzle/lib/shading.dsl` 的对应 `def` 行。
4. 在 `import "shading"` 上 F12 → 打开该库文件。
5. 故意造语法错 → 200ms 内出现位置准确的红波浪线；修正后消失。
6. `Ctrl+Shift+O` 列出当前文件所有 `def`。
7. 对 52 个既有 `.dsl` 逐一打开，服务器无未捕获异常、无误报 T1 诊断。
8. 全新环境装 `.vsix` 后，除 Python 3.10+ 外无需任何额外安装。

---

## 13. 建议动工顺序

先做 **M0 → M1**（高亮立刻可见，正反馈最强）→ **M2**（诊断，顺带建起索引）→ **M4**（跳转，依赖索引）→ **M3**（悬浮，依赖文档聚合）→ **M5**（打包）。

M3 放在 M4 之后是因为悬浮的文档聚合逻辑（D5 的注释扫描 + spec 变量读取）比跳转更琐碎，而跳转能更早验证索引正确性。
