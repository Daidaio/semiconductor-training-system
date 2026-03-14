# -*- coding: utf-8 -*-
"""
檢查介面組件類型
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr
from interface.simulation_interface import create_simulation_interface

# 找資料集
secom_path = None
for path in ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]:
    from pathlib import Path
    if Path(path).exists():
        secom_path = path
        break

if not secom_path:
    print("[ERROR] 找不到 uci-secom.csv")
    sys.exit(1)

print("=" * 60)
print("檢查介面組件")
print("=" * 60)

demo = create_simulation_interface(secom_path)

# 檢查組件類型
print("\n檢查 Gradio Blocks 中的組件：")
print(f"總組件數：{len(demo.blocks)}")

for i, (block_id, block) in enumerate(demo.blocks.items()):
    component_type = type(block).__name__
    label = getattr(block, 'label', '無標籤')

    if 'Chatbot' in component_type or 'Textbox' in component_type or 'HTML' in component_type:
        print(f"  [{i}] {component_type}: {label}")

print("\n" + "=" * 60)
print("如果看到 'Chatbot: 對話歷史'，表示修改成功！")
print("如果看到 'Textbox: 系統訊息'，表示還在使用舊版。")
print("=" * 60)
