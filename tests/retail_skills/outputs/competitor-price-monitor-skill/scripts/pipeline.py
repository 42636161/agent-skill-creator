#!/usr/bin/env python3
import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser(description="Competitor price monitor")
    p.add_argument("--products", required=True); p.add_argument("--output", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)

    with open(args.products, encoding="utf-8-sig") as f:
        products = list(csv.DictReader(f))

    # Generate comparison report
    lines = ["# Competitor Price Comparison", "", "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             "## Summary", "", "{} products tracked.".format(len(products)), "",
             "Note: Chinese e-commerce APIs (JD Open Platform, Taobao Open Platform) require OAuth setup.",
             "See references/platform-auth.md for authentication instructions."]

    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"tracked_products": len(products), "generated_at": datetime.now().isoformat()}, indent=2), encoding="utf-8")

    print("Price monitor: {} products tracked".format(len(products)))
    print("   Output: " + str(out / "report.md"))

if __name__ == "__main__":
    sys.exit(main())
