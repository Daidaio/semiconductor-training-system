# -*- coding: utf-8 -*-
"""
測試 SECOM 即時生成器整合
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.simulated_sensors import LithographyEquipmentSensors
import time

print("=" * 70)
print("SECOM 即時生成器整合測試")
print("=" * 70)

# 創建感測器系統（會自動載入 SECOM）
sensors = LithographyEquipmentSensors()

print("\n[測試 1] 正常運行 - 觀察 SECOM 逐秒變動")
print("-" * 70)
print(f"{'時間':>6s} | {'冷卻流量':>10s} | {'溫度':>10s} | {'真空':>12s} | {'光強':>10s}")
print("-" * 70)

for i in range(10):
    readings = sensors.read_all()
    print(f"{i+1:>6d}s | {readings['cooling_flow']:>10.4f} | "
          f"{readings['lens_temp']:>10.4f} | "
          f"{readings['vacuum_pressure']:>12.6e} | "
          f"{readings['light_intensity']:>10.2f}")
    time.sleep(0.5)

print("\n[測試 2] 故障注入 - 觀察 SECOM + 物理耦合效果")
print("-" * 70)
sensors.simulate_cooling_failure(flow_reduction=0.3)

print(f"\n{'時間':>6s} | {'冷卻流量':>10s} | {'溫度變化':>10s} | {'對準誤差':>12s}")
print("-" * 70)

initial_temp = sensors.read_all()['lens_temp']
for i in range(15):
    time.sleep(1)
    readings = sensors.read_all()
    temp_delta = readings['lens_temp'] - initial_temp

    print(f"{i+1:>6d}s | {readings['cooling_flow']:>10.4f} | "
          f"{temp_delta:>+9.4f}°C | "
          f"{readings['alignment_error']:>+11.4f} nm")

print("\n" + "=" * 70)
print("測試完成！")
print("=" * 70)
print("觀察重點:")
print("1. 參數是否平滑變動（SECOM 特性）")
print("2. 故障後是否有連鎖效應（物理耦合）")
print("3. 冷卻↓ → 溫度↑ → 對準誤差↑")
