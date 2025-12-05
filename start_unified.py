# -*- coding: utf-8 -*-
"""
啟動整合訓練系統
理論學習 + 實作訓練 統一介面
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Integrated Semiconductor Training System")
print("Theory Learning + Practice Training")
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

print("[OK] Loading unified training system...")
print()

# 創建必要的目錄
os.makedirs("data/student_progress", exist_ok=True)
os.makedirs("data/sop_documents", exist_ok=True)

from interface.unified_training_interface import create_unified_interface

demo = create_unified_interface(secom_path)

print("=" * 60)
print("[SUCCESS] Integrated Training System Started!")
print("=" * 60)
print()
print("System Features:")
print("  Stage 1: Theory Learning")
print("    - Theory BOT Q&A")
print("    - Knowledge Tests")
print("    - Must pass 70+ to unlock Stage 2")
print()
print("  Stage 2: Practice Training")
print("    - Real fault scenarios")
print("    - Natural language operations")
print("    - AI expert guidance")
print("    - Must score 80+ to complete")
print()
print("  Learning Report:")
print("    - Performance statistics")
print("    - Learning curves")
print("    - Knowledge gaps analysis")
print("    - Improvement recommendations")
print()
print("Open your browser and start training!")
print("Press Ctrl+C to stop")
print()

demo.launch(
    server_name="127.0.0.1",
    server_port=None,
    share=False
)
