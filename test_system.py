"""
系統測試腳本
驗證所有模組是否正常運作
"""

import sys
from pathlib import Path

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_digital_twin():
    """測試數位孿生模擬器"""
    print("\n" + "=" * 60)
    print("測試 1: 曝光機數位孿生模擬器")
    print("=" * 60)

    try:
        from core.digital_twin import LithographyDigitalTwin

        twin = LithographyDigitalTwin("../uci-secom.csv")

        # 測試基本功能
        summary = twin.get_all_sensors_summary()
        print(f"✅ 初始化成功")
        print(f"   - 感測器數: {summary['total_sensors']}")

        # 測試故障注入
        result = twin.inject_fault("vacuum_leak")
        print(f"✅ 故障注入成功")
        print(f"   - 故障類型: {result['fault_type']}")
        print(f"   - 影響感測器: {result['affected_sensors']} 個")

        # 測試感測器讀取
        status = twin.get_sensor_status("0")
        print(f"✅ 感測器讀取成功")
        print(f"   - 感測器 0 狀態: {status['status']}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_a2a_system():
    """測試 A2A 系統"""
    print("\n" + "=" * 60)
    print("測試 2: A2A 多專家系統")
    print("=" * 60)

    try:
        from core.a2a_coordinator import A2ACoordinator

        coordinator = A2ACoordinator()
        print(f"✅ A2A 協調器初始化成功")

        # 測試診斷專家
        from core.agents.diagnostic_agent import DiagnosticAgent
        diag = DiagnosticAgent()
        print(f"✅ 診斷專家初始化成功")

        # 測試操作專家
        from core.agents.operation_agent import OperationAgent
        op = OperationAgent()
        print(f"✅ 操作專家初始化成功")

        # 測試安全專家
        from core.agents.safety_agent import SafetyAgent
        safety = SafetyAgent()
        print(f"✅ 安全專家初始化成功")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scenario_generator():
    """測試情境生成器"""
    print("\n" + "=" * 60)
    print("測試 3: 訓練情境生成器")
    print("=" * 60)

    try:
        from core.scenario_generator import ScenarioGenerator

        generator = ScenarioGenerator("../uci-secom.csv")
        print(f"✅ 情境生成器初始化成功")

        # 測試情境生成
        scenario = generator.generate_scenario(difficulty="MEDIUM")
        print(f"✅ 情境生成成功")
        print(f"   - 情境類型: {scenario['type']}")
        print(f"   - 難度: {scenario['difficulty']}")
        print(f"   - 名稱: {scenario['template']['name']}")

        # 測試訓練集生成
        training_set = generator.generate_training_set(n_scenarios=5)
        stats = generator.get_scenario_statistics(training_set)
        print(f"✅ 訓練集生成成功")
        print(f"   - 情境數: {stats['total']}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scoring_system():
    """測試評分系統"""
    print("\n" + "=" * 60)
    print("測試 4: 評分系統")
    print("=" * 60)

    try:
        from evaluation.scoring_system import ScoringSystem

        scorer = ScoringSystem()
        print(f"✅ 評分系統初始化成功")

        # 模擬評分
        test_scenario = {
            "scenario_id": "TEST_001",
            "type": "vacuum_leak",
            "difficulty": "MEDIUM",
            "expected_diagnosis": "vacuum_leak",
            "time_limit": 30
        }

        test_actions = [
            {"action": "檢查真空計", "is_correct": True},
            {"action": "執行修復", "is_correct": True}
        ]

        test_diagnosis = {
            "diagnosis": "vacuum_leak",
            "confidence": 0.85,
            "safety": {"required_ppe": []}
        }

        result = scorer.evaluate_session(
            student_id="TEST_STUDENT",
            scenario=test_scenario,
            student_actions=test_actions,
            diagnosis_result=test_diagnosis,
            completion_time=20.0
        )

        print(f"✅ 評分成功")
        print(f"   - 總分: {result['scores']['total']:.1f}")
        print(f"   - 等級: {result['grade']}")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """測試整合流程"""
    print("\n" + "=" * 60)
    print("測試 5: 完整整合流程")
    print("=" * 60)

    try:
        from core.digital_twin import LithographyDigitalTwin
        from core.a2a_coordinator import A2ACoordinator
        from core.scenario_generator import ScenarioGenerator
        from evaluation.scoring_system import ScoringSystem

        # 初始化所有組件
        twin = LithographyDigitalTwin("../uci-secom.csv")
        coordinator = A2ACoordinator()
        generator = ScenarioGenerator("../uci-secom.csv")
        scorer = ScoringSystem()

        print("✅ 所有組件初始化成功")

        # 生成情境
        scenario = generator.generate_scenario()
        print(f"✅ 情境生成: {scenario['type']}")

        # 注入故障
        twin.inject_fault(scenario['type'])
        equipment_state = twin.export_current_state()
        print(f"✅ 故障注入完成")

        # A2A 診斷
        diagnosis = coordinator.start_diagnosis_session(
            equipment_state=equipment_state,
            student_level="beginner"
        )
        print(f"✅ A2A 診斷完成")
        print(f"   - 診斷結果: {diagnosis['session_summary']['fault_type']}")

        # 評分
        evaluation = scorer.evaluate_session(
            student_id="INTEGRATION_TEST",
            scenario=scenario,
            student_actions=[{"action": "test", "is_correct": True}],
            diagnosis_result=diagnosis,
            completion_time=15.0
        )
        print(f"✅ 評分完成: {evaluation['scores']['total']:.1f} 分")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試程式"""
    print("\n" + "=" * 60)
    print("🧪 半導體訓練系統 - 自動測試")
    print("=" * 60)

    tests = [
        ("數位孿生模擬器", test_digital_twin),
        ("A2A 多專家系統", test_a2a_system),
        ("訓練情境生成器", test_scenario_generator),
        ("評分系統", test_scoring_system),
        ("完整整合流程", test_integration)
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 測試發生例外: {e}")
            results.append((name, False))

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"總計: {passed}/{total} 通過")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有測試通過！系統運作正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗，請檢查錯誤訊息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
