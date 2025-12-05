# -*- coding: utf-8 -*-
"""
啟動視覺化訓練介面
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Visual Semiconductor Training System")
print("=" * 60)
print()

# 找資料集
secom_paths = ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]
secom_path = None

for path in secom_paths:
    if os.path.exists(path):
        secom_path = path
        print(f"[OK] Found dataset: {path}")
        break

if not secom_path:
    print("[ERROR] Cannot find uci-secom.csv")
    sys.exit(1)

print("[OK] Loading visual interface...")
print()

from interface.visual_training_interface import create_visual_interface

demo = create_visual_interface(secom_path)

print("=" * 60)
print("[SUCCESS] Visual Training System Started!")
print("=" * 60)
print()
print("Features:")
print("  - Interactive equipment diagram")
print("  - Real-time parameter monitoring")
print("  - Click buttons to perform actions")
print("  - AI expert consultation")
print()
print("Open your browser and enjoy training!")
print("Press Ctrl+C to stop")
print()

demo.launch(
    server_name="127.0.0.1",
    server_port=None,
    share=False
)
