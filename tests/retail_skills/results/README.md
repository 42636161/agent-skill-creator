# results/ — 测试结果目录

## 目录结构

```
results/
├── scorecards/           # 每个 case 的独立评分卡
│   ├── a1_scorecard.md
│   ├── a2_scorecard.md
│   ├── a3_scorecard.md
│   ├── b4_scorecard.md
│   ├── b5_scorecard.md
│   ├── b6_scorecard.md
│   ├── c7_scorecard.md
│   ├── c8_scorecard.md
│   ├── d9_scorecard.md
│   ├── d10_scorecard.md
│   ├── e11_scorecard.md
│   ├── e12_scorecard.md
├── reports/
│   └── creator_defect_report.md   # creator 缺陷归因报告
└── score_results.json     # 机器可读的汇总评分（score_skill.py --all 生成）
```

## 填写顺序

1. 每生成完一个 case，填写 `scorecards/<case_id>_scorecard.md`
2. 全部 case 跑完，运行 `python3 tests/retail_skills/score_skill.py --all outputs/`
3. 将机器评分的 `score_results.json` 对照填入 `reports/creator_defect_report.md`
4. 总结 creator 优化清单，按优先级排 P0/P1/P2