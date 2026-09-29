# 验证与交付

按变更选择验证范围。规则解释不需要启动整个应用；实现完整前端与 DSL 时，需要验证数据、语义和实际交互。

## 规则证据

对新规则至少准备一个有实际线索/区域的样例和关键规则反例。选择能暴露错误的检查：

- 固定已知合法答案，确认 SAT，防止过度约束。
- 固定违反某条规则的答案，确认 UNSAT，防止漏约束。反例最好保留其他条件合法，以便定位。
- 改变一个数字应改变允许答案时，测试这一点；不要只比较约束条数。
- 连通检查可用独立 BFS，段长可按固定序列直接计数；小盘面枚举是很好的对照。不要用被测 helper 本身计算期望值。
- 需要宣称唯一时，将所有**可见答案变量**与已知解逐项比较，用 `any([...])` 要求至少一项不同，再求解。排除给定常量和辅助编号，避免将辅助变量的多种表示算成多个答案。

示意：求解 `x` 后，在原 DSL 后追加 `any([x[cell(0,0)] != 1, x[cell(0,1)] != 0, ...])`；包含全部答案位置，不能只排除一个格子。
多解是规则/题目属性，不自动是错误；用户要求唯一时才需继续调整题目或定位漏约束。

`tests/cases/` 适合普通整数线索与固定答案回归，但 `unique: true` 本身不执行第二解证明；列表线索当前应参照 `tests/test_preset_rules.py` 用 `Instance` 写直接测试。
示例验证脚本见 [example.md](example.md)，它同时演示穷举对照和第二解检查。

## 后端与命令

从仓库根目录运行，显式选择已安装的后端：

```sh
python -m tools.check compile <key>
python -m tools.check solve <key> --backend z3 --timeout 10000
python -m unittest tests.test_<相关模块>
```

`tools.check compile` 是合成数据编译检查，不是原生后端的执行测试；当前其 `--backend` 参数只用于 solve 分支。
修改公共编译/绑定能力时扩大到相关回归，必要时运行 `python -m unittest discover -s tests`。
新增或改变预设状态时运行 `python -m tools.status --write`，随后 `--check`。

本机有 cspuz Python 包和 Z3、但没有 cspuz_core 时：

- 用真实 cspuz 模型及显式 Z3 运行语义、反例和小盘面穷举。
- 原生算子表达式检查只能证明生成路径，不等于原生求解成功。
- 在有 cspuz_core 的环境显式运行同一批测试，检查实际返回的 backend；本机 unavailable 项如实跳过，不静默切换后端再报通过。
- 若没有任何可用求解器，仍可编写并检查配置/DSL，但交付时明确求解未验证；不要用 mock SAT 完成验收。

## 前端闭环

只使用已有层也要做一次目标预设的真实操作。核对：

1. 预设列表能发现新 key，导入后变量、默认参数、样例和 DSL 一致。
2. 选择正确的“绘制到”变量后画一笔；新建变量后第一笔归属正确。同工具多变量的内容不串层。
3. 实际提交 `/api/solve`，确认读取的是当前文档；答案回填到正确工具、位置、颜色和变量。
4. 显隐不修改数据；编辑线索/参数/DSL 后旧答案失效，手工 Solution 答案仍保留。
5. 使用特殊标记、列表线索或区域时，检查导入和样例往返；不要仅靠截图判断绑定。

可复用现有测试：

```sh
npm --prefix web test
npm --prefix web run build
npm --prefix web run test:browser
```

浏览器测试需要 Playwright 与浏览器；Windows 使用 Edge。可通过 `PUZZLE_PLAYWRIGHT` 指定已安装包的路径，不把某台机器的绝对路径写进项目。
现有浏览器用例在 `web/tests/browser.cjs` 中明确列出代表题，新预设不会自动得到浏览器覆盖；补目标案例或实际手动完成上述操作。
单纯跑通已有题型不能声称新题型通过。

## 启动和交付

依赖已安装时复用。按需安装与构建：

```sh
python -m pip install -r requirements.txt
npm --prefix web ci
npm --prefix puzzle/importing install
npm --prefix web run build
python -m puzzle.server --port 8000
```

确认服务实际启动后再提供 `http://127.0.0.1:8000/`。端口被占用时先确认已有服务是什么，不随意终止；可选择空闲端口。
修改后端后，已有 Python 进程不会因重新构建前端而自动载入新代码。仅修改预设文件通常随 API 请求重新读取。

开发前端可另用 `npm --prefix web run dev`；仍需 API 服务，地址以启动输出为准。
当前 HTTP 求解是同步的，耗时约束应设置合理超时，不承诺已有取消/并行任务能力。

最终回复应让用户立即操作：入口、预设名、绘制变量和线索格式、交付文件、实际验证结果以及必要限制。
不重复整个实现过程，也不将“文件已写好”说成“服务已启动”。提交/推送/发布按用户授权执行。
