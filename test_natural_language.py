# -*- coding: utf-8 -*-
"""
測試自然語言控制器的口語化理解能力
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.natural_language_controller import NaturalLanguageController

def test_natural_language():
    """測試各種口語化輸入"""

    nlu = NaturalLanguageController()

    # 測試案例
    test_cases = [
        # 檢查類
        ("冷卻水怎麼樣", "check", "cooling"),
        ("溫度正常嗎", "check", "temperature"),
        ("流量OK嗎", "check", "cooling"),
        ("看一下光源", "check", "light"),
        ("看看過濾網", "check", "filter"),
        ("真空有問題嗎", "check", "vacuum"),

        # 詢問類
        ("學長，為什麼溫度上升", "ask", None),
        ("問一下該怎麼辦", "ask", None),
        ("有什麼建議嗎", "ask", None),
        ("這是什麼原因", "ask", None),
        ("請問為什麼", "ask", None),

        # 動作類
        ("先停一下", "shutdown", None),
        ("趕快停", "shutdown", None),
        ("換過濾網", "replace", "filter"),
        ("換個新的濾網", "replace", "filter"),
        ("清一下鏡片", "clean", "lens"),
        ("擦鏡頭", "clean", "lens"),

        # 調整類
        ("調一下流量", "adjust", "cooling_flow"),
        ("改一下溫度", "adjust", "temperature"),

        # 正式用語（應該也要能理解）
        ("檢查冷卻水流量", "check", "cooling"),
        ("詢問專家建議", "ask", None),
        ("更換過濾網", "replace", "filter"),
        ("停機", "shutdown", None),
    ]

    print("=" * 80)
    print("自然語言理解測試")
    print("=" * 80)
    print()

    success_count = 0
    total_count = len(test_cases)

    for user_input, expected_intent, expected_target in test_cases:
        result = nlu.parse_input(user_input)

        intent_match = result["intent"] == expected_intent
        target_match = (expected_target is None) or (result["target"] == expected_target)

        success = intent_match and target_match

        if success:
            success_count += 1
            status = "[OK]"
        else:
            status = "[FAIL]"

        print(f"{status} 輸入: 「{user_input}」")
        print(f"  期望: intent={expected_intent}, target={expected_target}")
        print(f"  結果: intent={result['intent']}, target={result['target']}, confidence={result['confidence']:.2f}")

        if not success:
            print(f"  [錯誤] 意圖或目標不符！")

        print()

    print("=" * 80)
    print(f"測試結果: {success_count}/{total_count} 通過 ({success_count/total_count*100:.1f}%)")
    print("=" * 80)

    if success_count == total_count:
        print("\n[SUCCESS] 所有測試通過！自然語言理解功能正常！")
    else:
        print(f"\n[WARNING] 有 {total_count - success_count} 個測試失敗，請檢查！")


if __name__ == "__main__":
    test_natural_language()
