## v0.2.0 — 平台中立技能输出模式（2026-07-30）

### 新增

- **``--universal`` 生成模式** — 生成纯能力包，不含平台适配器和生命周期工具
- **references/universal-standard.md** — universal 模式的唯一权威规范文件
- **scripts/run_evals_universal.py** — 精简 eval 引擎（569 行，移除了 llm-judge、模型比较、EVOLUTION.md）
- **scripts/validate.py --check-universal** — universal 布局合规性检查（禁止 platform-specific 文件）

### 设计决策

| 决策 | 结果 |
|---|---|
| skill 本体 vs 生命周期管理 | skill = 能力包；agent-skill-creator + skillctl = 生命周期管理器 |
| 工具 vs 技能分类 | Phase 2 新增二分类：工具（无领域判断）和技能（领域知识 + 对话模式） |
| SKILL.md 结构 | 工具 7 段、技能 12 段（含 Agent behavior、Diagnostics、Feature discovery） |
| 领域知识存儲 | 数据文件（assets/JSON），非 hardcode Python |
| 分发路径 | skillctl 外部分发，generated skill 不携带任何平台适配器 |

### 改动文件

```
references/universal-standard.md       — 新增：universal 输出规范（517 行）
scripts/run_evals_universal.py         — 新增：精简 eval 引擎（569 行）
SKILL.md                               — 修改：--universal 标志检测 + Trigger 示例
references/architecture-guide.md       — 修改：Section 2.2 universal 目录布局
references/pipeline-phases.md          — 修改：Phase 2/3/4/5 universal 分支条件
references/phase2-eval-assessment.md   — 修改：universal mode 子节
scripts/validate.py                    — 修改：--check-universal 验证标志
scripts/tests/test_skillctl_publish.py — 修改：universal skill 发布测试
```

### 历史版本

- v0.1.0 存档在 `archive/v0.1-skill-distribution` 分支

---

# 版本说明

## v0.1.0 — 技能分发架构（2026-07-29）

### 新增

- **skillctl CLI** — 技能发现、安装、发布、更新
- **集中索引仓库** — `42636161/skillhub`，registry.json + JSON Schema
- **语义匹配** — 自然语言意图匹配，中文/英文双语言支持
- **Agent 自动发现** — 索引仓库 AGENTS.md 驱动，置信度 >70% 自动安装
- **安全模型** — 来源信任、内容扫描、校验和验证三层
- **17 平台支持** — 同 agent-skill-creator 的跨平台安装矩阵

### 命令速查

```
skillctl search <关键词>        # 搜索技能
skillctl install <名称>         # 安装技能
skillctl info <名称>            # 查看详情
skillctl update <名称>          # 升级技能
skillctl publish <目录>         # 发布技能
skillctl list                   # 列出全部
skillctl categories             # 列出分类
skillctl doctor                 # 健康检查
```

### 文件清单

```
scripts/skillctl/     — CLI 包（models，config，index，search，install，publish，update）
scripts/tests/        — 16 个单元测试
skillctl              — Shell 包装器
```

### 索引仓库

| 文件 | 用途 |
|------|------|
| `registry.json` | 技能目录，按名索引 |
| `registry.schema.json` | JSON Schema |
| `AGENTS.md` | Agent 自动发现指令 |

### 协作

在 `registry.json` 提交 PR 注册新技能。第三方技能标记 `verified: false`。
