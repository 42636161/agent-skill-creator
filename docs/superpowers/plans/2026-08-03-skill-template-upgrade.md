# v0.8.0 — SKILL.md / AGENTS.md 模板升级

**Date:** 2026-08-03
**Source:** 12-skill user-quality evaluation + 评估标准文档
**Ref:** [user-quality-evaluation-design.md](../specs/2026-07-29-user-quality-evaluation-design.md)
**Scope:** 工厂模板和提示词修改。不涉及架构变更、不新增运行模式。
**Expected impact:** A-a-1 (触发词), A-a-2 (错误诊断), A-a-4 (执行指引), A-b-1 (输出呈现), A-b-2 (配置可见) — 五项一次性解决。

---

## 0. 当前状态基线

**已解决（v0.7.x）：**
- B-2: 技能定义与分发机制耦合 — universal mode + skillctl
- B-4: 核心能力与维护设施捆绑 — universal mode 去除了维护脚本
- 代码质量：Validate-Compute-Report 模式、三段式错误消息
- AGENTS.md 削减为一行 `Run:` 指令（减少 agent 阅读长度）

**仍待解决（本版本目标）：**
- 触发词从"功能术语列表"升级为"场景驱动 + 多语言"
- Agent 不知道如何呈现结果
- 配置参数对用户不可见
- Runtime Contract 完整度在技能间差异大（store-daily-report 好、其他差）
- 异常输入静默失败

---

## 1. 工厂提示词：触发词生成规则升级（对应 A-a-1）

**改什么。** Phase 3（技能规范）提示词中触发词相关指令。

**现状。** 模型生成的触发词形如 `RFM, customer segmentation, member analysis` — 功能术语列表，英文为主。

**目标。** 

```
触发词生成规则：

1. 从目标用户的原生语言出发。如果用户描述是中文场景，生成中文触发词为第一语言。
2. 覆盖三种说话方式：
   - 功能请求（用户知道技能叫什么）："帮我把会员分个层"
   - 问题描述（用户说问题不说工具）："哪些会员很久没买了"
   - 半信息态（用户给了文件但没说明白）："帮我看看这个表格"
3. 禁止仅输出技术术语缩写。同步给出术语对应的日常说法。
4. 目标：一个不会说 RFM 的零售店长也能触发此技能。

示例输出（member-rfm-segmenter-skill）：
   Triggers on: 会员分层, 哪些会员最近没买了, 帮我看看会员数据,
               把客户分一下类, 高价值会员是谁, 沉睡会员唤醒,
               customer segmentation, member loyalty analysis
```

**涉及文件。** `SKILL.md` 第 3 阶段提示词。

---

## 2. SKILL.md 模板：新增 Presenting Results 章节（对应 A-b-1）

**改什么。** SKILL.md 生成模板新增一个章节。

**目标。** 告诉 agent 拿到输出后如何组织回答。

**模板。**

```
## Presenting Results

After running the pipeline, ALWAYS present results to the user as follows:

1. Lead with the headline. Read the primary summary field and display
   a one-line conclusion. Example: "今日门店总销售额 ¥92,400，共 50 笔交易。"

2. Show the primary breakdown. For the most relevant dimension, render
   a table of top 5 entries sorted by value. If the user's prompt mentioned
   a specific dimension, show that first.

3. Surface notable findings. Mention:
   - Any outliers or anomalies detected
   - Any data quality issues (duplicates removed, missing values filled)
   - Top vs bottom performers

4. Offer one natural follow-up. Choose a question connected to the data.
   Example: "华东区域销售下降明显，需要深入分析吗？"
```

**涉及文件。** SKILL.md 生成模板。

---

## 3. SKILL.md 模板：新增 Tuning 章节（对应 A-b-2）

**改什么。** SKILL.md 生成模板新增配置可见性章节。

**目标。** agent 知道有哪些参数可调、默认值是多少、什么情况下应该向用户提议调整。

**模板。**

```
## Tuning

The following parameters can be adjusted. The agent should suggest
changes when the data suggests defaults are inappropriate.

| Parameter | Default | What it controls | When to adjust |
|-----------|---------|------------------|---------------|
| ... | ... | ... | ... |
```

技能生成时需填充此表。参数名称应翻译为面向用户的语言（例如："异常值敏感度" 而非 "outlier_std_threshold"）。

**涉及文件。** SKILL.md 生成模板 + Phase 5 生成逻辑。

---

## 4. SKILL.md 模板：Runtime Contract 标准化（对应 A-a-4）

**改什么。** Runtime Contract 段落的必需字段标准化。

**现状。** store-daily-report-skill 的 Runtime Contract 有 4 条规则，其他技能只有 1 条。

**目标。** 所有技能的 Runtime Contract 强制包含以下字段：

```

## Runtime Contract

- Only run: `python3 scripts/pipeline.py --input <...> --output <...> [flags]`
- Do not read scripts/. Implementation is in pipeline.py.
- Output: <format and location description>
- Primary anchor: <which file/section to read first for conclusions>
- stdout: <what stdout produces — human summary, JSON, or silent>
```

**涉及文件。** SKILL.md 生成模板（Phase 5）。

---

## 5. Pipeline 模板：结构化的 _diagnostics 输出（对应 A-a-2）

**改什么。** `scripts/pipeline.py` 模板的异常处理逻辑。

**现状。** 输入列名不匹配时静默返回空结果。竞争对手价格监控 pipeline 是 stub。

**目标。** 当输入不符合预期时，输出中增加 `_diagnostics` 字段：

```
_diagnostics:
  status: partial | failed
  column_detection:
    unmatched: [列名列表]
    best_guess: {列名: 最接近角色}
    hint: "列名不支持当前语言。支持的列名参见 SKILL.md。"
  missing_required:
    [必填字段列表]
```

agent 读取后可以向用户说："没找到金额列，你的列 'Deal Value' 没在我的支持列表里。需要加入吗？"

**涉及文件。** `scripts/pipeline.py` 生成模板（Phase 5）。仅新生成技能受益。

---

## 文件影响范围

| 变更项 | 涉及文件 | 变更类型 |
|--------|---------|---------|
| 1. 触发词提示词 | Phase 3 prompt | 提示词修改 |
| 2. Presenting Results | SKILL.md template | 模板新增章节 |
| 3. Tuning | SKILL.md template | 模板新增章节 |
| 4. Runtime Contract | SKILL.md template (Phase 5) | 模板标准化 |
| 5. _diagnostics | pipeline.py template (Phase 5) | 代码模板修改 |

全部变更均为模板/提示词层面，不触碰运行模式、架构分层、技能文件结构。

---

## 验收标准

- [ ] 新生成的 12 个零售技能包含 Presenting Results + Tuning 章节
- [ ] 所有技能的 Runtime Contract 有 4 个标准字段
- [ ] 触发词包含场景驱动 + 目标语言的日常说法
- [ ] pipeline.py 在输入不匹配时输出 `_diagnostics`
- [ ] 新技能在 `outputs/` 下符合标准，重新跑 agent 评估对比本次基线
