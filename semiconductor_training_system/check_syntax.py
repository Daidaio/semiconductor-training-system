#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check for JavaScript syntax errors in generated HTML"""

import re

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the <script> section
script_start = content.find('<script>')
script_end = content.find('</script>')

if script_start != -1 and script_end != -1:
    script = content[script_start+8:script_end]
    
    # Split into lines
    lines = script.split('\n')
    
    print(f"Total JavaScript lines: {len(lines)}\n")
    
    # Check each line for incomplete string quotes
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        # Count quotes - should be even unless escaped
        single = line.count("'") - line.count("\\'")
        double = line.count('"') - line.count('\\"')
        
        if single % 2 != 0 or double % 2 != 0:
            print(f"Line {i}: Unbalanced quotes")
            print(f"  Single: {single % 2}, Double: {double % 2}")
            print(f"  Content: {line[:120]}")
            print()
