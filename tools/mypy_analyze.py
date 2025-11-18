import re
from collections import Counter
p='mypy_backend_shared.txt'
with open(p,'rb') as f:
    s_bytes=f.read()
    # Detect BOM / encoding: prefer utf-8, fallback to utf-16 if BOM present
    if s_bytes.startswith(b'\xff\xfe') or s_bytes.startswith(b'\xfe\xff'):
        s=s_bytes.decode('utf-16', errors='replace')
    else:
        try:
            s=s_bytes.decode('utf-8')
        except Exception:
            s=s_bytes.decode('utf-8', errors='replace')
codes=re.findall(r"\[([^\]]+)\]",s)
code_counts=Counter(codes)
files=re.findall(r"([\w\\/\.\-]+\.py):\d+: error",s)
file_counts=Counter(files)
print('Top 12 error codes:')
for k,v in code_counts.most_common(12):
    print(f'{k}: {v}')
print('\nTop 20 files by error count:')
for k,v in file_counts.most_common(20):
    print(f'{k}: {v}')
print('\nDEBUG: total filename matches =', len(files))
print('DEBUG sample matches:', files[:20])

# Heuristic: locate occurrences of ' error:' and show surrounding text to find filename patterns
err_positions=[m.start() for m in re.finditer(r' error:', s)]
print('\nDEBUG: found', len(err_positions), "' error:' occurrences; showing surrounding snippets:")
for i,pos in enumerate(err_positions[:20]):
    start=max(0,pos-80)
    end=min(len(s), pos+40)
    snippet=s[start:end].replace('\n','\\n')
    print(f'[{i}] ...{snippet}...')

print('\nDEBUG: file head repr:')
print(repr(s[:400]))
