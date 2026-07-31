# agent-skill-creator v0.4.0 生成产物评价报告

**日期**：2026-07-31
**探针**：`sqlite-crm-weekly-report-skill`（首次生成产物）
**评价对象**：agent-skill-creator（creator）新规则是否真正落到生成产物
**状态**：定稿（基于实际验证）

---

## 结论摘要

生成的 skill 功能上可运行：`check_pipeline` 通过、安全扫描通过、eval spec 有效。
但 creator 在 VERSION.md 中声明的规则没有完全落到产物，且存在三处结构性问题和
多处规则自相矛盾：

1. 提示文件没有把「运行时契约」立起来，Agent 仍倾向通读 `scripts/` 源码（P1）。
2. 面向用户的输出是数据视角而不是阅读视角，`report.json / report.md / report.csv`
   过于原始（P1）。
3. creator 新规则没有同步到生成模板，产物仍携带旧结构：8 个 markdown 文件、
   bash/ps1 wrapper、README 手动安装表、开发期 EVOLUTION.md（P1）。

根因：VERSION.md 的新规没有回流到 Phase 5 模板与 `validate.py`；creator 内部文档
（AGENTS.md 政策）自相矛盾；生成时把「机器可读」当成「用户可读」。

---

## 评价范围与方法

范围：

- 只评价 `sqlite-crm-weekly-report-skill` 这一份首次生成产物，以及 creator 的相关
  规则、模板与校验代码。
- 不评价 CRM 业务逻辑本身的优劣。

方法：

- 文件清单核对（`find`）。
- 实际运行 `validate.py`、`check_pipeline.py`、`security_scan.py`、
  `run_evals.py --validate`、`validate.py --check-contract`。
- 对照 VERSION.md v0.2.0 / v0.3.0 / v0.4.0 声明。
- 核对 factory `SKILL.md`、`references/pipeline-phases.md`、`scripts/validate.py`
  的规则一致性。
- 每条证据标注「已验证」或「存疑」。

环境说明：`check_pipeline.py` 写 `__pycache__` 受限，运行时加
`PYTHONPYCACHEPREFIX=/private/tmp/creator-eval-pyc` 以确保结果可信。

---

## VERSION 声明 vs 产物对照表

| VERSION 声明 | 来源 | 产物实际情况 | 状态 |
|---|---|---|---|
| 删除本地安装器，统一 `skillctl install` 安装 | v0.4.0「统一安装方式」 | 产物根目录仍有 `sqlite-crm-weekly-report-skill`（bash）和 `.ps1` wrapper；README 仍列逐平台手动安装表 | 未落实 |
| skill = 能力包，lifecycle 归 skillctl | v0.2.0「设计决策」 | 产物携带开发期 EVOLUTION.md、3 个 references 文件、README 安装指南 | 未落实 |
| 删除插件清单入口 | v0.4.0「删除插件清单入口」 | 产物无 `.claude-plugin` 等插件清单 | 已落实 |
| AGENTS.md 含 `## Agent Constraints` 且 validate 阻断检查 | v0.3.0「Agent Constraints 检查」 | 产物有 AGENTS.md 且含约束段；但 validate.py 对 AGENTS.md 同时发 warning，工作区 pipeline-phases 又说不再生成 | 规则漂移 |

---

## 问题一：运行时契约缺失（P1）

### 现象与证据（已验证）

- 产物 `SKILL.md` 只有 `## Workflow` 的 4 个步骤名，没有「`scripts/` 是实现细节、
  运行时不读」的阅读边界说明。
- 产物 `AGENTS.md` 只写「Read SKILL.md and follow it」，没有一行说明「不需要读
  `scripts/*.py`」。
- `references/` 三份文档以「loaded on demand」式描述，等于邀请 Agent 在不确定时
  自行翻文件。
- factory `SKILL.md` Phase 5 只强制生成 `## How to run it`，没有强制它出现在
  Workflow 之前，也没有强制「不读 scripts」指令。
- 运行时契约分散在 `pipeline.py`、`run_pipeline.py`、`contract.json`、README、
  SKILL.md 多处，Agent 只有通读才能确信。

### 影响

- 每次调用多消耗大量 token。
- Agent 可能按自己读到的源码「手动编排步骤」，绕过 `--report` 单入口。
- 文档与代码版本漂移时，Agent 更容易相信过时的源码注释。

### 建议（creator 侧）

1. SKILL.md 模板强制 `## Runtime Contract` 段：正常使用只运行
   `python3 scripts/pipeline.py --input <db> --output <out> --report`；
   `scripts/*.py` 是实现细节，默认不读；仅在排障、改规则、扩展 schema 时才读
   `references/` 和对应模块。
2. AGENTS.md 收敛为 ≤25 行的 dispatch card（对齐 `references/universal-standard.md`
   §2），只保留一句话用途、运行命令、SKILL.md 链接。
3. `validate.py` 对 `Runtime Contract` 存在性做 warning 检查；README 删除手动安装表。

---

## 问题二：输出面向数据而非阅读（P1）

### 现象与证据（已验证）

- `report.json` 没有 `summary` / `highlights` / `alerts` 这类面向阅读的字段。
- `report.md` 从 KPI 表格开始，没有「本周结论」、环比、异常提醒。
- pipeline 结束后 stdout 输出完整 `kpis` 对象，而不是 5–8 行人读摘要。
- SKILL.md 的 `## Output Example` 展示的也是原始 JSON。

### 影响

- 用户（或上层 Agent）需要二次加工才能回答「这周怎么样、哪里有问题」。
- 表格越多越容易漏掉关键信号（成交下滑、重复率上升、孤儿数据变多）。

### 建议（creator 侧）

1. `report.md` 顶部新增 `## 本周结论`（executive summary）：3–5 句由 pipeline 按
   KPI 与告警规则生成的模板文本，不依赖 LLM，保证可复现。
2. `report.json` 新增 `summary`：`summary_text`、`highlights[]`、`alerts[]`，
   机器字段保持不变。
3. pipeline stdout 在 `--report` 后打印人读摘要 + 输出文件路径；JSON 状态改为
   `--json` 可选。
4. 可加 `--brief` 只输出摘要；`report.csv` 与 `report.json` 继续作为原始数据层，
   文档标注「raw data」。
5. SKILL.md 的 Output Example 改为先展示摘要，再给 JSON 结构。

---

## 问题三：creator 新规则未落到模板（P1）

### 现象与证据（已验证）

产物 markdown 文件共 8 个：

```
SKILL.md
AGENTS.md
README.md
EVOLUTION.md
evals/sqlite-crm-weekly-report-skill.eval.md
references/schema-guide.md
references/analysis-methods.md
references/troubleshooting.md
```

其他旧结构残留：

- `sqlite-crm-weekly-report-skill`（bash wrapper）与
  `sqlite-crm-weekly-report-skill.ps1` 仍在根目录；VERSION.md v0.4.0 已删除本地
  安装器并把 lifecycle 归给 skillctl。
- `README.md` 仍保留「Manual installation」逐平台复制路径；VERSION.md v0.4.0
  要求统一 `skillctl install <name>`。
- `EVOLUTION.md` 被打包进交付物，内容是开发期 `run_evals --rollout` 三次 error
  的失败证据；该文件应只在交付后失败时按需生成。

creator 自己的规范互相矛盾（已验证）：

- factory `SKILL.md` Phase 5 第 3 步要求生成 AGENTS.md（含 `## Agent Constraints`），
  第 8 步又说 skill repo carries only `SKILL.md, AGENTS.md, scripts/, evals/,
  contract.json`；
- `references/pipeline-phases.md` Step 2.5 与 checklist 明确「No per-skill
  AGENTS.md」，validate.py 却又对存在 AGENTS.md 发 warning；
- v0.3.0 要求 AGENTS.md 的 `## Agent Constraints` 做阻断检查，而新 pipeline-phases
  又把约束放进 SKILL.md 正文，双写导致漂移。

### 影响

- 每个新 skill 都会继续按旧模板产出多余文件，用户要手动清理。
- 多个 markdown 文件让 Agent 的阅读面更大，加剧问题一。
- 交付物携带开发期失败证据，污染用户侧排查。

### 建议（creator 侧）

1. 以 VERSION 为源头收敛出一份**唯一权威文件清单**，默认模式与 universal 模式
   分别明确，并让 `validate.py` 按清单检查。
2. 生成模板删除 bash/ps1 wrapper；README 只写 `skillctl install <name>`。
3. 交付前清理 `EVOLUTION.md`；validate.py 增加「初始包不得携带 EVOLUTION.md」
   检查，只有 post-delivery 失败才生成。
4. AGENTS.md 政策以 VERSION v0.3.0 为准：保留 AGENTS.md 与 Agent Constraints；
   同步 factory `SKILL.md` 与 `pipeline-phases.md`；若未来要移除，必须先改 VERSION
   再改模板。

---

## P2 发现（已验证）

1. `scripts/validate.py:414` 的 description 正则 `r"^(A|An)\\s+"` 存在双反斜杠 bug，
   合法描述 `A cleaning pipeline ...` 被误判为不匹配；建议改为 `\s` 并补单测。
2. `validate.py --check-contract` 对 `<output>` 模板路径固定报 5 条
   「file does not exist」warning；建议 contract schema 支持变量路径，或检查时
   跳过占位符。
3. `--check-contract` 把 `pipeline.py` 的 `STEPS` dict 解析成「0 个 pipeline
   function」（diff=4），与模板的 `STEPS` / `resolve_steps()` 写法不匹配；建议
   放宽统计或改读 `contract.json.dag`。
4. AGENTS.md 与 SKILL.md 双写 Agent Constraints，长期会漂移；收敛后只保留一份。

---

## 三项推荐决策

| 决策 | 推荐 | 依据（VERSION） | 状态 |
|---|---|---|---|
| `references/` 去留 | 默认不再生成多文件，合并为单一 `references/guide.md` | v0.2.0「skill = 能力包；agent-skill-creator + skillctl = 生命周期管理器」 | 建议，需 VERSION v0.5 补充权威文件清单后再实施 |
| AGENTS.md 政策 | 保留生成，收敛为 ≤25 行 dispatch card；Agent Constraints 按 v0.3.0 保留在 AGENTS.md，SKILL.md 不再双写 | v0.3.0「AGENTS.md 新增 Agent Constraints 节，validate.py 阻断检查」 | 保留；若未来移除必须先改 VERSION |
| 摘要语言 | pipeline 支持 `--lang zh/en` 或配置项，默认跟随报告语言配置，不依赖 LLM | v0.4.0 未规定 | 新增能力建议，需 VERSION 记录后再实施 |

---

## 行动清单

1. 文档层：VERSION v0.5 补充权威文件清单与 AGENTS.md 政策，消除 factory SKILL.md
   与 pipeline-phases.md 的矛盾。
2. 模板层：SKILL.md 模板强制 `Runtime Contract` + 不读 scripts；AGENTS.md 收敛为
   ≤25 行 dispatch card；删除 wrapper；README 只写 `skillctl install <name>`。
3. 输出层：report.md 增加「本周结论」，report.json 增加 `summary`，stdout 输出
   人读摘要，支持 `--json` / `--brief`。
4. 校验层：修复 validate.py 正则 bug；增加 EVOLUTION.md 初始包检查、文件清单检查、
   Runtime Contract 检查；修复 contract 路径与 DAG 检查。
5. 回归验证：重新生成探针 skill，跑 5 条校验命令，确认 0 error 且文件清单收敛。

---

## 验证附录

以下命令均在本环境实际运行（`PYTHONPYCACHEPREFIX=/private/tmp/creator-eval-pyc`
仅为沙箱限制下让 `check_pipeline.py` 可写字节码缓存）：

`<skill>` 表示探针产物路径
`/Users/syh/Documents/Codex/2026-07-31/agent-skill-creator-users-syh-desktop-2/outputs/sqlite-crm-weekly-report-skill`。

```bash
python3 scripts/validate.py <skill>
```

输出：`Status: INVALID`；1 error（description 正则 bug，命中
`A cleaning pipeline for SQLite CRM data....`）；1 warning（per-skill AGENTS.md）。

```bash
python3 scripts/validate.py <skill> --check-contract
```

输出：6 条 contract warning — `<output>` / `.md` / `.csv` / `.changes.csv` / `.db`
路径不存在共 5 条，DAG diff=4 一条。

```bash
PYTHONPYCACHEPREFIX=/private/tmp/creator-eval-pyc python3 scripts/check_pipeline.py <skill>
```

输出：`pipeline OK`。

```bash
python3 scripts/security_scan.py <skill>
```

输出：`Status: CLEAN`。

```bash
python3 <skill>/scripts/run_evals.py <skill> --validate
```

输出：`VALID sqlite-crm-weekly-report-skill.eval.md`（含 pending-first-green 提示）。

```bash
find <skill> -name '*.md' | wc -l
```

输出：`8`。

```bash
ls -la <skill>/sqlite-crm-weekly-report-skill*
```

输出：bash wrapper 与 `.ps1` wrapper 均存在。

```bash
sed -n '1,12p' <skill>/EVOLUTION.md
```

输出：`2026-07-31T02:49:53Z — run_evals --rollout FAILED`，`errors=3`。
