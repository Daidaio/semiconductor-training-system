# -*- coding: utf-8 -*-
"""
啟動 Virtual Fab 第一人稱操作員視角訓練系統

使用方式：
    python start_firstperson.py

瀏覽器開啟：http://127.0.0.1:7861
"""

import sys
import os
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("  Virtual Fab — ASML Operator Training (First-Person View)")
print("=" * 60)
print()

# ── 尋找資料集 ────────────────────────────────────────────────────────────────
_CANDIDATE_PATHS = [
    "uci-secom.csv",
    "../uci-secom.csv",
    "../../uci-secom.csv",
    str(Path(__file__).parent / "uci-secom.csv"),
]

secom_path = None
for candidate in _CANDIDATE_PATHS:
    if os.path.exists(candidate):
        secom_path = candidate
        print(f"[OK]  Dataset found : {os.path.abspath(candidate)}")
        break

if secom_path is None:
    print("[ERROR] Cannot find uci-secom.csv in any of:")
    for p in _CANDIDATE_PATHS:
        print(f"         {os.path.abspath(p)}")
    print()
    print("Please place uci-secom.csv in the project root directory.")
    sys.exit(1)

# ── 建立必要目錄 ──────────────────────────────────────────────────────────────
os.makedirs("data/student_progress", exist_ok=True)

# ── 載入介面 ──────────────────────────────────────────────────────────────────
print("[OK]  Loading Virtual Fab interface…")
print()

from interface.first_person_interface import create_firstperson_interface

demo = create_firstperson_interface(secom_path, use_ai_mentor=True)

print("=" * 60)
print("  [SUCCESS] Virtual Fab is ready!")
print("=" * 60)
print()
print("  Features:")
print("    - 第一人稱操作員視角（ASML 設備剖面圖）")
print("    - HMI 快捷操作面板（點擊按鈕即執行指令）")
print("    - 定時情境自動演進（模擬真實工廠節奏）")
print("    - AI 學長輔助（蘇格拉底式引導）")
print()
print("  Open your browser: http://127.0.0.1:7861")
print("  Press Ctrl+C to stop.")
print()

demo.launch(
    server_name="127.0.0.1",
    server_port=7861,
    share=False,
    show_error=True,
)
