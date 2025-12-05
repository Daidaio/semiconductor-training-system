# -*- coding: utf-8 -*-
"""
簡易系統測試
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "=" * 60)
print("System Test - Semiconductor Training System")
print("=" * 60)

# Test 1: Digital Twin
print("\nTest 1: Digital Twin...")
try:
    from core.digital_twin import LithographyDigitalTwin
    twin = LithographyDigitalTwin("../uci-secom.csv")
    summary = twin.get_all_sensors_summary()
    print(f"[OK] Digital Twin - {summary['total_sensors']} sensors")
except Exception as e:
    print(f"[FAIL] Digital Twin - {e}")

# Test 2: A2A System
print("\nTest 2: A2A Coordinator...")
try:
    from core.a2a_coordinator import A2ACoordinator
    coordinator = A2ACoordinator()
    print("[OK] A2A Coordinator")
except Exception as e:
    print(f"[FAIL] A2A Coordinator - {e}")

# Test 3: Scenario Generator
print("\nTest 3: Scenario Generator...")
try:
    from core.scenario_generator import ScenarioGenerator
    generator = ScenarioGenerator("../uci-secom.csv")
    scenario = generator.generate_scenario()
    print(f"[OK] Scenario Generator - {scenario['type']}")
except Exception as e:
    print(f"[FAIL] Scenario Generator - {e}")

# Test 4: Scoring System
print("\nTest 4: Scoring System...")
try:
    from evaluation.scoring_system import ScoringSystem
    scorer = ScoringSystem()
    print("[OK] Scoring System")
except Exception as e:
    print(f"[FAIL] Scoring System - {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
