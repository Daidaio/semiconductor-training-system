# -*- coding: utf-8 -*-
"""
情境引擎 (Scenario Engine)
管理故障情境的初始化、演進和狀態模擬
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


class ScenarioEngine:
    """情境引擎 - 動態故障演進模擬"""

    def __init__(self, secom_data_path: str):
        """
        初始化情境引擎

        Args:
            secom_data_path: SECOM 資料集路徑
        """
        print("[Init] Scenario engine...")

        # 載入 SECOM 資料
        self.df = pd.read_csv(secom_data_path)
        self.sensor_cols = [col for col in self.df.columns
                           if col not in ['Time', 'Pass/Fail']]

        # 分離正常和故障資料
        self.normal_data = self.df[self.df['Pass/Fail'] == 0]
        self.fault_data = self.df[self.df['Pass/Fail'] == 1]

        print(f"  - Normal samples: {len(self.normal_data)}")
        print(f"  - Fault samples: {len(self.fault_data)}")

        # 故障情境定義
        self.fault_scenarios = self._define_fault_scenarios()

        # 當前情境狀態
        self.current_scenario = None
        self.current_state = None
        self.scenario_start_time = None
        self.progression_stage = 0
        self.time_elapsed = 0  # 秒

        print("[OK] Scenario engine ready!")

    def _define_fault_scenarios(self) -> Dict:
        """定義故障情境"""
        return {
            "cooling_failure": {
                "name": "冷卻系統故障",
                "description": "冷卻水過濾網堵塞導致流量不足",
                "initial_symptoms": ["鏡頭溫度開始上升"],
                "root_cause": "過濾網堵塞",
                "progression": [
                    {
                        "stage": 0,
                        "time": 0,
                        "state": {
                            "lens_temp": 23.5,
                            "cooling_flow": 4.8,
                            "filter_blocked": False,
                            "temp_trend": "stable"
                        },
                        "symptoms": ["溫度略微上升"]
                    },
                    {
                        "stage": 1,
                        "time": 120,  # 2分鐘後
                        "state": {
                            "lens_temp": 24.8,
                            "cooling_flow": 3.5,
                            "filter_blocked": True,
                            "temp_trend": "rising"
                        },
                        "symptoms": ["溫度持續上升", "冷卻水流量下降"]
                    },
                    {
                        "stage": 2,
                        "time": 300,  # 5分鐘後
                        "state": {
                            "lens_temp": 26.2,
                            "cooling_flow": 2.5,
                            "filter_blocked": True,
                            "temp_trend": "rising",
                            "warnings": ["高溫警告"]
                        },
                        "symptoms": ["溫度異常", "流量嚴重不足", "可能影響產品品質"]
                    },
                    {
                        "stage": 3,
                        "time": 600,  # 10分鐘後
                        "state": {
                            "lens_temp": 28.5,
                            "cooling_flow": 2.0,
                            "filter_blocked": True,
                            "temp_trend": "rising",
                            "critical": True,
                            "warnings": ["嚴重高溫", "產品報廢風險"]
                        },
                        "symptoms": ["溫度危險", "設備可能損壞"]
                    }
                ],
                "correct_actions": [
                    "檢查冷卻水系統",
                    "發現流量異常",
                    "檢查過濾網",
                    "停機",
                    "更換過濾網",
                    "重新啟動"
                ],
                "resolution_time": 1800  # 30分鐘
            },

            "vacuum_leak": {
                "name": "真空系統洩漏",
                "description": "密封圈老化導致真空洩漏",
                "initial_symptoms": ["真空壓力下降"],
                "root_cause": "密封圈失效",
                "progression": [
                    {
                        "stage": 0,
                        "time": 0,
                        "state": {
                            "vacuum_pressure": 2e-6,
                            "vacuum_leak": False,
                            "pressure_trend": "stable"
                        },
                        "symptoms": ["真空度略微下降"]
                    },
                    {
                        "stage": 1,
                        "time": 180,
                        "state": {
                            "vacuum_pressure": 5e-6,
                            "vacuum_leak": True,
                            "pressure_trend": "rising"
                        },
                        "symptoms": ["真空洩漏檢測異常", "壓力持續上升"]
                    },
                    {
                        "stage": 2,
                        "time": 360,
                        "state": {
                            "vacuum_pressure": 1e-5,
                            "vacuum_leak": True,
                            "pressure_trend": "rising",
                            "warnings": ["真空度不足"]
                        },
                        "symptoms": ["真空系統異常", "可能影響製程"]
                    },
                    {
                        "stage": 3,
                        "time": 600,
                        "state": {
                            "vacuum_pressure": 5e-5,
                            "vacuum_leak": True,
                            "pressure_trend": "rising",
                            "critical": True,
                            "warnings": ["真空失效", "必須停機"]
                        },
                        "symptoms": ["無法維持真空", "無法繼續生產"]
                    }
                ],
                "correct_actions": [
                    "檢查真空系統",
                    "使用氦氣檢測",
                    "定位洩漏點",
                    "停機",
                    "更換密封圈",
                    "真空測試",
                    "重新啟動"
                ],
                "resolution_time": 3600  # 60分鐘
            },

            "alignment_drift": {
                "name": "對準系統偏移",
                "description": "機械振動導致對準偏移",
                "initial_symptoms": ["對準誤差增加"],
                "root_cause": "機械穩定性問題",
                "progression": [
                    {
                        "stage": 0,
                        "time": 0,
                        "state": {
                            "alignment_error_x": 0.05,
                            "alignment_error_y": 0.03,
                            "alignment_status": "warning"
                        },
                        "symptoms": ["X軸對準誤差略增"]
                    },
                    {
                        "stage": 1,
                        "time": 240,
                        "state": {
                            "alignment_error_x": 0.12,
                            "alignment_error_y": 0.08,
                            "alignment_status": "abnormal"
                        },
                        "symptoms": ["對準誤差超出規格", "產品良率下降"]
                    },
                    {
                        "stage": 2,
                        "time": 480,
                        "state": {
                            "alignment_error_x": 0.25,
                            "alignment_error_y": 0.18,
                            "alignment_status": "critical",
                            "warnings": ["對準失效"]
                        },
                        "symptoms": ["嚴重偏移", "產品無法使用"]
                    }
                ],
                "correct_actions": [
                    "檢查對準系統",
                    "暫停生產",
                    "執行對準校正",
                    "驗證校正結果",
                    "恢復生產"
                ],
                "resolution_time": 900  # 15分鐘
            },

            "optical_contamination": {
                "name": "光學污染",
                "description": "鏡片表面有污染物",
                "initial_symptoms": ["光源強度下降"],
                "root_cause": "環境污染或維護不當",
                "progression": [
                    {
                        "stage": 0,
                        "time": 0,
                        "state": {
                            "light_intensity": 95,
                            "lens_contamination": 0.05,
                            "intensity_trend": "falling"
                        },
                        "symptoms": ["光源強度略降"]
                    },
                    {
                        "stage": 1,
                        "time": 300,
                        "state": {
                            "light_intensity": 85,
                            "lens_contamination": 0.15,
                            "intensity_trend": "falling"
                        },
                        "symptoms": ["曝光不足", "可能影響線寬"]
                    },
                    {
                        "stage": 2,
                        "time": 600,
                        "state": {
                            "light_intensity": 75,
                            "lens_contamination": 0.25,
                            "intensity_trend": "falling",
                            "warnings": ["強度不足"]
                        },
                        "symptoms": ["嚴重曝光不足", "產品報廢"]
                    }
                ],
                "correct_actions": [
                    "檢查光源系統",
                    "檢查鏡片",
                    "停機",
                    "清潔光學鏡片",
                    "驗證光源強度",
                    "重新啟動"
                ],
                "resolution_time": 1200  # 20分鐘
            },

            "power_fluctuation": {
                "name": "電力波動",
                "description": "供電不穩定導致系統異常",
                "initial_symptoms": ["多個參數同時波動"],
                "root_cause": "電源供應問題",
                "progression": [
                    {
                        "stage": 0,
                        "time": 0,
                        "state": {
                            "power_stability": 0.95,
                            "voltage_fluctuation": True,
                            "multiple_alarms": True
                        },
                        "symptoms": ["多個系統同時報警"]
                    },
                    {
                        "stage": 1,
                        "time": 60,
                        "state": {
                            "power_stability": 0.85,
                            "voltage_fluctuation": True,
                            "multiple_alarms": True,
                            "warnings": ["電源不穩"]
                        },
                        "symptoms": ["設備運行不穩定", "有跳機風險"]
                    },
                    {
                        "stage": 2,
                        "time": 180,
                        "state": {
                            "power_stability": 0.70,
                            "voltage_fluctuation": True,
                            "critical": True,
                            "warnings": ["緊急停機風險"]
                        },
                        "symptoms": ["極度不穩定", "需緊急處理"]
                    }
                ],
                "correct_actions": [
                    "識別多系統異常",
                    "懷疑電源問題",
                    "緊急停機",
                    "檢查電源供應",
                    "聯絡設施部門",
                    "等待電源穩定",
                    "重新啟動"
                ],
                "resolution_time": 2400  # 40分鐘
            }
        }

    def initialize_scenario(self, scenario_type: Optional[str] = None,
                           difficulty: str = "medium") -> Dict:
        """
        初始化新情境

        Args:
            scenario_type: 指定情境類型，None 則隨機選擇
            difficulty: 難度等級

        Returns:
            情境資訊
        """
        # 選擇情境
        if scenario_type is None:
            scenario_type = random.choice(list(self.fault_scenarios.keys()))

        self.current_scenario = self.fault_scenarios[scenario_type]
        self.scenario_type = scenario_type
        self.scenario_start_time = datetime.now()
        self.progression_stage = 0
        self.time_elapsed = 0

        # 初始化狀態
        initial_state = self.current_scenario["progression"][0]["state"].copy()

        # 基礎狀態
        self.current_state = {
            "is_running": True,
            "scenario_type": scenario_type,
            "scenario_name": self.current_scenario["name"],
            "start_time": self.scenario_start_time.isoformat(),
            "difficulty": difficulty,
            **initial_state
        }

        # 生成初始警報
        alarm_message = self._generate_alarm_message()

        return {
            "scenario_type": scenario_type,
            "scenario_name": self.current_scenario["name"],
            "description": self.current_scenario["description"],
            "alarm_message": alarm_message,
            "initial_state": self.current_state.copy(),
            "hints": self._generate_hints(difficulty)
        }

    def _generate_alarm_message(self) -> str:
        """生成警報訊息"""
        scenario = self.current_scenario
        symptoms = scenario["initial_symptoms"]

        timestamp = datetime.now().strftime("%H:%M:%S")

        message = f"[警報] [{timestamp}]\n\n"
        message += f"!! {scenario['name']} !!\n\n"

        for symptom in symptoms:
            message += f"- {symptom}\n"

        message += f"\n機台目前正在生產中...\n"
        message += f"你是現場工程師，請立即處理！"

        return message

    def _generate_hints(self, difficulty: str) -> List[str]:
        """根據難度生成提示"""
        if difficulty == "easy":
            return [
                "提示：從基礎檢查開始",
                "提示：注意觀察相關系統的參數"
            ]
        elif difficulty == "medium":
            return [
                "觀察所有異常現象，找出關聯性"
            ]
        else:  # hard
            return []

    def update_progression(self, time_delta: int) -> Dict:
        """
        更新故障演進

        Args:
            time_delta: 經過的時間（秒）

        Returns:
            更新資訊
        """
        self.time_elapsed += time_delta

        # 檢查是否進入下一階段
        progression = self.current_scenario["progression"]
        next_stage = self.progression_stage + 1

        if next_stage < len(progression):
            stage_info = progression[next_stage]

            if self.time_elapsed >= stage_info["time"]:
                # 進入下一階段
                self.progression_stage = next_stage

                # 更新狀態
                self.current_state.update(stage_info["state"])

                # 生成演進訊息
                message = self._generate_progression_message(stage_info)

                return {
                    "progressed": True,
                    "new_stage": next_stage,
                    "message": message,
                    "symptoms": stage_info["symptoms"],
                    "state": self.current_state.copy()
                }

        return {
            "progressed": False,
            "current_stage": self.progression_stage,
            "time_elapsed": self.time_elapsed
        }

    def _generate_progression_message(self, stage_info: Dict) -> str:
        """生成演進訊息"""
        message = "\n[系統狀態更新]\n\n"

        for symptom in stage_info["symptoms"]:
            message += f"!! {symptom}\n"

        if "warnings" in stage_info["state"]:
            message += "\n警告：\n"
            for warning in stage_info["state"]["warnings"]:
                message += f"- {warning}\n"

        if stage_info["state"].get("critical"):
            message += "\n[!!!嚴重警告!!!]\n"
            message += "情況持續惡化，必須立即處理！\n"

        return message

    def apply_action_effect(self, action_result: Dict) -> Dict:
        """
        應用動作效果到情境狀態

        Args:
            action_result: 動作執行結果

        Returns:
            更新後的情境資訊
        """
        if not action_result["success"]:
            return {"state_updated": False}

        # 更新狀態
        state_changes = action_result.get("state_changes", {})
        self.current_state.update(state_changes)

        # 檢查是否解決了問題
        resolved = self._check_resolution()

        return {
            "state_updated": True,
            "current_state": self.current_state.copy(),
            "resolved": resolved
        }

    def _check_resolution(self) -> bool:
        """檢查問題是否已解決"""
        scenario_type = self.scenario_type

        if scenario_type == "cooling_failure":
            # 需要：停機 + 更換過濾網 + 重啟
            if (not self.current_state.get("is_running") and
                not self.current_state.get("filter_blocked")):
                return True

        elif scenario_type == "vacuum_leak":
            # 需要：停機 + 修復洩漏
            if (not self.current_state.get("is_running") and
                not self.current_state.get("vacuum_leak")):
                return True

        elif scenario_type == "alignment_drift":
            # 需要：停機 + 校正
            if (not self.current_state.get("is_running") and
                self.current_state.get("alignment_error_x", 1.0) < 0.05):
                return True

        elif scenario_type == "optical_contamination":
            # 需要：停機 + 清潔
            if (not self.current_state.get("is_running") and
                self.current_state.get("lens_contamination", 1.0) < 0.05):
                return True

        elif scenario_type == "power_fluctuation":
            # 需要：緊急停機
            if not self.current_state.get("is_running"):
                return True

        return False

    def get_current_state(self) -> Dict:
        """取得當前狀態"""
        return self.current_state.copy()

    def get_scenario_info(self) -> Dict:
        """取得情境資訊"""
        if self.current_scenario is None:
            return {}

        return {
            "type": self.scenario_type,
            "name": self.current_scenario["name"],
            "description": self.current_scenario["description"],
            "root_cause": self.current_scenario["root_cause"],
            "correct_actions": self.current_scenario["correct_actions"],
            "current_stage": self.progression_stage,
            "time_elapsed": self.time_elapsed,
            "resolved": self._check_resolution()
        }

    def evaluate_actions(self, action_history: List[Dict]) -> Dict:
        """
        評估學員的動作序列

        Args:
            action_history: 動作歷史記錄

        Returns:
            評估結果
        """
        correct_actions = self.current_scenario["correct_actions"]
        student_actions = [self._extract_action_type(a) for a in action_history]

        # 計算匹配度
        matches = 0
        for correct_action in correct_actions:
            for student_action in student_actions:
                if self._actions_match(correct_action, student_action):
                    matches += 1
                    break

        accuracy = matches / len(correct_actions) if correct_actions else 0

        # 時間評估
        expected_time = self.current_scenario["resolution_time"]
        time_ratio = self.time_elapsed / expected_time if expected_time > 0 else 1

        time_score = max(0, 1.0 - (time_ratio - 1.0) * 0.5) if time_ratio > 1 else 1.0

        # 安全性評估（是否在關鍵時刻停機）
        safety_score = self._evaluate_safety(action_history)

        return {
            "accuracy": accuracy,
            "time_score": time_score,
            "safety_score": safety_score,
            "overall_score": (accuracy * 0.5 + time_score * 0.3 + safety_score * 0.2),
            "matches": matches,
            "total_expected": len(correct_actions),
            "time_elapsed": self.time_elapsed,
            "expected_time": expected_time
        }

    def _extract_action_type(self, action: Dict) -> str:
        """從動作記錄中提取動作類型"""
        # 簡化的動作類型提取
        raw_input = action.get("raw_input", "").lower()

        if "檢查" in raw_input or "查看" in raw_input:
            if "冷卻" in raw_input:
                return "檢查冷卻水系統"
            elif "真空" in raw_input:
                return "檢查真空系統"
            elif "過濾" in raw_input:
                return "檢查過濾網"

        elif "停機" in raw_input:
            return "停機"

        elif "更換" in raw_input:
            if "過濾" in raw_input:
                return "更換過濾網"

        elif "重啟" in raw_input or "啟動" in raw_input:
            return "重新啟動"

        elif "校正" in raw_input:
            return "執行對準校正"

        elif "清潔" in raw_input:
            return "清潔光學鏡片"

        return raw_input

    def _actions_match(self, expected: str, actual: str) -> bool:
        """判斷動作是否匹配"""
        expected_lower = expected.lower()
        actual_lower = actual.lower()

        # 關鍵字匹配
        expected_keywords = expected_lower.split()
        return any(keyword in actual_lower for keyword in expected_keywords)

    def _evaluate_safety(self, action_history: List[Dict]) -> float:
        """評估安全性"""
        # 檢查是否在情況嚴重時及時停機
        critical_stage_reached = self.progression_stage >= 2

        shutdown_executed = any(
            "停機" in action.get("raw_input", "") or "shutdown" in action.get("intent", "")
            for action in action_history
        )

        if critical_stage_reached and not shutdown_executed:
            return 0.5  # 情況嚴重但未停機

        if shutdown_executed:
            return 1.0  # 正確停機

        return 0.8  # 一般情況
