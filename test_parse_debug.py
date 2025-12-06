# -*- coding: utf-8 -*-
"""
Debug: 看看「請問學長，甚麼情況會造成對準偏移」是怎麼被解析的
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.natural_language_controller import NaturalLanguageController

print("=" * 60)
print("Debug: 解析過程")
print("=" * 60)

nlu = NaturalLanguageController()

test_input = "請問學長，甚麼情況會造成對準偏移"

print(f"\n原始輸入: {test_input}")

# 測試解析
result = nlu.parse_input(test_input)

print(f"\n解析結果:")
print(f"  Intent: {result['intent']}")
print(f"  Target: {result.get('target', 'None')}")
print(f"  Confidence: {result.get('confidence', 0):.2f}")
print(f"  Raw input: {result.get('raw_input', '')}")

print("\n" + "=" * 60)

# 測試 AI 理解（如果有的話）
print("\n測試 AI 理解:")
from interface.simulation_interface import SimulationTrainingSystem

secom_path = None
for path in ["../uci-secom.csv", "../../uci-secom.csv", "uci-secom.csv"]:
    if Path(path).exists():
        secom_path = path
        break

if secom_path:
    system = SimulationTrainingSystem(secom_path, use_ai_mentor=True)

    # 測試 AI 理解
    if system.ai_mentor:
        scenario_info = {"name": "冷卻系統故障", "current_stage": 1}
        state = {"lens_temp": 26.5}

        ai_result = system.ai_mentor.understand_unclear_input(
            test_input, scenario_info, state
        )

        print(f"  AI 理解結果: {ai_result}")

        if ai_result:
            print(f"  AI 建議: {ai_result['suggestion']}")
