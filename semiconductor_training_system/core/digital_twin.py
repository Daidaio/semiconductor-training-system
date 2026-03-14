"""
曝光機數位孿生模擬器 (Lithography Equipment Digital Twin)
高擬真版本 - 基於 SECOM 真實資料

功能:
1. 模擬 590 個感測器參數
2. 支援正常/異常狀態切換
3. 即時參數更新與監控
4. 故障注入模擬
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class SensorSpec:
    """感測器規格定義"""
    sensor_id: str
    name: str
    unit: str
    normal_range: Tuple[float, float]
    critical_range: Tuple[float, float]
    category: str  # pressure, temperature, flow, electrical, optical


class LithographyDigitalTwin:
    """曝光機數位孿生系統"""

    def __init__(self, secom_data_path: str):
        """
        初始化數位孿生系統

        Args:
            secom_data_path: SECOM 資料集路徑
        """
        self.df = pd.read_csv(secom_data_path)
        self.sensor_cols = [col for col in self.df.columns if col not in ['Time', 'Pass/Fail']]

        # 建立感測器規格
        self.sensor_specs = self._build_sensor_specs()

        # 當前狀態
        self.current_state = {}
        self.is_fault = False
        self.fault_type = None
        self.fault_sensors = []

        # 歷史記錄
        self.operation_log = []

        # 初始化為正常狀態
        self._initialize_normal_state()

    def _build_sensor_specs(self) -> Dict[str, SensorSpec]:
        """建立感測器規格（基於真實資料統計）"""
        specs = {}

        # 從資料中提取統計資訊
        normal_data = self.df[self.df['Pass/Fail'] == -1]

        for sensor_id in self.sensor_cols:
            values = normal_data[sensor_id].dropna()

            if len(values) == 0:
                continue

            mean = values.mean()
            std = values.std()

            # 根據感測器 ID 分類（簡化版，可根據實際需求調整）
            category = self._categorize_sensor(sensor_id, mean, std)

            # 正常範圍: μ ± 2σ
            normal_range = (mean - 2*std, mean + 2*std)
            # 臨界範圍: μ ± 3σ
            critical_range = (mean - 3*std, mean + 3*std)

            specs[sensor_id] = SensorSpec(
                sensor_id=sensor_id,
                name=f"Sensor_{sensor_id}",
                unit=self._get_sensor_unit(sensor_id, category),
                normal_range=normal_range,
                critical_range=critical_range,
                category=category
            )

        return specs

    def _categorize_sensor(self, sensor_id: str, mean: float, std: float) -> str:
        """根據統計特性自動分類感測器"""
        # 簡化版分類邏輯（可根據領域知識優化）
        sensor_num = int(sensor_id)

        if sensor_num < 100:
            return "chamber_pressure"
        elif sensor_num < 200:
            return "temperature"
        elif sensor_num < 300:
            return "flow_rate"
        elif sensor_num < 400:
            return "electrical"
        elif sensor_num < 500:
            return "optical_intensity"
        else:
            return "alignment_accuracy"

    def _get_sensor_unit(self, sensor_id: str, category: str) -> str:
        """根據類別返回單位"""
        units = {
            "chamber_pressure": "mTorr",
            "temperature": "°C",
            "flow_rate": "sccm",
            "electrical": "V",
            "optical_intensity": "mW/cm²",
            "alignment_accuracy": "nm"
        }
        return units.get(category, "")

    def _initialize_normal_state(self):
        """初始化為正常狀態"""
        normal_data = self.df[self.df['Pass/Fail'] == -1]

        # 隨機選擇一筆正常資料作為初始狀態
        sample = normal_data.sample(1).iloc[0]

        for sensor_id in self.sensor_cols:
            if sensor_id in self.sensor_specs:
                self.current_state[sensor_id] = float(sample[sensor_id]) if pd.notna(sample[sensor_id]) else 0.0

        self.is_fault = False
        self.fault_type = None
        self.fault_sensors = []

    def inject_fault(self, fault_scenario: str) -> Dict:
        """
        注入故障情境

        Args:
            fault_scenario: 故障情境名稱 (例如: "vacuum_leak", "temperature_spike", "alignment_drift")

        Returns:
            故障注入結果
        """
        # 從真實異常資料中選擇一筆
        fault_data = self.df[self.df['Pass/Fail'] == 1]

        if len(fault_data) == 0:
            return {"error": "No fault data available"}

        # 隨機選擇一筆異常資料
        fault_sample = fault_data.sample(1).iloc[0]

        # 更新狀態
        for sensor_id in self.sensor_cols:
            if sensor_id in self.sensor_specs:
                self.current_state[sensor_id] = float(fault_sample[sensor_id]) if pd.notna(fault_sample[sensor_id]) else 0.0

        self.is_fault = True
        self.fault_type = fault_scenario

        # 識別異常的感測器
        self.fault_sensors = self._identify_fault_sensors()

        # 記錄操作
        self.operation_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": "fault_injected",
            "fault_type": fault_scenario,
            "affected_sensors": len(self.fault_sensors)
        })

        return {
            "status": "fault_injected",
            "fault_type": fault_scenario,
            "affected_sensors": len(self.fault_sensors),
            "critical_sensors": [s for s in self.fault_sensors if self._is_critical(s)]
        }

    def _identify_fault_sensors(self) -> List[str]:
        """識別超出正常範圍的感測器"""
        fault_sensors = []

        for sensor_id, value in self.current_state.items():
            if sensor_id in self.sensor_specs:
                spec = self.sensor_specs[sensor_id]
                if value < spec.normal_range[0] or value > spec.normal_range[1]:
                    fault_sensors.append(sensor_id)

        return fault_sensors

    def _is_critical(self, sensor_id: str) -> bool:
        """判斷感測器是否超出臨界範圍"""
        if sensor_id not in self.sensor_specs:
            return False

        spec = self.sensor_specs[sensor_id]
        value = self.current_state.get(sensor_id, 0)

        return value < spec.critical_range[0] or value > spec.critical_range[1]

    def get_sensor_status(self, sensor_id: str) -> Dict:
        """
        取得單一感測器狀態

        Args:
            sensor_id: 感測器 ID

        Returns:
            感測器詳細資訊
        """
        if sensor_id not in self.sensor_specs:
            return {"error": f"Sensor {sensor_id} not found"}

        spec = self.sensor_specs[sensor_id]
        value = self.current_state.get(sensor_id, 0)

        # 判斷狀態
        if value < spec.critical_range[0] or value > spec.critical_range[1]:
            status = "CRITICAL"
        elif value < spec.normal_range[0] or value > spec.normal_range[1]:
            status = "WARNING"
        else:
            status = "NORMAL"

        return {
            "sensor_id": sensor_id,
            "name": spec.name,
            "category": spec.category,
            "current_value": round(value, 4),
            "unit": spec.unit,
            "status": status,
            "normal_range": spec.normal_range,
            "critical_range": spec.critical_range,
            "deviation": round(abs(value - np.mean(spec.normal_range)) / (spec.normal_range[1] - spec.normal_range[0]) * 100, 2)
        }

    def get_all_sensors_summary(self) -> Dict:
        """取得所有感測器概覽"""
        summary = {
            "total_sensors": len(self.sensor_specs),
            "normal": 0,
            "warning": 0,
            "critical": 0,
            "is_fault": self.is_fault,
            "fault_type": self.fault_type
        }

        for sensor_id in self.sensor_specs.keys():
            status = self.get_sensor_status(sensor_id)
            if status["status"] == "NORMAL":
                summary["normal"] += 1
            elif status["status"] == "WARNING":
                summary["warning"] += 1
            elif status["status"] == "CRITICAL":
                summary["critical"] += 1

        return summary

    def get_sensors_by_category(self, category: str) -> List[Dict]:
        """取得特定類別的所有感測器"""
        sensors = []

        for sensor_id, spec in self.sensor_specs.items():
            if spec.category == category:
                sensors.append(self.get_sensor_status(sensor_id))

        return sensors

    def perform_action(self, action: str, params: Dict = None) -> Dict:
        """
        執行操作動作

        Args:
            action: 動作名稱 (例如: "adjust_pressure", "reset_system", "emergency_stop")
            params: 動作參數

        Returns:
            執行結果
        """
        params = params or {}

        # 記錄操作
        self.operation_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "params": params
        })

        if action == "reset_system":
            self._initialize_normal_state()
            return {"status": "success", "message": "System reset to normal state"}

        elif action == "adjust_sensor":
            sensor_id = params.get("sensor_id")
            new_value = params.get("value")

            if sensor_id in self.current_state:
                old_value = self.current_state[sensor_id]
                self.current_state[sensor_id] = new_value
                return {
                    "status": "success",
                    "sensor_id": sensor_id,
                    "old_value": old_value,
                    "new_value": new_value
                }
            else:
                return {"status": "error", "message": f"Sensor {sensor_id} not found"}

        elif action == "emergency_stop":
            # 模擬緊急停機
            return {"status": "success", "message": "Emergency stop executed"}

        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def get_operation_log(self, last_n: int = 10) -> List[Dict]:
        """取得操作記錄"""
        return self.operation_log[-last_n:]

    def export_current_state(self) -> Dict:
        """匯出當前完整狀態"""
        return {
            "timestamp": datetime.now().isoformat(),
            "is_fault": self.is_fault,
            "fault_type": self.fault_type,
            "sensors": self.current_state,
            "summary": self.get_all_sensors_summary()
        }


if __name__ == "__main__":
    # 測試程式
    twin = LithographyDigitalTwin("../../../uci-secom.csv")

    print("=== 曝光機數位孿生系統測試 ===\n")

    # 1. 檢查初始狀態
    print("1. 初始狀態:")
    summary = twin.get_all_sensors_summary()
    print(f"   總感測器: {summary['total_sensors']}")
    print(f"   正常: {summary['normal']}, 警告: {summary['warning']}, 臨界: {summary['critical']}\n")

    # 2. 注入故障
    print("2. 注入故障:")
    result = twin.inject_fault("vacuum_leak")
    print(f"   故障類型: {result['fault_type']}")
    print(f"   影響感測器: {result['affected_sensors']}\n")

    # 3. 檢查故障後狀態
    print("3. 故障後狀態:")
    summary = twin.get_all_sensors_summary()
    print(f"   正常: {summary['normal']}, 警告: {summary['warning']}, 臨界: {summary['critical']}\n")

    # 4. 查看壓力類感測器
    print("4. 壓力類感測器狀態 (前 5 個):")
    pressure_sensors = twin.get_sensors_by_category("chamber_pressure")
    for sensor in pressure_sensors[:5]:
        print(f"   {sensor['sensor_id']}: {sensor['current_value']} {sensor['unit']} - {sensor['status']}")
