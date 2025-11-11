import json
from collections import defaultdict

targets = {
    "B608": "hardcoded_sql_expressions",
    "B324": "weak_hash",
    "B701": "jinja2_autoescape_false",
    "B104": "bind_all_interfaces",
}

with open("bandit_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

findings = defaultdict(lambda: defaultdict(int))
for item in data.get("results", []):
    tid = item.get("test_id")
    if tid in targets:
        fname = item.get("filename") or item.get("file") or "<unknown>"
        findings[tid][fname] += 1

for tid in targets:
    total = sum(findings[tid].values())
    print(f"{tid} ({targets[tid]}): {total} findings")
    for fn, c in sorted(findings[tid].items(), key=lambda x: -x[1]):
        print(f"  {c:4d}  {fn}")
    print()
