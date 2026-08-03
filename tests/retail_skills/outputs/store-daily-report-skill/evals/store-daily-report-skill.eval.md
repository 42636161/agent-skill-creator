# store-daily-report-skill — Eval Spec

## Binary Checks

| # | Name | Type | Command / Criteria |
|---|---|---|---|
| 1 | pipeline runs | command | `python3 scripts/pipeline.py --input evals/golden/case-1/input.xlsx --output /tmp/sdr_test && exit 0` |
| 2 | report.md exists | command | `test -f /tmp/sdr_test/report.md` |
| 3 | report starts with summary | command | `head -3 /tmp/sdr_test/report.md | grep -q "本周结论"` |
| 4 | report.json has summary field | command | `python3 -c "import json; d=json.load(open('/tmp/sdr_test/report.json')); assert 'summary_text' in d"` |
| 5 | sales revenue correct | command | `python3 -c "import json; d=json.load(open('/tmp/sdr_test/report.json')); assert d['sales']['total_revenue'] == 94.30"` |

## Golden Cases

### case-1
- **split**: train
- **input**: evals/golden/case-1/input.xlsx
- **expected_revenue**: 94.30
- **expected_txns**: 5
- **expected_returns**: 1
- **expected_members**: 3
