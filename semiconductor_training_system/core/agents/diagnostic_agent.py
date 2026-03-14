"""
診斷專家 Agent
負責分析設備狀態、識別故障原因
"""

import numpy as np
from typing import Dict, List
from .base_agent import BaseAgent, AgentMessage


class DiagnosticAgent(BaseAgent):
    """診斷專家 - 負責故障診斷與根因分析"""

    def __init__(self, api_key: str = None):
        """
        初始化診斷專家

        Args:
            api_key: OpenAI/Claude API 金鑰（選填，用於進階診斷）
        """
        super().__init__(agent_name="DiagnosticAgent", role="Fault Diagnosis Expert")
        self.api_key = api_key

        # 建立故障知識庫
        self.knowledge_base = self._build_fault_knowledge_base()

    def _build_fault_knowledge_base(self) -> Dict:
        """建立故障診斷知識庫"""
        return {
            "vacuum_leak": {
                "symptoms": ["chamber_pressure異常升高", "氣體流量不穩定"],
                "root_causes": ["密封圈老化", "真空閥故障", "管路破損"],
                "severity": "high",
                "affected_subsystems": ["真空系統", "製程腔體"]
            },
            "temperature_spike": {
                "symptoms": ["temperature急劇上升", "加熱器電流異常"],
                "root_causes": ["溫控器故障", "冷卻系統失效", "感測器誤差"],
                "severity": "critical",
                "affected_subsystems": ["溫控系統", "冷卻系統"]
            },
            "alignment_drift": {
                "symptoms": ["alignment_accuracy超出容差", "光學信號弱化"],
                "root_causes": ["振動干擾", "光學元件污染", "機械磨損"],
                "severity": "medium",
                "affected_subsystems": ["對準系統", "光學系統"]
            },
            "optical_intensity_drop": {
                "symptoms": ["optical_intensity下降", "曝光劑量不足"],
                "root_causes": ["光源老化", "光路遮擋", "鏡片污染"],
                "severity": "high",
                "affected_subsystems": ["光學系統", "光源模組"]
            },
            "electrical_fluctuation": {
                "symptoms": ["electrical電壓/電流波動", "控制信號不穩"],
                "root_causes": ["電源供應器異常", "接地不良", "EMI干擾"],
                "severity": "medium",
                "affected_subsystems": ["電力系統", "控制系統"]
            }
        }

    def analyze(self, data: Dict) -> Dict:
        """
        分析設備狀態

        Args:
            data: {
                "sensors": {...},  # 所有感測器數據
                "summary": {...}   # 狀態摘要
            }

        Returns:
            診斷結果
        """
        sensors = data.get("sensors", {})
        summary = data.get("summary", {})

        # 1. 識別異常感測器
        abnormal_sensors = self._identify_abnormal_sensors(sensors)

        # 2. 分類異常
        categorized_faults = self._categorize_faults(abnormal_sensors)

        # 3. 根因分析
        root_cause_analysis = self._analyze_root_cause(categorized_faults)

        # 4. 評估嚴重程度
        severity_assessment = self._assess_severity(categorized_faults, summary)

        return {
            "abnormal_sensors_count": len(abnormal_sensors),
            "abnormal_sensors": abnormal_sensors,
            "fault_categories": categorized_faults,
            "root_cause_analysis": root_cause_analysis,
            "severity": severity_assessment,
            "diagnostic_confidence": self._calculate_confidence(abnormal_sensors)
        }

    def _identify_abnormal_sensors(self, sensors: Dict) -> List[Dict]:
        """識別異常感測器（簡化版，實際會從 digital_twin 取得）"""
        # 這裡簡化處理，實際應從 digital_twin.get_sensor_status 取得
        return []

    def _categorize_faults(self, abnormal_sensors: List) -> Dict:
        """將異常感測器分類到故障類型"""
        categories = {
            "chamber_pressure": [],
            "temperature": [],
            "flow_rate": [],
            "electrical": [],
            "optical_intensity": [],
            "alignment_accuracy": []
        }

        for sensor in abnormal_sensors:
            category = sensor.get("category", "unknown")
            if category in categories:
                categories[category].append(sensor)

        # 過濾空分類
        return {k: v for k, v in categories.items() if len(v) > 0}

    def _analyze_root_cause(self, categorized_faults: Dict) -> List[Dict]:
        """根因分析"""
        root_causes = []

        for category, sensors in categorized_faults.items():
            # 根據異常類別推斷可能的故障類型
            if category == "chamber_pressure":
                root_causes.append({
                    "fault_type": "vacuum_leak",
                    "confidence": 0.85,
                    "evidence": f"{len(sensors)} pressure sensors abnormal",
                    "knowledge": self.knowledge_base.get("vacuum_leak", {})
                })

            elif category == "temperature":
                root_causes.append({
                    "fault_type": "temperature_spike",
                    "confidence": 0.90,
                    "evidence": f"{len(sensors)} temperature sensors abnormal",
                    "knowledge": self.knowledge_base.get("temperature_spike", {})
                })

            elif category == "alignment_accuracy":
                root_causes.append({
                    "fault_type": "alignment_drift",
                    "confidence": 0.75,
                    "evidence": f"{len(sensors)} alignment sensors abnormal",
                    "knowledge": self.knowledge_base.get("alignment_drift", {})
                })

            elif category == "optical_intensity":
                root_causes.append({
                    "fault_type": "optical_intensity_drop",
                    "confidence": 0.80,
                    "evidence": f"{len(sensors)} optical sensors abnormal",
                    "knowledge": self.knowledge_base.get("optical_intensity_drop", {})
                })

            elif category == "electrical":
                root_causes.append({
                    "fault_type": "electrical_fluctuation",
                    "confidence": 0.70,
                    "evidence": f"{len(sensors)} electrical sensors abnormal",
                    "knowledge": self.knowledge_base.get("electrical_fluctuation", {})
                })

        return sorted(root_causes, key=lambda x: x["confidence"], reverse=True)

    def _assess_severity(self, categorized_faults: Dict, summary: Dict) -> str:
        """評估故障嚴重程度"""
        critical_count = summary.get("critical", 0)
        warning_count = summary.get("warning", 0)

        if critical_count > 10:
            return "CRITICAL"
        elif critical_count > 0 or warning_count > 50:
            return "HIGH"
        elif warning_count > 20:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_confidence(self, abnormal_sensors: List) -> float:
        """計算診斷信心度"""
        if len(abnormal_sensors) == 0:
            return 1.0
        elif len(abnormal_sensors) < 10:
            return 0.9
        elif len(abnormal_sensors) < 30:
            return 0.8
        else:
            return 0.7

    def make_decision(self, analysis_result: Dict) -> Dict:
        """
        基於分析結果做出診斷建議

        Args:
            analysis_result: analyze() 的輸出

        Returns:
            診斷建議
        """
        root_causes = analysis_result.get("root_cause_analysis", [])
        severity = analysis_result.get("severity", "UNKNOWN")

        if not root_causes:
            return {
                "diagnosis": "NORMAL",
                "recommendation": "設備運行正常，無需處理",
                "next_steps": []
            }

        # 選擇信心度最高的故障類型
        primary_fault = root_causes[0]

        recommendations = []
        next_steps = []

        # 根據故障類型給出建議
        fault_type = primary_fault["fault_type"]
        knowledge = primary_fault.get("knowledge", {})

        if fault_type == "vacuum_leak":
            recommendations.append("1. 立即停機檢查真空系統")
            recommendations.append("2. 檢查密封圈完整性")
            recommendations.append("3. 執行真空洩漏測試")
            next_steps = ["停機", "洩漏檢測", "更換密封件", "真空測試"]

        elif fault_type == "temperature_spike":
            recommendations.append("1. 降低製程溫度")
            recommendations.append("2. 檢查冷卻系統運作")
            recommendations.append("3. 校驗溫度感測器")
            next_steps = ["降溫", "冷卻系統檢查", "感測器校驗"]

        elif fault_type == "alignment_drift":
            recommendations.append("1. 執行對準校正程序")
            recommendations.append("2. 檢查振動源")
            recommendations.append("3. 清潔光學元件")
            next_steps = ["對準校正", "振動檢查", "光學清潔"]

        elif fault_type == "optical_intensity_drop":
            recommendations.append("1. 檢查光源狀態")
            recommendations.append("2. 清潔光路鏡片")
            recommendations.append("3. 校驗曝光劑量")
            next_steps = ["光源檢查", "鏡片清潔", "劑量校驗"]

        elif fault_type == "electrical_fluctuation":
            recommendations.append("1. 檢查電源穩定性")
            recommendations.append("2. 檢查接地系統")
            recommendations.append("3. 隔離EMI干擾源")
            next_steps = ["電源檢查", "接地檢查", "EMI隔離"]

        return {
            "diagnosis": fault_type.upper(),
            "confidence": primary_fault["confidence"],
            "severity": severity,
            "root_causes": [rc["fault_type"] for rc in root_causes],
            "recommendations": recommendations,
            "next_steps": next_steps,
            "estimated_repair_time": self._estimate_repair_time(fault_type, severity)
        }

    def _estimate_repair_time(self, fault_type: str, severity: str) -> str:
        """估計維修時間"""
        time_matrix = {
            ("vacuum_leak", "CRITICAL"): "4-6 hours",
            ("vacuum_leak", "HIGH"): "2-3 hours",
            ("temperature_spike", "CRITICAL"): "3-5 hours",
            ("temperature_spike", "HIGH"): "1-2 hours",
            ("alignment_drift", "MEDIUM"): "30-60 minutes",
            ("optical_intensity_drop", "HIGH"): "1-2 hours",
            ("electrical_fluctuation", "MEDIUM"): "1-3 hours"
        }
        return time_matrix.get((fault_type, severity), "1-2 hours")

    def _process_message(self, message: AgentMessage) -> Dict:
        """處理來自其他 Agent 的訊息"""
        content = message.content

        if message.message_type == "query":
            # 其他 Agent 請求診斷意見
            return self.analyze(content)

        elif message.message_type == "feedback":
            # 接收操作結果反饋，更新知識庫
            return {"status": "feedback_received"}

        return {"status": "message_processed"}


if __name__ == "__main__":
    # 測試診斷專家
    agent = DiagnosticAgent()

    # 模擬異常數據
    test_data = {
        "sensors": {},
        "summary": {
            "total_sensors": 558,
            "normal": 500,
            "warning": 30,
            "critical": 28
        }
    }

    print("=== 診斷專家測試 ===\n")

    # 執行分析
    analysis = agent.analyze(test_data)
    print("分析結果:")
    print(f"  嚴重程度: {analysis['severity']}")
    print(f"  診斷信心度: {analysis['diagnostic_confidence']}\n")

    # 執行決策
    decision = agent.make_decision(analysis)
    print("診斷建議:")
    print(f"  診斷結果: {decision['diagnosis']}")
    print(f"  信心度: {decision.get('confidence', 'N/A')}")
    print(f"  建議:")
    for rec in decision.get('recommendations', []):
        print(f"    {rec}")
