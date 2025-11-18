from pathlib import Path
p=Path('mypy_backend_shared.txt')
raw=p.read_bytes()
enc='utf-8'
if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
    enc='utf-16'
print('detected encoding:', enc)
text=raw.decode(enc, errors='replace')
print('\n--- START ---\n')
print(repr(text[:800]))
print('\n--- RAW SLICE ---\n')
print(text[:800])
