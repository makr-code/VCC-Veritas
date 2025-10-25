#!/usr/bin/env python3
"""Fix Unicode quotes in PowerShell script"""

with open(r'c:\VCC\veritas\scripts\start_services.ps1', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace smart quotes with regular quotes
replacements = [
    ('\u201c', '"'),  # Left double quotation mark
    ('\u201d', '"'),  # Right double quotation mark
    ('\u201e', '"'),  # Double low-9 quotation mark
    ('\u2018', "'"),  # Left single quotation mark
    ('\u2019', "'"),  # Right single quotation mark
]

for old, new in replacements:
    content = content.replace(old, new)

with open(r'c:\VCC\veritas\scripts\start_services.ps1', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed Unicode quotes in start_services.ps1")
