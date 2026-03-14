# -*- coding: utf-8 -*-
"""
測試用戶具體案例：「請問學長，甚麼情況會造成對準偏移」
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
    print("[ERROR] Cannot find uci-secom.csv")
    sys.exit(1)

print("=" * 60)
print("測試用戶案例")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# 開始新情境
print("\n[Step 1] 開始新情境...")
eq, dash, eq_status, conv_history, log = system.start_new_scenario("medium")
print(f"  Initial conversation: {len(conv_history)} messages")

# 用戶輸入：請問學長，甚麼情況會造成對準偏移
print("\n[Step 2] 用戶輸入：請問學長，甚麼情況會造成對準偏移")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "請問學長，甚麼情況會造成對準偏移", eq, dash, eq_status, conv_history, log
)

print(f"\n[Result]")
print(f"  Conversation history: {len(conv_history)} messages")
print(f"  Equipment status keys: {list(system.equipment_status.keys())}")

# 檢查結果
if len(conv_history) > 1:
    print("\n  [OK] 對話歷史有增加（正確）")
    last_msg = conv_history[-1]
    print(f"  最後一條訊息角色: {last_msg.get('role')}")
    print(f"  最後一條訊息內容: {last_msg.get('content', '')[:150]}...")

    if "學長" in last_msg.get('content', ''):
        print("\n  [SUCCESS] 包含學長回應！")
    else:
        print("\n  [WARNING] 沒有看到學長回應")
else:
    print("\n  [FAIL] 對話歷史沒有增加（錯誤）")

# 檢查設備狀態是否被更新（不應該被更新）
if not system.equipment_status:
    print("\n  [SUCCESS] 設備狀態沒有被更新（正確，因為這是詢問，不是檢查）")
else:
    print(f"\n  [WARNING] 設備狀態意外被更新: {system.equipment_status}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
