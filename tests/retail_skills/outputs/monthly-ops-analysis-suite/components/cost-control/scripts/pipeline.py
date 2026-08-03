#!/usr/bin/env python3
import argparse, csv, sys
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--input", required=True); p.add_argument("--output", required=True)
args = p.parse_args()
out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
with open(args.input, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
(out / "report.md").write_text("Report: {} records\n".format(len(rows)), encoding="utf-8")
print("Done: {} records".format(len(rows)))
