#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find actual newlines within strings"""

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

script_start = None
for i, line in enumerate(lines):
    if '<script>' in line:
        script_start = i
        break

if script_start:
    print(f"Script starts at line {script_start + 1}")
    
    # 检查<script>标签后面的内容中是否有problematic patterns
    in_string = False
    string_char = None
    line_num = script_start
    
    for i in range(script_start, min(script_start + 100, len(lines))):
        line = lines[i]
        
        # 查找字符串内含有<br>的地方
        if '<br>' in line and ("'" in line or '"' in line):
            print(f"Line {i+1}: Found <br> in string context")
            print(f"  {line.rstrip()[:120]}")
            
        # 查找单行中有多个\n的地方（escaped newlines）
        if line.count('\\n') > 3:
            print(f"Line {i+1}: Many \\n sequences")
            print(f"  {line.rstrip()[:120]}")
