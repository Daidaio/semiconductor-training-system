#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check for JavaScript syntax errors"""

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 script 标签
script_start = None
script_end = None

for i, line in enumerate(lines):
    if '<script>' in line:
        script_start = i
    if '</script>' in line and script_start is not None:
        script_end = i
        break

if script_start is None or script_end is None:
    print("Could not find script tags")
else:
    print(f"Script found from line {script_start+1} to {script_end+1}")
    
    # Check specifically around the early part of script
    print("\nFirst 100 lines of script:")
    for i in range(script_start, min(script_start + 100, len(lines))):
        line = lines[i].rstrip()
        if len(line) > 100:
            line = line[:100] + "..."
        print(f"{i+1:4d}: {line}")
