# -*- coding: utf-8 -*-
"""
最終驗證測試：確認「詢問」和「檢查」正確分離
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
print("Final Verification Test")
print("=" * 60)

system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

# 開始新情境
print("\nStarting new scenario...")
eq, dash, eq_status, conv_history, log = system.start_new_scenario("medium")
initial_conv_len = len(conv_history)
print(f"Initial conversation: {initial_conv_len} messages")

# 測試案例
test_cases = [
    {
        "input": "請問學長，甚麼情況會造成對準偏移",
        "expected_type": "ask",
        "should_update_equipment": False,
        "should_add_conversation": True,
    },
    {
        "input": "檢查冷卻水",
        "expected_type": "check",
        "should_update_equipment": True,
        "should_add_conversation": False,
    },
    {
        "input": "流量正常嗎",
        "expected_type": "ask",
        "should_update_equipment": False,
        "should_add_conversation": True,
    },
    {
        "input": "學長，為什麼流量會降低",
        "expected_type": "ask",
        "should_update_equipment": False,
        "should_add_conversation": True,
    },
    {
        "input": "檢查過濾網",
        "expected_type": "check",
        "should_update_equipment": True,
        "should_add_conversation": False,
    },
]

success_count = 0
total_count = len(test_cases)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}: {test['input']}")
    print(f"Expected: {test['expected_type']}")
    print(f"{'='*60}")

    # 記錄測試前狀態
    conv_before = len(conv_history)
    eq_status_before = len(system.equipment_status)

    # 執行輸入
    user_input, eq, dash, eq_status, conv_history, log = system.process_user_input(
        test["input"], eq, dash, eq_status, conv_history, log
    )

    # 檢查結果
    conv_after = len(conv_history)
    eq_status_after = len(system.equipment_status)

    conv_added = conv_after > conv_before
    equipment_updated = eq_status_after > eq_status_before

    # 驗證
    all_checks_pass = True

    if test["should_add_conversation"]:
        if conv_added:
            print(f"  [OK] Conversation added ({conv_before} -> {conv_after})")
        else:
            print(f"  [FAIL] Conversation should be added but wasn't")
            all_checks_pass = False
    else:
        if not conv_added:
            print(f"  [OK] Conversation not added (silent check)")
        else:
            print(f"  [FAIL] Conversation shouldn't be added but was ({conv_before} -> {conv_after})")
            all_checks_pass = False

    if test["should_update_equipment"]:
        if equipment_updated:
            print(f"  [OK] Equipment status updated ({eq_status_before} -> {eq_status_after})")
        else:
            print(f"  [FAIL] Equipment status should be updated but wasn't")
            all_checks_pass = False
    else:
        if not equipment_updated:
            print(f"  [OK] Equipment status not updated")
        else:
            print(f"  [FAIL] Equipment status shouldn't be updated but was ({eq_status_before} -> {eq_status_after})")
            all_checks_pass = False

    if all_checks_pass:
        print(f"\n  [SUCCESS] All checks passed for test {i}")
        success_count += 1
    else:
        print(f"\n  [FAILED] Some checks failed for test {i}")

print("\n" + "=" * 60)
print(f"Final Results: {success_count}/{total_count} tests passed ({success_count/total_count*100:.1f}%)")
print("=" * 60)

if success_count == total_count:
    print("\n[SUCCESS] All tests passed!")
    print("- Ask intents correctly trigger conversation")
    print("- Check intents correctly update equipment status")
    print("- Separation between ask and check is working perfectly!")
else:
    print(f"\n[PARTIAL SUCCESS] {total_count - success_count} tests failed")

print(f"\nFinal state:")
print(f"  Total conversation messages: {len(conv_history)}")
print(f"  Equipment checks performed: {len(system.equipment_status)}")
print(f"  Equipment checked: {list(system.equipment_status.keys())}")
