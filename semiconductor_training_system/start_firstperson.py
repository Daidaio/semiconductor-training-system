# -*- coding: utf-8 -*-
"""
啟動 Virtual Fab 第一人稱遊戲訓練系統

使用方式：
    python start_firstperson.py

瀏覽器會自動開啟，或手動前往 http://127.0.0.1:8765/viewer.html
"""

import sys
import os
import webbrowser
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("  Virtual Fab — ASML 第一人稱遊戲訓練系統")
print("=" * 60)
print()

# ── 尋找資料集 ────────────────────────────────────────────────────────────────
_CANDIDATES = [
    "uci-secom.csv",
    "../uci-secom.csv",
    "../../uci-secom.csv",
    str(Path(__file__).parent / "uci-secom.csv"),
]

secom_path = None
for c in _CANDIDATES:
    if os.path.exists(c):
        secom_path = c
        print(f"[OK]  Dataset: {os.path.abspath(c)}")
        break

if secom_path is None:
    print("[ERROR] Cannot find uci-secom.csv")
    sys.exit(1)

os.makedirs("data/student_progress", exist_ok=True)

# ── 啟動遊戲伺服器 ────────────────────────────────────────────────────────────
from interface.first_person_interface import start_game

game_url = start_game(secom_path, use_ai_mentor=True, port=8765)

print()
print("=" * 60)
print("  [SUCCESS] Virtual Fab 已啟動！")
print("=" * 60)
print()
print(f"  遊戲網址: {game_url}")
print()
print("  操作說明:")
print("    WASD      — 移動")
print("    滑鼠      — 旋轉視角（點擊畫面鎖定）")
print("    E         — 檢查靠近的設備部件")
print("    C         — 與 AI 學長對話")
print("    ESC       — 暫停 / 解鎖滑鼠")
print()
print("  按 Ctrl+C 關閉伺服器")
print()

# 3 秒後自動開瀏覽器
def _open():
    import time; time.sleep(2)
    webbrowser.open(game_url)

threading.Thread(target=_open, daemon=True).start()

try:
    threading.Event().wait()
except KeyboardInterrupt:
    print("\n[BYE] 訓練系統已關閉。")
