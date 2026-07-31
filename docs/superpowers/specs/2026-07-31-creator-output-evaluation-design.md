# creator 生成产物评价报告 — 设计文档

**日期**：2026-07-31
**状态**：已批准，待实施

## 背景与目标

以 `sqlite-crm-weekly-report-skill`（agent-skill-creator 首次生成产物）为探针，
评价新版本 creator 的规则（以 VERSION.md v0.4.0 为主线）是否真正落到生成产物。
评价对象是 creator，不是单个 skill。

交付物：把根目录 `crm-skill-issue-report.md` 从草稿升级为定稿评价报告，并提交 git。

## 核心原则

- 以 VERSION.md 为基准：每条结论与建议标注「依据（VERSION 条目）」和「状态
  （已落实 / 未落实 / VERSION 未规定-建议补充）」。
- 不偏离 VERSION：VERSION 已规定的内容以 VERSION 为准；VERSION 未规定的内容作为
  建议提出，并注明「需先更新 VERSION 再实施」。
- 证据核实：逐条标注「已验证 / 存疑」；实际运行校验命令，核对产物文件清单与
  creator 源码/文档，不直接沿用草稿观察。

## 评价方法

1. 检查产物文件清单：markdown 文件数、bash/ps1 wrapper、EVOLUTION.md、
   references/、README 安装表。
2. 运行校验命令：`validate.py`、`security_scan.py`、`check_pipeline.py`、
   `run_evals.py --validate`。
3. 对照 VERSION.md v0.4.0（及 v0.2.0 / v0.3.0 相关条目）与产物差异。
4. 核对 factory `SKILL.md`、`references/pipeline-phases.md`、`scripts/validate.py`
   的规则一致性（AGENTS.md、Agent Constraints、文件清单）。
5. 每个证据记录来源与验证方式。

## 报告结构

1. 结论摘要
2. 评价范围与方法
3. VERSION 声明 vs 产物对照表
4. 问题一：运行时契约缺失（P1）
5. 问题二：输出面向数据而非阅读（P1）
6. 问题三：creator 新规则未落到模板（P1）
7. P2 发现
8. 三项推荐决策
9. 行动清单
10. 验证附录

## 三项推荐决策（含 VERSION 锚点）

### 1. references/ 合并为单一 references/guide.md

- 依据：VERSION v0.2.0「skill = 能力包；agent-skill-creator + skillctl =
  生命周期管理器」「generated skill 不携带平台适配器」。
- 状态：VERSION 未逐项规定 references 数量 → 属于建议，需 VERSION v0.5 补充
  权威文件清单后再实施。

### 2. AGENTS.md 保留并收敛为 ≤25 行 dispatch card

- 依据：VERSION v0.3.0 明确要求 AGENTS.md 含 `## Agent Constraints` 节且
  validate.py 做阻断检查。
- 边界：不推荐「不再生成 AGENTS.md」，否则偏离 VERSION v0.3.0。工作区未提交的
  pipeline-phases 与 VERSION 的矛盾作为「规则漂移」写入报告，结论以 VERSION 为准；
  若未来要移除 AGENTS.md，必须先改 VERSION 再改模板。

### 3. 摘要输出支持 --lang zh/en 或配置项

- 依据：问题二要求输出面向阅读；VERSION 未规定输出语言。
- 状态：新增能力建议，需 VERSION 记录后实施，不偏离现状。

## 交付与验收

- 定稿写入根目录 `crm-skill-issue-report.md`，包含证据标注与验证附录。
- 报告提交 git（作者 `srt`）。
- 验收：每条结论可追溯到证据或 VERSION 条目；任何超出 VERSION 的推荐都明确标注
  「建议，需更新 VERSION」，不把建议冒充为已规定。
