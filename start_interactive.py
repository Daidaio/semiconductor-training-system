# -*- coding: utf-8 -*-
"""
啟動互動式訓練介面
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interface.interactive_training import create_interactive_interface

# 找資料集
secom_paths = ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]
secom_path = None

for path in secom_paths:
    if os.path.exists(path):
        secom_path = path
        break

if not secom_path:
    print("[ERROR] Cannot find uci-secom.csv")
    print("Please download and place it in project directory")
    sys.exit(1)

print("=" * 60)
print("Interactive Semiconductor Training System")
print("=" * 60)
print()
print("[OK] Starting interactive interface...")
print()

demo = create_interactive_interface(secom_path)

print("=" * 60)
print("[SUCCESS] System started!")
print("=" * 60)
print()
print("Open browser and start training!")
print("Press Ctrl+C to stop")
print()

demo.launch(
    server_name="127.0.0.1",
    server_port=None,
    share=False
)
