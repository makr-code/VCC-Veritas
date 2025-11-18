import re
text=open('mypy_backend_shared.txt', 'rb').read()
enc='utf-8'
if text.startswith(b'\xff\xfe') or text.startswith(b'\xfe\xff'):
    enc='utf-16'
text=text.decode(enc, errors='replace')
pattern=re.compile(r"(?P<path>[^\s].*?:\d+):.*?\[(?P<code>[^\]]+)\]")
matches=list(pattern.finditer(text))
print('matches', len(matches))
for m in matches[:10]:
    print('MATCH:', m.group('path'), m.group('code'))
