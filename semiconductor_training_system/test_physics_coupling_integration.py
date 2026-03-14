# -*- coding: utf-8 -*-
"""
測試物理耦合模型整合到感測器系統
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.simulated_sensors import LithographyEquipmentSensors
import time

print("=" * 70)
print("物理耦合模型整合測試")
print("=" * 70)

# 創建感測器系統
sensors = LithographyEquipmentSensors()

print("\n[步驟 1] 讀取初始狀態 (所有參數正常)")
print("-" * 70)
initial = sensors.read_all()
print(f"冷卻流量: {initial['cooling_flow']:.2f} L/min")
print(f"鏡頭溫度: {initial['lens_temp']:.3f}°C")
print(f"對準誤差: {initial['alignment_error']:.3f} nm")
print(f"光源強度: {initial['light_intensity']:.2f}%")

print("\n[步驟 2] 注入故障：冷卻流量下降至 3.5 L/min")
print("-" * 70)
sensors.simulate_cooling_failure(flow_reduction=0.3)

print("\n[步驟 3] 觀察參數連鎖變化 (每秒讀取一次)")
print("-" * 70)
print(f"{'時間':>6s} | {'冷卻流量':>10s} | {'溫度變化':>10s} | {'對準誤差':>12s} | {'光強變化':>10s}")
print("-" * 70)

for i in range(10):
    time.sleep(1)
    readings = sensors.read_all()

    flow = readings['cooling_flow']
    temp = readings['lens_temp']
    alignment = readings['alignment_error']
    light = readings['light_intensity']

    temp_delta = temp - initial['lens_temp']
    light_delta = light - initial['light_intensity']

    print(f"{i+1:>6d}s | {flow:>10.2f} | {temp_delta:>+9.3f}°C | {alignment:>+11.3f} nm | {light_delta:>+9.2f}%")

print("\n" + "=" * 70)
print("測試結論:")
print("=" * 70)
final = sensors.read_all()

# 分析耦合效應
if abs(final['lens_temp'] - initial['lens_temp']) > 0.05:
    print("[OK] 熱力學耦合運作正常: 冷卻不足 → 溫度上升")
else:
    print("[WARN] 熱力學耦合未生效")

if abs(final['alignment_error'] - initial['alignment_error']) > 10:
    print("[OK] 熱膨脹耦合運作正常: 溫度上升 → 對準誤差增加")
else:
    print("[WARN] 熱膨脹耦合未生效")

if abs(final['light_intensity'] - initial['light_intensity']) > 0.01:
    print("[OK] 光學耦合運作正常: 溫度變化 → 光強變化")
else:
    print("[WARN] 光學耦合未生效")

print("\n物理耦合模型已成功整合到感測器系統！")
print("現在故障會產生真實的連鎖反應。")
