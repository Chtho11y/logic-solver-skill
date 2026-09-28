"""Generate file coverage, without claiming rules are fully verified.

python -m tools.status --write
python -m tools.status --check
"""
import argparse
import json
from pathlib import Path

from puzzle.registry import catalogue
from tests.puzzles import iter_cases

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / 'IMPLEMENTATION_STATUS.md'


def report():
    rules = catalogue()
    specs = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'impls').glob('*.json'))}
    implemented = {key for key in specs if (ROOT / 'impls' / f'{key}.dsl').is_file()}
    missing = sorted({rule['key'] for rule in rules} - implemented)
    partial = [key for key, spec in specs.items() if spec.get('unencodedClues') or '部分实现' in spec.get('notes', '')]
    no_sample = sorted(key for key in implemented if not (ROOT / 'impls/samples' / f'{key}.json').is_file())
    cases = list(iter_cases())
    matches = sum(bool(case.get('answer')) and case.get('unique', True) is not False for _, case, _ in cases)
    names = lambda keys: ' '.join(f'`{key}`' for key in keys) or '无'
    return f'''# 项目实现状态

由 `python -m tools.status --write` 从目录、元数据及测试案例生成；
`python -m tools.status --check` 检查是否过期。这里统计文件覆盖，不代表完整规则验收。

## 覆盖情况

| 项目 | 数量 | 口径 |
|---|---:|---|
| 规则目录 | {len(rules)} | rules.txt |
| 已有实现 | {len(implemented)} | 同时有 JSON 与 DSL，占 {len(implemented) / len(rules):.1%} |
| 尚未实现 | {len(missing)} | 目录内缺少实现 |
| 标注部分实现 | {len(partial)} | notes 或 unencodedClues 声明缺口 |
| 随附样例 | {len(implemented) - len(no_sample)} | 已实现题型中有 sample 的数量 |
| 缺少随附样例 | {len(no_sample)} | 不等同于没有任何测试案例 |
| 答案回归案例 | {len(cases)} | 覆盖 {len({key for key, _, _ in cases})} 个题型 |
| 启用答案比对 | {matches} | 有答案且没有标记 unique=false |

未标注“部分实现”不等于已证明完整。SAT 只证明满足当前编码；
答案比对也不能替代非法解反例和第二解检查。

## 部分实现

{names(partial)}

具体缺口以 `impls/<key>.json` 为准，能力规划见 [规则缺口](docs/RULE_GAPS.md)。

## 缺少随附样例

{names(no_sample)}

## 尚未实现

{names(missing)}

## 已具备的工程能力

- DSL 解析、编译、共享规则库及 cspuz 后端适配。
- Penpa+ / puzz.link 图层导入，原生 Penpa+ 画布与题型绑定。
- 中央棋盘工作区包含题型、尺寸、参数、导入、求解及结果；右侧编辑 DSL。
- VS Code 语法高亮、诊断、悬浮、跳转、补全、签名帮助和引用查找。

## 待办顺序

1. 完善 Penpa 标记与答案映射、保护手工答案、细分图层显隐。
2. 为已有规则补充真实题答案、非法解反例和唯一性检查，补齐缺失样例。
3. 将同步 HTTP 求解迁移为可取消的独立进程任务；当前长任务仍阻塞服务。
4. 统一前后端绑定规则与测试案例，再扩展形状、区域内连通和路径能力。
5. 接入 Web 语言服务，扩充尚未实现的题型。

具体实施顺序及验收标准见 [下一步计划](docs/NEXT_STEPS.md)。
运行与测试入口见 [README](README.md)。测试通过数量应引用实际运行结果，
不要将本表当成测试报告。旧阶段报告可通过 Git 历史查阅。
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    content = report()
    if args.write:
        TARGET.write_text(content, encoding='utf-8')
    elif args.check:
        if not TARGET.exists() or TARGET.read_text(encoding='utf-8') != content:
            print('Implementation status is stale; run python -m tools.status --write')
            return 1
        print('Implementation status is current')
    else:
        print(content)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
