# -*- coding: utf-8 -*-
"""
啟動情境模擬訓練系統
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Semiconductor Fault Handling Simulation Training")
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

print("[OK] Loading simulation system...")
print()

from interface.simulation_interface import create_simulation_interface

demo = create_simulation_interface(secom_path)

print("=" * 60)
print("[SUCCESS] Simulation Training System Started!")
print("=" * 60)
print()
print("Features:")
print("  - Natural language input")
print("  - Real-time fault progression")
print("  - Dynamic equipment visualization")
print("  - AI expert advisor with Socratic questioning")
print("  - Automatic evaluation")
print()
print("Example inputs:")
print("  - Check cooling water flow")
print("  - Adjust cooling flow to 5.5")
print("  - Ask expert why temperature rising")
print("  - Shutdown and replace filter")
print()
print("Open your browser and start training!")
print("Press Ctrl+C to stop")
print()

demo.launch(
    server_name="127.0.0.1",
    server_port=None,
    share=False
)
