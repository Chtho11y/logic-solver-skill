# Logic Puzzle Studio

逻辑谜题 DSL、求解器和 真正的 Penpa+ 画布。规则保存在 `impls/*.dsl`，题型元数据保存在同名 JSON。

## 启动

需要 Python 3.10+、Node.js 和 npm。安装依赖并构建前端：

```sh
pip install -r requirements.txt
npm --prefix web ci
npm --prefix puzzle/importing install
npm --prefix web run build
python -m puzzle.server --port 8000
```

浏览器打开 `http://127.0.0.1:8000`。开发时可在另一个终端运行 `npm --prefix web run dev`，使用 Vite 提供的地址。

Penpa+ 内部提供导入预设、清空、求解和参数操作；选择绘制元素后，用水平按钮选择目标变量或新增变量。
左侧总览所有变量并控制显隐，右侧编辑 DSL。无需选题即可建立自定义工作区；导入预设后仍能新增变量和修改规则。

## 验证

```sh
python -m unittest discover -s tests -v
python -m tools.check compile
python -m tools.check solve easyasabc fuzuli domino-search
python verify.py easyasabc fuzuli
npm --prefix web test
npm --prefix web run build
python -m tools.status --check
```

- `compile` 检查合成盘面能否编译，不证明规则完整。
- `solve` 验证随附样例 SAT；目前没有样例的题型会跳过。
- `verify.py` 验证样例编译、SAT 和启发式线索影响；失败返回非零退出码。`sample-checked` 不是“完整实现”。
- 答案回归位于 `tests/cases/`；非唯一案例不做固定答案比对，仍检查给定答案被约束接受。
- 前端单元测试覆盖实例参数往返和跨题型隔离。

浏览器集成测试：安装 Playwright 并准备浏览器后运行 `npm --prefix web run test:browser`。
Windows 使用已安装的 Edge，其他平台使用 Playwright Chromium。可通过 `PUZZLE_PLAYWRIGHT`
指定已有 Playwright 包的绝对路径。测试加载真正的 Penpa+，调用实际 Python 解码及代表题求解，并用延迟响应检查竞态、快捷键与布局；
截图输出到忽略版本管理的 `web/.artifacts/`，求解正确性由 Python 测试负责。

## 文档与维护

- [下一步实施计划](docs/NEXT_STEPS.md)：按优先级列出任务及验收标准。
- [实现状态](IMPLEMENTATION_STATUS.md)：自动统计覆盖、部分实现及缺失样例；更新用 `python -m tools.status --write`。
- [前端交互与边界](docs/FRONTEND.md)
- [规则能力缺口](docs/RULE_GAPS.md)
- [语言服务状态](docs/LSP_PLAN.md) / [VS Code 安装说明](editors/vscode/README.md)
- [后端配置](docs/CSPUZ_BACKENDS.md) / [DSL 语法](puzzle/dsl/GRAMMAR.md)

`gen*.py` 是批量规则的生成源，并非废弃代码。修改由其维护的规则时同步修改生成源，避免重新生成覆盖修复。
请勿把空盘 SAT、约束条数增长或一个样例答案一致当作规则完整性的证明。
