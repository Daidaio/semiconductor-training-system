# -*- coding: utf-8 -*-
"""
測試停機確認流程
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
print("Test Shutdown Confirmation Flow")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# 開始新情境
print("\n[Step 1] Starting new scenario...")
eq, dash, eq_status, conv_history, log = system.start_new_scenario("medium")
print(f"  Initial conversation: {len(conv_history)} messages")

# 第一次嘗試停機（應該要求確認）
print("\n[Step 2] First shutdown attempt: '停機'")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "停機", eq, dash, eq_status, conv_history, log
)

print(f"  Conversation messages: {len(conv_history)}")
if len(conv_history) >= 2:
    last_msg = conv_history[-1]["content"]
    if "確認停機" in last_msg:
        print("  [OK] System asked for confirmation")
        print(f"  Message preview: {last_msg[:100]}...")
    else:
        print("  [FAIL] System didn't ask for confirmation")
        print(f"  Message: {last_msg}")
else:
    print("  [FAIL] No conversation added")

# 確認停機
print("\n[Step 3] Confirm shutdown: '確認停機'")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "確認停機", eq, dash, eq_status, conv_history, log
)

print(f"  Conversation messages: {len(conv_history)}")
if len(conv_history) >= 4:
    last_msg = conv_history[-1]["content"]
    print(f"  Last message preview: {last_msg[:150]}...")

    if "停機" in last_msg and "確認" not in last_msg:
        print("  [OK] Shutdown executed")
    else:
        print("  [?] Unexpected message")
else:
    print("  [FAIL] Shutdown not executed properly")

# 測試後續操作能否繼續
print("\n[Step 4] Test if system still responsive after shutdown")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "學長，停機後該做什麼", eq, dash, eq_status, conv_history, log
)

print(f"  Conversation messages: {len(conv_history)}")
if len(conv_history) > 4:
    print("  [OK] System still responsive")
else:
    print("  [FAIL] System not responding")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
