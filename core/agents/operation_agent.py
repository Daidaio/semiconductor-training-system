"""
操作專家 Agent
負責提供操作指引、步驟建議
"""

from typing import Dict, List
from .base_agent import BaseAgent, AgentMessage


class OperationAgent(BaseAgent):
    """操作專家 - 負責提供詳細的操作步驟與指引"""

    def __init__(self):
        super().__init__(agent_name="OperationAgent", role="Equipment Operation Expert")

        # 建立操作程序知識庫
        self.knowledge_base = self._build_operation_knowledge_base()

    def _build_operation_knowledge_base(self) -> Dict:
        """建立操作程序知識庫"""
        return {
            "vacuum_leak": {
                "procedure": [
                    "1. 執行緊急停機程序 (按下 E-STOP 按鈕)",
                    "2. 關閉氣體供應閥門",
                    "3. 等待腔體洩壓至大氣壓",
                    "4. 開啟腔體檢查門",
                    "5. 使用氦氣洩漏檢測器檢查密封面",
                    "6. 更換損壞的密封圈 (O-ring)",
                    "7. 重新組裝並執行真空測試",
                    "8. 確認真空度達到 1e-6 Torr 以下",
                    "9. 執行製程驗證測試"
                ],
                "tools_required": ["氦氣洩漏檢測器", "真空計", "O-ring更換工具包"],
                "safety_precautions": [
                    "確保腔體完全洩壓後才開啟",
                    "佩戴防護手套",
                    "避免在密封面留下指紋或污染"
                ],
                "estimated_time": "3-4 hours"
            },
            "temperature_spike": {
                "procedure": [
                    "1. 降低加熱器功率至 50%",
                    "2. 啟動緊急冷卻程序",
                    "3. 監控溫度下降趨勢",
                    "4. 檢查冷卻水流量 (應 > 5 LPM)",
                    "5. 檢查溫控器設定值",
                    "6. 校驗溫度感測器讀數 (使用標準測溫儀)",
                    "7. 檢查加熱器電流是否正常",
                    "8. 執行溫控系統自我診斷",
                    "9. 逐步恢復正常溫度"
                ],
                "tools_required": ["標準測溫儀", "電流錶", "冷卻水流量計"],
                "safety_precautions": [
                    "避免急速冷卻造成熱應力",
                    "確認冷卻系統運作正常",
                    "監控相鄰模組溫度"
                ],
                "estimated_time": "1-2 hours"
            },
            "alignment_drift": {
                "procedure": [
                    "1. 暫停當前製程",
                    "2. 執行對準校正程序",
                    "3. 使用校正片進行光學對準",
                    "4. 調整 X/Y/θ 三軸至規格內",
                    "5. 檢查振動監測器讀數",
                    "6. 清潔對準鏡頭",
                    "7. 執行重複性測試 (10次)",
                    "8. 記錄對準誤差數據",
                    "9. 確認精度在 ±50nm 以內"
                ],
                "tools_required": ["校正片", "光學顯微鏡", "振動監測器"],
                "safety_precautions": [
                    "避免碰觸光學元件表面",
                    "使用無塵布清潔",
                    "確保環境溫度穩定"
                ],
                "estimated_time": "30-60 minutes"
            },
            "optical_intensity_drop": {
                "procedure": [
                    "1. 測量光源輸出功率",
                    "2. 檢查光源使用時數",
                    "3. 清潔光路中所有鏡片",
                    "4. 檢查光闌開度設定",
                    "5. 測量曝光劑量均勻性",
                    "6. 若光源老化,安排更換計劃",
                    "7. 調整曝光時間補償",
                    "8. 執行測試片曝光驗證",
                    "9. 確認CD均勻性在規格內"
                ],
                "tools_required": ["功率計", "光學清潔套件", "測試片"],
                "safety_precautions": [
                    "關閉光源後等待冷卻",
                    "佩戴防UV眼鏡",
                    "避免直視光源"
                ],
                "estimated_time": "1-2 hours"
            },
            "electrical_fluctuation": {
                "procedure": [
                    "1. 記錄電壓/電流波形",
                    "2. 檢查電源供應器狀態指示燈",
                    "3. 測量輸入電壓穩定性",
                    "4. 檢查接地電阻 (應 < 1Ω)",
                    "5. 檢查電源線路連接",
                    "6. 使用頻譜分析儀檢測EMI",
                    "7. 隔離可能的干擾源",
                    "8. 必要時更換電源供應器",
                    "9. 執行系統重啟測試"
                ],
                "tools_required": ["示波器", "頻譜分析儀", "接地電阻測試儀"],
                "safety_precautions": [
                    "執行前關閉主電源",
                    "使用絕緣工具",
                    "確認無帶電部件"
                ],
                "estimated_time": "2-3 hours"
            }
        }

    def analyze(self, data: Dict) -> Dict:
        """
        分析操作需求

        Args:
            data: {
                "fault_type": "...",
                "severity": "...",
                "student_level": "beginner/intermediate/advanced"
            }

        Returns:
            操作指引
        """
        fault_type = data.get("fault_type", "unknown")
        severity = data.get("severity", "MEDIUM")
        student_level = data.get("student_level", "beginner")

        if fault_type not in self.knowledge_base:
            return {
                "error": f"Unknown fault type: {fault_type}",
                "available_procedures": list(self.knowledge_base.keys())
            }

        procedure_data = self.knowledge_base[fault_type]

        # 根據學員程度調整指引詳細度
        detailed_steps = self._adjust_for_level(
            procedure_data["procedure"],
            student_level
        )

        return {
            "fault_type": fault_type,
            "severity": severity,
            "procedure_steps": detailed_steps,
            "tools_required": procedure_data["tools_required"],
            "safety_precautions": procedure_data["safety_precautions"],
            "estimated_time": procedure_data["estimated_time"],
            "difficulty_level": self._assess_difficulty(fault_type, severity)
        }

    def _adjust_for_level(self, steps: List[str], level: str) -> List[str]:
        """根據學員程度調整步驟詳細度"""
        if level == "beginner":
            # 新手：提供詳細說明
            return steps
        elif level == "intermediate":
            # 中級：保持原樣
            return steps
        else:  # advanced
            # 進階：簡化步驟
            return [step.split(".")[1].strip() for step in steps]

    def _assess_difficulty(self, fault_type: str, severity: str) -> str:
        """評估操作難度"""
        difficulty_matrix = {
            "alignment_drift": "EASY",
            "optical_intensity_drop": "MEDIUM",
            "electrical_fluctuation": "MEDIUM",
            "temperature_spike": "HARD",
            "vacuum_leak": "HARD"
        }

        base_difficulty = difficulty_matrix.get(fault_type, "MEDIUM")

        # 嚴重程度影響難度
        if severity == "CRITICAL":
            if base_difficulty == "EASY":
                return "MEDIUM"
            elif base_difficulty == "MEDIUM":
                return "HARD"

        return base_difficulty

    def make_decision(self, analysis_result: Dict) -> Dict:
        """
        基於分析結果提供操作決策

        Args:
            analysis_result: analyze() 的輸出

        Returns:
            操作建議
        """
        return {
            "action": "execute_procedure",
            "procedure": analysis_result.get("procedure_steps", []),
            "checkpoints": self._generate_checkpoints(analysis_result),
            "estimated_completion_time": analysis_result.get("estimated_time", "Unknown")
        }

    def _generate_checkpoints(self, analysis_result: Dict) -> List[Dict]:
        """生成操作檢查點"""
        steps = analysis_result.get("procedure_steps", [])
        checkpoints = []

        # 每 3 步設置一個檢查點
        for i in range(0, len(steps), 3):
            checkpoints.append({
                "checkpoint_id": f"CP{i//3 + 1}",
                "after_step": min(i + 3, len(steps)),
                "verification": f"確認步驟 {i+1}-{min(i+3, len(steps))} 已正確完成",
                "can_proceed": True
            })

        return checkpoints

    def provide_hint(self, step_number: int, fault_type: str) -> Dict:
        """
        提供特定步驟的提示

        Args:
            step_number: 步驟編號
            fault_type: 故障類型

        Returns:
            提示資訊
        """
        hints = {
            "vacuum_leak": {
                5: "提示: 氦氣洩漏檢測器應調整到最高靈敏度,沿著密封面緩慢移動",
                6: "提示: 更換O-ring時,確保溝槽清潔無異物,塗抹真空油脂"
            },
            "temperature_spike": {
                6: "提示: 標準測溫儀探頭應接觸到晶圓表面,等待讀數穩定",
                7: "提示: 正常加熱器電流應在 15-20A 範圍內"
            },
            "alignment_drift": {
                4: "提示: 調整順序為 X → Y → θ,每次調整後重新確認",
                7: "提示: 重複性測試應使用相同校正點,記錄誤差標準差"
            }
        }

        fault_hints = hints.get(fault_type, {})
        hint = fault_hints.get(step_number, "目前無額外提示,請參考標準操作程序")

        return {
            "step_number": step_number,
            "hint": hint,
            "has_hint": step_number in fault_hints
        }

    def validate_action(self, action: str, context: Dict) -> Dict:
        """
        驗證學員操作是否正確

        Args:
            action: 學員執行的動作
            context: 當前情境

        Returns:
            驗證結果
        """
        expected_step = context.get("expected_step", "")
        fault_type = context.get("fault_type", "")

        # 簡化版驗證邏輯
        is_correct = action.lower() in expected_step.lower()

        return {
            "is_correct": is_correct,
            "expected": expected_step,
            "actual": action,
            "feedback": "正確!" if is_correct else f"不正確,應該: {expected_step}",
            "allow_retry": not is_correct
        }

    def _process_message(self, message: AgentMessage) -> Dict:
        """處理來自其他 Agent 的訊息"""
        content = message.content

        if message.message_type == "query":
            # 診斷專家請求操作建議
            return self.analyze(content)

        elif message.message_type == "validation_request":
            # 安全專家請求驗證操作安全性
            return {"status": "validation_pending"}

        return {"status": "message_processed"}


if __name__ == "__main__":
    # 測試操作專家
    agent = OperationAgent()

    print("=== 操作專家測試 ===\n")

    # 測試操作指引生成
    test_data = {
        "fault_type": "vacuum_leak",
        "severity": "HIGH",
        "student_level": "beginner"
    }

    analysis = agent.analyze(test_data)
    print(f"故障類型: {analysis['fault_type']}")
    print(f"難度等級: {analysis['difficulty_level']}")
    print(f"預估時間: {analysis['estimated_time']}\n")

    print("操作步驟:")
    for step in analysis['procedure_steps'][:5]:  # 只顯示前5步
        print(f"  {step}")

    print(f"\n所需工具: {', '.join(analysis['tools_required'])}")

    # 測試提示功能
    print("\n提示測試:")
    hint = agent.provide_hint(5, "vacuum_leak")
    print(f"  步驟 5 提示: {hint['hint']}")
