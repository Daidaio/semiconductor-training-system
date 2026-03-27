#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract and check JavaScript syntax"""

import re

with open('static/viewer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取<script>标签内容
match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if match:
    script_content = match.group(1)
    
    # 写到临时文件然后用Node检查
    with open('temp_script.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("Extracted script to temp_script.js")
    print(f"Script length: {len(script_content)} characters")
    print(f"Script lines: {len(script_content.splitlines())}")
    
    # 查找可能有问题的地方
    lines = script_content.splitlines()
    
    print("\nSearching for potential issues in early part...")
    for i in range(min(150, len(lines))):
        line = lines[i]
        # 查找未平衡的引号或括号或可能有问题的unicode
        if "'" in line or '"' in line:
            if len(line) > 150:
                print(f"Line {i+1}: {line[:150]}...")
            # 检查转义
            if '\\' in line and i < 50:
                print(f"Line {i+1} [HAS BACKSLASH]: {line[:120]}")
