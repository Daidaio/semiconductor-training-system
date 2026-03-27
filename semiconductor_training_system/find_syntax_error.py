#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find JavaScript syntax errors"""

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Checking lines 450-2200 for syntax issues...")

# State machine to track if we're in a string
in_single = False
in_double = False

for i in range(452, min(2200, len(lines))):
    line = lines[i]
    
    j = 0
    while j < len(line):
        char = line[j]
        
        # Handle escape sequences
        if j > 0 and line[j-1] == '\\':
            j += 1
            continue
        
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == '\n' and (in_single or in_double):
            print(f"Line {i+1}: String literal broken across lines!")
            print(f"  Prev: {lines[i][:100]}")
            print(f"  Next: {lines[i+1][:100]}")
            print()
        
        j += 1
