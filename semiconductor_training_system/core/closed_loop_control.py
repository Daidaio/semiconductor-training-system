# -*- coding: utf-8 -*-
"""
閉環控制系統 (Closed-loop Control System)
基於論文 "Digital twin driven intelligent manufacturing" 的閉環控制機制

功能:
1. 即時監控感測器數據 (Real-time Monitoring)
2. 自動故障偵測 (Automatic Fault Detection)
3. 故障告警機制 (Fault Alarm)
4. 診斷建議生成 (Diagnostic Suggestion)
5. 故障處置記錄 (Fault Handling Record)
6. 閉環控制流程 (Closed-loop Control Flow)

閉環流程:
故障告警 (Fault Alarm) → 故障診斷 (Diagnosis) →
故障處理 (Handling) → 故障解除 (Removal) → 記錄 (Logging)
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class AlarmSeverity(Enum):
    """告警嚴重程度"""
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


@dataclass
class AlarmEvent:
    """告警事件"""
    alarm_id: str
    timestamp: str
    parameter_name: str
    current_value: float
    expected_value: float
    deviation_percent: float
    severity: AlarmSeverity
    diagnosis: str
    suggestion: str
    resolved: bool = False
    resolved_timestamp: Optional[str] = None
    handling_duration: Optional[float] = None


class ClosedLoopController:
    """閉環控制器"""

    def __init__(self, sensors, process_db):
        """
        初始化閉環控制器

        Args:
            sensors: 模擬感測器系統 (LithographyEquipmentSensors)
            process_db: 製程參數資料庫 (ProcessParameterDB)
        """
        self.sensors = sensors
        self.process_db = process_db

        # 監控狀態
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 1.0  # 每秒監控一次

        # 告警狀態
        self.active_alarms: Dict[str, AlarmEvent] = {}
        self.alarm_history: List[AlarmEvent] = []
        self.alarm_counter = 0

        # 回調函數
        self.alarm_callback: Optional[Callable] = None
        self.clear_callback: Optional[Callable] = None

        # 統計數據
        self.total_alarms = 0
        self.total_resolved = 0
        self.total_monitoring_time = 0.0
        self.start_time = None

    def start_monitoring(self, interval: float = 1.0,
                        alarm_callback: Callable = None,
                        clear_callback: Callable = None):
        """
        啟動即時監控

        Args:
            interval: 監控間隔 (秒)
            alarm_callback: 告警回調函數 (接收 AlarmEvent)
            clear_callback: 告警解除回調函數 (接收 AlarmEvent)
        """
        if self.is_monitoring:
            print("[Warning] 監控已在執行中")
            return

        self.monitor_interval = interval
        self.alarm_callback = alarm_callback
        self.clear_callback = clear_callback
        self.is_monitoring = True
        self.start_time = time.time()

        def monitor_loop():
            """監控迴圈"""
            while self.is_monitoring:
                # 讀取所有感測器
                current_readings = self.sensors.read_all()

                # 檢查每個參數
                for param_name, value in current_readings.items():
                    self._check_parameter(param_name, value)

                # 等待下次監控
                time.sleep(self.monitor_interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[OK] 閉環監控已啟動 (間隔: {interval} 秒)")

    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        if self.start_time:
            self.total_monitoring_time += time.time() - self.start_time

        print("[OK] 閉環監控已停止")

    def _check_parameter(self, param_name: str, current_value: float):
        """
        檢查參數狀態

        Args:
            param_name: 參數名稱
            current_value: 當前值
        """
        # 向資料庫查詢參數狀態
        status = self.process_db.check_parameter_status(
            "lithography", param_name, current_value
        )

        if status["status"] == "unknown":
            return  # 未知參數,跳過

        # 判斷是否需要告警
        if status["status"] in ["warning", "critical"]:
            # 檢查是否已有告警
            if param_name not in self.active_alarms:
                # 新告警
                self._trigger_alarm(param_name, status)
        else:
            # 正常狀態,檢查是否需要解除告警
            if param_name in self.active_alarms:
                self._clear_alarm(param_name)

    def _trigger_alarm(self, param_name: str, status: Dict):
        """觸發告警"""
        self.alarm_counter += 1
        alarm_id = f"ALARM-{self.alarm_counter:04d}"

        # 生成診斷與建議
        diagnosis, suggestion = self._generate_diagnosis(param_name, status)

        # 建立告警事件
        alarm = AlarmEvent(
            alarm_id=alarm_id,
            timestamp=datetime.now().isoformat(),
            parameter_name=param_name,
            current_value=status["current_value"],
            expected_value=status["optimal_value"],
            deviation_percent=status["deviation_percent"],
            severity=AlarmSeverity.CRITICAL if status["status"] == "critical" else AlarmSeverity.WARNING,
            diagnosis=diagnosis,
            suggestion=suggestion
        )

        # 記錄告警
        self.active_alarms[param_name] = alarm
        self.alarm_history.append(alarm)
        self.total_alarms += 1

        # 輸出告警訊息
        print(f"\n{'='*70}")
        print(f"[ALARM] [{alarm.severity.name}] {alarm_id} - {param_name} 異常")
        print(f"{'='*70}")
        print(f"時間: {alarm.timestamp}")
        print(f"當前值: {alarm.current_value:.4f} {status['unit']}")
        print(f"最佳值: {alarm.expected_value:.4f} {status['unit']}")
        print(f"偏移: {alarm.deviation_percent:.1f}%")
        print(f"診斷: {alarm.diagnosis}")
        print(f"建議: {alarm.suggestion}")
        print(f"{'='*70}\n")

        # 呼叫回調函數
        if self.alarm_callback:
            self.alarm_callback(alarm)

    def _clear_alarm(self, param_name: str):
        """解除告警"""
        if param_name not in self.active_alarms:
            return

        alarm = self.active_alarms[param_name]
        alarm.resolved = True
        alarm.resolved_timestamp = datetime.now().isoformat()

        # 計算處理時間
        start = datetime.fromisoformat(alarm.timestamp)
        end = datetime.fromisoformat(alarm.resolved_timestamp)
        alarm.handling_duration = (end - start).total_seconds()

        # 移除活動告警
        del self.active_alarms[param_name]
        self.total_resolved += 1

        # 輸出解除訊息
        print(f"\n{'='*70}")
        print(f"[OK] {alarm.alarm_id} - {param_name} 已恢復正常")
        print(f"{'='*70}")
        print(f"告警時間: {alarm.timestamp}")
        print(f"解除時間: {alarm.resolved_timestamp}")
        print(f"處置時長: {alarm.handling_duration:.1f} 秒")
        print(f"{'='*70}\n")

        # 呼叫回調函數
        if self.clear_callback:
            self.clear_callback(alarm)

    def _generate_diagnosis(self, param_name: str, status: Dict) -> tuple:
        """
        生成診斷與建議

        Args:
            param_name: 參數名稱
            status: 狀態字典

        Returns:
            (診斷, 建議) 字串
        """
        current = status["current_value"]
        optimal = status["optimal_value"]
        deviation = status["deviation_percent"]

        # 診斷規則庫
        diagnosis_rules = {
            "cooling_flow": {
                "low": f"冷卻水流量過低 ({current:.1f} L/min < {optimal:.1f} L/min)",
                "high": f"冷卻水流量過高 ({current:.1f} L/min > {optimal:.1f} L/min)"
            },
            "lens_temp": {
                "low": f"鏡頭溫度過低 ({current:.1f}°C < {optimal:.1f}°C)",
                "high": f"鏡頭溫度過高 ({current:.1f}°C > {optimal:.1f}°C)"
            },
            "vacuum_pressure": {
                "low": f"真空度良好 ({current:.2e} Torr)",
                "high": f"真空洩漏 ({current:.2e} Torr > {optimal:.2e} Torr)"
            },
            "light_intensity": {
                "low": f"光源強度衰減 ({current:.1f}% < {optimal:.1f}%)",
                "high": f"光源強度過強 ({current:.1f}% > {optimal:.1f}%)"
            },
            "filter_pressure_drop": {
                "low": f"過濾網壓降過低 ({current:.1f} Pa)",
                "high": f"過濾網堵塞 ({current:.1f} Pa > {optimal:.1f} Pa)"
            }
        }

        # 建議規則庫
        suggestion_rules = {
            "cooling_flow": {
                "low": "1) 檢查冷卻水閥門是否完全開啟\n2) 檢查過濾網是否堵塞\n3) 檢查管路是否有洩漏\n4) 檢查冷卻泵運轉狀態",
                "high": "1) 調整冷卻水閥門\n2) 檢查流量控制器設定"
            },
            "lens_temp": {
                "low": "1) 檢查冷卻水溫度設定\n2) 增加環境溫度",
                "high": "1) 增加冷卻水流量\n2) 降低冷卻水溫度\n3) 檢查鏡頭散熱片\n4) 檢查環境溫度"
            },
            "vacuum_pressure": {
                "low": "真空狀態良好",
                "high": "1) 檢查真空腔體密封圈\n2) 檢查 O-ring 是否老化\n3) 檢查閥門是否關緊\n4) 執行漏率測試 (He leak test)"
            },
            "light_intensity": {
                "low": "1) 檢查光源使用時數\n2) 更換光源模組\n3) 清潔光學元件\n4) 校正光強度計",
                "high": "1) 調整光源功率設定\n2) 檢查光強度計校正"
            },
            "filter_pressure_drop": {
                "low": "過濾網狀態良好",
                "high": "1) 更換 HEPA 過濾網\n2) 清潔預過濾網\n3) 檢查風機轉速"
            }
        }

        # 判斷高低
        direction = "low" if current < optimal else "high"

        # 取得診斷與建議
        diagnosis = diagnosis_rules.get(param_name, {}).get(
            direction,
            f"{param_name} 偏離最佳值 {deviation:.1f}%"
        )

        suggestion = suggestion_rules.get(param_name, {}).get(
            direction,
            f"請調整 {param_name} 至 {optimal:.2f} {status['unit']}"
        )

        return diagnosis, suggestion

    def get_active_alarms(self) -> List[AlarmEvent]:
        """取得所有活動告警"""
        return list(self.active_alarms.values())

    def get_alarm_history(self, limit: int = 100) -> List[AlarmEvent]:
        """取得告警歷史"""
        return self.alarm_history[-limit:]

    def get_statistics(self) -> Dict:
        """取得統計資訊"""
        active_count = len(self.active_alarms)
        total_duration = self.total_monitoring_time
        if self.start_time and self.is_monitoring:
            total_duration += time.time() - self.start_time

        avg_handling_time = 0.0
        if self.total_resolved > 0:
            resolved_alarms = [a for a in self.alarm_history if a.resolved]
            total_handling = sum(a.handling_duration for a in resolved_alarms)
            avg_handling_time = total_handling / len(resolved_alarms)

        return {
            "total_alarms": self.total_alarms,
            "active_alarms": active_count,
            "resolved_alarms": self.total_resolved,
            "total_monitoring_time": total_duration,
            "average_handling_time": avg_handling_time,
            "alarm_rate": self.total_alarms / total_duration if total_duration > 0 else 0.0
        }

    def reset_statistics(self):
        """重置統計資料"""
        self.alarm_history.clear()
        self.total_alarms = 0
        self.total_resolved = 0
        self.total_monitoring_time = 0.0
        self.alarm_counter = 0


# ==================== 測試程式 ====================

if __name__ == "__main__":
    from simulated_sensors import LithographyEquipmentSensors
    from process_database import ProcessParameterDB

    print("=" * 80)
    print("閉環控制系統測試")
    print("=" * 80)

    # 初始化
    sensors = LithographyEquipmentSensors()
    process_db = ProcessParameterDB()
    controller = ClosedLoopController(sensors, process_db)

    print("\n[測試 1] 正常狀態監控")
    print("-" * 80)

    # 啟動監控
    controller.start_monitoring(interval=1.0)

    print("正常運轉中... (5 秒)")
    time.sleep(5)

    print("\n[測試 2] 注入冷卻系統故障")
    print("-" * 80)

    # 注入故障 (流量降低 30%)
    sensors.simulate_cooling_failure(flow_reduction=0.3)

    print("觀察故障偵測與告警... (10 秒)")
    time.sleep(10)

    print("\n[測試 3] 修復故障")
    print("-" * 80)

    # 清除故障
    sensors.clear_all_faults()
    sensors.reset_all()

    print("觀察告警解除... (5 秒)")
    time.sleep(5)

    print("\n[測試 4] 注入真空洩漏故障")
    print("-" * 80)

    # 注入真空洩漏
    sensors.simulate_vacuum_leak(leak_rate=5.0e-7)

    print("觀察真空告警... (5 秒)")
    time.sleep(5)

    # 修復
    sensors.clear_all_faults()
    sensors.reset_all()
    time.sleep(3)

    # 停止監控
    controller.stop_monitoring()

    print("\n[統計資訊]")
    print("-" * 80)
    stats = controller.get_statistics()
    print(f"總告警次數: {stats['total_alarms']}")
    print(f"活動告警: {stats['active_alarms']}")
    print(f"已解除告警: {stats['resolved_alarms']}")
    print(f"總監控時間: {stats['total_monitoring_time']:.1f} 秒")
    print(f"平均處置時間: {stats['average_handling_time']:.1f} 秒")
    print(f"告警發生率: {stats['alarm_rate']:.3f} 次/秒")

    print("\n[告警歷史]")
    print("-" * 80)
    for alarm in controller.get_alarm_history():
        status = "[OK] 已解除" if alarm.resolved else "[ACTIVE] 活動中"
        duration = f"{alarm.handling_duration:.1f}秒" if alarm.resolved else "進行中"
        print(f"{alarm.alarm_id} | {alarm.parameter_name:20s} | "
              f"{alarm.severity.name:8s} | {status} | 處置時長: {duration}")

    print("\n" + "=" * 80)
    print("測試完成!")
    print("=" * 80)
