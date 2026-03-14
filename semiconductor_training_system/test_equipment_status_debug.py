# -*- coding: utf-8 -*-
"""
測試設備狀態顯示功能 - Debug 版本
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
print("Equipment Status Display Test (Debug)")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# Start new scenario
print("\n[Test 1] Starting new scenario...")
eq, dash, eq_status, conv_history, log = system.start_new_scenario("medium")

print(f"  Equipment diagram: {len(eq)} chars")
print(f"  Dashboard: {len(dash)} chars")
print(f"  Equipment status: {len(eq_status)} chars")
print(f"  Conversation history: {len(conv_history)} messages")

# Check initial equipment status
print(f"\n[Debug] Initial equipment_status dict: {system.equipment_status}")

# Execute check action
print("\n[Test 2] Execute check: Check cooling...")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "Check cooling", eq, dash, eq_status, conv_history, log
)

print(f"\n[Debug] After 'Check cooling':")
print(f"  equipment_status dict: {system.equipment_status}")
print(f"  Keys: {list(system.equipment_status.keys())}")

# Try with Chinese
print("\n[Test 3] Execute check: 檢查冷卻水...")
user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
    "檢查冷卻水", eq, dash, eq_status, conv_history, log
)

print(f"\n[Debug] After '檢查冷卻水':")
print(f"  equipment_status dict: {system.equipment_status}")
print(f"  Keys: {list(system.equipment_status.keys())}")

# Check what the NLU controller is parsing
print("\n[Test 4] Testing NLU parsing...")
test_inputs = ["檢查冷卻水", "檢查真空", "檢查溫度", "檢查過濾網"]
for input_text in test_inputs:
    parsed = system.nlu_controller.parse_input(input_text)
    if parsed:
        print(f"  '{input_text}' -> intent: {parsed['intent']}, target: {parsed.get('target', 'None')}")
    else:
        print(f"  '{input_text}' -> None")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
