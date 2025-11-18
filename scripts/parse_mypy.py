import re
from collections import Counter, defaultdict

path = "mypy_backend_shared.txt"
file_counts = Counter()
class_counts = Counter()
file_class_counts = defaultdict(Counter)
pattern = re.compile(r"(?P<path>[^\s].*?:\d+):.*?\[(?P<code>[^\]]+)\]")

raw = open(path, 'rb').read()
if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
    try:
        text = raw.decode('utf-16')
    except Exception:
        text = raw.decode('utf-16', errors='replace')
else:
    try:
        text = raw.decode('utf-8')
    except Exception:
        text = raw.decode('utf-8', errors='replace')
for m in pattern.finditer(text):
        full = m.group(0)
        # extract filename without the :lineno suffix
        path_part = m.group('path')
        # path_part is like 'backend\foo.py:123'
        if ":" in path_part:
            fname = path_part.rsplit(":", 1)[0]
        else:
            fname = path_part
        errclass = m.group('code')
        file_counts[fname] += 1
        class_counts[errclass] += 1
        file_class_counts[fname][errclass] += 1

# Totals
total_errors = sum(file_counts.values())
unique_files = len(file_counts)

# Top files
top_files = file_counts.most_common(30)

print(f"Total errors parsed: {total_errors}")
print(f"Files with errors: {unique_files}")
print("\nTop files (by error count):")
for i, (fname, cnt) in enumerate(top_files, 1):
    top_classes = file_class_counts[fname].most_common(3)
    classes_str = ", ".join(f"{c}:{n}" for c, n in top_classes)
    print(f"{i:2d}. {fname} — {cnt} errors — top: {classes_str}")

print("\nTop error classes overall:")
for cls, cnt in class_counts.most_common(30):
    print(f"- {cls}: {cnt}")

# Also dump per-class top files for the top classes
print("\nPer-class hotspots (top 5 files each):")
for cls, _ in class_counts.most_common(10):
    ranked = sorted(((f, file_class_counts[f][cls]) for f in file_class_counts if file_class_counts[f][cls] > 0), key=lambda x: -x[1])[:5]
    print(f"\n{cls}:")
    for f, n in ranked:
        print(f"  {n:4d}  {f}")
