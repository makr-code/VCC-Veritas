"""
Auto-fix script for backend/ and shared/ files.
- Convert f-strings without placeholders (no `{` or `}`) into normal strings.
- Add spaces around simple arithmetic operators (+ - * /) inside {...} expressions in f-strings.

This script is conservative: it modifies only files under backend/ and shared/ that
are tracked by git. It creates a .bak copy for each changed file.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRS = [ROOT / 'backend', ROOT / 'shared']

# regex for f-string without placeholders: starts with f" or f' and contains no { or }
FSTRING_NO_PLACEHOLDER = re.compile(r"(?P<prefix>f)(?P<quote>[\"'])(?P<body>[^\{\}]*)\2")
# regex to find expressions inside braces
BRACE_EXPR = re.compile(r"\{([^}]*)\}")
# add spaces around operators inside expressions (simple heuristic)
OP_RE = re.compile(r"(?P<a>[^\s+\-*/%<>!=&|]+)(?P<op>[+\-*/])(?P<b>[^\s+\-*/%<>!=&|]+)")

def git_tracked_py_files():
    p = subprocess.run(['git', 'ls-files'] + [str(d) for d in TARGET_DIRS], capture_output=True, text=True, cwd=str(ROOT))
    if p.returncode != 0:
        raise SystemExit('git ls-files failed: ' + p.stderr)
    files = [ROOT / line.strip() for line in p.stdout.splitlines() if line.strip().endswith('.py')]
    return files


def fix_content(text: str) -> (str, bool):
    changed = False

    # 1) Convert f-strings without placeholders to normal strings
    def replace_f_no_placeholder(m):
        nonlocal changed
        body = m.group('body')
        # keep same quotes
        quote = m.group('quote')
        changed = True
        return f"{quote}{body}{quote}"

    text2 = FSTRING_NO_PLACEHOLDER.sub(replace_f_no_placeholder, text)

    # 2) For f-strings, add spaces around simple operators inside {...}
    def replace_brace_expr(m):
        expr = m.group(1)
        expr2 = OP_RE.sub(lambda mo: f"{mo.group('a')} {mo.group('op')} {mo.group('b')}", expr)
        if expr2 != expr:
            return '{' + expr2 + '}'
        return m.group(0)

    text3 = BRACE_EXPR.sub(replace_brace_expr, text2)
    if text3 != text:
        changed = True
    return text3, changed


def main():
    files = git_tracked_py_files()
    changed_files = []
    for f in files:
        try:
            s = f.read_text(encoding='utf-8')
        except Exception:
            continue
        new, changed = fix_content(s)
        if changed and new != s:
            bak = f.with_suffix(f.suffix + '.bak')
            # create a unique backup if a .bak already exists
            if bak.exists():
                for i in range(1, 100):
                    bak_candidate = f.with_suffix(f.suffix + f'.bak{i}')
                    if not bak_candidate.exists():
                        bak = bak_candidate
                        break
            # write original content to backup, then write new content
            bak.write_text(s, encoding='utf-8')
            f.write_text(new, encoding='utf-8')
            changed_files.append((f, bak))
    if changed_files:
        print('Modified files:')
        for f, bak in changed_files:
            print(f' - {f} (backup: {bak})')
    else:
        print('No changes made')

if __name__ == '__main__':
    main()
