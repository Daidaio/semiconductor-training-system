#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check for unbalanced quotes"""

with open('temp_script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Checking {len(lines)} lines for quote issues...\n")

for i, line in enumerate(lines, 1):
    # Count quotes (ignoring escaped quotes for simplicity - may need better approach)
    line_clean = line.replace("\\'", "").replace('\\"', '')
    
    single_count = line_clean.count("'")
    double_count = line_clean.count('"')
    
    # Report unbalanced
    if single_count % 2 != 0 or double_count % 2 != 0:
        if i < 100 or i > 1700:  # First 100 or last 35 lines
            print(f"Line {i}: unbalanced (' count={single_count}, \" count={double_count})")
            print(f"  Content: {line.rstrip()[:120]}")
            print()
