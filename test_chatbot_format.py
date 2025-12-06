# -*- coding: utf-8 -*-
"""
測試 Chatbot 訊息格式
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interface.simulation_interface import SimulationTrainingSystem

# 找資料集
secom_path = None
for path in ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]:
    if Path(path).exists():
        secom_path = path
        break

if not secom_path:
    print("[ERROR] 找不到 uci-secom.csv")
    sys.exit(1)

print("=" * 60)
print("測試 Chatbot 訊息格式")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# 開始新情境
eq, dash, conv_history, log = system.start_new_scenario("medium")

print("\n[測試] 開始新情境後的對話歷史格式：")
print(f"  類型: {type(conv_history)}")
print(f"  長度: {len(conv_history)}")

if len(conv_history) > 0:
    print(f"\n[測試] 第一條訊息：")
    first_msg = conv_history[0]
    print(f"  類型: {type(first_msg)}")
    print(f"  內容: {first_msg}")

    # 檢查格式
    if isinstance(first_msg, dict):
        if "role" in first_msg and "content" in first_msg:
            print("\n[OK] 訊息格式正確！（字典，有 role 和 content）")
        else:
            print("\n[FAIL] 訊息格式錯誤！（字典但缺少 role 或 content）")
    else:
        print(f"\n[FAIL] 訊息格式錯誤！（應該是字典，但是 {type(first_msg)}）")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
