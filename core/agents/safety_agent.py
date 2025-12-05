"""
安全專家 Agent
負責監控操作安全性、提供安全警告
"""

from typing import Dict, List
from .base_agent import BaseAgent, AgentMessage


class SafetyAgent(BaseAgent):
    """安全專家 - 負責監控操作安全與風險控制"""

    def __init__(self):
        super().__init__(agent_name="SafetyAgent", role="Safety & Risk Management Expert")

        # 建立安全規則知識庫
        self.knowledge_base = self._build_safety_knowledge_base()

    def _build_safety_knowledge_base(self) -> Dict:
        """建立安全規則知識庫"""
        return {
            "critical_parameters": {
                "chamber_pressure": {
                    "safe_range": [1e-7, 1e-3],  # Torr
                    "danger_threshold": [1e-3, 760],
                    "risk": "真空破裂可能導致晶圓污染或人員受傷"
                },
                "temperature": {
                    "safe_range": [20, 450],  # °C
                    "danger_threshold": [450, 600],
                    "risk": "高溫可能導致燒傷或設備損壞"
                },
                "electrical": {
                    "safe_range": [0, 500],  # V
                    "danger_threshold": [500, 1000],
                    "risk": "高壓可能導致觸電危險"
                }
            },
            "prohibited_actions": {
                "open_chamber_under_vacuum": {
                    "description": "真空狀態下開啟腔體",
                    "risk_level": "CRITICAL",
                    "consequence": "可能導致內爆、人員受傷",
                    "prevention": "必須先洩壓至大氣壓"
                },
                "adjust_high_voltage_online": {
                    "description": "設備運行中調整高壓參數",
                    "risk_level": "HIGH",
                    "consequence": "觸電風險",
                    "prevention": "必須先斷電並上鎖掛牌"
                },
                "bypass_interlock": {
                    "description": "繞過安全互鎖",
                    "risk_level": "CRITICAL",
                    "consequence": "失去安全保護機制",
                    "prevention": "絕對禁止,違反安全規範"
                },
                "skip_purge_procedure": {
                    "description": "跳過氣體置換程序",
                    "risk_level": "HIGH",
                    "consequence": "可能導致氣體混合爆炸",
                    "prevention": "必須完成完整的purge循環"
                }
            },
            "mandatory_ppe": {
                "vacuum_work": ["防護手套", "安全眼鏡"],
                "temperature_work": ["隔熱手套", "安全眼鏡", "長袖工作服"],
                "electrical_work": ["絕緣手套", "絕緣鞋", "安全眼鏡"],
                "optical_work": ["防UV眼鏡", "防護手套"],
                "chemical_work": ["化學防護手套", "防護面罩", "實驗衣"]
            },
            "emergency_procedures": {
                "vacuum_leak": {
                    "immediate_actions": [
                        "按下緊急停止按鈕",
                        "關閉氣體供應",
                        "疏散人員至安全區域"
                    ],
                    "notify": ["設備工程師", "安全部門"]
                },
                "temperature_runaway": {
                    "immediate_actions": [
                        "關閉加熱器電源",
                        "啟動緊急冷卻",
                        "監控相鄰設備溫度"
                    ],
                    "notify": ["設備工程師", "製程部門"]
                },
                "electrical_shock": {
                    "immediate_actions": [
                        "切斷電源(確保自身安全)",
                        "呼叫醫療支援",
                        "執行CPR(如需要)"
                    ],
                    "notify": ["緊急醫療", "安全部門", "主管"]
                }
            }
        }

    def analyze(self, data: Dict) -> Dict:
        """
        分析操作安全性

        Args:
            data: {
                "proposed_action": "...",
                "current_state": {...},
                "fault_type": "...",
                "severity": "..."
            }

        Returns:
            安全評估結果
        """
        proposed_action = data.get("proposed_action", "")
        current_state = data.get("current_state", {})
        fault_type = data.get("fault_type", "")
        severity = data.get("severity", "")

        # 1. 檢查禁止操作
        prohibited_check = self._check_prohibited_actions(proposed_action)

        # 2. 檢查參數安全性
        parameter_safety = self._check_parameter_safety(current_state)

        # 3. 評估整體風險
        risk_assessment = self._assess_risk(
            proposed_action,
            current_state,
            severity,
            prohibited_check,
            parameter_safety
        )

        # 4. 生成安全建議
        safety_recommendations = self._generate_safety_recommendations(
            fault_type,
            risk_assessment
        )

        return {
            "is_safe": risk_assessment["overall_risk"] in ["LOW", "MEDIUM"],
            "risk_level": risk_assessment["overall_risk"],
            "prohibited_violations": prohibited_check["violations"],
            "parameter_warnings": parameter_safety["warnings"],
            "required_ppe": self._get_required_ppe(fault_type),
            "safety_recommendations": safety_recommendations,
            "emergency_procedure": self.knowledge_base["emergency_procedures"].get(fault_type, {})
        }

    def _check_prohibited_actions(self, action: str) -> Dict:
        """檢查是否違反禁止操作"""
        violations = []

        for prohibited_action, info in self.knowledge_base["prohibited_actions"].items():
            # 簡化版關鍵字匹配
            keywords = {
                "open_chamber_under_vacuum": ["開啟", "打開", "腔體"],
                "adjust_high_voltage_online": ["調整", "高壓", "電壓"],
                "bypass_interlock": ["繞過", "互鎖", "bypass"],
                "skip_purge_procedure": ["跳過", "purge", "置換"]
            }

            if prohibited_action in keywords:
                if all(kw in action for kw in keywords[prohibited_action]):
                    violations.append({
                        "action": prohibited_action,
                        "risk_level": info["risk_level"],
                        "consequence": info["consequence"],
                        "prevention": info["prevention"]
                    })

        return {
            "has_violations": len(violations) > 0,
            "violations": violations
        }

    def _check_parameter_safety(self, current_state: Dict) -> Dict:
        """檢查參數是否在安全範圍"""
        warnings = []

        # 模擬參數檢查（實際應從 digital_twin 取得）
        for param_type, spec in self.knowledge_base["critical_parameters"].items():
            # 這裡簡化處理
            pass

        return {
            "has_warnings": len(warnings) > 0,
            "warnings": warnings
        }

    def _assess_risk(
        self,
        action: str,
        state: Dict,
        severity: str,
        prohibited: Dict,
        parameters: Dict
    ) -> Dict:
        """綜合評估風險等級"""

        # 基礎風險評估
        risk_score = 0

        # 嚴重程度影響
        severity_scores = {
            "CRITICAL": 3,
            "HIGH": 2,
            "MEDIUM": 1,
            "LOW": 0
        }
        risk_score += severity_scores.get(severity, 0)

        # 禁止操作違規
        if prohibited["has_violations"]:
            risk_score += 3

        # 參數警告
        if parameters["has_warnings"]:
            risk_score += len(parameters["warnings"])

        # 計算整體風險
        if risk_score >= 5:
            overall_risk = "CRITICAL"
        elif risk_score >= 3:
            overall_risk = "HIGH"
        elif risk_score >= 1:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        return {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "factors": {
                "severity": severity,
                "prohibited_violations": prohibited["has_violations"],
                "parameter_warnings": parameters["has_warnings"]
            }
        }

    def _get_required_ppe(self, fault_type: str) -> List[str]:
        """取得所需個人防護裝備"""
        ppe_mapping = {
            "vacuum_leak": self.knowledge_base["mandatory_ppe"]["vacuum_work"],
            "temperature_spike": self.knowledge_base["mandatory_ppe"]["temperature_work"],
            "electrical_fluctuation": self.knowledge_base["mandatory_ppe"]["electrical_work"],
            "optical_intensity_drop": self.knowledge_base["mandatory_ppe"]["optical_work"],
            "alignment_drift": self.knowledge_base["mandatory_ppe"]["optical_work"]
        }

        return ppe_mapping.get(fault_type, ["安全眼鏡", "防護手套"])

    def _generate_safety_recommendations(
        self,
        fault_type: str,
        risk_assessment: Dict
    ) -> List[str]:
        """生成安全建議"""
        recommendations = []

        risk_level = risk_assessment["overall_risk"]

        if risk_level == "CRITICAL":
            recommendations.append("⚠️ 高風險操作！請主管在場監督")
            recommendations.append("⚠️ 確保緊急停止按鈕可正常觸及")

        if risk_level in ["CRITICAL", "HIGH"]:
            recommendations.append("✓ 執行操作前完成安全檢查清單")
            recommendations.append("✓ 準備好緊急應變程序")

        # 根據故障類型添加特定建議
        if fault_type == "vacuum_leak":
            recommendations.append("✓ 確認腔體已完全洩壓")
            recommendations.append("✓ 檢查氣體供應已關閉")

        elif fault_type == "temperature_spike":
            recommendations.append("✓ 確認冷卻系統運作正常")
            recommendations.append("✓ 避免快速溫度變化")

        elif fault_type == "electrical_fluctuation":
            recommendations.append("✓ 執行前完成電氣隔離")
            recommendations.append("✓ 使用絕緣工具")

        return recommendations

    def make_decision(self, analysis_result: Dict) -> Dict:
        """
        基於安全分析做出決策

        Args:
            analysis_result: analyze() 的輸出

        Returns:
            安全決策
        """
        is_safe = analysis_result["is_safe"]
        risk_level = analysis_result["risk_level"]

        if not is_safe:
            return {
                "decision": "REJECT",
                "reason": "操作存在安全風險",
                "risk_level": risk_level,
                "violations": analysis_result["prohibited_violations"],
                "required_actions": [
                    "重新評估操作步驟",
                    "消除安全風險",
                    "取得主管批准"
                ]
            }

        elif risk_level in ["HIGH", "CRITICAL"]:
            return {
                "decision": "APPROVE_WITH_CONDITIONS",
                "reason": "可執行但需滿足安全條件",
                "risk_level": risk_level,
                "conditions": [
                    "主管監督",
                    "完成安全檢查清單",
                    "準備緊急應變程序"
                ],
                "required_ppe": analysis_result["required_ppe"]
            }

        else:
            return {
                "decision": "APPROVE",
                "reason": "操作安全可行",
                "risk_level": risk_level,
                "required_ppe": analysis_result["required_ppe"]
            }

    def monitor_realtime(self, sensor_data: Dict) -> Dict:
        """即時監控安全狀態"""
        alerts = []

        # 檢查關鍵參數
        for param_type, spec in self.knowledge_base["critical_parameters"].items():
            # 實際應從 sensor_data 取得數值
            pass

        return {
            "status": "SAFE" if len(alerts) == 0 else "WARNING",
            "alerts": alerts,
            "timestamp": "2024-01-01T00:00:00"
        }

    def _process_message(self, message: AgentMessage) -> Dict:
        """處理來自其他 Agent 的訊息"""
        content = message.content

        if message.message_type == "safety_check":
            # 操作專家請求安全檢查
            return self.analyze(content)

        elif message.message_type == "alert":
            # 接收緊急警報
            return {"status": "alert_received", "action": "initiating_emergency_procedure"}

        return {"status": "message_processed"}


if __name__ == "__main__":
    # 測試安全專家
    agent = SafetyAgent()

    print("=== 安全專家測試 ===\n")

    # 測試安全檢查
    test_data = {
        "proposed_action": "開啟腔體檢查密封圈",
        "current_state": {},
        "fault_type": "vacuum_leak",
        "severity": "HIGH"
    }

    analysis = agent.analyze(test_data)
    print(f"操作安全性: {'✓ 安全' if analysis['is_safe'] else '✗ 不安全'}")
    print(f"風險等級: {analysis['risk_level']}")
    print(f"\n所需防護裝備:")
    for ppe in analysis['required_ppe']:
        print(f"  • {ppe}")

    print(f"\n安全建議:")
    for rec in analysis['safety_recommendations']:
        print(f"  {rec}")

    # 測試決策
    decision = agent.make_decision(analysis)
    print(f"\n決策結果: {decision['decision']}")
    print(f"原因: {decision['reason']}")
