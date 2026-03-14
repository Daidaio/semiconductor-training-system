# -*- coding: utf-8 -*-
"""
啟動情境模擬訓練系統
"""

import sys
import os
import tempfile
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
print("  - AI 情境學長 - 像學長般自然引導！")
print("  - Automatic evaluation")
print()
print("AI 學長模式:")
print("  - 支援本地 LLM (Qwen/Ollama) 或 Claude API")
print("  - 自然對話，就像學長在旁邊一起處理")
print("  - 會反問、引導思考，不直接給答案")
print("  - 適時給予肯定和建議")
print()
print("Example inputs (支援口語化表達!):")
print("  正式： 檢查冷卻水流量")
print("  口語： 冷卻水怎麼樣 / 看一下冷卻水 / 流量正常嗎")
print()
print("  正式： 詢問專家為什麼溫度上升")
print("  口語： 學長，為什麼溫度一直上升 / 問一下該怎麼辦")
print()
print("  正式： 停機更換過濾網")
print("  口語： 先停一下 / 換過濾網 / 換個新的")
print()
print("Open your browser and start training!")
print("Press Ctrl+C to stop")
print()

static_dir = str(Path(__file__).parent / "static")
demo.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False,
    allowed_paths=[static_dir, tempfile.gettempdir()]
)
