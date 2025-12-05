"""
訓練情境生成器
基於 SECOM 真實異常資料生成訓練場景
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import random
from datetime import datetime


class ScenarioGenerator:
    """訓練情境生成器"""

    def __init__(self, secom_data_path: str):
        """
        初始化情境生成器

        Args:
            secom_data_path: SECOM 資料集路徑
        """
        self.df = pd.read_csv(secom_data_path)
        self.sensor_cols = [col for col in self.df.columns if col not in ['Time', 'Pass/Fail']]

        # 分離正常和異常資料
        self.normal_data = self.df[self.df['Pass/Fail'] == -1]
        self.fault_data = self.df[self.df['Pass/Fail'] == 1]

        # 建立情境庫
        self.scenario_templates = self._build_scenario_templates()

        print(f"[OK] 情境生成器初始化完成")
        print(f"  - 正常資料: {len(self.normal_data)} 筆")
        print(f"  - 異常資料: {len(self.fault_data)} 筆")
        print(f"  - 情境範本: {len(self.scenario_templates)} 種")

    def _build_scenario_templates(self) -> Dict:
        """建立情境範本"""
        return {
            "vacuum_leak": {
                "name": "真空洩漏事件",
                "difficulty": "HARD",
                "description": "製程腔體發生真空洩漏，需要快速診斷並處理",
                "story": "你注意到真空計讀數異常上升，警報器開始響起。根據經驗，這可能是真空系統出現洩漏。",
                "learning_objectives": [
                    "識別真空系統異常徵兆",
                    "理解真空洩漏的成因",
                    "掌握洩漏檢測與修復程序"
                ],
                "time_limit": 30  # 分鐘
            },
            "temperature_spike": {
                "name": "溫度異常事件",
                "difficulty": "MEDIUM",
                "description": "製程溫度突然升高，可能影響產品品質",
                "story": "製程進行到一半，你發現晶圓溫度顯示異常，比設定值高出 50°C。如果不及時處理，這批晶圓可能報廢。",
                "learning_objectives": [
                    "識別溫控系統異常",
                    "理解溫度控制原理",
                    "掌握緊急降溫程序"
                ],
                "time_limit": 20
            },
            "alignment_drift": {
                "name": "對準漂移事件",
                "difficulty": "EASY",
                "description": "曝光對準精度超出規格，需要重新校正",
                "story": "品質部門回報最近幾片晶圓的圖形對準誤差超標。檢查後發現對準系統出現漂移。",
                "learning_objectives": [
                    "理解對準系統原理",
                    "掌握校正程序",
                    "熟悉精度檢測方法"
                ],
                "time_limit": 15
            },
            "optical_intensity_drop": {
                "name": "光強度下降事件",
                "difficulty": "MEDIUM",
                "description": "曝光光源強度不足，影響曝光品質",
                "story": "檢查發現曝光劑量監控器顯示光強度只有正常值的 70%。這將導致曝光不足。",
                "learning_objectives": [
                    "理解光學系統運作",
                    "掌握光源檢測方法",
                    "熟悉劑量補償技術"
                ],
                "time_limit": 25
            },
            "electrical_fluctuation": {
                "name": "電氣波動事件",
                "difficulty": "MEDIUM",
                "description": "電源系統出現異常波動",
                "story": "設備運行中出現間歇性的電壓波動，控制系統偶爾出現錯誤訊息。",
                "learning_objectives": [
                    "理解電力系統架構",
                    "掌握電氣故障診斷",
                    "熟悉EMI排除方法"
                ],
                "time_limit": 20
            }
        }

    def generate_scenario(
        self,
        difficulty: str = None,
        scenario_type: str = None,
        student_level: str = "beginner"
    ) -> Dict:
        """
        生成訓練情境

        Args:
            difficulty: 難度 (EASY/MEDIUM/HARD)，None 為隨機
            scenario_type: 情境類型，None 為隨機
            student_level: 學員程度

        Returns:
            完整的訓練情境
        """
        # 選擇情境類型
        if scenario_type is None:
            # 根據難度篩選
            if difficulty:
                available = [k for k, v in self.scenario_templates.items()
                           if v["difficulty"] == difficulty]
            else:
                available = list(self.scenario_templates.keys())

            scenario_type = random.choice(available)

        if scenario_type not in self.scenario_templates:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        template = self.scenario_templates[scenario_type]

        # 從真實資料中選擇對應的異常案例
        fault_sample = self._select_fault_sample()

        # 生成情境
        scenario = {
            "scenario_id": f"SCENARIO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": scenario_type,
            "template": template,
            "difficulty": template["difficulty"],
            "student_level": student_level,
            "initial_state": self._generate_initial_state(fault_sample),
            "expected_diagnosis": scenario_type,
            "time_limit": template["time_limit"],
            "created_at": datetime.now().isoformat()
        }

        return scenario

    def _select_fault_sample(self) -> pd.Series:
        """從異常資料中隨機選擇一筆"""
        if len(self.fault_data) == 0:
            # 如果沒有異常資料，使用正常資料並添加人工異常
            sample = self.normal_data.sample(1).iloc[0]
            return self._inject_artificial_fault(sample)
        else:
            return self.fault_data.sample(1).iloc[0]

    def _inject_artificial_fault(self, sample: pd.Series) -> pd.Series:
        """注入人工異常（當沒有真實異常資料時）"""
        # 隨機選擇幾個感測器注入異常
        fault_sensors = random.sample(self.sensor_cols, k=min(10, len(self.sensor_cols)))

        for sensor in fault_sensors:
            if pd.notna(sample[sensor]):
                # 添加 20-50% 的異常偏移
                deviation = random.uniform(0.2, 0.5) * random.choice([-1, 1])
                sample[sensor] *= (1 + deviation)

        return sample

    def _generate_initial_state(self, fault_sample: pd.Series) -> Dict:
        """生成初始設備狀態"""
        sensors = {}

        for sensor_id in self.sensor_cols:
            if pd.notna(fault_sample[sensor_id]):
                sensors[sensor_id] = float(fault_sample[sensor_id])

        return {
            "sensors": sensors,
            "summary": {
                "total_sensors": len(sensors),
                "is_fault": True,
                "timestamp": datetime.now().isoformat()
            }
        }

    def generate_training_set(
        self,
        n_scenarios: int = 10,
        difficulty_distribution: Dict[str, float] = None
    ) -> List[Dict]:
        """
        生成訓練集

        Args:
            n_scenarios: 生成情境數量
            difficulty_distribution: 難度分布 {"EASY": 0.3, "MEDIUM": 0.5, "HARD": 0.2}

        Returns:
            訓練情境列表
        """
        if difficulty_distribution is None:
            difficulty_distribution = {
                "EASY": 0.3,
                "MEDIUM": 0.5,
                "HARD": 0.2
            }

        # 根據分布生成難度序列
        difficulties = []
        for diff, ratio in difficulty_distribution.items():
            count = int(n_scenarios * ratio)
            difficulties.extend([diff] * count)

        # 補足到目標數量
        while len(difficulties) < n_scenarios:
            difficulties.append("MEDIUM")

        random.shuffle(difficulties)

        # 生成情境
        scenarios = []
        for i, difficulty in enumerate(difficulties):
            scenario = self.generate_scenario(difficulty=difficulty)
            scenario["scenario_number"] = i + 1
            scenarios.append(scenario)

        return scenarios

    def get_scenario_statistics(self, scenarios: List[Dict]) -> Dict:
        """取得情境統計資訊"""
        stats = {
            "total": len(scenarios),
            "by_difficulty": {},
            "by_type": {},
            "average_time_limit": 0
        }

        for scenario in scenarios:
            # 按難度統計
            diff = scenario["difficulty"]
            stats["by_difficulty"][diff] = stats["by_difficulty"].get(diff, 0) + 1

            # 按類型統計
            stype = scenario["type"]
            stats["by_type"][stype] = stats["by_type"].get(stype, 0) + 1

            # 平均時限
            stats["average_time_limit"] += scenario["time_limit"]

        stats["average_time_limit"] /= len(scenarios) if scenarios else 1

        return stats


if __name__ == "__main__":
    # 測試情境生成器
    generator = ScenarioGenerator("../../uci-secom.csv")

    print("\n=== 訓練情境生成器測試 ===\n")

    # 生成單一情境
    print("1. 生成單一情境:")
    scenario = generator.generate_scenario(difficulty="MEDIUM")
    print(f"   情境 ID: {scenario['scenario_id']}")
    print(f"   類型: {scenario['type']}")
    print(f"   難度: {scenario['difficulty']}")
    print(f"   時限: {scenario['time_limit']} 分鐘")
    print(f"   名稱: {scenario['template']['name']}")
    print(f"   描述: {scenario['template']['description']}\n")

    # 生成訓練集
    print("2. 生成訓練集:")
    training_set = generator.generate_training_set(n_scenarios=10)
    stats = generator.get_scenario_statistics(training_set)

    print(f"   總情境數: {stats['total']}")
    print(f"   難度分布:")
    for diff, count in stats["by_difficulty"].items():
        print(f"     - {diff}: {count} 個")
    print(f"   類型分布:")
    for stype, count in stats["by_type"].items():
        print(f"     - {stype}: {count} 個")
    print(f"   平均時限: {stats['average_time_limit']:.1f} 分鐘")
