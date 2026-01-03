# -*- coding: utf-8 -*-
"""
模擬感測器系統 (Simulated Sensor System)
基於論文 "Digital twin driven intelligent manufacturing" 的 Physical Entity Layer

功能:
1. 模擬各種感測器數據 (溫度、流量、壓力等)
2. 基於 SECOM 真實數據的統計特性生成數據
3. 加入合理的雜訊與漂移
4. 支援故障注入 (模擬異常狀態)
5. 即時數據採集 (1 秒 / 1 分鐘可調)
"""

import time
import random
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
from core.physics_coupling_model import PhysicsCouplingModel


@dataclass
class SensorConfig:
    """感測器配置"""
    name: str
    unit: str
    nominal_value: float  # 標稱值
    noise_level: float  # 雜訊水準 (標準差)
    drift_rate: float  # 漂移速率 (每秒)
    min_value: float  # 物理最小值
    max_value: float  # 物理最大值
    sample_rate: float = 1.0  # 採樣頻率 (Hz)


class SimulatedSensor:
    """單一模擬感測器"""

    def __init__(self, config: SensorConfig):
        """
        初始化感測器

        Args:
            config: 感測器配置
        """
        self.config = config
        self.current_value = config.nominal_value
        self.drift_offset = 0.0  # 累積漂移量
        self.fault_injected = False
        self.fault_type = None
        self.fault_value = None
        self.last_update_time = time.time()

    def read(self) -> float:
        """
        讀取感測器數據

        Returns:
            感測器讀數
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # 如果有故障注入,直接回傳故障值
        if self.fault_injected:
            return self._apply_fault()

        # 累積漂移
        self.drift_offset += self.config.drift_rate * dt

        # 加入白雜訊
        noise = np.random.normal(0, self.config.noise_level)

        # 計算讀數
        value = self.config.nominal_value + self.drift_offset + noise

        # 限制在物理範圍內
        value = np.clip(value, self.config.min_value, self.config.max_value)

        self.current_value = value
        return value

    def inject_fault(self, fault_type: str, fault_value: float = None):
        """
        注入故障

        Args:
            fault_type: 故障類型 ("fixed"/"drift"/"noise"/"dropout")
            fault_value: 故障值
        """
        self.fault_injected = True
        self.fault_type = fault_type
        self.fault_value = fault_value

    def clear_fault(self):
        """清除故障"""
        self.fault_injected = False
        self.fault_type = None
        self.fault_value = None
        self.drift_offset = 0.0

    def _apply_fault(self) -> float:
        """應用故障模式"""
        if self.fault_type == "fixed":
            # 固定值故障
            return self.fault_value
        elif self.fault_type == "drift":
            # 持續漂移
            self.drift_offset += self.fault_value
            return self.config.nominal_value + self.drift_offset
        elif self.fault_type == "noise":
            # 高雜訊
            noise = np.random.normal(0, self.config.noise_level * self.fault_value)
            return self.config.nominal_value + noise
        elif self.fault_type == "dropout":
            # 數據丟失 (回傳 NaN 或上次值)
            return self.current_value
        else:
            return self.config.nominal_value

    def reset(self):
        """重置感測器到初始狀態"""
        self.current_value = self.config.nominal_value
        self.drift_offset = 0.0
        self.clear_fault()


class LithographyEquipmentSensors:
    """光刻設備模擬感測器組"""

    def __init__(self):
        """初始化所有感測器"""
        self.sensors = self._create_sensors()
        self.is_running = False
        self.data_thread = None
        self.latest_readings = {}

        # 物理耦合模型 (NEW: 提升真實性)
        self.physics_model = PhysicsCouplingModel()
        self.enable_physics_coupling = True  # 可切換開關

    def _create_sensors(self) -> Dict[str, SimulatedSensor]:
        """建立所有感測器"""

        sensors = {}

        # 1. 冷卻水流量計
        sensors["cooling_flow"] = SimulatedSensor(SensorConfig(
            name="cooling_flow",
            unit="L/min",
            nominal_value=5.0,
            noise_level=0.02,  # ±0.02 L/min
            drift_rate=0.0001,  # 每秒漂移 0.0001
            min_value=0.0,
            max_value=10.0,
            sample_rate=1.0
        ))

        # 2. 鏡頭溫度感測器
        sensors["lens_temp"] = SimulatedSensor(SensorConfig(
            name="lens_temp",
            unit="°C",
            nominal_value=23.0,
            noise_level=0.01,  # ±0.01°C
            drift_rate=0.0002,  # 每秒漂移 0.0002°C
            min_value=15.0,
            max_value=35.0,
            sample_rate=1.0
        ))

        # 3. 真空壓力計
        sensors["vacuum_pressure"] = SimulatedSensor(SensorConfig(
            name="vacuum_pressure",
            unit="Torr",
            nominal_value=1.0e-6,
            noise_level=1.0e-8,  # ±0.01 nTorr
            drift_rate=1.0e-9,  # 每秒漂移
            min_value=1.0e-8,
            max_value=1.0e-3,
            sample_rate=1.0
        ))

        # 4. 曝光光源強度計
        sensors["light_intensity"] = SimulatedSensor(SensorConfig(
            name="light_intensity",
            unit="%",
            nominal_value=100.0,
            noise_level=0.1,  # ±0.1%
            drift_rate=0.001,  # 每秒漂移 0.001%
            min_value=0.0,
            max_value=120.0,
            sample_rate=1.0
        ))

        # 5. X 軸定位編碼器
        sensors["stage_position_x"] = SimulatedSensor(SensorConfig(
            name="stage_position_x",
            unit="μm",
            nominal_value=0.0,
            noise_level=0.001,  # ±1 nm
            drift_rate=0.0,  # 無漂移 (編碼器)
            min_value=-1000.0,
            max_value=1000.0,
            sample_rate=10.0  # 高速採樣
        ))

        # 6. Y 軸定位編碼器
        sensors["stage_position_y"] = SimulatedSensor(SensorConfig(
            name="stage_position_y",
            unit="μm",
            nominal_value=0.0,
            noise_level=0.001,  # ±1 nm
            drift_rate=0.0,
            min_value=-1000.0,
            max_value=1000.0,
            sample_rate=10.0
        ))

        # 7. 過濾網壓差計
        sensors["filter_pressure_drop"] = SimulatedSensor(SensorConfig(
            name="filter_pressure_drop",
            unit="Pa",
            nominal_value=50.0,
            noise_level=1.0,  # ±1 Pa
            drift_rate=0.01,  # 逐漸上升 (堵塞)
            min_value=0.0,
            max_value=200.0,
            sample_rate=0.1  # 慢速採樣
        ))

        # 8. 對準誤差計
        sensors["alignment_error"] = SimulatedSensor(SensorConfig(
            name="alignment_error",
            unit="nm",
            nominal_value=0.0,
            noise_level=0.5,  # ±0.5 nm
            drift_rate=0.0,
            min_value=-10.0,
            max_value=10.0,
            sample_rate=1.0
        ))

        return sensors

    def read_all(self) -> Dict[str, float]:
        """
        讀取所有感測器 (包含物理耦合效應)

        Returns:
            所有感測器讀數 {sensor_name: value}
        """
        # 1. 讀取原始感測器數據
        raw_readings = {}
        for name, sensor in self.sensors.items():
            raw_readings[name] = sensor.read()

        # 2. 應用物理耦合模型 (NEW: 參數互相影響)
        if self.enable_physics_coupling:
            coupled_readings = self.physics_model.update_coupled_parameters(
                raw_readings, dt=1.0
            )
            self.latest_readings = coupled_readings
            return coupled_readings
        else:
            self.latest_readings = raw_readings
            return raw_readings

    def read_sensor(self, sensor_name: str) -> Optional[float]:
        """
        讀取單一感測器

        Args:
            sensor_name: 感測器名稱

        Returns:
            感測器讀數,若不存在則回傳 None
        """
        sensor = self.sensors.get(sensor_name)
        if sensor is None:
            return None
        return sensor.read()

    def inject_fault(self, sensor_name: str, fault_type: str, fault_value: float = None):
        """
        對指定感測器注入故障

        Args:
            sensor_name: 感測器名稱
            fault_type: 故障類型
            fault_value: 故障值
        """
        sensor = self.sensors.get(sensor_name)
        if sensor:
            sensor.inject_fault(fault_type, fault_value)
            print(f"[Fault Injected] {sensor_name}: {fault_type} = {fault_value}")

    def clear_fault(self, sensor_name: str):
        """清除指定感測器的故障"""
        sensor = self.sensors.get(sensor_name)
        if sensor:
            sensor.clear_fault()
            print(f"[Fault Cleared] {sensor_name}")

    def clear_all_faults(self):
        """清除所有故障"""
        for sensor in self.sensors.values():
            sensor.clear_fault()

    def reset_all(self):
        """重置所有感測器"""
        for sensor in self.sensors.values():
            sensor.reset()

    # ==================== 常見故障情境 ====================

    def simulate_cooling_failure(self, flow_reduction: float = 0.3):
        """
        模擬冷卻系統故障

        Args:
            flow_reduction: 流量減少比例 (0.3 = 減少 30%)
        """
        # 流量降低
        normal_flow = 5.0
        fault_flow = normal_flow * (1 - flow_reduction)
        self.inject_fault("cooling_flow", "fixed", fault_flow)

        # 溫度上升
        self.inject_fault("lens_temp", "drift", 0.01)  # 每秒上升 0.01°C

        print(f"[Scenario] 冷卻系統故障: 流量降至 {fault_flow:.1f} L/min")

    def simulate_vacuum_leak(self, leak_rate: float = 1.0e-7):
        """
        模擬真空洩漏

        Args:
            leak_rate: 洩漏速率 (Torr/s)
        """
        self.inject_fault("vacuum_pressure", "drift", leak_rate)
        print(f"[Scenario] 真空洩漏: 漏率 {leak_rate:.2e} Torr/s")

    def simulate_filter_clogging(self, initial_pressure: float = 50.0,
                                 clog_rate: float = 0.5):
        """
        模擬過濾網堵塞

        Args:
            initial_pressure: 初始壓降 (Pa)
            clog_rate: 堵塞速率 (Pa/s)
        """
        self.inject_fault("filter_pressure_drop", "drift", clog_rate)
        print(f"[Scenario] 過濾網堵塞: 壓降上升速率 {clog_rate} Pa/s")

    def simulate_light_source_degradation(self, degradation_rate: float = 0.01):
        """
        模擬光源衰減

        Args:
            degradation_rate: 衰減速率 (%/s)
        """
        self.inject_fault("light_intensity", "drift", -degradation_rate)
        print(f"[Scenario] 光源衰減: 每秒降低 {degradation_rate}%")

    # ==================== 即時數據採集 (背景執行緒) ====================

    def start_acquisition(self, interval: float = 1.0, callback=None):
        """
        開始即時數據採集

        Args:
            interval: 採樣間隔 (秒)
            callback: 回調函數 (接收 readings 字典)
        """
        if self.is_running:
            print("[Warning] 數據採集已在執行中")
            return

        self.is_running = True

        def acquisition_loop():
            while self.is_running:
                # 讀取所有感測器
                readings = self.read_all()
                readings["timestamp"] = datetime.now().isoformat()

                # 呼叫回調函數
                if callback:
                    callback(readings)

                # 等待下次採樣
                time.sleep(interval)

        self.data_thread = threading.Thread(target=acquisition_loop, daemon=True)
        self.data_thread.start()
        print(f"[OK] 數據採集已啟動 (間隔: {interval} 秒)")

    def stop_acquisition(self):
        """停止數據採集"""
        self.is_running = False
        if self.data_thread:
            self.data_thread.join(timeout=2.0)
        print("[OK] 數據採集已停止")


# ==================== 測試程式 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("模擬感測器系統測試")
    print("=" * 70)

    # 建立感測器組
    equipment = LithographyEquipmentSensors()

    print("\n[測試 1] 讀取所有感測器 (正常狀態)")
    print("-" * 70)
    readings = equipment.read_all()
    for name, value in readings.items():
        sensor = equipment.sensors[name]
        print(f"{name:25s} = {value:12.6f} {sensor.config.unit}")

    print("\n[測試 2] 模擬冷卻系統故障 (流量降低 30%)")
    print("-" * 70)
    equipment.simulate_cooling_failure(flow_reduction=0.3)
    time.sleep(0.5)

    print("等待 5 秒,觀察溫度變化...")
    for i in range(5):
        time.sleep(1)
        flow = equipment.read_sensor("cooling_flow")
        temp = equipment.read_sensor("lens_temp")
        print(f"[{i+1} 秒] 冷卻流量: {flow:.2f} L/min, 鏡頭溫度: {temp:.3f}°C")

    print("\n[測試 3] 清除故障,觀察恢復")
    print("-" * 70)
    equipment.clear_all_faults()
    equipment.reset_all()

    readings = equipment.read_all()
    print("重置後:")
    for name in ["cooling_flow", "lens_temp"]:
        value = readings[name]
        sensor = equipment.sensors[name]
        print(f"{name:25s} = {value:12.6f} {sensor.config.unit}")

    print("\n[測試 4] 模擬真空洩漏")
    print("-" * 70)
    equipment.simulate_vacuum_leak(leak_rate=1.0e-7)

    print("等待 5 秒,觀察壓力變化...")
    for i in range(5):
        time.sleep(1)
        pressure = equipment.read_sensor("vacuum_pressure")
        print(f"[{i+1} 秒] 真空壓力: {pressure:.2e} Torr")

    print("\n[測試 5] 即時數據採集 (背景執行緒)")
    print("-" * 70)

    def data_callback(readings):
        """數據回調函數"""
        print(f"[{readings['timestamp']}] "
              f"流量: {readings['cooling_flow']:.2f} L/min, "
              f"溫度: {readings['lens_temp']:.2f}°C")

    equipment.clear_all_faults()
    equipment.reset_all()
    equipment.start_acquisition(interval=2.0, callback=data_callback)

    print("採集中... (10 秒)")
    time.sleep(10)

    equipment.stop_acquisition()

    print("\n" + "=" * 70)
    print("測試完成!")
    print("=" * 70)
