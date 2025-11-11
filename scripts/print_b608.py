import json

with open("bandit_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
for item in data.get("results", []):
    if item.get("test_id") == "B608":
        print("---")
        print("file:", item.get("filename"))
        print("line:", item.get("line_number"))
        print(item.get("code"))
        count += 1

print("Total B608:", count)
