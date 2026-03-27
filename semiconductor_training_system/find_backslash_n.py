#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find syntax errors in HTML"""

import re

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有 backslash-n 序列（可能导致问题的）
pattern = r"(['\"]).*?\\n.*?\1"
matches = re.findall(pattern, content, re.DOTALL)
print(f"Found {len(matches)} potential backslash-n in strings")

# 更精确：查找在字符串内的 backslash-n
lines = content.split('\n')
print(f"\nSearching through {len(lines)} lines...")

for i, line in enumerate(lines[1020:1100], start=1021):
    # 查找 \n 但不是在注释中
    if '\\n' in line and not line.strip().startswith('//'):
        print(f"Line {i}: {line[:120]}")
