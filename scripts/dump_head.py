from pathlib import Path
p=Path('mypy_backend_shared.txt')
if not p.exists():
    print('Mypy file not found')
else:
    b=p.read_bytes()
    s=b[:400]
    print('RAW REPR:')
    print(repr(s))
    print('\nHEX:')
    print(' '.join(hex(c) for c in s[:200]))
    print('\nFIRST 4 newlines indexes:')
    for i,c in enumerate(s[:400]):
        if c in (10,13):
            print(i, c)
