"""
Render 雲端部署入口
執行方式：python render_start.py
"""
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── 資料集路徑 ──────────────────────────────────────────────────────────────
secom_path = os.environ.get("SECOM_DATA_PATH", "uci-secom.csv")
if not os.path.exists(secom_path):
    print(f"[ERROR] Cannot find dataset: {secom_path}")
    sys.exit(1)

os.makedirs("data/student_progress", exist_ok=True)

# ── 啟動遊戲伺服器 ──────────────────────────────────────────────────────────
from interface.first_person_interface import start_game

port = int(os.environ.get("PORT", 8765))
print(f"[OK] Starting on port {port}…")
start_game(secom_path, use_ai_mentor=True, port=port)

print("[OK] Server running. Press Ctrl+C to stop.")
try:
    threading.Event().wait()
except KeyboardInterrupt:
    print("Stopped.")
