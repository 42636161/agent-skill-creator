#!/usr/bin/env python3
import argparse, csv, json, re, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--employees", required=True); p.add_argument("--rules", required=True)
    p.add_argument("--attendance", required=True); p.add_argument("--output", required=True)
    return p.parse_args()

def sf(v, d=0.0):
    try: return float(v)
    except: return d

def parse_rules(path):
    text = Path(path).read_text(encoding="utf-8")
    rules = {"commission": {}, "bonus": {}, "social_insurance": {}}

    # Parse tiered commission by role
    current_role = None
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("### "):
            current_role = line[4:].strip()
        elif current_role and ">=" in line and "%" in line:
            m = re.search(r">=\s*(\d+)%[：:]\s*[^×xX*]*[×xX*]\s*(\d+\.?\d*)%", line)
            if m:
                rules["commission"].setdefault(current_role, []).append(
                    {"threshold": int(m.group(1)), "rate": float(m.group(2)) / 100})

    # Full attendance bonus
    bonus_m = re.search(r"[+＋]\s*(\d+)\s*元", text)
    if bonus_m:
        rules["bonus"]["full_attendance"] = float(bonus_m.group(1))

    # Social insurance
    for m in re.finditer(r"(养老|医疗|失业)(\d+(?:\.\d+)?)%", text):
        name_map = {"养老": "pension", "医疗": "medical", "失业": "unemployment"}
        rules["social_insurance"][name_map.get(m.group(1), m.group(1))] = float(m.group(2)) / 100

    return rules

def main():
    args = parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)

    with open(args.employees, encoding="utf-8-sig") as f:
        employees = list(csv.DictReader(f))
    rules = parse_rules(args.rules)
    with open(args.attendance, encoding="utf-8-sig") as f:
        attendance = list(csv.DictReader(f))

    att_by_emp = defaultdict(list)
    for a in attendance:
        att_by_emp[a["\u5458\u5de5\u7f16\u53f7"]].append(a)

    results = []; total_cost = 0.0

    for emp in employees:
        eid = emp["\u5458\u5de5\u7f16\u53f7"]; name = emp["\u59d3\u540d"]; role = emp["\u5c97\u4f4d"]
        base = sf(emp["\u57fa\u672c\u5de5\u8d44"]); social_base = sf(emp["\u793e\u4fdd\u57fa\u6570"])

        commission = 0.0
        role_rules = rules.get("commission", {}).get(role, [])
        for rr in role_rules:
            commission += base * rr["rate"]

        atts = att_by_emp.get(eid, [])
        has_absence = any(a.get("\u8bf7\u5047\u7c7b\u578b", "\u65e0") != "\u65e0" for a in atts)
        has_late = any(a.get("\u662f\u5426\u8fdf\u5230") == "\u662f" for a in atts)
        bonus = rules.get("bonus", {}).get("full_attendance", 0) if not has_absence and not has_late else 0

        deductions = 0.0
        for a in atts:
            if a.get("\u662f\u5426\u8fdf\u5230") == "\u662f": deductions += 20
            if a.get("\u662f\u5426\u65e9\u9000") == "\u662f": deductions += 30
            leave = a.get("\u8bf7\u5047\u7c7b\u578b", "\u65e0")
            if leave == "\u4e8b\u5047": deductions += base / 21.75
            elif leave == "\u75c5\u5047": deductions += base / 21.75 * 0.4

        si_rates = rules.get("social_insurance", {})
        social_ins = social_base * sum(si_rates.values())
        total = base + commission + bonus - deductions - social_ins
        total_cost += total
        results.append({
            "\u5458\u5de5\u7f16\u53f7": eid, "\u59d3\u540d": name, "\u5c97\u4f4d": role,
            "\u57fa\u672c\u5de5\u8d44": base, "\u63d0\u6210": round(commission, 2),
            "\u5168\u52e4\u5956": bonus, "\u6263\u6b3e": round(deductions, 2),
            "\u793e\u4fdd\u4e2a\u4eba": round(social_ins, 2), "\u5b9e\u53d1\u5408\u8ba1": round(total, 2),
        })

    n = len(results); avg = total_cost / n if n else 0

    (out / "report.json").write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "total_employees": n, "total_labor_cost": round(total_cost, 2),
        "average_salary": round(avg, 2), "details": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_md = "Generated: {}\n\n{} employees, total cost: {:,.2f}, avg: {:,.2f}\n".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), n, total_cost, avg)
    (out / "report.md").write_text(summary_md, encoding="utf-8")

    with open(out / "report.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["\u5458\u5de5\u7f16\u53f7","\u59d3\u540d","\u5c97\u4f4d","\u57fa\u672c\u5de5\u8d44","\u63d0\u6210","\u5168\u52e4\u5956","\u6263\u6b3e","\u793e\u4fdd\u4e2a\u4eba","\u5b9e\u53d1\u5408\u8ba1"])
        w.writeheader(); w.writerows(results)

    print("Payroll complete: {} employees, total: {:,.2f}, avg: {:,.2f}".format(n, total_cost, avg))
    print("   Output: " + str(out))

if __name__ == "__main__":
    sys.exit(main())
