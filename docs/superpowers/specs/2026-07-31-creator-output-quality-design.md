# Creator Output Quality — 文件清单 + 输出层设计文档

**日期**：2026-07-31
**来源**：crm-skill-issue-report.md 原始问题 + VERSION v0.5.0 未覆盖项
**状态**：设计阶段，待批准

## 背景

VERSION v0.5.0 已收敛 AGENTS.md 政策、Runtime Contract、EVOLUTION 初始包检查、
wrapper 删除和 contract 修复。但报告中的两项需求未触及：

1. 权威文件清单 — VERSION 尚未定义默认/universal 模式各自应产出的文件集。
2. 输出层模板 — 生成技能的 report 格式仍是数据视角（表格/JSON），缺少「本周结论」和
   人读摘要。

本设计给这两项补上方案。**不涉及** creator 自身提示文件的 token 效率优化（v2），
那是架构文件组织问题，单独讨论。

---

## 一、权威文件清单

### 规则

以 VERSION 为唯一锚点，定义默认模式和 universal 模式下生成技能应产出的文件集合。

| 文件/目录 | 默认模式 | universal 模式 | 说明 |
|---|---|---|---|
| `SKILL.md` | ✅ 必须 | ✅ 必须 | |
| `AGENTS.md` | ✅ 必须（≤25 行 dispatch card） | ✅ 必须（≤25 行 dispatch card） | Agent Constraints 在此 |
| `README.md` | ✅ 必须（仅含 `skillctl install`） | ✅ 必须（仅含 `skillctl install`） | 不写手动安装表 |
| `scripts/` | ✅ 必须（含功能代码 + run_pipeline.py） | ✅ 必须（含 pipeline.py） | |
| `evals/` | ✅ 必须（除非 --no-eval） | ✅ 必须（除非 --no-eval） | .eval.md + golden/ |
| `scripts/evolve.py` | ✅ 必须 | ❌ 禁止 | 默认模式有自维护循环 |
| `contract.json` | ✅ 必须 | ✅ 必须 | |
| `assets/` | 🔵 可选 | 🔵 可选 | 有 config/template 就生成 |
| `references/` | ❌ 禁止生成多文件 | ❌ 禁止生成多文件 | 确需细节时合并为单一 `references/guide.md` 或移入 SKILL.md |
| `EVOLUTION.md` | ❌ 初始包禁止 | ❌ 初始包禁止 | 仅 post-delivery 失败时按需生成 |
| `./skill-name` (bash) | ❌ 禁止 | ❌ 禁止 | wrapper 已删除，由 skillctl 接管 |
| `.\skill-name.ps1` | ❌ 禁止 | ❌ 禁止 | 同上 |
| `.claude-plugin/` 等 | ❌ 禁止 | ❌ 禁止 | plugin 清单已在 v0.4.0 删除 |
| `__pycache__/` | ❌ 禁止 | ❌ 禁止 | 字节码不提交 |
| `requirements.txt` | 🔵 有第三方依赖时生成 | 🔵 有第三方依赖时生成 | |

### validate.py 清单检查

在 `validate_skill` 中新增 `_validate_file_manifest` 函数：

1. 扫描技能目录根层的文件和子目录名。
2. 对照清单：
   - 缺少 `SKILL.md` / `scripts/` / `evals/` → error
   - 缺少 `AGENTS.md` / `README.md` / `contract.json` → warning
   - 存在 `EVOLUTION.md` / 根层 wrapper / 根层多个 `references/` 文件 → error
   - 存在 `references/` 目录且子文件 > 1 个 → warning
   - 存在 `__pycache__/` → warning
3. universal 模式下升级缺失项为 error，并对 `scripts/evolve.py` 存在报 error。

---

## 二、输出层模板

### 现状

生成的 `report.md` 从 KPI 表格开始，没有「本周结论」；`report.json` 无 summary
字段；stdout 打印原始 JSON。用户/Agent 需要二次加工。

### 设计

#### 2.1 report.md 增加「本周结论」

在 `report.md` 顶部插入规则生成的 executive summary（不依赖 LLM）：

```markdown
# Weekly CRM Report — W30 2026

## 本周结论

本周新增 12 位联系人，成交 3 单共 $45,600；开放管道 $184,500，较上周 -8%；
数据质量 96.4，仍有 2 个无效邮箱待处理。

- ⚠️ 开放管道连续两周下降，关注区域 West 的 deal velocity。
- ⚠️ 重复联系人合并 4 条，较上周增加 2 条，检查数据入口。
- ✅ 邮箱正常化率 98.3%，优于上周的 97.1%。

## KPI 总结

| 指标 | 值 |
|------|-----|
| 本周新增联系人 | 12 |
| 开放管道总额 | $184,500 |
| 成交额 | $45,600 |
```

生成规则：
- 首句固定模板：「本周新增 {new_contacts} 位联系人，成交 {won_deals} 单共
  ${closed_value}；开放管道 ${open_pipeline}，较上周 {trend_pct}%；
  数据质量 {quality_score}，仍有 {issues_count} 个问题待处理。」
- 后续 bullet 从告警列表生成：环比下降/上升超过阈值、重复率变化、质量分变化、
  孤儿数据量变化。
- 无异常则不生成 bullet。

#### 2.2 report.json 增加 summary 字段

```json
{
  "summary": {
    "summary_text": "本周新增 12 位联系人...",
    "highlights": [
      "开放管道连续两周下降",
      "重复联系人合并 4 条"
    ],
    "alerts": [
      "邮箱无效: 2 (jane@bad, tom@test)"
    ]
  },
  "kpis": { },
  "cleaning": { }
}
```

summary 字段与现有 kpis/cleaning/metrics 同级，不破坏现有结构。

#### 2.3 stdout 输出人读摘要

- 默认 `--report` 后 stdout 打印人读摘要（5-8 行）+ 输出文件路径列表。
- `--json` 标志输出完整 JSON status。
- `--brief` 标志只输出摘要文本（无 JSON、无文件路径列表）。

```bash
python3 scripts/pipeline.py --input crm.db --output out --report
# Weekly CRM Report W30 2026
#   本周新增 12 位联系人，成交 3 单共 $45,600
#   开放管道 $184,500（↓ 8%），数据质量 96.4
#   详见 out/report.md

python3 scripts/pipeline.py --input crm.db --output out --report --json
# {"kpis": {}, "summary": {}}

python3 scripts/pipeline.py --input crm.db --output out --report --brief
# 本周新增 12 位联系人，成交 3 单共 $45,600。管道 $184,500（↓ 8%）。
```

#### 2.4 creator 模板侧改动

- `pipeline_template.py`：新增 `_build_summary()`、`_build_alerts()`、
  `_print_stdout_summary()` 函数模板。
- `references/pipeline-phases.md` Step 7b：在 harness patterns 中增加
  `--json` / `--brief` 命令行参数要求。
- factory `SKILL.md` Phase 5 `## Output Example` 模板：先展示摘要文本，再给
  JSON 结构。

---

## 实施顺序

1. VERSION.md 补充权威文件清单（追加到 v0.5.0 条目）。
2. `validate.py` 新增 `_validate_file_manifest`。
3. `scripts/tests/test_validate.py` 补单测。
4. `pipeline_template.py` 新增 summary/brief 函数模板。
5. `references/pipeline-phases.md` Step 7b 补 `--json`/`--brief` 要求。
6. factory `SKILL.md` Phase 5 Output Example 更新。
7. 回归：重新生成探针技能跑校验。

## 交付

- VERSION.md 补清单定义
- `scripts/validate.py` 清单检查
- `scripts/tests/test_validate.py` 对应测试
- `scripts/pipeline_template.py` 输出模板更新
- `references/pipeline-phases.md` harness 更新
- factory `SKILL.md` Output Example 更新
