# -*- coding: utf-8 -*-
"""
測試「請問學長」開頭的句子是否正確識別為詢問
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.natural_language_controller import NaturalLanguageController

print("=" * 60)
print("測試「請問學長」詢問意圖識別")
print("=" * 60)

nlu = NaturalLanguageController()

# 測試案例：這些都應該被識別為「詢問學長」(ask intent)
test_cases = [
    "請問學長，甚麼情況會造成對準偏移",
    "學長，為什麼流量會降低",
    "請問專家，這個問題怎麼處理",
    "學長這是什麼原因",
    "什麼情況會造成真空洩漏",
    "怎樣會導致溫度上升",
    "為什麼會引起對準偏移",
    "插頭鬆了嗎",
    "溫度正常嗎",
    "現在還有異常嗎",
]

print("\n測試案例（預期：全部都應該是 ask intent）：\n")

success_count = 0
for i, input_text in enumerate(test_cases, 1):
    result = nlu.parse_input(input_text)

    if result and result["intent"] == "ask":
        status = "[OK]"
        success_count += 1
    else:
        status = "[FAIL]"

    intent = result["intent"] if result else "None"
    target = result.get("target", "None") if result else "None"

    print(f"{status} 測試 {i}: {input_text}")
    print(f"     結果: intent={intent}, target={target}")
    print()

print("=" * 60)
print(f"測試結果: {success_count}/{len(test_cases)} 通過 ({success_count/len(test_cases)*100:.1f}%)")
print("=" * 60)

if success_count == len(test_cases):
    print("\n[SUCCESS] 所有「請問學長」類型的句子都正確識別為詢問！")
else:
    print(f"\n[FAIL] 有 {len(test_cases) - success_count} 個測試失敗")
